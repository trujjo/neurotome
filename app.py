
from flask import Flask, render_template_string, jsonify
from py2neo import Graph
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# HTML template with Bootstrap and interactive features
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Neuronetwork Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { margin-top: 50px; }
        .search-box { margin-bottom: 20px; }
        .refresh-section { margin-bottom: 20px; }
        .last-updated { font-size: 0.9em; color: #666; }
        #graph-container { 
            min-height: 500px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Neuronetwork Explorer</a>
            <div class="d-flex">
                <span class="navbar-text text-light me-3">
                    Last updated: <span id="lastUpdated">Never</span>
                </span>
                <button id="refreshButton" class="btn btn-outline-light">
                    Refresh Data
                </button>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <div class="search-box">
                    <input type="text" class="form-control" placeholder="Search nodes... (Coming soon)">
                </div>
                <div id="graph-container">
                    <h3>Graph Visualization</h3>
                    <div id="visualization-area"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('refreshButton').addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = 'Refreshing...';
            
            fetch('/refresh-data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lastUpdated').textContent = data.timestamp;
                    if (data.success) {
                        // Update visualization here
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error refreshing data. Please try again.');
                })
                .finally(() => {
                    this.disabled = false;
                    this.innerHTML = 'Refresh Data';
                });
        });
    </script>
</body>
</html>
'''

def get_neo4j_data():
    try:
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        query = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100"
        results = graph.run(query).data()
        return True, results
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return False, str(e)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    success, data = get_neo4j_data()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        'success': success,
        'timestamp': timestamp,
        'message': 'Data refreshed successfully' if success else f'Error: {data}'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
