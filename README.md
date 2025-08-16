# Neurotome

Interactive brain anatomy visualization platform with real-time neural network animations and Neo4j database exploration.

## Features

- 🧠 3D brain visualization
- 🔄 Neural network animations
- 🧭 Interactive anatomy explorer
- 🔍 Comprehensive search database
- 📚 Educational resources
- **🗄️ Neo4j Database Explorer** - Interactive exploration of neuroanatomy data with dynamic graph visualization

## Database Explorer

The Neo4j Database Explorer provides a comprehensive interface to explore your neuroanatomy database:

### Features:
- **Interactive Graph Visualization**: D3.js-powered network graphs showing nodes and relationships
- **Real-time Search**: Search through nodes by properties with instant results
- **Node Labels Browser**: Browse all node types (Sensation, SpinalLevel, artery, body, nerve, vertebra)
- **Relationship Explorer**: Explore various neurological pathways and connections
- **Detailed Node Information**: View properties and relationships for individual nodes
- **Database Statistics**: Overview of total nodes, relationships, and data distribution
- **Dynamic Filtering**: Filter graphs by node labels and relationship types

### Access:
Visit `/explorer` endpoint to access the database explorer interface.

## Setup

### For Node.js Server (Static Files):
1. Clone the repository
2. Run `npm install`
3. Start the server with `npm start`
4. Visit `http://localhost:3000`

### For Python Flask Server (With Neo4j Explorer):
1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Start the Flask server: `python app.py`
4. Visit `http://localhost:5000` for the main app
5. Visit `http://localhost:5000/explorer` for the database explorer

## Development

- `npm run dev` for Node.js development mode
- `npm test` to run tests
- `python app.py` to run Flask server with database connectivity

## Database Schema

Your Neo4j database contains:
- **Node Types**: Sensation, SpinalLevel, artery, body, nerve, vertebra
- **Relationship Types**: Various neurological pathways including corticospinal_tract, spinothalamic, dorsal_column, and many others
- **Statistics**: 2,143+ nodes and 6,565+ relationships