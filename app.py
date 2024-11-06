from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import json

app = Flask(__name__)

# Neo4j connection
uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

class UI_Design:
    def __init__(self):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_initial_data(self):
        with self.driver.session() as session:
            # Get all anatomical regions for the dropdown
            locations = session.run("""
                MATCH (n)
                WITH DISTINCT n.location as location
                WHERE location IS NOT NULL
                RETURN location
                ORDER BY location
            """).values()
            
            # Get all node types for filtering
            node_types = session.run("""
                MATCH (n)
                WITH DISTINCT labels(n)[0] as type
                RETURN type
                ORDER BY type
            """).values()
            
            # Get relationship types
            rel_types = session.run("""
                MATCH ()-[r]->()
                WITH DISTINCT type(r) as type
                RETURN type
                ORDER BY type
            """).values()
            
            return {
                'locations': [loc[0] for loc in locations],
                'node_types': [type[0] for type in node_types],
                'relationship_types': [rel[0] for rel in rel_types]
            }

    def close(self):
        self.driver.close()

# Create HTML template
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Anatomical Pathway Explorer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        
        .sidebar {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .main-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .search-box {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .filter-section {
            margin-bottom: 20px;
        }
        
        .filter-section h3 {
            margin-top: 0;
            color: #333;
        }
        
        .visualization {
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .path-info {
            margin-top: 20px;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 4px;
        }
        
        button {
            background-color: #CC5500;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        
        button:hover {
            background-color: #A34400;
        }
        
        select {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .legend {
            margin-top: 20px;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 4px;
        }
    </style>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="filter-section">
                <h3>Source Node</h3>
                <input type="text" id="source-search" class="search-box" placeholder="Search source node...">
                <select id="source-type">
                    <option value="">All Types</option>
                    {% for type in node_types %}
                    <option value="{{ type }}">{{ type }}</option>
                    {% endfor %}
                </select>
                <select id="source-location">
                    <option value="">All Locations</option>
                    {% for location in locations %}
                    <option value="{{ location }}">{{ location }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="filter-section">
                <h3>Target Node</h3>
                <input type="text" id="target-search" class="search-box" placeholder="Search target node...">
                <select id="target-type">
                    <option value="">All Types</option>
                    {% for type in node_types %}
                    <option value="{{ type }}">{{ type }}</option>
                    {% endfor %}
                </select>
                <select id="target-location">
                    <option value="">All Locations</option>
                    {% for location in locations %}
                    <option value="{{ location }}">{{ location }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="filter-section">
                <h3>Relationship Types</h3>
                <select id="relationship-type" multiple>
                    {% for rel in relationship_types %}
                    <option value="{{ rel }}">{{ rel }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <button onclick="findPath()">Find Pathway</button>
            <button onclick="clearVisualization()">Clear</button>
        </div>
        
        <div class="main-content">
            <div id="visualization" class="visualization"></div>
            <div id="path-info" class="path-info">
                <h3>Pathway Information</h3>
                <div id="path-details"></div>
            </div>
            <div class="legend">
                <h3>Legend</h3>
                <!-- Add dynamic legend based on node and relationship types -->
            </div>
        </div>
    </div>
    
    <script>
        // Initialize network visualization
        var container = document.getElementById('visualization');
        var data = {
            nodes: new vis.DataSet([]),
            edges: new vis.DataSet([])
        };
        var options = {
            nodes: {
                shape: 'dot',
                size: 16,
                font: {
                    size: 12
                }
            },
            edges: {
                arrows: 'to',
                smooth: {
                    type: 'cubicBezier'
                }
            },
            physics: {
                stabilization: false,
                barnesHut: {
                    gravitationalConstant: -80000,
                    springConstant: 0.001,
                    springLength: 200
                }
            }
        };
        var network = new vis.Network(container, data, options);
        
        function findPath() {
            // Implement pathway finding logic
            // Make API call to backend to get path between source and target nodes
            // Update visualization with results
        }
        
        function clearVisualization() {
            data.nodes.clear();
            data.edges.clear();
            document.getElementById('path-details').innerHTML = '';
        }
        
        // Add event listeners for search boxes and filters
        // Implement auto-complete functionality
        // Add hover effects for nodes and edges
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    ui = UI_Design()
    data = ui.get_initial_data()
    ui.close()
    return render_template_string(html_template, **data)

@app.route('/api/find_path', methods=['POST'])
def find_path():
    # Implement path finding logic
    pass

if __name__ == '__main__':
    app.run(debug=True)
