
from flask import Flask, render_template_string, jsonify
from py2neo import Graph
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import logging
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://4e5eeae5.databases.neo4j.io:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

# Create SSL context for secure connection
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_neo4j_connection():
    try:
        logger.info(f"Attempting to connect to Neo4j at {NEO4J_URI}")
        graph = Graph(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            secure=True,
            verify=True
        )
        # Test the connection
        graph.run("MATCH (n) RETURN count(n) LIMIT 1").data()
        logger.info("Successfully connected to Neo4j")
        return graph
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_neo4j_data():
    try:
        graph = get_neo4j_connection()
        
        # Query to get nodes and relationships
        query = '''
        MATCH (n)-[r]->(m)
        RETURN DISTINCT 
            id(n) as source_id, 
            labels(n) as source_labels,
            properties(n) as source_props,
            type(r) as relationship_type,
            id(m) as target_id,
            labels(m) as target_labels,
            properties(m) as target_props
        LIMIT 100
        '''
        
        logger.info("Executing Neo4j query")
        results = graph.run(query).data()
        logger.info(f"Query returned {len(results)} results")
        
        # Process results into vis.js format
        nodes = {}
        edges = []
        
        for record in results:
            # Process source node
            source_id = str(record['source_id'])
            if source_id not in nodes:
                nodes[source_id] = {
                    'id': source_id,
                    'label': record['source_labels'][0],
                    'properties': record['source_props'],
                    'color': '#97c2fc'
                }
            
            # Process target node
            target_id = str(record['target_id'])
            if target_id not in nodes:
                nodes[target_id] = {
                    'id': target_id,
                    'label': record['target_labels'][0],
                    'properties': record['target_props'],
                    'color': '#97c2fc'
                }
            
            # Process relationship
            edges.append({
                'from': source_id,
                'to': target_id,
                'label': record['relationship_type'],
                'arrows': 'to'
            })
        
        graph_data = {
            'nodes': list(nodes.values()),
            'edges': edges
        }
        
        return True, graph_data
    except Exception as e:
        logger.error(f"Error in get_neo4j_data: {str(e)}")
        return False, str(e)

# [Previous HTML template code remains the same]

<!DOCTYPE html>
<html>
<head>
    <title>Neo4j Graph Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { margin-top: 50px; }
        .search-box { margin-bottom: 20px; }
        .refresh-section { margin-bottom: 20px; }
        .last-updated { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Neo4j Graph Explorer</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <div class="refresh-section">
                    <button id="refreshButton" class="btn btn-primary">Refresh Data</button>
                    <p class="last-updated">Last updated: <span id="lastUpdated">Never</span></p>
                </div>
                <div class="search-box">
                    <input type="text" class="form-control" placeholder="Search nodes... (Coming soon)">
                </div>
                <div id="graph-container">
                    <h3>Graph Visualization</h3>
# [Previous HTML template code remains the same]

<!DOCTYPE html>
<html>
<head>
    <title>Neo4j Graph Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { margin-top: 50px; }
        .search-box { margin-bottom: 20px; }
        .refresh-section { margin-bottom: 20px; }
        .last-updated { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Neo4j Graph Explorer</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <div class="refresh-section">
                    <button id="refreshButton" class="btn btn-primary">Refresh Data</button>
                    <p class="last-updated">Last updated: <span id="lastUpdated">Never</span></p>
                </div>
                <div class="search-box">
                    <input type="text" class="form-control" placeholder="Search nodes... (Coming soon)">
                </div>
                <div id="graph-container">
                    <h3>Graph Visualization</h3>


@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    success, data = get_neo4j_data()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {
        'success': success,
        'timestamp': timestamp,
        'message': 'Data refreshed successfully' if success else f'Error: {data}',
        'graph_data': data if success else None
    }
    logger.info(f"Refresh data response: {response_data['message']}")
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
