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
        
        # Filter out labels with 0 nodes
        filtered_labels = []
        for label in labels:
            count_query = f"MATCH (n:`{label}`) RETURN count(n) as count"
            count_result = session.run(count_query)
            count = count_result.single()["count"]
            if count > 0:
                filtered_labels.append(label)
        
        return jsonify(filtered_labels)

# API endpoint to get all relationship types
@app.route("/api/relationships")
def get_relationships():
    with driver.session() as session:
        query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
        result = session.run(query)
        relationships = [record["relationshipType"] for record in result]
        
        # Filter out relationship types with 0 relationships
        filtered_relationships = []
        for rel_type in relationships:
            count_query = f"MATCH ()-[r:`{rel_type}`]-() RETURN count(r) as count"
            count_result = session.run(count_query)
            count = count_result.single()["count"]
            if count > 0:
                filtered_relationships.append(rel_type)
        
        return jsonify(filtered_relationships)

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
                "id": node.element_id,
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
                    "id": record["n"].element_id,
                    "labels": list(record["n"].labels),
                    "properties": dict(record["n"])
                },
                "target": {
                    "id": record["m"].element_id,
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
                "id": node.element_id,
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
    relationship_filter = request.args.get('relationships', None)  # Comma-separated list
    
    with driver.session() as session:
        # Build the query based on filters
        if relationship_filter:
            # Parse comma-separated relationship types
            rel_types = [rel.strip() for rel in relationship_filter.split(',') if rel.strip()]
            rel_type_conditions = ' OR '.join([f'type(r) = "{rel_type}"' for rel_type in rel_types])
            
            if label_filter:
                query = f"""
                MATCH (n:`{label_filter}`)-[r]-(m)
                WHERE {rel_type_conditions}
                RETURN n, r, m
                LIMIT {limit}
                """
            else:
                query = f"""
                MATCH (n)-[r]-(m)
                WHERE {rel_type_conditions}
                RETURN n, r, m
                LIMIT {limit}
                """
        elif label_filter:
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
            source_id = source_node.element_id
            if source_id not in nodes:
                nodes[source_id] = {
                    "id": source_id,
                    "labels": list(source_node.labels),
                    "properties": dict(source_node),
                    "name": dict(source_node).get("name", f"Node {source_id}"),
                    "color": "gray"  # Default color for regular graph
                }
            
            # Add target node
            target_id = target_node.element_id
            if target_id not in nodes:
                nodes[target_id] = {
                    "id": target_id,
                    "labels": list(target_node.labels),
                    "properties": dict(target_node),
                    "name": dict(target_node).get("name", f"Node {target_id}"),
                    "color": "gray"  # Default color for regular graph
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

# API endpoint to get all sensation nodes
@app.route("/api/sensations")
def get_sensations():
    with driver.session() as session:
        query = """
        MATCH (s:sensation)
        RETURN s
        ORDER BY s.name
        """
        result = session.run(query)
        sensations = []
        for record in result:
            sensation = record["s"]
            sensation_data = {
                "id": sensation.element_id,
                "name": sensation.get("name", f"Sensation {sensation.element_id}"),
                "properties": dict(sensation)
            }
            sensations.append(sensation_data)
        return jsonify(sensations)

# API endpoint to find intersections between selected sensations
@app.route("/api/sensations/intersections", methods=["POST"])
def find_sensation_intersections():
    data = request.get_json()
    sensation_names = data.get('sensations', [])
    
    if not sensation_names:
        return jsonify({"nodes": [], "links": []})
    
    with driver.session() as session:
        # Find paths between selected sensations and their common pathways
        if len(sensation_names) == 1:
            # For single sensation, show its direct connections
            pathway_query = """
            MATCH (s:sensation)-[r]-(connected)
            WHERE s.name = $sensation_name
            RETURN s, r, connected
            LIMIT 50
            """
            params = {"sensation_name": sensation_names[0]}
            result = session.run(pathway_query, params)
        else:
            # For multiple sensations, find shared pathways between them
            pathway_query = """
            // Find paths between any two selected sensations
            MATCH (s1:sensation), (s2:sensation)
            WHERE s1.name IN $sensation_names AND s2.name IN $sensation_names 
            AND s1.name < s2.name  // Avoid duplicate paths
            
            // Find shortest paths between them (up to length 4)
            MATCH path = shortestPath((s1)-[*1..4]-(s2))
            WHERE ALL(r IN relationships(path) WHERE r IS NOT NULL)
            
            // Return all nodes and relationships in these paths
            UNWIND nodes(path) as n
            UNWIND relationships(path) as r
            RETURN DISTINCT n, r, startNode(r) as source, endNode(r) as target
            LIMIT 200
            """
            params = {"sensation_names": sensation_names}
            result = session.run(pathway_query, params)
        
        nodes = {}
        links = []
        selected_sensation_ids = set()
        
        # Process the pathway results
        for record in result:
            # Handle single sensation case
            if 'connected' in record:
                source_node = record["s"]
                relationship = record["r"] 
                target_node = record["connected"]
            else:
                # Handle pathway case
                node = record["n"]
                relationship = record["r"]
                source_node = record["source"]
                target_node = record["target"]
                
                # Add the intermediate node to our collection
                node_id = node.element_id
                if node_id not in nodes:
                    color = "blue" if 'sensation' in node.labels and node.get("name") in sensation_names else "gray"
                    if 'sensation' in node.labels and node.get("name") in sensation_names:
                        selected_sensation_ids.add(node_id)
                    
                    nodes[node_id] = {
                        "id": node_id,
                        "labels": list(node.labels),
                        "properties": dict(node),
                        "name": dict(node).get("name", f"Node {node_id}"),
                        "color": color
                    }
            
            # Process source and target nodes
            source_id = source_node.element_id
            target_id = target_node.element_id
            
            # Add source node
            if source_id not in nodes:
                color = "blue" if 'sensation' in source_node.labels and source_node.get("name") in sensation_names else "gray"
                if 'sensation' in source_node.labels and source_node.get("name") in sensation_names:
                    selected_sensation_ids.add(source_id)
                
                nodes[source_id] = {
                    "id": source_id,
                    "labels": list(source_node.labels),
                    "properties": dict(source_node),
                    "name": dict(source_node).get("name", f"Node {source_id}"),
                    "color": color
                }
            
            # Add target node  
            if target_id not in nodes:
                color = "blue" if 'sensation' in target_node.labels and target_node.get("name") in sensation_names else "gray"
                if 'sensation' in target_node.labels and target_node.get("name") in sensation_names:
                    selected_sensation_ids.add(target_id)
                
                nodes[target_id] = {
                    "id": target_id,
                    "labels": list(target_node.labels),
                    "properties": dict(target_node),
                    "name": dict(target_node).get("name", f"Node {target_id}"),
                    "color": color
                }
            
            # Add relationship if it doesn't already exist
            link_exists = any(
                (link["source"] == source_id and link["target"] == target_id) or
                (link["source"] == target_id and link["target"] == source_id)
                for link in links
            )
            
            if not link_exists:
                links.append({
                    "source": source_id,
                    "target": target_id,
                    "type": type(relationship).__name__,
                    "properties": dict(relationship)
                })
        
        # Now identify pathway intersection nodes (nodes that appear in multiple paths)
        # These are the key nodes that connect multiple sensations
        pathway_nodes = set()
        for node_id, node_data in nodes.items():
            if node_id not in selected_sensation_ids:  # Not an original sensation
                # Count how many selected sensations this node connects to
                connected_sensations = 0
                for link in links:
                    other_node_id = None
                    if link["source"] == node_id:
                        other_node_id = link["target"]
                    elif link["target"] == node_id:
                        other_node_id = link["source"]
                    
                    if other_node_id and other_node_id in selected_sensation_ids:
                        connected_sensations += 1
                
                # If this node connects to multiple sensations, it's a pathway intersection
                if connected_sensations >= 2 or (len(sensation_names) == 1 and connected_sensations >= 1):
                    nodes[node_id]["color"] = "orange"
                    pathway_nodes.add(node_id)
        
        return jsonify({
            "nodes": list(nodes.values()),
            "links": links
        })

@app.route("/")
def index():
    return send_from_directory('public', 'index.html')

# API endpoint to get dermatomes and myotomes data
@app.route("/api/dermatomes-myotomes")
def get_dermatomes_myotomes_api():
    dermatomes, myotomes = get_dermatomes_and_myotomes()
    return jsonify({
        "dermatomes": dermatomes,
        "myotomes": myotomes
    })

# Route for database explorer
@app.route("/explorer")
def explorer():
    return send_from_directory('public', 'explorer.html')

@app.route("/explorer.html")
def explorer_html():
    return send_from_directory('public', 'explorer.html')

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('public', filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)