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
                # Modified query: Only show connections between nodes of the same label
                query = f"""
                MATCH (n:`{label_filter}`)-[r]-(m:`{label_filter}`)
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
            # Modified query: Only show connections between nodes of the same label
            query = f"""
            MATCH (n:`{label_filter}`)-[r]-(m:`{label_filter}`)
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
                    color = "#f97316" if 'sensation' in node.labels and node.get("name") in sensation_names else "gray"
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
                color = "#f97316" if 'sensation' in source_node.labels and source_node.get("name") in sensation_names else "gray"
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
                color = "#f97316" if 'sensation' in target_node.labels and target_node.get("name") in sensation_names else "gray"
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

# API endpoint for advanced lesion localization with pathfinding
@app.route("/api/localize-lesion", methods=["POST"])
def localize_lesion():
    data = request.get_json()
    sensations = data.get('sensations', [])
    muscles = data.get('muscles', [])
    
    # Combine sensations and muscles
    selected_items = sensations + muscles
    
    if len(selected_items) < 2:
        return jsonify({
            "error": "At least 2 items (sensations/muscles) required for localization",
            "paths": [],
            "hub": None
        }), 400
    
    with driver.session() as session:
        try:
            # Build the dynamic query based on selected items
            # Create the WITH clause for selected nodes
            selected_nodes_conditions = []
            params = {}
            
            for i, item in enumerate(selected_items):
                param_name = f"item_{i}"
                selected_nodes_conditions.append(f"n.name = ${param_name}")
                params[param_name] = item
            
            where_clause = " OR ".join(selected_nodes_conditions)
            
            # Build the dynamic query
            query = f"""
            // 1) Get the selected nodes (sensations and muscles)
            MATCH (n)
            WHERE ({where_clause}) AND NOT n:artery
            WITH collect(n) AS picks
            WHERE size(picks) >= {len(selected_items)}
            """
            
            # Add dynamic path finding based on number of selected items
            if len(selected_items) == 2:
                query += """
                WITH picks[0] AS a, picks[1] AS b
                WHERE a <> b
                
                // 2) Try to find the best meeting hub (exclude artery hubs)
                CALL {
                WITH a, b
                MATCH (m)
                WHERE m <> a AND m <> b AND NOT m:artery
                MATCH p1 = shortestPath((a)-[*..300]-(m))
                MATCH p2 = shortestPath((b)-[*..300]-(m))
                WITH p1, p2, m, length(p1) + length(p2) AS totalLen
                ORDER BY totalLen ASC
                RETURN p1, p2, m AS hub, totalLen
                LIMIT 1
                }
                
                // 3) Return results
                RETURN
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN null ELSE p1 END AS p1,
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN null ELSE p2 END AS p2,
                null AS p3,
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN null ELSE hub END AS hub,
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN a ELSE null END AS a_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN b ELSE null END AS b_only,
                null AS c_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL
                THEN 0 ELSE totalLen END AS totalLen
                """
            elif len(selected_items) == 3:
                query += """
                WITH picks[0] AS a, picks[1] AS b, picks[2] AS c
                WHERE a <> b AND a <> c AND b <> c
                
                // 2) Try to find the best meeting hub (exclude artery hubs)
                CALL {
                WITH a, b, c
                MATCH (m)
                WHERE m <> a AND m <> b AND m <> c AND NOT m:artery
                MATCH p1 = shortestPath((a)-[*..300]-(m))
                MATCH p2 = shortestPath((b)-[*..300]-(m))
                MATCH p3 = shortestPath((c)-[*..300]-(m))
                WITH p1, p2, p3, m, length(p1) + length(p2) + length(p3) AS totalLen
                ORDER BY totalLen ASC
                RETURN p1, p2, p3, m AS hub, totalLen
                LIMIT 1
                }
                
                // 3) Return results
                RETURN
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p1 END AS p1,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p2 END AS p2,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p3 END AS p3,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE hub END AS hub,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN a ELSE null END AS a_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN b ELSE null END AS b_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN c ELSE null END AS c_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN 0 ELSE totalLen END AS totalLen
                """
            else:  # 4 or more items
                query += f"""
                WITH picks[0..{min(4, len(selected_items))-1}] AS selectedPicks
                WITH selectedPicks[0] AS a, selectedPicks[1] AS b, selectedPicks[2] AS c, 
                     CASE WHEN size(selectedPicks) > 3 THEN selectedPicks[3] ELSE null END AS d
                WHERE a <> b AND a <> c AND b <> c AND (d IS NULL OR (a <> d AND b <> d AND c <> d))
                
                // 2) Try to find the best meeting hub (exclude artery hubs)
                CALL {{
                WITH a, b, c, d
                MATCH (m)
                WHERE m <> a AND m <> b AND m <> c AND (d IS NULL OR m <> d) AND NOT m:artery
                MATCH p1 = shortestPath((a)-[*..300]-(m))
                MATCH p2 = shortestPath((b)-[*..300]-(m))
                MATCH p3 = shortestPath((c)-[*..300]-(m))
                OPTIONAL MATCH p4 = CASE WHEN d IS NOT NULL THEN shortestPath((d)-[*..300]-(m)) ELSE null END
                WITH p1, p2, p3, p4, m, 
                     length(p1) + length(p2) + length(p3) + CASE WHEN p4 IS NOT NULL THEN length(p4) ELSE 0 END AS totalLen
                ORDER BY totalLen ASC
                RETURN p1, p2, p3, p4, m AS hub, totalLen
                LIMIT 1
                }}
                
                // 3) Return results
                RETURN
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p1 END AS p1,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p2 END AS p2,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE p3 END AS p3,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN null ELSE hub END AS hub,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN a ELSE null END AS a_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN b ELSE null END AS b_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN c ELSE null END AS c_only,
                CASE WHEN p1 IS NULL OR p2 IS NULL OR p3 IS NULL
                THEN 0 ELSE totalLen END AS totalLen,
                p4
                """
            
            result = session.run(query, params)
            record = result.single()
            
            if record:
                # Extract paths and nodes
                paths = []
                all_nodes = {}
                all_links = []
                
                # Process each path
                for path_key in ['p1', 'p2', 'p3', 'p4']:
                    path = record.get(path_key)
                    if path:
                        path_nodes = []
                        for i, node in enumerate(path.nodes):
                            node_id = node.element_id
                            node_data = {
                                "id": node_id,
                                "labels": list(node.labels),
                                "properties": dict(node),
                                "name": dict(node).get("name", f"Node {node_id}"),
                                "color": "orange" if i == 0 or i == len(path.nodes)-1 else "lightblue"
                            }
                            all_nodes[node_id] = node_data
                            path_nodes.append(node_id)
                        
                        # Add relationships
                        for rel in path.relationships:
                            all_links.append({
                                "source": rel.start_node.element_id,
                                "target": rel.end_node.element_id,
                                "type": type(rel).__name__,
                                "properties": dict(rel)
                            })
                        
                        paths.append(path_nodes)
                
                # Highlight hub if found
                hub = record.get('hub')
                if hub:
                    hub_id = hub.element_id
                    if hub_id in all_nodes:
                        all_nodes[hub_id]["color"] = "red"
                        all_nodes[hub_id]["isHub"] = True
                
                return jsonify({
                    "paths": paths,
                    "hub": hub.element_id if hub else None,
                    "nodes": list(all_nodes.values()),
                    "links": all_links,
                    "totalLength": record.get('totalLen', 0),
                    "found": len(paths) > 0
                })
            else:
                return jsonify({
                    "paths": [],
                    "hub": None,
                    "nodes": [],
                    "links": [],
                    "totalLength": 0,
                    "found": False,
                    "message": "No pathways found between selected items"
                })
                
        except Exception as e:
            return jsonify({
                "error": f"Error in lesion localization: {str(e)}",
                "paths": [],
                "hub": None,
                "nodes": [],
                "links": [],
                "found": False
            }), 500

@app.route("/")
def index():
    """Main page - serves the database explorer"""
    return send_from_directory('public', 'explorer.html')

# API endpoint to get dermatomes and myotomes data
@app.route("/api/dermatomes-myotomes")
def get_dermatomes_myotomes_api():
    dermatomes, myotomes = get_dermatomes_and_myotomes()
    return jsonify({
        "dermatomes": dermatomes,
        "myotomes": myotomes
    })

# Legacy routes for backward compatibility
@app.route("/explorer")
def explorer():
    return send_from_directory('public', 'explorer.html')

@app.route("/explorer.html")
def explorer_html():
    return send_from_directory('public', 'explorer.html')

# Route to access the old index page if needed
@app.route("/old-index")
def old_index():
    return send_from_directory('public', 'index.html')

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('public', filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)