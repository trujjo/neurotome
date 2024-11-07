# Complete Neo4j connection and query code
from neo4j import GraphDatabase
import json

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
            
    def get_all_nodes(self):
        query = """
        MATCH (n)
        RETURN n
        LIMIT 100
        """
        return self.query(query)
    
    def get_all_relationships(self):
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        return self.query(query)
    
    def get_nodes_with_relationships(self):
        query = """
        MATCH (n1)-[r]->(n2)
        RETURN n1, type(r) as relationship_type, n2
        LIMIT 100
        """
        return self.query(query)

# Connection details
uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

# Create connection instance
conn = Neo4jConnection(uri, user, password)

# Example usage
print("Getting nodes...")
nodes = conn.get_all_nodes()
print(json.dumps(nodes[:5], indent=2))  # Print first 5 nodes

print("\
Getting relationship types...")
relationships = conn.get_all_relationships()
print(json.dumps(relationships, indent=2))

print("\
Getting nodes with their relationships...")
connected_nodes = conn.get_nodes_with_relationships()
print(json.dumps(connected_nodes[:5], indent=2))  # Print first 5 relationships

# Close the connection
conn.close()
print("\
Connection closed")
