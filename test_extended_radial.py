#!/usr/bin/env python3
"""
Test radial artery connection with bidirectional search and extended hops
"""

from neo4j import GraphDatabase
import json

# Neo4j connection credentials
NEO4J_URI = "neo4j+s://415ed9b1.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU"

def test_extended_radial_connection():
    """Test radial artery connection with extended search"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        try:
            print("🔍 Testing EXTENDED radial artery connection...")
            print("🎯 Target: left radial artery ↔ right radial artery")
            print("=" * 70)
            
            # Test 1: Check if arteries exist
            check_query = """
            MATCH (left {name: 'left radial artery'})
            MATCH (right {name: 'right radial artery'})
            MATCH (aortic {name: 'aortic arch'})
            RETURN left, right, aortic
            """
            
            result = session.run(check_query)
            record = result.single()
            
            if not record:
                print("❌ Could not find both radial arteries or aortic arch")
                return {"found": False, "error": "Missing nodes"}
            
            print("✅ Found both radial arteries and aortic arch")
            
            # Test 2: Bidirectional pathfinding with more hops
            path_query = """
            MATCH (left {name: 'left radial artery'})
            MATCH (right {name: 'right radial artery'})
            
            // Try to find any path between them (bidirectional, up to 10 hops)
            MATCH p = shortestPath((left)-[*1..10]-(right))
            
            RETURN p, length(p) as path_length, 
                   nodes(p) as path_nodes, 
                   relationships(p) as path_rels
            """
            
            result = session.run(path_query)
            record = result.single()
            
            if record:
                path_length = record["path_length"]
                path_nodes = record["path_nodes"]
                path_rels = record["path_rels"]
                
                print(f"🎉 BIDIRECTIONAL PATH FOUND!")
                print(f"📏 Path length: {path_length} hops")
                print(f"📊 Total nodes: {len(path_nodes)}")
                print(f"🔗 Total relationships: {len(path_rels)}")
                print()
                
                # Check for aortic arch in path
                aortic_found = False
                for i, node in enumerate(path_nodes):
                    name = node.get("name", "")
                    if "aortic" in name.lower() or "arch" in name.lower():
                        print(f"🎯 FOUND AORTIC CONNECTION: {name} (position {i+1}/{len(path_nodes)})")
                        aortic_found = True
                
                print("\n" + "="*70)
                print("📋 COMPLETE PATH FROM LEFT TO RIGHT RADIAL ARTERY:")
                print("="*70)
                
                for i, node in enumerate(path_nodes):
                    name = node.get("name", f"Node_{i}")
                    labels = ", ".join(list(node.labels))
                    
                    # Highlight key nodes
                    if i == 0:
                        marker = "🟢 START"
                    elif i == len(path_nodes) - 1:
                        marker = "🔴 END"
                    elif "aortic" in name.lower() or "arch" in name.lower():
                        marker = "🎯 AORTIC"
                    else:
                        marker = "🔵 PATH"
                    
                    arrow = " → " if i < len(path_nodes) - 1 else ""
                    print(f"  {i+1:2d}. {name} ({labels}) {marker}{arrow}")
                
                # Show relationships
                print(f"\n🔗 RELATIONSHIPS IN PATH:")
                print("-" * 40)
                for i, rel in enumerate(path_rels):
                    rel_type = type(rel).__name__
                    start_node = path_nodes[i].get("name", f"Node_{i}")
                    end_node = path_nodes[i+1].get("name", f"Node_{i+1}")
                    print(f"  {i+1}. {start_node} --[{rel_type}]--> {end_node}")
                
                return {
                    "found": True,
                    "path_length": path_length,
                    "total_nodes": len(path_nodes),
                    "aortic_found": aortic_found,
                    "path": [node.get("name") for node in path_nodes]
                }
            else:
                print("❌ NO BIDIRECTIONAL PATH FOUND")
                
                # Test 3: Check upstream paths from each artery
                print("\n🔍 Testing individual upstream paths...")
                print("-" * 50)
                
                upstream_query = """
                // Check what each artery connects to upstream
                MATCH (left {name: 'left radial artery'})
                MATCH (right {name: 'right radial artery'})
                
                // Find upstream from left (incoming relationships)
                OPTIONAL MATCH (left)<-[*1..5]-(left_upstream)
                
                // Find upstream from right (incoming relationships)  
                OPTIONAL MATCH (right)<-[*1..5]-(right_upstream)
                
                RETURN collect(DISTINCT left_upstream.name) as left_sources,
                       collect(DISTINCT right_upstream.name) as right_sources
                """
                
                result = session.run(upstream_query)
                record = result.single()
                
                if record:
                    left_sources = [s for s in record["left_sources"] if s]
                    right_sources = [s for s in record["right_sources"] if s]
                    
                    print(f"📊 Left radial artery upstream connections: {len(left_sources)}")
                    for source in left_sources[:10]:
                        print(f"  - {source}")
                    
                    print(f"\n📊 Right radial artery upstream connections: {len(right_sources)}")
                    for source in right_sources[:10]:
                        print(f"  - {source}")
                    
                    # Check for common sources
                    common = set(left_sources) & set(right_sources)
                    if common:
                        print(f"\n🎯 COMMON UPSTREAM SOURCES: {len(common)}")
                        for source in common:
                            print(f"  - {source}")
                    else:
                        print(f"\n❌ No common upstream sources found")
                
                return {"found": False, "reason": "No path exists"}
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            return {"error": str(e)}
        finally:
            driver.close()

if __name__ == "__main__":
    result = test_extended_radial_connection()
    print(f"\n📋 FINAL RESULT: {json.dumps(result, indent=2)}")