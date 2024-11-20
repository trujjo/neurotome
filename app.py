from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from typing import List, Dict, Any

app = Flask(__name__)

class NeuroanatomyDatabase:
    def __init__(self):
        self.uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
        self.user = "neo4j"
        self.password = "Poconoco16!"
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def function1_dynamic_filter(self, label: str = None, location: str = None, 
                               sublocation: str = None, relationship: str = None) -> List[Dict]:
        """
        Dynamic filtering system that builds visualization based on selected criteria
        """
        with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE 1=1
            """
            
            if label:
                query += f" AND n:`{label}`"
            if location:
                query += f" AND n.location = '{location}'"
            if sublocation:
                query += f" AND n.sublocation = '{sublocation}'"
            
            if relationship:
                query += f" MATCH (n)-[r:`{relationship}`]-(m)"
            else:
                query += " MATCH (n)-[r]-(m)"
                
            query += " RETURN n, r, m LIMIT 100"
            
            result = session.run(query)
            return [record.data() for record in result]

    def function2_diagnostic_analysis(self, lesion_location: str) -> Dict[str, Any]:
        """
        Analyze lesions and determine neurological vs vascular pathologies
        """
        with self.driver.session() as session:
            query = """
            MATCH (l:Lesion {location: $location})
            OPTIONAL MATCH (l)-[r:AFFECTS]->(t:Tract)
            OPTIONAL MATCH (a:Artery)-[s:SUPPLIES]->(tissue:Tissue)
            WHERE a.status = 'occluded' AND tissue.location = $location
            RETURN {
                neurological: collect(DISTINCT t.name),
                vascular: collect(DISTINCT tissue.name)
            } as results
            """
            result = session.run(query, location=lesion_location)
            return result.single()["results"]

    def function3_path_identification(self, start_node_id: str, 
                                    end_node_id: str) -> List[Dict]:
        """
        Identify all possible paths between two nodes
        """
        with self.driver.session() as session:
            query = """
            MATCH paths = allShortestPaths(
                (start)-[*]->(end)
            )
            WHERE id(start) = $start_id AND id(end) = $end_id
            RETURN paths
            """
            result = session.run(query, 
                               start_id=start_node_id, 
                               end_id=end_node_id)
            return [record.data() for record in result]

    def function4_downstream_analysis(self, affected_node_id: str) -> Dict[str, List]:
        """
        Analyze downstream effects with complete and partial loss
        """
        with self.driver.session() as session:
            query = """
            // Complete loss
            MATCH (source) WHERE id(source) = $node_id
            MATCH path = (source)-[:SUPPLIES*]->(affected:Tissue)
            WHERE NOT EXISTS((affected)<-[:SUPPLIES]-(:Artery {status: 'patent'}))
            WITH collect(affected.name) as complete_loss
            
            // Partial loss
            MATCH (source) WHERE id(source) = $node_id
            MATCH path = (source)-[:SUPPLIES*]->(affected:Tissue)
            WHERE EXISTS((affected)<-[:SUPPLIES]-(:Artery {status: 'patent'}))
            AND EXISTS((affected)<-[:SUPPLIES]-(:Artery {status: 'occluded'}))
            WITH complete_loss, collect(affected.name) as partial_loss
            
            RETURN {
                complete_loss: complete_loss,
                partial_loss: partial_loss
            } as results
            """
            result = session.run(query, node_id=affected_node_id)
            return result.single()["results"]

db = NeuroanatomyDatabase()

@app.route('/api/filter', methods=['GET'])
def filter_nodes():
    label = request.args.get('label')
    location = request.args.get('location')
    sublocation = request.args.get('sublocation')
    relationship = request.args.get('relationship')
    try:
        results = db.function1_dynamic_filter(label, location, sublocation, relationship)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/diagnosis', methods=['GET'])
def diagnosis():
    lesion_location = request.args.get('location')
    try:
        results = db.function2_diagnostic_analysis(lesion_location)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/paths', methods=['GET'])
def paths():
    start_node_id = request.args.get('start')
    end_node_id = request.args.get('end')
    try:
        results = db.function3_path_identification(start_node_id, end_node_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/downstream', methods=['GET'])
def downstream():
    affected_node_id = request.args.get('node')
    try:
        results = db.function4_downstream_analysis(affected_node_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)