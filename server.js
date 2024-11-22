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
        const result = await session.run('CALL db.labels()');
        const labels = result.records.map(record => record.get(0));
        res.json(labels);
    } finally {
        await session.close();
    }
});

app.get('/api/distinct-values', async (req, res) => {
    const session = driver.session();
    try {
        const locationResult = await session.run('MATCH (n) WHERE EXISTS(n.location) RETURN DISTINCT n.location');
        const systemResult = await session.run('MATCH (n) WHERE EXISTS(n.system) RETURN DISTINCT n.system');
        
        res.json({
            locations: locationResult.records.map(record => record.get(0)),
            systems: systemResult.records.map(record => record.get(0))
        });
    } finally {
        await session.close();
    }
});

app.post('/api/nodes', async (req, res) => {
    const { labels, location, system } = req.body;
    const session = driver.session();
    try {
        let query = 'MATCH (n)';
        const conditions = [];
        if (labels && labels.length) {
            conditions.push(`ANY(label IN labels(n) WHERE label IN $labels)`);
        }
        if (location) {
            conditions.push('n.location = $location');
        }
        if (system) {
            conditions.push('n.system = $system');
        }
        if (conditions.length) {
            query += ' WHERE ' + conditions.join(' AND ');
        }
        query = query.replace('RETURN n, labels(n)', 
            'MATCH (n)-[r]->(m) RETURN n, labels(n), collect({rel: r, target: m}) as relationships');
        
        const result = await session.run(query, { labels, location, system });
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