from flask import Flask, render_template_string, jsonify, request, send_from_directory
from flask_cors import CORS
from neo4j import GraphDatabase
import json
import os

app = Flask(__name__, static_folder='public')
CORS(app)  # Enable CORS for all routes

# Neo4j database connection credentials
NEO4J_URI = "neo4j+s://415ed9b1.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Query function to get dermatomes and myotomes
def get_dermatomes_and_myotomes():
    with driver.session() as session:
        query = """
        MATCH (d:Dermatome)-[:CONNECTED_TO]->(m:Myotome)
        RETURN d.level AS dermatome_level, d.name AS dermatome_name, 
               m.name AS myotome_name, m.level AS myotome_level
        """
        result = session.run(query)
        dermatomes = []
        myotomes = []
        for record in result:
            dermatomes.append({
                "level": record["dermatome_level"],
                "name": record["dermatome_name"]
            })
            myotomes.append({
                "level": record["myotome_level"],
                "name": record["myotome_name"]
            })
        return dermatomes, myotomes

# API endpoint to get all node labels
@app.route("/api/labels")
def get_labels():
    with driver.session() as session:
        query = "CALL db.labels() YIELD label RETURN label ORDER BY label"
        result = session.run(query)
        labels = [record["label"] for record in result]
        return jsonify(labels)

# API endpoint to get all relationship types
@app.route("/api/relationships")
def get_relationships():
    with driver.session() as session:
        query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
        result = session.run(query)
        relationships = [record["relationshipType"] for record in result]
        return jsonify(relationships)

# API endpoint to get nodes by label with pagination
@app.route("/api/nodes/<label>")
def get_nodes_by_label(label):
    limit = request.args.get('limit', 50, type=int)
    skip = request.args.get('skip', 0, type=int)
    
    with driver.session() as session:
        query = f"""
        MATCH (n:`{label}`)
        RETURN n
        ORDER BY id(n)
        SKIP {skip}
        LIMIT {limit}
        """
        result = session.run(query)
        nodes = []
        for record in result:
            node = record["n"]
            node_data = {
                "id": node.id,
                "labels": list(node.labels),
                "properties": dict(node)
            }
            nodes.append(node_data)
        return jsonify(nodes)

# API endpoint to get node count by label
@app.route("/api/nodes/<label>/count")
def get_node_count(label):
    with driver.session() as session:
        query = f"MATCH (n:`{label}`) RETURN count(n) as count"
        result = session.run(query)
        count = result.single()["count"]
        return jsonify({"count": count})

# API endpoint to get relationships for a specific node
@app.route("/api/node/<int:node_id>/relationships")
def get_node_relationships(node_id):
    with driver.session() as session:
        query = """
        MATCH (n)-[r]-(m)
        WHERE id(n) = $node_id
        RETURN n, r, m, type(r) as rel_type
        LIMIT 100
        """
        result = session.run(query, node_id=node_id)
        relationships = []
        for record in result:
            rel_data = {
                "source": {
                    "id": record["n"].id,
                    "labels": list(record["n"].labels),
                    "properties": dict(record["n"])
                },
                "target": {
                    "id": record["m"].id,
                    "labels": list(record["m"].labels),
                    "properties": dict(record["m"])
                },
                "relationship": {
                    "type": record["rel_type"],
                    "properties": dict(record["r"])
                }
            }
            relationships.append(rel_data)
        return jsonify(relationships)

# API endpoint to search nodes by property
@app.route("/api/search")
def search_nodes():
    query_param = request.args.get('q', '')
    property_name = request.args.get('property', 'name')
    limit = request.args.get('limit', 20, type=int)
    
    if not query_param:
        return jsonify([])
    
    with driver.session() as session:
        query = f"""
        MATCH (n)
        WHERE n.{property_name} CONTAINS $query
        RETURN n, labels(n) as labels
        LIMIT {limit}
        """
        result = session.run(query, query=query_param)
        nodes = []
        for record in result:
            node = record["n"]
            node_data = {
                "id": node.id,
                "labels": record["labels"],
                "properties": dict(node)
            }
            nodes.append(node_data)
        return jsonify(nodes)

# API endpoint to get database statistics
@app.route("/api/stats")
def get_database_stats():
    with driver.session() as session:
        # Get node counts by label
        labels_query = """
        CALL db.labels() YIELD label
        CALL {
            WITH label
            MATCH (n)
            WHERE label IN labels(n)
            RETURN count(n) as count
        }
        RETURN label, count
        ORDER BY count DESC
        """
        labels_result = session.run(labels_query)
        label_counts = {record["label"]: record["count"] for record in labels_result}
        
        # Get relationship counts by type
        rels_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        CALL {
            WITH relationshipType
            MATCH ()-[r]->()
            WHERE type(r) = relationshipType
            RETURN count(r) as count
        }
        RETURN relationshipType, count
        ORDER BY count DESC
        """
        rels_result = session.run(rels_query)
        rel_counts = {record["relationshipType"]: record["count"] for record in rels_result}
        
        # Get total counts
        total_nodes_query = "MATCH (n) RETURN count(n) as total_nodes"
        total_rels_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
        
        total_nodes = session.run(total_nodes_query).single()["total_nodes"]
        total_relationships = session.run(total_rels_query).single()["total_relationships"]
        
        return jsonify({
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "labels": label_counts,
            "relationship_types": rel_counts
        })

# API endpoint to get graph data for visualization
@app.route("/api/graph")
def get_graph_data():
    limit = request.args.get('limit', 100, type=int)
    label_filter = request.args.get('label', None)
    
    with driver.session() as session:
        if label_filter:
            query = f"""
            MATCH (n:`{label_filter}`)-[r]-(m)
            RETURN n, r, m
            LIMIT {limit}
            """
        else:
            query = f"""
            MATCH (n)-[r]-(m)
            RETURN n, r, m
            LIMIT {limit}
            """
        
        result = session.run(query)
        nodes = {}
        links = []
        
        for record in result:
            source_node = record["n"]
            target_node = record["m"]
            relationship = record["r"]
            
            # Add source node
            source_id = source_node.id
            if source_id not in nodes:
                nodes[source_id] = {
                    "id": source_id,
                    "labels": list(source_node.labels),
                    "properties": dict(source_node),
                    "name": dict(source_node).get("name", f"Node {source_id}")
                }
            
            # Add target node
            target_id = target_node.id
            if target_id not in nodes:
                nodes[target_id] = {
                    "id": target_id,
                    "labels": list(target_node.labels),
                    "properties": dict(target_node),
                    "name": dict(target_node).get("name", f"Node {target_id}")
                }
            
            # Add relationship
            links.append({
                "source": source_id,
                "target": target_id,
                "type": type(relationship).__name__,
                "properties": dict(relationship)
            })
        
        return jsonify({
            "nodes": list(nodes.values()),
            "links": links
        })

@app.route("/")
def index():
    # Get dermatomes and myotomes data from Neo4j
    dermatomes, myotomes = get_dermatomes_and_myotomes()

    # Define the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spinal Lesion Locator</title>
        <style>
            :root {
                --primary-color: #2196F3;
                --hover-color: #1976D2;
                --background-color: #f5f5f5;
                --border-radius: 8px;
            }

            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background-color);
                margin: 0;
                padding: 0;
            }

            .container {
                display: flex;
                height: 100vh;
            }

            /* Sidebar */
            .sidebar {
                width: 250px;
                background-color: #fff;
                padding: 20px;
                box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
                border-right: 1px solid #ddd;
            }

            .sidebar h2 {
                text-align: center;
                color: var(--primary-color);
            }

            .spinal-level {
                margin: 10px 0;
                padding: 8px;
                background-color: #f5f5f5;
                cursor: pointer;
                border-radius: var(--border-radius);
                transition: background-color 0.3s;
            }

            .spinal-level:hover {
                background-color: var(--primary-color);
                color: white;
            }

            .selected {
                background-color: var(--primary-color);
                color: white;
            }

            /* Right Content Area */
            .content {
                flex-grow: 1;
                padding: 20px;
            }

            .interactive-body {
                height: 500px;
                background-color: #e0e0e0;
                position: relative;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
            }

            .interactive-body .highlight {
                position: absolute;
                width: 50px;
                height: 50px;
                background-color: rgba(33, 150, 243, 0.5);
                border-radius: 50%;
                transition: top 0.3s, left 0.3s;
            }

            /* Spinal Level Section */
            .level-section {
                display: none;
            }

            .level-section.active {
                display: block;
            }

            .modern-button {
                background-color: var(--primary-color);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: var(--border-radius);
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .modern-button:hover {
                background-color: var(--hover-color);
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Sidebar -->
            <div class="sidebar">
                <h2>Spinal Levels</h2>
                <div id="level-list">
                    {% for dermatome in dermatomes %}
                        <div class="spinal-level" data-level="{{ dermatome.level }}">{{ dermatome.level }}: {{ dermatome.name }}</div>
                    {% endfor %}
                </div>
            </div>

            <!-- Right Content Area -->
            <div class="content">
                <div class="interactive-body" id="body">
                    <div class="highlight" id="highlight"></div>
                </div>
                <div id="level-content"></div>
                <button class="modern-button" onclick="analyzeLesion()">Analyze Lesion Location</button>
                <div id="results" style="display:none;">
                    <h3>Analysis Results</h3>
                    <div id="result-content"></div>
                </div>
            </div>
        </div>

        <script>
            // Fetch dermatomes and myotomes data from the Flask API
            const dermatomes = {{ dermatomes | tojson }};
            const myotomes = {{ myotomes | tojson }};

            // Attach event listener for the levels
            document.querySelectorAll('.spinal-level').forEach(button => {
                button.addEventListener('click', function() {
                    document.querySelectorAll('.spinal-level').forEach(b => b.classList.remove('selected'));
                    this.classList.add('selected');
                    const level = this.dataset.level;
                    updateBodyVisualization(level);
                });
            });

            function updateBodyVisualization(level) {
                const body = document.getElementById('highlight');
                let position;

                // Define position based on spinal level (dummy positions for demo)
                switch(level) {
                    case 'c1':
                        position = { top: '10%', left: '50%' };
                        break;
                    case 'c2':
                        position = { top: '20%', left: '50%' };
                        break;
                    case 'c3':
                        position = { top: '30%', left: '50%' };
                        break;
                    case 'c4':
                        position = { top: '40%', left: '50%' };
                        break;
                    default:
                        position = { top: '50%', left: '50%' };
                        break;
                }

                body.style.top = position.top;
                body.style.left = position.left;
            }

            function analyzeLesion() {
                // Collect and display analysis
                const results = document.getElementById('results');
                const resultContent = document.getElementById('result-content');
                resultContent.innerHTML = '<p>Analysis based on selected lesions will appear here.</p>';
                results.style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

    return render_template_string(html_content, dermatomes=dermatomes, myotomes=myotomes)

# Route for database explorer
@app.route("/explorer")
def explorer():
    return send_from_directory('public', 'explorer.html')

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('public', filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)