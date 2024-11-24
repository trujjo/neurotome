const express = require('express');
const neo4j = require('neo4j-driver');
const app = express();

const driver = neo4j.driver(
    'neo4j+s://4e5eeae5.databases.neo4j.io:7687',
    neo4j.auth.basic('neo4j', 'Poconoco16!')
);

app.use(express.static('public'));
app.use(express.json());

app.get('/api/labels', async (req, res) => {
    const session = driver.session();
    try {
        const { locations, sublocations, systems } = req.query;
        let query = 'MATCH (n)';
        const conditions = [];
        const params = {};
        
        if (locations) {
            conditions.push('n.location IN $locations');
            params.locations = locations.split(',');
        }
        if (sublocations) {
            conditions.push('n.sublocation IN $sublocations');
            params.sublocations = sublocations.split(',');
        }
        if (systems) {
            conditions.push('n.system IN $systems');
            params.systems = systems.split(',');
        }
        
        if (conditions.length) {
            query += ' WHERE ' + conditions.join(' AND ');
        }
        
        query += ' WITH DISTINCT labels(n) as nodeLabels UNWIND nodeLabels as label RETURN DISTINCT label';
        
        const result = await session.run(query, params);
        const labels = result.records.map(record => record.get(0));
        res.json(labels);
    } finally {
        await session.close();
    }
});

app.get('/api/distinct-values', async (req, res) => {
    const session = driver.session();
    try {
        const { label } = req.query;
        
        // Simpler property queries with better error handling
        const propertyQuery = (property) => {
            return {
                text: `
                    MATCH (n)
                    ${label ? 'WHERE n:' + label : ''} 
                    WITH n
                    WHERE n.${property} IS NOT NULL
                    RETURN DISTINCT n.${property} AS value
                    ORDER BY value`,
                params: {}
            };
        };

        try {
            // Run queries one at a time to avoid session conflicts
            const locationQuery = propertyQuery('location');
            const sublocationQuery = propertyQuery('sublocation');
            const systemQuery = propertyQuery('system');

            const locationResult = await session.run(locationQuery.text, locationQuery.params);
            const sublocationResult = await session.run(sublocationQuery.text, sublocationQuery.params);
            const systemResult = await session.run(systemQuery.text, systemQuery.params);

            const response = {
                locations: locationResult.records.map(record => record.get('value')).filter(Boolean),
                sublocations: sublocationResult.records.map(record => record.get('value')).filter(Boolean),
                systems: systemResult.records.map(record => record.get('value')).filter(Boolean)
            };

            res.json(response);
        } catch (error) {
            console.error('Neo4j query error:', error);
            res.status(500).json({ 
                error: 'Database query failed',
                details: error.message 
            });
        }
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({ 
            error: 'Server error occurred',
            details: error.message 
        });
    } finally {
        await session.close();
    }
});

app.post('/api/nodes', async (req, res) => {
    const { labels, locations, sublocations, systems, detail } = req.body;
    const session = driver.session();
    
    try {
        // Build label pattern and query
        const labelPattern = labels && labels.length 
            ? ':' + labels.join(':')
            : '';

        const conditions = [];
        const params = {};

        if (locations && locations.length) {
            conditions.push('n.location IN $locations');
            params.locations = locations;
        }
        if (sublocations && sublocations.length) {
            conditions.push('n.sublocation IN $sublocations');
            params.sublocations = sublocations;
        }
        if (systems && systems.length) {
            conditions.push('n.system IN $systems');
            params.systems = systems;
        }
        if (detail && detail.length) {
            conditions.push('n.detail IN $detail');
            params.detail = detail;
        }

        const query = `
            MATCH (n${labelPattern})
            ${conditions.length ? 'WHERE ' + conditions.join(' AND ') : ''}
            MATCH (n)-[r]->(m)
            RETURN n, labels(n), collect({rel: r, target: m}) as relationships`;

        const result = await session.run(query, params);
        const nodes = new Map();
        const relationships = [];

        result.records.forEach(record => {
            const node = record.get('n');
            const nodeId = node.identity.toString();
            
            // Add node if not already added
            if (!nodes.has(nodeId)) {
                nodes.set(nodeId, {
                    id: nodeId,
                    labels: record.get('labels(n)'),
                    properties: node.properties,
                    size: node.properties.detail === 'comprehensive' ? 'large' :
                          node.properties.detail === 'meticulous' ? 'medium' : 'small'
                });
            }

            // Add relationships and target nodes
            record.get('relationships').forEach(rel => {
                relationships.push({
                    source: nodeId,
                    target: rel.target.identity.toString(),
                    type: rel.rel.type,
                    properties: rel.rel.properties
                });

                // Add target node if not already added
                const targetId = rel.target.identity.toString();
                if (!nodes.has(targetId)) {
                    nodes.set(targetId, {
                        id: targetId,
                        labels: rel.target.labels,
                        properties: rel.target.properties,
                        size: rel.target.properties.detail === 'comprehensive' ? 'large' :
                              rel.target.properties.detail === 'meticulous' ? 'medium' : 'small'
                    });
                }
            });
        });

        res.json({
            nodes: Array.from(nodes.values()),
            relationships: relationships
        });
    } finally {
        await session.close();
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});