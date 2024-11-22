
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
        query += ' RETURN n, labels(n)';
        
        const result = await session.run(query, { labels, location, system });
        const nodes = result.records.map(record => {
            const node = record.get('n');
            return {
                id: node.identity.toString(),
                labels: record.get('labels(n)'),
                properties: node.properties,
                size: node.properties.detail === 'major' ? 'large' :
                      node.properties.detail === 'intermediate' ? 'medium' : 'small'
            };
        });
        res.json(nodes);
    } finally {
        await session.close();
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});