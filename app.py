from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
from flask_cors import CORS
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Neo4j connection configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Poconoco16!")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_neo4j_driver():
    return driver

@app.route('/')
def index():
    return render_template('index.html')

def convert_neo4j_to_json(record):
    """Convert Neo4j records to JSON-serializable format"""
    try:
        source = record['n']
        target = record['m']
        rel = record['r']
        
        logger.debug(f"Processing record: {source.labels}, {target.labels if target else 'None'}")
        
        node_data = {
            'id': source.id,
            'labels': [label.lower() for label in source.labels],
            'properties': {
                k.lower(): str(v).lower() if isinstance(v, str) else v 
                for k, v in source.items()
            }
        }
        
        if target and rel:
            relationship_data = {
                'source': source.id,
                'target': target.id,
                'type': rel.type.lower(),
                'properties': {
                    k.lower(): str(v).lower() if isinstance(v, str) else v 
                    for k, v in rel.items()
                }
            }
            return node_data, relationship_data
            
        return node_data, None
            
    except Exception as e:
        logger.error(f"Error converting Neo4j record: {str(e)}")
        raise

@app.route('/api/nodes/random')
def get_random_nodes():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('''
                MATCH (n)
                WITH n, rand() as random
                ORDER BY random
                LIMIT 5
                MATCH (n)-[r]-(m)
                RETURN DISTINCT n, r, m
                LIMIT 100
            ''')
            
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                source = record['n']
                target = record['m']
                rel = record['r']
                
                # Add nodes if not already added
                for node in (source, target):
                    if node.id not in node_ids:
                        nodes.append({
                            'id': node.id,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        })
                        node_ids.add(node.id)
                
                # Add relationship
                relationships.append({
                    'source': source.id,
                    'target': target.id,
                    'type': rel.type
                })
            
            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })
            
    except Exception as e:
        app.logger.error(f"Error in get_random_nodes: {str(e)}")
        return jsonify({"error": str(e)}), 500
                
@app.route('/api/neo4j/status')
def neo4j_status():
    try:
        with get_neo4j_driver().session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "disconnected"}), 500

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/api/nodes/filtered', methods=['GET'])
def get_filtered_nodes():
    try:
        labels = request.args.getlist('labels')
        relationships = request.args.getlist('relationships')
        location = request.args.get('location')

        query = """
        MATCH (n)
        WHERE 1=1
        """
        params = {}

        if labels:
            query += " AND any(label IN $labels WHERE label in labels(n))"
            params['labels'] = labels

        if location:
            query += " AND n.location = $location"
            params['location'] = location

        if relationships:
            query += """
            WITH n
            MATCH (n)-[r]->(m)
            WHERE type(r) IN $relationships
            """
            params['relationships'] = relationships
        else:
            query += """
            WITH n
            MATCH (n)-[r]->(m)
            """

        query += " RETURN DISTINCT n, r, m LIMIT 100"

        with get_neo4j_driver().session() as session:
            result = session.run(query, params)
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                source = record['n']
                target = record['m']
                rel = record['r']
                
                for node in (source, target):
                    if node.id not in node_ids:
                        nodes.append({
                            'id': node.id,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        })
                        node_ids.add(node.id)
                
                relationships.append({
                    'source': source.id,
                    'target': target.id,
                    'type': rel.type
                })

            logger.debug(f"Filtered nodes: {nodes}")
            logger.debug(f"Filtered relationships: {relationships}")
            
            return jsonify({
                'nodes': nodes,
                'relationships': relationships
            })

    except Exception as e:
        logger.error(f"Error in get_filtered_nodes: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Backend returns:
{
    'nodes': [
        {
            'id': node.id,
            'labels': list(node.labels),
            'properties': dict(node)
        }
    ],
    'relationships': [
        {
            'source': source.id,
            'target': target.id,
            'type': rel.type
        }
    ]
}

function visualizeData(data) {
    console.log('Visualizing data:', data);
    if (!data || !data.nodes || !data.relationships) {
        console.error('Invalid data format:', data);
        return;
    }

    const width = document.getElementById('visualization').clientWidth;
    const height = document.getElementById('visualization').clientHeight;

    // Clear previous visualization
    d3.select('#visualization').selectAll('*').remove();

    const svg = d3.select('#visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create simulation with proper data references
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.relationships)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Draw relationships
    const link = svg.append('g')
        .selectAll('line')
        .data(data.relationships)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 1);

    // Draw nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter()
        .append('circle')
        .attr('r', 5)
        .attr('fill', d => getNodeColor(d.labels[0]))
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Add node labels
    const labels = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter()
        .append('text')
        .text(d => d.properties.name || d.labels[0])
        .attr('font-size', '8px')
        .attr('dx', 8)
        .attr('dy', 3)
        .style('fill', '#fff');

    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

        labels
            .attr('x', d => d.x + 8)
            .attr('y', d => d.y);
    });
}

function getNodeColor(label) {
    const colors = {
        'nerve': '#ff7f0e',
        'bone': '#2ca02c',
        'neuro': '#d62728',
        'region': '#9467bd',
        'viscera': '#8c564b',
        'muscle': '#e377c2',
        'sense': '#7f7f7f',
        'vein': '#bcbd22',
        'artery': '#17becf',
        'cv': '#1f77b4'
    };
    return colors[label.toLowerCase()] || '#666666';
}
