# Example code to connect to Neo4j and query data
from neo4j import GraphDatabase

# Connection details
uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

# Create a driver instance
driver = GraphDatabase.driver(uri, auth=(user, password))

# Function to execute queries
def run_query(tx, query):
    result = tx.run(query)
    return [record for record in result]

# Test connection and get some basic info
with driver.session() as session:
    # Example query to get node labels
    query = "CALL db.labels()"
    result = session.execute_write(run_query, query)
    print("Available node labels:")
    for record in result:
        print(record[0])
        
    # Example query to get relationship types
    query = "CALL db.relationshipTypes()"
    result = session.execute_write(run_query, query)
    print("\
Available relationship types:")
    for record in result:
        print(record[0])

driver.close()
