from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging
import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=True
        )
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
            logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_metadata():
    """Get all node labels, locations, sublocations, and relationship types"""
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Get all node labels
            labels_query = """
            MATCH (n)
            RETURN DISTINCT labels(n) as labels
            """
            labels_result = session.run(labels_query)
            all_labels = set()
            for record in labels_result:
                all_labels.update(record["labels"])

            # Get all locations
            locations_query = """
            MATCH (n)
            WHERE n.location IS NOT NULL
            RETURN DISTINCT n.location as location
            """
            locations_result = session.run(locations_query)
            locations = [record["location"] for record in locations_result]

            # Get all sublocations
            sublocations_query = """
            MATCH (n)
            WHERE n.sublocation IS NOT NULL
            RETURN DISTINCT n.sublocation as sublocation
            """
            sublocations_result = session.run(sublocations_query)
            sublocations = [record["sublocation"] for record in sublocations_result]

            # Get all relationship types
            rel_types_query = """
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as relationship_type
            """
            rel_types_result = session.run(rel_types_query)
            relationship_types = [record["relationship_type"] for record in rel_types_result]

            return {
                "labels": sorted(list(all_labels)),
                "locations": sorted(locations),
                "sublocations": sorted(sublocations),
                "relationship_types": sorted(relationship_types)
            }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        raise

def get_graph_data(label=None, location=None, sublocation=None, relationship_type=None):
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Build query based on filters
            query = "MATCH (n)"
            where_clauses = []
            
            if label:
                where_clauses.append(f"'{label}' IN labels(n)")
            if location:
                where_clauses.append("n.location = $location")
            if sublocation:
                where_clauses.append("n.sublocation = $sublocation")
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            if relationship_type:
                query += f" MATCH (n)-[r:{relationship_type}]->()"
                
            query += " RETURN DISTINCT n, labels(n) as labels"
            
            # Parameters for the query
            params = {
                "location": location,
                "sublocation": sublocation
            }
            
            result = session.run(query, params)
            
            data = []
            for record in result:
                node = record["n"]
                data.append({
                    "labels": record["labels"],
                    "properties": dict(node)
                })
            
            return data
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        # Get filter values from request
        selected_label = request.args.get('label', '')
        selected_location = request.args.get('location', '')
        selected_sublocation = request.args.get('sublocation', '')
        selected_relationship_type = request.args.get('relationship_type', '')

        # Get metadata for filters
        metadata = get_metadata()
        
        # Get filtered data
        data = get_graph_data(
            label=selected_label,
            location=selected_location,
            sublocation=selected_sublocation,
            relationship_type=selected_relationship_type
        )

        return render_template('index.html',
                             data=data,
                             metadata=metadata,
                             selected_label=selected_label,
                             selected_location=selected_location,
                             selected_sublocation=selected_sublocation,
                             selected_relationship_type=selected_relationship_type)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in index route: {error_msg}")
        return render_template('index.html', error=error_msg, metadata={})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
