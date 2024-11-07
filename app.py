# Write the corrected app.py code
app_code = '''from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import json
import os

app = Flask(__name__)

# Get Neo4j connection details from environment variables or use defaults
URI = os.getenv("NEO4J_URI", "neo4j+s://4e5eeae5.databases.neo4j.io:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "Poconoco16!")

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
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        rel_types = self.query(rel_query)
        
        total_rels = sum(r['count'] for r in rel_types)
        
        return {
            'total_nodes': node_count,
            'total_relationships': total_rels,
            'relationship_types': len(rel_types)
        }
    
    def search_nodes(self, search_term):
        query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($search_term)
        WITH n
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, type(r) as relationship_type, m
        LIMIT 100
        """
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
    try:
        stats = neo4j_conn.get_stats()
        return render_template('index.html', stats=stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    try:
        search_term = request.args.get('term', '')
        if not search_term:
            return jsonify({'nodes': [], 'edges': []})
        
        results = neo4j_conn.search_nodes(search_term)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

# Write the code to app.py
with open('app.py', 'w') as f:
    f.write(app_code)

print("Created corrected app.py with all CSS removed (CSS should be in templates/index.html)")
print("\
Make sure your project structure looks like this:")
print("project/")
print("\u251c\u2500\u2500 app.py")
print("\u251c\u2500\u2500 requirements.txt")
print("\u2514\u2500\u2500 templates/")
print("    \u2514\u2500\u2500 index.html")
