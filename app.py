# Create requirements.txt
with open('requirements.txt', 'w') as f:
    f.write("""flask==2.3.3
neo4j==5.26.0
gunicorn==21.2.0""")

# Create app.py
with open('app.py', 'w') as f:
    f.write("""from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import json

app = Flask(__name__)

# Neo4j connection details
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
USER = "neo4j"
PASSWORD = "Poconoco16!"

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def get_stats(self):
        # Get total nodes
        node_query = "MATCH (n) RETURN count(n) as count"
        node_count = self.query(node_query)[0]['count']
        
        # Get relationship types and counts
        rel_query = '''
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        '''
        rel_types = self.query(rel_query)
        
        total_rels = sum(r['count'] for r in rel_types)
        
        return {
            'total_nodes': node_count,
            'total_relationships': total_rels,
            'relationship_types': len(rel_types)
        }
    
    def search_nodes(self, search_term):
        query = '''
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($search_term)
        WITH n
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, type(r) as relationship_type, m
        LIMIT 100
        '''
        results = self.query(query, {'search_term': search_term})
        
        # Process results into visualization format
        nodes = {}
        relationships = []
        
        for record in results:
            # Add source node
            source_node = record['n']
            source_id = source_node['name']
            if source_id not in nodes:
                nodes[source_id] = {
                    'id': source_id,
                    'label': source_node['name'],
                    'location': source_node.get('location', 'unknown')
                }
            
            # Add target node and relationship if present
            if record['m']:
                target_node = record['m']
                target_id = target_node['name']
                if target_id not in nodes:
                    nodes[target_id] = {
                        'id': target_id,
                        'label': target_node['name'],
                        'location': target_node.get('location', 'unknown')
                    }
                
                relationships.append({
                    'from': source_id,
                    'to': target_id,
                    'label': record['relationship_type']
                })
        
        return {
            'nodes': list(nodes.values()),
            'edges': relationships
        }

# Initialize Neo4j connection
neo4j_conn = Neo4jConnection(URI, USER, PASSWORD)

@app.route('/')
def index():
    stats = neo4j_conn.get_stats()
    return render_template('index.html', stats=stats)

@app.route('/search')
def search():
    search_term = request.args.get('term', '')
    if not search_term:
        return jsonify({'nodes': [], 'edges': []})
    
    results = neo4j_conn.search_nodes(search_term)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
""")

# Create templates directory and index.html
import os
os.makedirs('templates', exist_ok=True)

with open('templates/index.html', 'w') as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Neo4j Database Dashboard</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2d333b;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .card {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            flex: 1;
            margin: 0 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #2d333b;
        }
        .search-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-bar {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .search-button {
            padding: 10px 20px;
            background-color: #2d333b;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .search-button:hover {
            background-color: #404854;
        }
        #visualization {
            height: 600px;
            border: 1px solid #ddd;
            background-color: white;
            border-radius: 8px;
        }
        .legend {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .legend-item {
            margin: 5px 0;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 8px;
            vertical-align: middle;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Neo4j Database Dashboard</h1>
            <p>Connected to: neo4j+s://4e5eeae5.databases.neo4j.io:7687</p>
        </div>

        <div class="search-container">
            <input type="text" id="searchInput" class="search-bar" placeholder="Search nodes (e.g., 'right suprahyoid muscles')">
            <button onclick="searchNodes()" class="search-button">Search</button>
            <button onclick="clearVisualization()" class="search-button" style="background-color: #dc3545;">Clear</button>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_nodes }}</div>
                <div>Total Nodes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.relationship_types }}</div>
                <div>Relationship Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_relationships }}</div>
                <div>Total Relationships</div>
            </div>
        </div>

        <div class="card">
            <h2>Network Visualization</h2>
            <div id="visualization"></div>
        </div>
    </div>

    <script type="text/javascript">
        // Initialize network visualization
        let nodes = new vis.DataSet([]);
        let edges = new vis.DataSet([]);
        
        const container = document.getElementById('visualization');
        const data = {
            nodes: nodes,
            edges: edges
        };
        
        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                font: {
                    size: 14
                }
            },
            edges: {
                arrows: 'to',
                font: {
                    size: 12,
                    align: 'middle'
                },
                color: {
                    color: '#848484',
                    highlight: '#848484'
                }
            },
            physics: {
                stabilization: true,
                barnesHut: {
                    gravitationalConstant: -80000,
                    springConstant: 0.001,
                    springLength: 200
                }
            }
        };
        
        const network = new vis.Network(container, data, options);

        function getNodeColor(location) {
            const colors = {
                'neck': '#ff7675',
                'thorax': '#74b9ff',
                'pelvis': '#55efc4',
                'default': '#a8a8a8'
            };
            return colors[location] || colors.default;
        }

        async function searchNodes() {
            const searchTerm = document.getElementById('searchInput').value;
            
            try {
                const response = await fetch(`/search?term=${encodeURIComponent(searchTerm)}`);
                const data = await response.json();
                
                // Clear previous nodes and edges
                nodes.clear();
                edges.clear();
                
                // Add new nodes
                data.nodes.forEach(node => {
                    nodes.add({
                        ...node,
                        color: getNodeColor(node.location)
                    });
                });
                
                // Add new edges
                data.edges.forEach(edge => {
                    edges.add(edge);
                });
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function clearVisualization() {
            nodes.clear();
            edges.clear();
        }

        // Add legend
        const legend = document.createElement('div');
        legend.className = 'legend';
        legend.innerHTML = `
            <div class="legend-item">
                <span class="legend-color" style="background-color: #ff7675;"></span>
                Neck
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #74b9ff;"></span>
                Thorax
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #55efc4;"></span>
                Pelvis
            </div>
        `;
        container.appendChild(legend);
    </script>
</body>
</html>""")

print("Created the following files:")
print("1. requirements.txt")
print("2. app.py")
print("3. templates/index.html")
