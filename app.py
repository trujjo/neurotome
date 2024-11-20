from flask import Flask, jsonify, request
from flask_cors import CORS
from neo4j import GraphDatabase
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

class NeuroanatomyDatabase:
    def __init__(self):
        self.uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
        self.user = "neo4j"
        self.password = "Poconoco16!"
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def get_all_labels(self):
        """Get all available node labels from the database"""
        with self.driver.session() as session:
            result = session.run("CALL db.labels()")
            return [record["label"] for record in result]

    def get_all_relationship_types(self):
        """Get all relationship types from the database"""
        with self.driver.session() as session:
            result = session.run("CALL db.relationshipTypes()")
            return [record["relationshipType"] for record in result]

    def function1_dynamic_filter(self, label: str = None, location: str = None, 
                               sublocation: str = None, relationship: str = None) -> List[Dict]:
        """Dynamic filtering system that builds visualization based on selected criteria"""
        with self.driver.session() as session:
            # Base query
            query = "MATCH (n)"
            params = {}
            
            # Add label filter if provided
            if label:
                labels = label.split(',')
                label_conditions = []
                for i, l in enumerate(labels):
                    if l:
                        label_conditions.append(f"n:`{l}`")
                if label_conditions:
                    query += " WHERE " + " OR ".join(label_conditions)

            # Add relationship filter if provided
            if relationship:
                rel_types = relationship.split(',')
                rel_conditions = []
                for rel in rel_types:
                    if rel:
                        rel_conditions.append(f"type(r) = '{rel}'")
                if rel_conditions:
                    query += f" MATCH (n)-[r]->(m) WHERE " + " OR ".join(rel_conditions)
            else:
                query += " MATCH (n)-[r]->(m)"

            # Add LIMIT to prevent overwhelming response
            query += " RETURN n, r, m LIMIT 100"
            
            result = session.run(query)
            nodes = {}
            links = []
            
            for record in result:
                source = record['n']
                target = record['m']
                rel = record['r']
                
                # Add source node if not already added
                if source.id not in nodes:
                    nodes[source.id] = {
                        'id': source.id,
                        'labels': list(source.labels),
                        'properties': dict(source)
                    }
                
                # Add target node if not already added
                if target.id not in nodes:
                    nodes[target.id] = {
                        'id': target.id,
                        'labels': list(target.labels),
                        'properties': dict(target)
                    }
                
                # Add relationship
                links.append({
                    'source': source.id,
                    'target': target.id,
                    'type': type(rel).__name__,
                    'properties': dict(rel)
                })
            
            return {
                'nodes': list(nodes.values()),
                'links': links
            }

    def search_nodes(self, search_term: str) -> Dict[str, List]:
        """Search for nodes containing the search term in their properties"""
        with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $search)
            WITH n
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(distinct n) as nodes, collect(distinct r) as rels, collect(distinct m) as targets
            """
            result = session.run(query, search=search_term)
            record = result.single()
            
            if not record:
                return {'nodes': [], 'links': []}
            
            nodes = {}
            links = []
            
            # Process nodes
            for node in record['nodes']:
                nodes[node.id] = {
                    'id': node.id,
                    'labels': list(node.labels),
                    'properties': dict(node)
                }
            
            # Process relationships and target nodes
            for i, rel in enumerate(record['rels']):
                if rel is not None:
                    target = record['targets'][i]
                    if target.id not in nodes:
                        nodes[target.id] = {
                            'id': target.id,
                            'labels': list(target.labels),
                            'properties': dict(target)
                        }
                    
                    links.append({
                        'source': rel.start_node.id,
                        'target': rel.end_node.id,
                        'type': type(rel).__name__,
                        'properties': dict(rel)
                    })
            
            return {
                'nodes': list(nodes.values()),
                'links': links
            }

db = NeuroanatomyDatabase()

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Get all available node labels and relationship types"""
    try:
        labels = db.get_all_labels()
        relationship_types = db.get_all_relationship_types()
        return jsonify({
            'labels': labels,
            'relationshipTypes': relationship_types
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filter', methods=['GET'])
def filter_nodes():
    label = request.args.get('label')
    location = request.args.get('location')
    sublocation = request.args.get('sublocation')
    relationship = request.args.get('relationship')
    search = request.args.get('search')
    
    try:
        if search:
            results = db.search_nodes(search)
        else:
            results = db.function1_dynamic_filter(label, location, sublocation, relationship)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
