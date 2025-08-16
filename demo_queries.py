#!/usr/bin/env python3
"""
Demo script showing example Neo4j queries for the Neurotome database.
This script demonstrates how to explore your neuroanatomy database programmatically.
"""

from neo4j import GraphDatabase
import json

# Database connection
URI = "neo4j+s://415ed9b1.databases.neo4j.io:7687"
USERNAME = "neo4j"
PASSWORD = "7GBG6XDYOFdwcfgkdcNyDgbtMk6jnZXWxxoAT5vBPVU"

def run_demo_queries():
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    with driver.session() as session:
        print("🧠 NEUROTOME DATABASE EXPLORATION DEMO")
        print("=" * 50)
        
        # Query 1: Find all spinal levels
        print("\n1️⃣ Spinal Levels in Database:")
        result = session.run("MATCH (sl:SpinalLevel) RETURN sl.name as name, sl.level as level ORDER BY sl.level")
        for record in result:
            print(f"   📍 {record['level']}: {record['name']}")
        
        # Query 2: Find sensations and their connections
        print("\n2️⃣ Sample Sensations and Their Connections:")
        result = session.run("""
            MATCH (s:Sensation)-[r]-(connected)
            RETURN s.name as sensation, type(r) as relationship_type, labels(connected)[0] as connected_type
            LIMIT 10
        """)
        for record in result:
            print(f"   🔗 {record['sensation']} --[{record['relationship_type']}]--> {record['connected_type']}")
        
        # Query 3: Find neural pathways
        print("\n3️⃣ Neural Pathways (Tract Relationships):")
        result = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) CONTAINS 'tract' OR type(r) CONTAINS 'spinal'
            RETURN type(r) as pathway, count(r) as connection_count
            ORDER BY connection_count DESC
            LIMIT 8
        """)
        for record in result:
            print(f"   🛤️  {record['pathway']}: {record['connection_count']} connections")
        
        # Query 4: Body parts and their innervation
        print("\n4️⃣ Sample Body Parts:")
        result = session.run("""
            MATCH (b:body)
            WHERE b.name IS NOT NULL
            RETURN b.name as body_part
            LIMIT 10
        """)
        for record in result:
            print(f"   👤 {record['body_part']}")
        
        # Query 5: Complex pathway analysis
        print("\n5️⃣ Dorsal Column Pathway Analysis:")
        result = session.run("""
            MATCH (start)-[:dorsal_column]->(end)
            RETURN labels(start)[0] as start_type, start.name as start_name, 
                   labels(end)[0] as end_type, end.name as end_name
            LIMIT 5
        """)
        for record in result:
            start_name = record['start_name'] or f"[{record['start_type']}]"
            end_name = record['end_name'] or f"[{record['end_type']}]"
            print(f"   📡 {start_name} → {end_name}")
        
        # Query 6: Network analysis
        print("\n6️⃣ Network Connectivity Analysis:")
        result = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as connections
            WHERE connections > 0
            RETURN labels(n)[0] as node_type, avg(connections) as avg_connections, 
                   max(connections) as max_connections, count(n) as node_count
            ORDER BY avg_connections DESC
        """)
        for record in result:
            print(f"   📊 {record['node_type']}: {record['node_count']} nodes, "
                  f"avg {record['avg_connections']:.1f} connections, "
                  f"max {record['max_connections']} connections")
    
    driver.close()
    print("\n✨ Demo completed! Visit http://localhost:5000/explorer for interactive exploration.")

if __name__ == "__main__":
    try:
        run_demo_queries()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
