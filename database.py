
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def verify_connection(self):
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful!' as message")
                return result.single()['message']
        except Exception as e:
            return f"Connection failed: {str(e)}"
