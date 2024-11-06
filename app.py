from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import os
import logging
import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = "bolt://4e5eeae5.databases.neo4j.io:7687"
user = "neo4j"
password = "Poconoco16!"

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=True
        )
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
            logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_graph_metadata():
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Get node types with their locations and sublocations
            query = """
            MATCH (n)
            WITH DISTINCT labels(n) as labels, n.location as location, n.sublocation as sublocation
            RETURN labels, location, sublocation
            """
            result = session.run(query)
            
            node_types = set()
            locations = set()
            sublocations = set()
            
            for record in result:
                node_types.update(record['labels'])
                if record['location']:
                    locations.add(record['location'])
                if record['sublocation']:
                    sublocations.add(record['sublocation'])

            # Get relationship types
            rel_query = """
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as type
            """
            rel_result = session.run(rel_query)
            relationship_types = [record['type'] for record in rel_result]

            return {
                'node_types': sorted(list(node_types)),
                'locations': sorted(list(locations)),
                'sublocations': sorted(list(sublocations)),
...
 addNodesBySublocation(sublocation) {
            fetch('/get_nodes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    node_type: null,
                    location: null,
                    sublocation: sublocation
                })
            })
            .then(response => response.json())
            .then(newNodes => {
                nodes.update(newNodes);
                updateFilterButtons();
            });
        }

        function addRelationships(relType) {
            fetch('/get_relationships', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    relationship_type: relType
                })
            })
            .then(response => response.json())
            .then(newEdges => {
                edges.update(newEdges);
                updateFilterButtons();
            });
        }

        function clearNetwork() {
            nodes.clear();
            edges.clear();
            updateFilterButtons();
        }

        function updateFilterButtons() {
            // Disable buttons if no nodes match the criteria
            document.querySelectorAll('.filter-button').forEach(button => {
                const criteria = button.getAttribute('data-criteria');
                const value = button.getAttribute('data-value');
                const hasNodes = nodes.get().some(node => node[criteria] === value);
                button.disabled = !hasNodes;
            });
        }
    </script>
</body>
</html>
