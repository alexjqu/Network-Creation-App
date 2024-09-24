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

    def handle_hover(self, pos):
        if self.isOver(pos):
            self.color = self.hover_color
        else:
            self.color = self.original_color

    def click(self):
        pass  # To be overridden in subclasses

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

    def handle_hover(self, pos):
        if not self.active:
            super().handle_hover(pos)

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
    node_data[f"node{node_count+1}"] = pygame.mouse.get_pos()
    network[f"node{node_count+1}"] = []
    node_count += 1

# Clear all nodes
def clear_all_nodes():
    global node_count, node_data, network
    node_data.clear()
    network.clear()
    node_count = 0

# Variables-------------------
radius = 20
color = (100, 100, 100)
node_data = {}
node_count = 0
network = {}
active_node = None

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
    
    # Draw existing nodes
    for node_pos in node_data.values():
        pygame.draw.circle(screen, color, node_pos, radius)
    
    for event in pygame.event.get():
        pos = pygame.mouse.get_pos()
        
        # Handle hover effect
        for button in all_buttons:
            button.handle_hover(pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in all_buttons:
                if button.isOver(pos):
                    if isinstance(button, ToggleButton):
                        if button.click():
                            toggle_buttons(ToggleButton_list, button)
                    else:
                        button.click()
            
            # Create a node if the create_node_button is active and the click is not on any button
            if create_node_button.get_active() and not any(button.isOver(pos) for button in all_buttons):
                if node_data != {}:
                    # touching_node is True if the mouse position is too close to any existing node
                    touching_node = any(math.hypot(pos[0] - node_pos[0], pos[1] - node_pos[1]) <= radius*2 for node_pos in node_data.values())
                    if not touching_node:
                        create_node(screen, color, pos, radius)
                else:
                    create_node(screen, color, pos, radius)
            
            # Drag and drop button implementation
            if drag_drop_button.get_active():
                for node in node_data:
                    if math.hypot(pos[0] - node_data[node][0], pos[1] - node_data[node][1]) <= radius:
                        active_node = node
                        original_pos = node_data[active_node]
                        break
        
        # Letting go of the node after mouse button 1 is lifted
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # If the new position of the dragged node is over another existing node, return the node to original position
            if any(math.hypot(pos[0] - node_pos[0], pos[1] - node_pos[1]) <= radius*2 
                    for node,node_pos in node_data.items() if node != active_node) and active_node != None:
                node_data[active_node] = original_pos
                active_node = None
            else:
                active_node = None

        # The node follows the mouse position during dragging
        if event.type == pygame.MOUSEMOTION:
            if active_node != None:
                node_data[active_node] = pos

        if event.type == pygame.QUIT: 
            running = False
    
    pygame.display.update()

print(node_data)