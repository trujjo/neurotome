const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 3000;

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy' });
});

// Serve static files from the public directory
app.use(express.static('public'));

// Route for database explorer
app.get('/explorer', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'explorer.html'));
});

// Handle all other routes by serving index.html
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
    console.log(`Database explorer available at: http://localhost:${port}/explorer`);
});