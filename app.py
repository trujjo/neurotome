from neo4j import GraphDatabase

# Connection details
URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
AUTH = ("neo4j", "Poconoco16!")

class Neo4jConnection:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        
    def close(self):
        self.driver.close()
        
    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record for record in result]
