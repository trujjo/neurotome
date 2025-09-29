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
            "hub": None,
            "nodes": [],
            "links": [],
            "earliest_nodes": [],
            "totalLength": 0,
            "found": False
        }), 400
    
    with driver.session() as session:
        try:
            # Create parameters for the selected item names
            params = {"names": selected_items}
            
            # Build the query following the original pattern
            query = """
            WITH $names AS names

            // Gather sources
            MATCH (s)
            WHERE s.name IN names
            WITH collect(s) AS sources, size(names) AS total

            // Expand 1..6 hops from each source and record min distance to each candidate m
            // Only follow downstream (outgoing) relationships from sources
            UNWIND sources AS src
            MATCH p = (src)-[*1..6]->(m)
            WITH m, src, min(length(p)) AS d, sources, total
            WITH m, collect(d) AS dists, sources, total
            WHERE size(dists) = total

            // Earliest layer = minimal max distance across sources
            WITH m, sources,
                 reduce(mx = -1, d IN dists | CASE WHEN d > mx THEN d ELSE mx END) AS layer
            ORDER BY layer ASC
            WITH collect({m:m, layer:layer}) AS hits, sources

            // Earliest layer value
            WITH hits, sources,
                 reduce(minL = 999999, h IN hits | CASE WHEN h.layer < minL THEN h.layer ELSE minL END) AS earliest

            // Nodes in the earliest layer
            WITH sources, [h IN hits WHERE h.layer = earliest | h.m] AS earliest_nodes

            // Relationships among earliest nodes (induced subgraph)
            UNWIND earliest_nodes AS en1
            UNWIND earliest_nodes AS en2
            WITH DISTINCT earliest_nodes, sources, en1
            OPTIONAL MATCH (en1)-[r_between]->(en2)
            WITH DISTINCT earliest_nodes, sources,
                          collect(DISTINCT en1) AS en_nodes,
                          collect(DISTINCT r_between) AS en_edges

            // Shortest paths (<=6) from each source to each earliest node
            // Only follow downstream (outgoing) paths from sources
            UNWIND earliest_nodes AS target
            UNWIND sources AS src
            OPTIONAL MATCH p = shortestPath( (src)-[*..6]->(target) )
            WITH earliest_nodes, en_nodes, en_edges, collect(p) AS paths

            // Flatten and dedupe without APOC
            WITH earliest_nodes, en_nodes, en_edges,
                 [x IN paths WHERE x IS NOT NULL] AS paths2
            WITH earliest_nodes, en_nodes, en_edges,
                 reduce(ns = [], p IN paths2 | ns + nodes(p)) AS path_nodes,
                 reduce(rs = [], p IN paths2 | rs + relationships(p)) AS path_rels
            WITH earliest_nodes, en_nodes + path_nodes AS all_nodes_list,
                 en_edges + path_rels AS all_rels_list
            WITH earliest_nodes, [n IN all_nodes_list WHERE n IS NOT NULL] AS all_nodes_list,
                 [r IN all_rels_list  WHERE r IS NOT NULL] AS all_rels_list
            WITH earliest_nodes,
              reduce(seen = [], n IN all_nodes_list |
                CASE WHEN any(x IN seen WHERE id(x) = id(n)) THEN seen ELSE seen + n END) AS all_nodes,
              reduce(seenr = [], r IN all_rels_list |
                CASE WHEN any(x IN seenr WHERE id(x) = id(r)) THEN seenr ELSE seenr + r END) AS all_rels
            RETURN all_nodes AS nodes, all_rels AS relationships, earliest_nodes
            """
            
            result = session.run(query, params)
            record = result.single()
            
            if record and record["nodes"]:
                nodes = record["nodes"]
                relationships = record["relationships"]
                earliest_nodes = record.get("earliest_nodes", [])
                
                # Convert Neo4j nodes and relationships to JSON format
                all_nodes = {}
                all_links = []
                
                # Process nodes
                for node in nodes:
                    node_id = node.element_id
                    
                    # Determine node color based on type
                    is_source = node.get("name") in selected_items
                    is_earliest = any(id(node) == id(en) for en in earliest_nodes)
                    
                    if is_source:
                        color = "orange"  # Source nodes
                    elif is_earliest:
                        color = "red"     # Earliest layer nodes (potential lesion sites)
                    else:
                        color = "lightblue"  # Path nodes
                    
                    all_nodes[node_id] = {
                        "id": node_id,
                        "labels": list(node.labels),
                        "properties": dict(node),
                        "name": dict(node).get("name", f"Node {node_id}"),
                        "color": color,
                        "isSource": is_source,
                        "isEarliest": is_earliest
                    }
                
                # Process relationships - the query already returns only the relevant ones
                for rel in relationships:
                    if rel is not None:  # Filter out null relationships
                        start_id = rel.start_node.element_id
                        end_id = rel.end_node.element_id
                        start_node = rel.start_node
                        end_node = rel.end_node
                        
                        # Skip relationships involving malformed nodes (no labels and no meaningful properties)
                        if (not list(start_node.labels) and not start_node.get("name")) or \
                           (not list(end_node.labels) and not end_node.get("name")):
                            continue
                        
                        # Add the relationship
                        all_links.append({
                            "source": start_id,
                            "target": end_id,
                            "type": type(rel).__name__,
                            "properties": dict(rel),
                            "directed": True  # Mark as directed for arrow display
                        })
                        
                        # Ensure start_node is in the nodes list
                        if start_id not in all_nodes:
                            is_source = start_node.get("name") in selected_items
                            is_earliest = any(id(start_node) == id(en) for en in earliest_nodes)
                            
                            if is_source:
                                color = "orange"
                            elif is_earliest:
                                color = "red"
                            else:
                                color = "lightblue"
                                
                            all_nodes[start_id] = {
                                "id": start_id,
                                "labels": list(start_node.labels),
                                "properties": dict(start_node),
                                "name": dict(start_node).get("name", f"Node {start_id}"),
                                "color": color,
                                "isSource": is_source,
                                "isEarliest": is_earliest
                            }
                        
                        # Ensure end_node is in the nodes list
                        if end_id not in all_nodes:
                            is_source = end_node.get("name") in selected_items
                            is_earliest = any(id(end_node) == id(en) for en in earliest_nodes)
                            
                            if is_source:
                                color = "orange"
                            elif is_earliest:
                                color = "red"
                            else:
                                color = "lightblue"
                                
                            all_nodes[end_id] = {
                                "id": end_id,
                                "labels": list(end_node.labels),
                                "properties": dict(end_node),
                                "name": dict(end_node).get("name", f"Node {end_id}"),
                                "color": color,
                                "isSource": is_source,
                                "isEarliest": is_earliest
                            }
                
                return jsonify({
                    "nodes": list(all_nodes.values()),
                    "links": all_links,
                    "earliest_nodes": [node.element_id for node in earliest_nodes],
                    "paths": all_links,  # Frontend expects 'paths' for counting
                    "hub": earliest_nodes[0].element_id if earliest_nodes else None,  # Use first earliest node as hub
                    "totalLength": len(all_links),  # Use number of links as total length
                    "found": True,
                    "message": f"Found {len(earliest_nodes)} potential lesion site(s) in the earliest convergence layer"
                })
            else:
                return jsonify({
                    "nodes": [],
                    "links": [],
                    "earliest_nodes": [],
                    "paths": [],  # Frontend expects 'paths' for counting
                    "hub": None,  # Frontend checks for hub
                    "totalLength": 0,  # Frontend displays total length
                    "found": False,
                    "message": "No convergent pathways found between selected items"
                })
                
        except Exception as e:
            return jsonify({
                "error": f"Error in lesion localization: {str(e)}",
                "nodes": [],
                "links": [],
                "earliest_nodes": [],
                "paths": [],  # Frontend expects 'paths' for counting
                "hub": None,  # Frontend checks for hub  
                "totalLength": 0,  # Frontend displays total length
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