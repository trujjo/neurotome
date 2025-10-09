#!/usr/bin/env python3
"""
Test script to directly run the radial artery connection algorithm
without needing the Flask server running.
"""

from neo4j import GraphDatabase
import json

# Neo4j connection credentials
NEO4J_URI = "neo4j+s://415ed9b1.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU"

def test_radial_artery_connection():
    """Test connection between left and right radial arteries"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Target arteries
    selected_items = ["left radial artery", "right radial artery"]
    
    with driver.session() as session:
        try:
            print(f"🔍 Testing connection between: {selected_items}")
            print("=" * 60)
            
            # Create parameters for the selected item names
            params = {"names": selected_items}
            
            # The same query used in the lesion localizer
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
                
                print(f"✅ CONNECTION FOUND!")
                print(f"📊 Total nodes in path: {len(nodes)}")
                print(f"🔗 Total relationships: {len(relationships)}")
                print(f"🎯 Convergence points (earliest layer): {len(earliest_nodes)}")
                print()
                
                # Check for aortic arch
                aortic_found = False
                print("🔍 Searching for aortic arch in connection path...")
                
                for i, node in enumerate(nodes):
                    name = node.get("name", "").lower()
                    labels = list(node.labels)
                    
                    # Check if this could be the aortic arch
                    if "aortic" in name or "arch" in name:
                        is_source = node.get("name") in selected_items
                        is_earliest = any(id(node) == id(en) for en in earliest_nodes)
                        
                        if is_source:
                            color = "🟠 SOURCE"
                        elif is_earliest:
                            color = "🔴 CONVERGENCE POINT"
                        else:
                            color = "🔵 PATH NODE"
                            
                        print(f"🎯 FOUND AORTIC: {node.get('name')} ({color})")
                        aortic_found = True
                
                if not aortic_found:
                    print("❌ No aortic arch found in direct connection path")
                
                print("\n" + "="*60)
                print("📋 ALL NODES IN CONNECTION PATH:")
                print("="*60)
                
                for i, node in enumerate(nodes):
                    name = node.get("name", f"Node_{i}")
                    labels = ", ".join(list(node.labels))
                    
                    # Determine node role
                    is_source = node.get("name") in selected_items
                    is_earliest = any(id(node) == id(en) for en in earliest_nodes)
                    
                    if is_source:
                        role = "🟠 SOURCE"
                    elif is_earliest:
                        role = "🔴 CONVERGENCE"
                    else:
                        role = "🔵 PATH"
                        
                    print(f"  {i+1:2d}. {name} ({labels}) - {role}")
                
                # Show convergence points specifically
                if earliest_nodes:
                    print(f"\n🎯 CONVERGENCE POINTS (where paths meet):")
                    print("-" * 40)
                    for i, node in enumerate(earliest_nodes):
                        name = node.get("name", f"Convergence_{i}")
                        labels = ", ".join(list(node.labels))
                        print(f"  {i+1}. {name} ({labels})")
                
                return {
                    "found": True,
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships),
                    "convergence_points": len(earliest_nodes),
                    "aortic_found": aortic_found,
                    "nodes": [{"name": node.get("name"), "labels": list(node.labels)} for node in nodes]
                }
            else:
                print("❌ NO CONNECTION FOUND")
                print("The radial arteries do not appear to be connected in the database")
                return {"found": False}
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            return {"error": str(e)}
        finally:
            driver.close()

if __name__ == "__main__":
    result = test_radial_artery_connection()
    print(f"\n📋 SUMMARY: {json.dumps(result, indent=2)}")