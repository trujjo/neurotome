from flask import Flask, render_template_string, jsonify, request, send_from_directory
from flask_cors import CORS
from neo4j import GraphDatabase
import json
import os
import threading
import uuid

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

# API endpoint to get relationships for a specific node by element ID
@app.route("/api/node/<node_id>/relationships")
def get_node_relationships_by_element_id(node_id):
    with driver.session() as session:
        query = """
        MATCH (n)-[r]-(m)
        WHERE n.`element_id` = $node_id OR elementId(n) = $node_id
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

# API endpoint to get upstream relationships for a specific node by element ID
@app.route("/api/node/<node_id>/upstream")
def get_node_upstream_relationships(node_id):
    with driver.session() as session:
        query = """
        MATCH (target)-[r]->(n)
        WHERE n.`element_id` = $node_id OR elementId(n) = $node_id
        RETURN target, r, n, type(r) as rel_type
        LIMIT 50
        """
        result = session.run(query, node_id=node_id)
        relationships = []
        for record in result:
            rel_data = {
                "source": {
                    "id": record["target"].element_id,
                    "labels": list(record["target"].labels),
                    "properties": dict(record["target"])
                },
                "target": {
                    "id": record["n"].element_id,
                    "labels": list(record["n"].labels),
                    "properties": dict(record["n"])
                },
                "relationship": {
                    "type": record["rel_type"],
                    "properties": dict(record["r"])
                }
            }
            relationships.append(rel_data)
        return jsonify(relationships)

# API endpoint to get downstream relationships for a specific node by element ID
@app.route("/api/node/<node_id>/downstream")
def get_node_downstream_relationships(node_id):
    with driver.session() as session:
        query = """
        MATCH (n)-[r]->(target)
        WHERE n.`element_id` = $node_id OR elementId(n) = $node_id
        RETURN n, r, target, type(r) as rel_type
        LIMIT 50
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
                    "id": record["target"].element_id,
                    "labels": list(record["target"].labels),
                    "properties": dict(record["target"])
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
    limit = request.args.get('limit', 50, type=int)
    
    if not query_param:
        return jsonify([])
    
    with driver.session() as session:
        # Enhanced search to look in multiple properties and prioritize results
        # Using case-insensitive matching with toLower()
        query = f"""
        MATCH (n)
        WHERE (n.{property_name} IS NOT NULL AND toLower(n.{property_name}) CONTAINS toLower($search_term))
           OR (n.description IS NOT NULL AND toLower(n.description) CONTAINS toLower($search_term))
           OR any(label IN labels(n) WHERE toLower(label) CONTAINS toLower($search_term))
        RETURN n, labels(n) as labels
        ORDER BY 
            CASE 
                WHEN n.{property_name} IS NOT NULL AND toLower(n.{property_name}) STARTS WITH toLower($search_term) THEN 1
                WHEN n.{property_name} IS NOT NULL AND toLower(n.{property_name}) CONTAINS toLower($search_term) THEN 2
                WHEN any(label IN labels(n) WHERE toLower(label) CONTAINS toLower($search_term)) THEN 3
                ELSE 4
            END,
            n.{property_name}
        LIMIT {limit}
        """
        result = session.run(query, search_term=query_param)
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
            # 1. Fetch source nodes
            source_query = """
            MATCH (s) WHERE s.name IN $names RETURN s
            """
            src_records = session.run(source_query, names=selected_items)
            sources = [r["s"] for r in src_records]
            if len(sources) != len(selected_items):
                missing = set(selected_items) - set([s.get("name") for s in sources if s.get("name")])
            else:
                missing = []
            if not sources:
                return jsonify({
                    "nodes": [], "links": [], "earliest_nodes": [], "paths": [],
                    "hub": None, "totalLength": 0, "found": False,
                    "message": "No source nodes found", "missing": list(missing)
                })

            depth_limit = 6
            # 2. Collect directed distance maps per source based on label rule
            distance_maps = []  # list of dict element_id -> distance
            for s in sources:
                is_sensation = 'sensation' in s.labels
                if is_sensation:
                    dist_query = f"""
                    MATCH (src) WHERE elementId(src) = $id
                    MATCH p=(src)-[*1..{depth_limit}]->(m)
                    RETURN m AS node, min(length(p)) AS d
                    """
                else:
                    dist_query = f"""
                    MATCH (src) WHERE elementId(src) = $id
                    MATCH p=(src)<-[*1..{depth_limit}]-(m)
                    RETURN m AS node, min(length(p)) AS d
                    """
                recs = session.run(dist_query, id=s.element_id)
                dist_map = {}
                for r in recs:
                    n = r["node"]
                    if n is None: continue
                    dist_map[n.element_id] = r["d"]
                distance_maps.append(dist_map)

            # 3. Find intersection nodes reachable from all sources
            if not distance_maps:
                return jsonify({
                    "nodes": [], "links": [], "earliest_nodes": [], "paths": [],
                    "hub": None, "totalLength": 0, "found": False,
                    "message": "No paths explored"
                })

            common_ids = set(distance_maps[0].keys())
            for dm in distance_maps[1:]:
                common_ids &= set(dm.keys())

            # Remove the sources themselves to focus on convergence points
            source_ids = {s.element_id for s in sources}
            common_ids -= source_ids

            if not common_ids:
                return jsonify({
                    "nodes": [], "links": [], "earliest_nodes": [], "paths": [],
                    "hub": None, "totalLength": 0, "found": False,
                    "message": "No convergent pathways found between selected items"
                })

            # 4. Compute layer = max distance among sources for each candidate; choose minimal
            def layer_for(nid):
                return max(dm[nid] for dm in distance_maps if nid in dm)
            layers = {nid: layer_for(nid) for nid in common_ids}
            min_layer = min(layers.values()) if layers else None
            earliest_ids = [nid for nid, layer in layers.items() if layer == min_layer]

            # 5. Reconstruct shortest directed paths from each source to each earliest node respecting direction rule
            collected_nodes = {}
            collected_rels = []

            def add_node(n, color=None, is_source=False, is_earliest=False):
                if n.element_id in collected_nodes:
                    return
                if color is None:
                    if is_source:
                        color = 'orange'
                    elif is_earliest:
                        color = 'red'
                    else:
                        color = 'lightblue'
                collected_nodes[n.element_id] = {
                    'id': n.element_id,
                    'labels': list(n.labels),
                    'properties': dict(n),
                    'name': dict(n).get('name', f'Node {n.element_id}'),
                    'color': color,
                    'isSource': is_source,
                    'isEarliest': is_earliest
                }

            # Ensure sources added
            for s in sources:
                add_node(s, is_source=True, is_earliest=False)

            path_limit = depth_limit
            for s in sources:
                is_sensation = 'sensation' in s.labels
                for target_id in earliest_ids:
                    if is_sensation:
                        path_query = f"""
                        MATCH (src) WHERE elementId(src)=$sid
                        MATCH (t) WHERE elementId(t)=$tid
                        OPTIONAL MATCH p = shortestPath( (src)-[*..{path_limit}]->(t) )
                        RETURN p
                        """
                    else:
                        # Upstream: from target to source (so we can still use outgoing pattern)
                        path_query = f"""
                        MATCH (src) WHERE elementId(src)=$sid
                        MATCH (t) WHERE elementId(t)=$tid
                        OPTIONAL MATCH p = shortestPath( (t)-[*..{path_limit}]->(src) )
                        RETURN p
                        """
                    rec = session.run(path_query, sid=s.element_id, tid=target_id).single()
                    p = rec["p"] if rec else None
                    if not p:
                        continue
                    # Collect nodes
                    for n in p.nodes:
                        add_node(n, is_source=(n.element_id in source_ids), is_earliest=(n.element_id in earliest_ids))
                    # Collect relationships (directed true)
                    for r in p.relationships:
                        collected_rels.append({
                            'source': r.start_node.element_id,
                            'target': r.end_node.element_id,
                            'type': type(r).__name__,
                            'properties': dict(r),
                            'directed': True
                        })

            # Deduplicate relationships
            seen_rel = set()
            dedup_rels = []
            for rel in collected_rels:
                key = (rel['source'], rel['target'], rel['type'])
                if key in seen_rel:
                    continue
                seen_rel.add(key)
                dedup_rels.append(rel)

            # Mark earliest nodes (ensure they exist in collection)
            earliest_nodes_objs = []
            fetch_earliest_query = """
            MATCH (n) WHERE elementId(n) IN $ids RETURN n
            """
            for rec in session.run(fetch_earliest_query, ids=earliest_ids):
                earliest_nodes_objs.append(rec['n'])
                add_node(rec['n'], is_earliest=True, is_source=(rec['n'].element_id in source_ids))

            return jsonify({
                'nodes': list(collected_nodes.values()),
                'links': dedup_rels,
                'earliest_nodes': earliest_ids,
                'paths': dedup_rels,  # maintain shape expected by frontend
                'hub': earliest_ids[0] if earliest_ids else None,
                'totalLength': len(dedup_rels),
                'found': True,
                'message': f'Found {len(earliest_ids)} potential lesion site(s) (layer {min_layer})'
            })
        except Exception as e:
            return jsonify({
                'error': f'Error in lesion localization (directional): {str(e)}',
                'nodes': [], 'links': [], 'earliest_nodes': [], 'paths': [],
                'hub': None, 'totalLength': 0, 'found': False
            }), 500

# ------------------------------------------------------------
# Connect arbitrary nodes via directional convergence logic
# (Sensation sources expand downstream; all others expand upstream.)
# ------------------------------------------------------------
@app.route("/api/connect-nodes", methods=["POST"])
def connect_nodes():
    """Return combined shortest path subgraph connecting the supplied node names.

    Request JSON: {"nodes": [name1, name2, ...]}
    Response JSON: {
        nodes: [ {id, labels, properties, name, isSource, isHub, _vizCategory} ],
        links: [ {source, target, type, properties, _pathEdge: true} ],
        paths: [ {sourceName, targetName, nodeIds, relationshipIds} ],
        hubs: [nodeIds],
        found: bool,
        message: str
    }
    """
    data = request.get_json() or {}
    requested = data.get("nodes", [])
    if not isinstance(requested, list):
        return jsonify({"error": "'nodes' must be a list"}), 400
    # De-duplicate while preserving order
    seen = set()
    node_names = [n for n in requested if isinstance(n, str) and not (n in seen or seen.add(n))]
    if len(node_names) < 2:
        return jsonify({
            "nodes": [],
            "links": [],
            "paths": [],
            "hubs": [],
            "found": False,
            "message": "Provide at least 2 node names"
        }), 400
    if len(node_names) > 20:
        return jsonify({"error": "Maximum of 20 nodes allowed"}), 400

    lower_names = [n.lower() for n in node_names]

    with driver.session() as session:
        try:
            fetch_query = """
            WITH $namesLower AS namesLower
            MATCH (s)
            WHERE s.name IS NOT NULL AND toLower(s.name) IN namesLower
            RETURN s
            """
            records = session.run(fetch_query, namesLower=lower_names)
            sources = [r["s"] for r in records]

            if not sources:
                return jsonify({
                    'nodes': [], 'links': [], 'paths': [], 'hubs': [], 'found': False,
                    'message': 'No supplied names matched any nodes'
                })

            depth_limit = 25
            source_ids = {s.element_id for s in sources}

            # 1. Build directional distance maps for each source
            distance_maps = []
            for s in sources:
                is_sensation = 'sensation' in s.labels
                if is_sensation:
                    dist_query = f"""
                    MATCH (src) WHERE elementId(src)=$id
                    MATCH p=(src)-[*1..{depth_limit}]->(n)
                    RETURN n AS node, min(length(p)) AS d
                    """
                else:
                    dist_query = f"""
                    MATCH (src) WHERE elementId(src)=$id
                    MATCH p=(n)-[*1..{depth_limit}]->(src)
                    RETURN n AS node, min(length(p)) AS d
                    """
                recs = session.run(dist_query, id=s.element_id)
                dm = {}
                for r in recs:
                    node_obj = r['node']
                    if not node_obj:
                        continue
                    if node_obj.element_id == s.element_id:
                        continue
                    dm[node_obj.element_id] = r['d']
                distance_maps.append(dm)

            if not distance_maps:
                return jsonify({'nodes': [], 'links': [], 'paths': [], 'hubs': [], 'found': False, 'message': 'No traversals possible'})

            # 2. Intersection of reachable node ids
            common_ids = set(distance_maps[0].keys())
            for dm in distance_maps[1:]:
                common_ids &= set(dm.keys())
            common_ids -= source_ids

            if not common_ids:
                # Return only sources (no hubs)
                node_map = {}
                for s in sources:
                    node_map[s.element_id] = {
                        'id': s.element_id,
                        'labels': list(s.labels),
                        'properties': dict(s),
                        'name': dict(s).get('name', f'Node {s.element_id}'),
                        'isSource': True,
                        'isHub': False,
                        '_vizCategory': 'source'
                    }
                return jsonify({
                    'nodes': list(node_map.values()),
                    'links': [],
                    'paths': [],
                    'hubs': [],
                    'found': False,
                    'message': 'No directional intersection (hub) nodes found'
                })

            # 3. Determine earliest layer hubs (minimize max distance across sources)
            def layer_for(node_id):
                vals = [dm[node_id] for dm in distance_maps if node_id in dm]
                return max(vals) if vals else None
            layers = {nid: layer_for(nid) for nid in common_ids}
            min_layer = min(layers.values()) if layers else None
            earliest_ids = [nid for nid, lay in layers.items() if lay == min_layer]

            # 4. Reconstruct directional shortest paths source->hub (sensation) or hub->source (non-sensation)
            collected_nodes = {}
            collected_rels = []
            paths_data = []

            def add_node(n, is_source=False, is_hub=False):
                existing = collected_nodes.get(n.element_id)
                if existing:
                    if is_source:
                        existing['isSource'] = True
                        existing['_vizCategory'] = 'source'
                    if is_hub:
                        existing['isHub'] = True
                        existing['_vizCategory'] = 'hub'
                    return
                category = 'source' if is_source else ('hub' if is_hub else 'path')
                collected_nodes[n.element_id] = {
                    'id': n.element_id,
                    'labels': list(n.labels),
                    'properties': dict(n),
                    'name': dict(n).get('name', f'Node {n.element_id}'),
                    'isSource': is_source,
                    'isHub': is_hub,
                    '_vizCategory': category
                }

            for s in sources:
                add_node(s, is_source=True)

            hub_query = """
            MATCH (n) WHERE elementId(n) IN $ids RETURN n
            """
            hub_nodes = {r['n'].element_id: r['n'] for r in session.run(hub_query, ids=earliest_ids)}
            for hid in earliest_ids:
                if hid in hub_nodes:
                    add_node(hub_nodes[hid], is_hub=True)

            for s in sources:
                is_sensation = 'sensation' in s.labels
                for hid in earliest_ids:
                    if hid not in hub_nodes:
                        continue
                    if is_sensation:
                        path_query = f"""
                        MATCH (src) WHERE elementId(src)=$sid
                        MATCH (hub) WHERE elementId(hub)=$hid
                        OPTIONAL MATCH p = shortestPath( (src)-[*..{depth_limit}]->(hub) )
                        RETURN p
                        """
                    else:
                        path_query = f"""
                        MATCH (src) WHERE elementId(src)=$sid
                        MATCH (hub) WHERE elementId(hub)=$hid
                        OPTIONAL MATCH p = shortestPath( (hub)-[*..{depth_limit}]->(src) )
                        RETURN p
                        """
                    rec = session.run(path_query, sid=s.element_id, hid=hid).single()
                    p = rec['p'] if rec else None
                    if not p:
                        continue
                    node_ids = [n.element_id for n in p.nodes]
                    rel_ids = []
                    for n in p.nodes:
                        add_node(n, is_source=(n.element_id in source_ids), is_hub=(n.element_id in earliest_ids))
                    for r in p.relationships:
                        rel_ids.append(r.element_id)
                        collected_rels.append({
                            'source': r.start_node.element_id,
                            'target': r.end_node.element_id,
                            'type': type(r).__name__,
                            'properties': dict(r),
                            '_pathEdge': True,
                            'directed': True
                        })
                    paths_data.append({
                        'sourceName': s.get('name'),
                        'hubId': hid,
                        'nodeIds': node_ids,
                        'relationshipIds': rel_ids
                    })

            # Deduplicate relationships
            seen_rel = set()
            dedup_links = []
            for rel in collected_rels:
                key = (rel['source'], rel['target'], rel['type'])
                if key in seen_rel:
                    continue
                seen_rel.add(key)
                dedup_links.append(rel)

            return jsonify({
                'nodes': list(collected_nodes.values()),
                'links': dedup_links,
                'paths': paths_data,
                'hubs': earliest_ids,
                'found': True if earliest_ids else False,
                'message': f'Directional connect: {len(earliest_ids)} hub node(s); {len(paths_data)} path fragment(s); layer={min_layer}'
            })
        except Exception as e:
            return jsonify({
                'error': f'Directional connect failed: {str(e)}',
                'nodes': [], 'links': [], 'paths': [], 'hubs': [], 'found': False
            }), 500

# Legacy routes for backward compatibility
@app.route("/explorer")
def explorer():
    return send_from_directory('public', 'explorer.html')

@app.route("/explorer.html")
def explorer_html():
    return send_from_directory('public', 'explorer.html')

# Simple root route (was inadvertently removed during refactor)
@app.route("/")
def root():
    # Prefer serving index.html if it exists, else simple OK text
    index_path = os.path.join(app.static_folder or 'public', 'index.html')
    if os.path.exists(index_path):
        return send_from_directory('public', 'index.html')
    return "OK", 200

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