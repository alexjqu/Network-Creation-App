import pygame
import math

pygame.init()

background_color = (255, 255, 255) 
 
screen = pygame.display.set_mode((600,600))

pygame.display.set_caption('Network Creation') 

screen.fill(background_color)

pygame.display.flip()

class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.original_color = color
        self.hover_color = tuple(max(0, c - 30) for c in color)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, win, font_size, outline=None):
        if outline:
            pygame.draw.rect(win, outline, (self.x-2, self.y-2, self.width+4, self.height+4), 0)

        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.height), 0)

        if self.text != '':
            font = pygame.font.SysFont('Arial', font_size)
            text = font.render(self.text, 1, (0, 0, 0))
            win.blit(text, (self.x + (self.width/2 - text.get_width()/2), self.y + (self.height/2 - text.get_height()/2)))

    def isOver(self, pos):
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                return True
        return False

    def hover(self, pos):
        if self.isOver(pos):
            self.color = self.hover_color
        else:
            self.color = self.original_color

    def click(self):
        pass  # To be overridden

class ToggleButton(Button):
    def __init__(self, color, x, y, width, height, text=''):
        super().__init__(color, x, y, width, height, text)
        self.active = False
        self.active_color = tuple(max(0, c - 60) for c in color)

    def click(self):
        self.active = not self.active
        if self.active:
            self.color = self.active_color
        else:
            self.color = self.original_color
        return self.active
    
    def get_active(self):
        return self.active
    
    def set_active(self, state):
        self.active = state
        if self.active:
            self.color = self.active_color
        else:
            self.color = self.original_color

    def hover(self, pos):
        if not self.active:
            super().hover(pos)

class ClickButton(Button):
    def __init__(self, color, x, y, width, height, text='', action=None):
        super().__init__(color, x, y, width, height, text)
        self.action = action

    def click(self):
        if self.action:
            self.action()
            
# toggles other buttons off when a button is clicked
def toggle_buttons(buttons, clicked_button):
    for button in buttons:
        if button != clicked_button:
            button.set_active(False)

# Create node
def create_node(surface, color, center, radius):
    global node_count
    pygame.draw.circle(surface=surface, color=color, center=center, radius=radius)
    node_count += 1
    node_data[f"node{node_count}"] = {"pos": pygame.mouse.get_pos(), "highlighted": False}
    network[f"node{node_count}"] = []

# Clear all nodes
def clear_all_nodes():
    global node_count, node_data, network
    node_data.clear()
    network.clear()
    node_count = 0

# New function to highlight a node and create arrows
def connect_node(pos):
    global highlighted_node
    for node, data in node_data.items():
        if math.hypot(pos[0] - data["pos"][0], pos[1] - data["pos"][1]) <= radius:
            if highlighted_node is None:
                data["highlighted"] = True
                highlighted_node = node
            else:
                if highlighted_node != node:
                    if node not in network[highlighted_node]:
                        network[highlighted_node].append(node)
                node_data[highlighted_node]["highlighted"] = False
                highlighted_node = None
            return True
    return False

# Function to draw arrows
def draw_arrow(screen, start, end, color, width=2, arrow_size=10):
    # Angle of the line
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    
    # Start point of the line (at the edge of the start circle)
    start_x = start[0] + radius * math.cos(angle)
    start_y = start[1] + radius * math.sin(angle)
    
    # End point of the line (at the edge of the end circle)
    end_x = end[0] - radius * math.cos(angle)
    end_y = end[1] - radius * math.sin(angle)
    
    # Draw the line
    pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), width)
    
    # Arrow head points
    arrow_point1 = (end_x - arrow_size * math.cos(angle - math.pi/6),
                    end_y - arrow_size * math.sin(angle - math.pi/6))
    arrow_point2 = (end_x - arrow_size * math.cos(angle + math.pi/6),
                    end_y - arrow_size * math.sin(angle + math.pi/6))
    
    # Draw the arrow head
    pygame.draw.polygon(screen, color, [arrow_point1, arrow_point2, (end_x, end_y)])

# Variables-------------------
radius = 20
color = (100, 100, 100)
highlight_color = (255, 0, 0)
node_data = {}
node_count = 0
network = {}
active_node = None
highlighted_node = None

# Create buttons
create_node_button = ToggleButton((180, 180, 180), 0, 0, 60, 30, text='Create')
drag_drop_button = ToggleButton((180, 180, 180), 60, 0, 60, 30, text='Drag')
clear_all_button = ClickButton((180, 180, 180), 120, 0, 60, 30, text='Clear', action=clear_all_nodes)

ToggleButton_list = [create_node_button, drag_drop_button]
click_buttons_list = [clear_all_button]
all_buttons = ToggleButton_list + click_buttons_list

# Main loop
running = True
while running:

    screen.fill(background_color)

    # Draw buttons
    for button in all_buttons:
        button.draw(screen, 15, outline=None)
    
    # Draw existing nodes and arrows
    for node, data in node_data.items():
        node_color = highlight_color if data["highlighted"] else color
        pygame.draw.circle(screen, node_color, data["pos"], radius)
        for connected_node in network[node]:
            draw_arrow(screen, data["pos"], node_data[connected_node]["pos"], (0, 0, 0))
    
    for event in pygame.event.get():
        pos = pygame.mouse.get_pos()
        
        # Handle hover effect
        for button in all_buttons:
            button.hover(pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in all_buttons:
                if button.isOver(pos):
                    if isinstance(button, ToggleButton):
                        if button.click():
                            toggle_buttons(ToggleButton_list, button)
                    else:
                        button.click()
            
            # Create a node or highlight/connect nodes if the create_node_button is active
            if create_node_button.get_active() and not any(button.isOver(pos) for button in all_buttons):
                if not connect_node(pos):
                    if node_data != {}:
                        touching_node = any(math.hypot(pos[0] - data["pos"][0], pos[1] - data["pos"][1]) <= radius*2 for data in node_data.values())
                        if not touching_node:
                            create_node(screen, color, pos, radius)
                    else:
                        create_node(screen, color, pos, radius)
            
            # Drag and drop button implementation
            if drag_drop_button.get_active():
                for node, data in node_data.items():
                    if math.hypot(pos[0] - data["pos"][0], pos[1] - data["pos"][1]) <= radius:
                        active_node = node
                        original_pos = data["pos"]
                        break
        
        # Letting go of the node after mouse button 1 is lifted
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if any(math.hypot(pos[0] - data["pos"][0], pos[1] - data["pos"][1]) <= radius*2 
                    for node, data in node_data.items() if node != active_node) and active_node != None:
                node_data[active_node]["pos"] = original_pos
                active_node = None
            else:
                active_node = None

        # The node follows the mouse position during dragging
        if event.type == pygame.MOUSEMOTION:
            if active_node != None:
                node_data[active_node]["pos"] = pos

        if event.type == pygame.QUIT: 
            running = False
    
    pygame.display.update()

print(node_data)
print(network)