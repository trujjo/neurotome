#!/usr/bin/env python3
"""
Search for radial artery nodes in the database to see what exists
"""

from neo4j import GraphDatabase
import json

# Neo4j connection credentials
NEO4J_URI = "neo4j+s://415ed9b1.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU"

def search_radial_arteries():
    """Search for any nodes containing 'radial' in their name"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        try:
            print("🔍 Searching for nodes containing 'radial'...")
            print("=" * 60)
            
            # Search for nodes with 'radial' in name
            search_query = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS 'radial'
            RETURN n, labels(n) as labels
            ORDER BY n.name
            LIMIT 20
            """
            
            result = session.run(search_query)
            nodes = list(result)
            
            if nodes:
                print(f"📋 Found {len(nodes)} nodes containing 'radial':")
                print("-" * 60)
                
                for i, record in enumerate(nodes):
                    node = record["n"]
                    labels = record["labels"]
                    name = node.get("name", "Unknown")
                    
                    print(f"  {i+1:2d}. {name}")
                    print(f"      Labels: {', '.join(labels)}")
                    
                    # Show other properties
                    props = dict(node)
                    for key, value in props.items():
                        if key != "name":
                            print(f"      {key}: {value}")
                    print()
                
                # Now let's also search for 'artery' nodes
                print("\n" + "=" * 60)
                print("🔍 Searching for nodes containing 'artery'...")
                print("=" * 60)
                
                artery_query = """
                MATCH (n)
                WHERE toLower(n.name) CONTAINS 'artery'
                RETURN n, labels(n) as labels
                ORDER BY n.name
                LIMIT 30
                """
                
                artery_result = session.run(artery_query)
                artery_nodes = list(artery_result)
                
                print(f"📋 Found {len(artery_nodes)} nodes containing 'artery':")
                print("-" * 60)
                
                for i, record in enumerate(artery_nodes):
                    node = record["n"]
                    labels = record["labels"]
                    name = node.get("name", "Unknown")
                    
                    print(f"  {i+1:2d}. {name} ({', '.join(labels)})")
                    
                # Look specifically for aortic arch
                print("\n" + "=" * 60)
                print("🔍 Searching for aortic arch...")
                print("=" * 60)
                
                aortic_query = """
                MATCH (n)
                WHERE toLower(n.name) CONTAINS 'aortic' OR toLower(n.name) CONTAINS 'arch'
                RETURN n, labels(n) as labels
                ORDER BY n.name
                LIMIT 10
                """
                
                aortic_result = session.run(aortic_query)
                aortic_nodes = list(aortic_result)
                
                if aortic_nodes:
                    print(f"📋 Found {len(aortic_nodes)} aortic/arch nodes:")
                    print("-" * 60)
                    
                    for i, record in enumerate(aortic_nodes):
                        node = record["n"]
                        labels = record["labels"]
                        name = node.get("name", "Unknown")
                        
                        print(f"  {i+1:2d}. {name} ({', '.join(labels)})")
                else:
                    print("❌ No aortic arch nodes found")
                    
            else:
                print("❌ No nodes containing 'radial' found")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
        finally:
            driver.close()

if __name__ == "__main__":
    search_radial_arteries()