
require('dotenv').config();
const express = require('express');
const path = require('path');
const neo4j = require('neo4j-driver');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.static('public'));

// Neo4j Connection
const driver = neo4j.driver(
    process.env.NEO4J_URI || 'neo4j+s://4e5eeae5.databases.neo4j.io:7687',
    neo4j.auth.basic(
        process.env.NEO4J_USER || 'neo4j',
        process.env.NEO4J_PASSWORD || 'Poconoco16!'
    )
);

// Test database connection
const testConnection = async () => {
    const session = driver.session();
    try {
        await session.run('RETURN 1');
        console.log('Connected to Neo4j database');
    } catch (error) {
        console.error('Database connection failed:', error);
    } finally {
        await session.close();
    }
};

// API Routes
app.get('/api/test', async (req, res) => {
    try {
        const session = driver.session();
        const result = await session.run('RETURN "API is working" as message');
        await session.close();
        res.json({ message: result.records[0].get('message') });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Serve index.html for all other routes (SPA support)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Start server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
    testConnection();
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    await driver.close();
    process.exit(0);
});
