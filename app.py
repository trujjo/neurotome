from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import json

app = Flask(__name__)

def get_neo4j_driver():
    return GraphDatabase.driver(
        "neo4j+s://4e5eeae5.databases.neo4j.io:7687",
        auth=("neo4j", "Poconoco16!")
    )

@app.route('/api/search')
def search():
    search_term = request.args.get('term', '')
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # Query for nodes and their relationships
        query = '''
        MATCH (n)-[r]-(m)
        WHERE n.name =~ $search_term OR m.name =~ $search_term
        RETURN DISTINCT 
            n.name as source_name, 
            labels(n)[0] as source_type,
            n.location as source_location,
            type(r) as relationship,
            m.name as target_name,
            labels(m)[0] as target_type,
            m.location as target_location
        LIMIT 10
        '''
        
        results = session.run(query, search_term=f"(?i).*{search_term}.*")
        records = [dict(record) for record in results]
        
        # Process results into nodes and relationships
        nodes = []
        relationships = []
        node_ids = set()
        
        for record in records:
            # Add source node if not already added
            if record['source_name'] not in node_ids:
                nodes.append({
                    'id': record['source_name'],
                    'name': record['source_name'],
                    'type': record['source_type'],
                    'location': record['source_location']
                })
                node_ids.add(record['source_name'])
            
            # Add target node if not already added
            if record['target_name'] not in node_ids:
                nodes.append({
                    'id': record['target_name'],
                    'name': record['target_name'],
                    'type': record['target_type'],
                    'location': record['target_location']
                })
                node_ids.add(record['target_name'])
            
            # Add relationship
            relationships.append({
                'source': record['source_name'],
                'target': record['target_name'],
                'type': record['relationship']
            })
    
    driver.close()
    return jsonify({'nodes': nodes, 'relationships': relationships})

if __name__ == '__main__':
    app.run(port=5000)
