import sqlite3
from flask import Flask, request, g

API_PREFIX = '/api/v1'
DB_FILE = 'network.db'

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILE)

        db.execute('''
            PRAGMA foreign_keys = ON;
            ''')

        db.executescript('''
            BEGIN;
            CREATE TABLE IF NOT EXISTS graphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner TEXT,
                FOREIGN KEY (owner) REFERENCES users (username) ON DELETE CASCADE
        );

            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph INTEGER,
                name TEXT NOT NULL,
                pos_x INTEGER NOT NULL,
                pos_y INTEGER NOT NULL,
                FOREIGN KEY (graph) REFERENCES graphs (id) ON DELETE CASCADE
        );

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph INTEGER,
                src INTEGER,
                dst INTEGER,
                FOREIGN KEY (graph) REFERENCES graphs (id) ON DELETE CASCADE
                FOREIGN KEY (src) REFERENCES nodes (id) ON DELETE CASCADE
                FOREIGN KEY (dst) REFERENCES nodes (id) ON DELETE CASCADE
        );
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
        );
            COMMIT;
        ''')
        db.commit()
    return db

@app.put(API_PREFIX + '/graphs/<graphId>/nodes/<nodeId>')
def addNode(graphId, name, pos_x, pos_y):
    cur = get_db().cursor()
    cur.execute("BEGIN;")
    res = cur.execute("SELECT COUNT(id) FROM nodes WHERE graph = ? AND name = ?", (graphId, name))
    if res.fetchone()[0] != 0:
        cur.execute("ROLLBACK;")
        cur.close()
        return None
    cur.execute('''
    INSERT INTO nodes (graph, name, pos_x, pos_y) VALUES (?, ?, ?, ?);
    ''', (graphId, name, pos_x, pos_y))
    newNodeId = cur.lastrowid
    cur.execute("COMMIT;")
    cur.close()
    return {
        'id': newNodeId
    }

def delNode(nodeId, owner):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM nodes WHERE id = ?, owner = ?;
    ''', (nodeId, owner))

def clearGraph(graphId):
    cur = get_db().cursor()
    cur.executescript('''
        BEGIN;
        DELETE FROM nodes WHERE graph = ?;
        DELETE FROM edges WHERE graph = ?;
        COMMIT;
    ''', (graphId, graphId))
    cur.close()
    return ("", 200)

@app.put(API_PREFIX + '/graphs/<graphId>/nodes/<nodeId>')
def updateNode(graphId, nodeId):
    data = request.json
    cur = get_db().cursor()
    cur.execute("""
        UPDATE nodes
        SET pos_x = ?, pos_y = ?
        WHERE id = ?, graph = ?;
    """, (data['x'], data['y'], nodeId, graphId))

@app.get(API_PREFIX + '/users/<username>')
def getUser(username):
    cur = get_db().cursor()
    res = cur.execute("""
        SELECT id, username FROM users WHERE username = ?;
    """, (username,))
    row = res.fetchone()
    cur.close()
    if row is None:
        return ("User not found", 404)
    id, username = row
    return {
        'id': id,
        'username': username,
    }

# Make this take multiple nodeIds (with list?? idk)
def getNodes(graphId):
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, graph, name, pos_x, pos_y FROM nodes WHERE graph = ?;
    ''', (graphId,))
    nodeList = res.fetchall()
    if nodeList is None:
        return None
    nodeList = [{'x': x, 'y': y, 'name': name} for x, y, name in nodeList]
    return nodeList

# Same as getNodes, make this take multiple edgeIds
def getEdges(graphId):
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, graph, src, dst FROM nodes WHERE graph = ?;
    ''', (graphId,))
    edgeList = res.fetchall()
    if edgeList is None:
        return None
    edgeList = [{'id': edgeId, 'src':src, 'dst':dst} for edgeId, src, dst in edgeList]
    return edgeList

def getNodesAndEdges(graphId):
    return {
        'nodes': getNodes(graphId),
        'edges': getEdges(graphId)
    }

@app.post(API_PREFIX + '/users/')
def addUser():
    data = request.json
    cur = get_db().cursor()
    try:
        cur.execute('''
            INSERT INTO users (username, password) VALUES (?, ?);
        ''', (data['username'], data['password']))
    except sqlite3.Error:
        return ("Error inserting in database", 500)
    cur.close()
    get_db().commit()
    return ('', 200)

def addGraph(name, owner):
    cur = get_db().cursor()
    cur.execute('''
        INSERT INTO graphs (name, owner) VALUES (?, ?);
''', (name, owner))

def delUser(id, username, password):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM users WHERE id = ?, username = ?, password = ?;
''', (id, username, password))
    
def delGraph(name, owner):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM graphs WHERE name = ?, owner = ?;
''', (name, owner))

def clearAllGraphs(owner):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM graphs where owner = ?
''', (owner,))

def addEdge(id, graph, src, dst):
    cur = get_db().cursor()
    cur.execute("BEGIN;")
    res = cur.execute("SELECT COUNT(id) FROM edges WHERE graph = ? AND src = ? AND dst = ?", (id, src, dst))
    if res.fetchone()[0] != 0:
        cur.execute("ROLLBACK;")
        return None
    cur.execute('''
    INSERT INTO edges (graph, name, pos_x, pos_y) VALUES (?, ?, ?, ?);
    ''', (id, graph, src, dst))
    cur.execute("COMMIT;")
    return(cur.lastrowid)

def delEdge(node):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM edges WHERE src = ? OR dst = ?
''', (node, node))

def getGraphs(username):
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, name, owner FROM graphs WHERE owner = ?;
    ''', (username,))
    graphList = res.fetchall()
    if graphList is None:
        return None
    graphList = [{'id': graphId, 'name':name, 'owner':owner} for graphId, name, owner in graphList]
    return graphList

def exe_query(func, params:tuple = None):
    try:
        con = get_db()
        func(*params) if params != None else func()
        con.commit()
        return('OK', 200)
    except:
        return ('', 400)

print(*(1,2,3,4))

# with app.app_context():
#     addUser('testUser', 'alksjdflkjasf')
#     testUserId = getUser('testUser')['username']
#     addGraph('graph1', testUserId)
#     getGraphs('testUser')