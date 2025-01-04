const express = require('express');
const path = require('path');
const neo4j = require('neo4j-driver');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.static('public'));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/explore.html'));
});

app.get('/explore', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/explore.html'));
});

app.get('/search', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/search.html'));
});

app.get('/learn', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/learn.html'));
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});