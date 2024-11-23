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
        const { label, locations, sublocations, systems } = req.query;
        let conditions = [];
        const params = {};

        let baseQuery = query => {
            let q = 'MATCH (n) WHERE ' + query + ' IS NOT NULL';
            if (label) {
                q += ` AND n:${label}`;
            }
            if (locations) {
                q += ' AND n.location IN $locations';
                params.locations = locations.split(',');
            }
            if (sublocations) {
                q += ' AND n.sublocation IN $sublocations';
                params.sublocations = sublocations.split(',');
            }
            if (systems) {
                q += ' AND n.system IN $systems';
                params.systems = systems.split(',');
            }
            return q;
        };

        const locationQuery = baseQuery('n.location') + ' RETURN DISTINCT n.location';
        const sublocationQuery = baseQuery('n.sublocation') + ' RETURN DISTINCT n.sublocation';
        const systemQuery = baseQuery('n.system') + ' RETURN DISTINCT n.system';
        
        const locationResult = await session.run(locationQuery, params);
        const sublocationResult = await session.run(sublocationQuery, params);
        const systemResult = await session.run(systemQuery, params);
        
        res.json({
            locations: locationResult.records.map(record => record.get(0)).filter(Boolean),
            sublocations: sublocationResult.records.map(record => record.get(0)).filter(Boolean),
            systems: systemResult.records.map(record => record.get(0)).filter(Boolean)
        });
    } finally {
        await session.close();
    }
});

app.post('/api/nodes', async (req, res) => {
    const { labels, locations, sublocations, systems, detail } = req.body;
    const session = driver.session();
    try {
        let query = 'MATCH (n)';
        const conditions = [];
        const params = {};

        if (labels && labels.length) {
            conditions.push(`${labels.map(label => `n:${label}`).join(' AND ')}`);
        }
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

        if (conditions.length) {
            query += ' WHERE ' + conditions.join(' AND ');
        }
        
        query += ' MATCH (n)-[r]->(m) RETURN n, labels(n), collect({rel: r, target: m}) as relationships';
        
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
                    size: node.properties.detail === 'major' ? 'large' :
                          node.properties.detail === 'intermediate' ? 'medium' : 'small'
                });
            }

            // Add relationships
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
                        size: rel.target.properties.detail === 'major' ? 'large' :
                              rel.target.properties.detail === 'intermediate' ? 'medium' : 'small'
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