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

            INSERT OR IGNORE INTO graphs (id, name) 
            SELECT 1, 'Default Graph'
            WHERE NOT EXISTS (SELECT 1 FROM graphs WHERE id = 1);

            COMMIT;
        ''')
        
        db.commit()
    return db


@app.post(API_PREFIX + '/graphs/<graphId>/nodes')
def addNode(graphId):
    data = request.json
    name = data.get('name')
    pos_x = data.get('pos_x')
    pos_y = data.get('pos_y')
    
    cur = get_db().cursor()
    cur.execute("BEGIN;")
    res = cur.execute("SELECT COUNT(id) FROM nodes WHERE graph = ? AND name = ?", (graphId, name))
    if res.fetchone()[0] != 0:
        cur.execute("ROLLBACK;")
        cur.close()
        get_db().commit()
        return ("Node with that name already exists", 400)
    cur.execute('''
    INSERT INTO nodes (graph, name, pos_x, pos_y) VALUES (?, ?, ?, ?);
    ''', (graphId, name, pos_x, pos_y))
    newNodeId = cur.lastrowid
    cur.execute("COMMIT;")
    get_db().commit()
    cur.close()
    return {
        'id': newNodeId
    }

@app.delete(API_PREFIX + '/nodes/<nodeId>')
def delNode(nodeId):
    owner = request.args.get('owner')
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM nodes WHERE id = ? AND owner = ?;
    ''', (nodeId, owner))
    get_db().commit()
    return ('', 204)

@app.delete(API_PREFIX + '/graphs/<graphId>')
def clearGraph(graphId):
    cur = get_db().cursor()
    cur.execute('''BEGIN;''')
    cur.execute('''DELETE FROM nodes WHERE graph = ?;''', (graphId,))
    cur.execute('''DELETE FROM edges WHERE graph = ?;''', (graphId,))
    cur.execute('''DELETE FROM graphs WHERE id = ?;''', (graphId,))
    cur.execute('''COMMIT;''')
    get_db().commit()
    cur.close()
    return ('', 204)

@app.put(API_PREFIX + '/graphs/<graphId>/nodes/<nodeId>')
def updateNode(graphId, nodeId):
    data = request.json
    cur = get_db().cursor()
    cur.execute("""
        UPDATE nodes
        SET pos_x = ?, pos_y = ?
        WHERE id = ? AND graph = ?;
    """, (data['x'], data['y'], nodeId, graphId))
    get_db().commit()
    cur.close()
    return ('', 204)

@app.get(API_PREFIX + '/users/<username>')
def getUser(username):
    cur = get_db().cursor()
    res = cur.execute("""
        SELECT id, username FROM users WHERE username = ?;
    """, (username,))
    row = res.fetchone()
    get_db().commit()
    cur.close()
    if row is None:
        return ("User not found", 404)
    id, username = row
    return {
        'id': id,
        'username': username,
    }

@app.get(API_PREFIX + '/graphs/<graphId>/nodes')
def getNodes(graphId):
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, graph, name, pos_x, pos_y FROM nodes WHERE graph = ?;
    ''', (graphId,))
    nodeList = res.fetchall()
    get_db().commit()
    cur.close()
    if nodeList is None:
        nodeList = []
    nodeList = [{'id': id, 'x': x, 'y': y, 'name': name} 
                for id, _, name, x, y in nodeList]
    return {'nodes': nodeList}

@app.get(API_PREFIX + '/graphs/<graphId>/edges')
def getEdges(graphId):
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, graph, src, dst FROM edges WHERE graph = ?;
    ''', (graphId,))
    edgeList = res.fetchall()
    get_db().commit()
    cur.close()
    if edgeList is None:
        edgeList = []
    edgeList = [{'id': edgeId, 'src': src, 'dst': dst} 
                for edgeId, _, src, dst in edgeList]
    return {'edges': edgeList}

@app.get(API_PREFIX + '/graphs/<graphId>')
def getNodesAndEdges(graphId):
    nodes = getNodes(graphId)
    edges = getEdges(graphId)
    if isinstance(nodes, tuple):
        return nodes
    if isinstance(edges, tuple):
        return edges
    return {
        'nodes': nodes['nodes'],
        'edges': edges['edges']
    }

@app.post(API_PREFIX + '/users')
def addUser():
    data = request.json
    cur = get_db().cursor()
    try:
        cur.execute('''
            INSERT INTO users (username, password) VALUES (?, ?);
        ''', (data['username'], data['password']))
        get_db().commit()
    except sqlite3.Error:
        return ("Error inserting in database", 500)
    get_db().commit()
    cur.close()
    return ('', 201)

@app.post(API_PREFIX + '/graphs')
def addGraph():
    data = request.json
    name = data.get('name')
    owner = data.get('owner')
    cur = get_db().cursor()
    cur.execute('''
        INSERT INTO graphs (name, owner) VALUES (?, ?);
    ''', (name, owner))
    get_db().commit()
    cur.close()
    return ('', 201)

@app.delete(API_PREFIX + '/users/<username>')
def delUser(username):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM users WHERE username = ?;
    ''', (username))
    get_db().commit()
    cur.close()
    return ('', 204)

@app.delete(API_PREFIX + '/graphs/<graphId>')
def delGraph(graphId):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM graphs WHERE id = ?;
    ''', (graphId))
    get_db().commit()
    cur.close()
    return ('', 204)

# @app.delete(API_PREFIX + '/graphs')
# def clearAllGraphs():
#     cur = get_db().cursor()
#     cur.execute('''
#         DELETE FROM graphs WHERE owner = ?
#     ''', (owner,))
#     get_db().commit()
#     return ('', 204)

@app.post(API_PREFIX + '/graphs/<graphId>/edges')
def addEdge(graphId):
    data = request.json
    src = data.get('src')
    dst = data.get('dst')
    
    cur = get_db().cursor()
    cur.execute("BEGIN;")
    res = cur.execute("SELECT COUNT(id) FROM edges WHERE graph = ? AND src = ? AND dst = ?;", 
                     (graphId, src, dst))
    if res.fetchone()[0] != 0:
        cur.execute("ROLLBACK;")
        get_db().commit()
        cur.close()
        return ('Edge already exists', 400)
    
    cur.execute('''
    INSERT INTO edges (graph, src, dst) VALUES (?, ?, ?);
    ''', (graphId, src, dst))
    new_id = cur.lastrowid
    cur.execute("COMMIT;")
    get_db().commit()
    cur.close()
    return ({ 'id': new_id }, 201)

@app.delete(API_PREFIX + '/edges/<edgeId>')
def delEdge(edgeId):
    cur = get_db().cursor()
    cur.execute('''
        DELETE FROM edges WHERE id = ?;
    ''', (edgeId))
    get_db().commit()
    return ('', 204)

@app.get(API_PREFIX + '/graphs')
def getGraphs():
    # username = request.args.get('username')
    cur = get_db().cursor()
    res = cur.execute('''
        SELECT id, name, owner FROM graphs;
    ''')
    graphList = res.fetchall()
    if graphList is None:
        graphList = []
    graphList = [{'id': graphId, 'name': name, 'owner': owner} 
                 for graphId, name, owner in graphList]
    return {'graphs': graphList}

def exe_query(func, params:tuple = None):
    try:
        con = get_db()
        func(*params) if params != None else func()
        con.commit()
        return('OK', 200)
    except:
        return ('', 400)
    
if __name__ == '__main__':
    app.run(debug=True)