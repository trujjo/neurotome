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

            # Get all relationship types
            rel_query = """
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as type
            """
            rel_result = session.run(rel_query)
            relationship_types = [record["type"] for record in rel_result]

            return {
                "labels": sorted(list(all_labels)),
                "relationship_types": sorted(relationship_types)
            }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        raise

def get_filtered_graph_data(selected_labels=None, selected_relationships=None):
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Build query based on filters
            query = """
            MATCH (n)-[r]->(m)
            WHERE 1=1
            """
            if selected_labels:
                query += f"""
                AND ANY(label IN labels(n) WHERE label IN $labels)
                OR ANY(label IN labels(m) WHERE label IN $labels)
                """
            if selected_relationships:
                query += f"""
                AND type(r) IN $relationships
                """
            query += """
            RETURN 
                id(n) as source_id,
                labels(n) as source_labels,
                properties(n) as source_props,
                id(m) as target_id,
                labels(m) as target_labels,
                properties(m) as target_props,
                type(r) as relationship
            """

            params = {
                "labels": selected_labels or [],
                "relationships": selected_relationships or []
            }

            result = session.run(query, params)
            
            # Format data for vis.js
            nodes = {}
            edges = []
            
            for record in result:
                # Add source node if not exists
                if record["source_id"] not in nodes:
                    nodes[record["source_id"]] = {
                        "id": record["source_id"],
                        "label": record["source_props"].get("name", 
                                record["source_props"].get("title",
                                str(record["source_id"]))),
                        "group": record["source_labels"][0],  # Use first label for grouping
                        "title": f"Labels: {', '.join(record['source_labels'])}<br>" + 
                                "<br>".join(f"{k}: {v}" for k, v in record["source_props"].items())
                    }
                
                # Add target node if not exists
                if record["target_id"] not in nodes:
                    nodes[record["target_id"]] = {
                        "id": record["target_id"],
                        "label": record["target_props"].get("name",
                                record["target_props"].get("title",
                                str(record["target_id"]))),
                        "group": record["target_labels"][0],  # Use first label for grouping
                        "title": f"Labels: {', '.join(record['target_labels'])}<br>" + 
                                "<br>".join(f"{k}: {v}" for k, v in record["target_props"].items())
                    }
                
                # Add edge
                edges.append({
                    "from": record["source_id"],
                    "to": record["target_id"],
                    "label": record["relationship"],
                    "arrows": "to"
                })
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        # Get filter values
        selected_labels = request.args.getlist('labels')
        selected_relationships = request.args.getlist('relationships')
        
        # Get metadata for filters
        metadata = get_metadata()
        
        # Get graph data
        graph_data = get_filtered_graph_data(selected_labels, selected_relationships)
        
        return render_template('index.html',
                             metadata=metadata,
                             graph_data=graph_data,
                             selected_labels=selected_labels,
                             selected_relationships=selected_relationships)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in index route: {error_msg}")
        return render_template('index.html', error=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
