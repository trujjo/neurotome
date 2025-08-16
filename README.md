# Neurotome

A secure Flask application for visualizing Neo4j graph databases with interactive D3.js force-directed graphs.

## 🚀 Features

- **Secure Architecture**: No hardcoded credentials, environment variable validation
- **Modern UI**: Clean, responsive design with dark theme
- **Interactive Visualization**: D3.js powered force-directed graph
- **Robust Error Handling**: Comprehensive error handling with decorators
- **Health Monitoring**: Built-in health check endpoint for deployments
- **Production Ready**: Proper logging, connection management, and deployment configuration

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- Neo4j Database (local or cloud)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd neurotome
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Neo4j credentials:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password_here
   FLASK_ENV=development
   PORT=5000
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   Or use Flask directly:
   ```bash
   flask run
   ```

## 🌐 Deployment

### Render.com

The application is configured for Render.com deployment with `render.yaml`. Set the following environment variables in your Render dashboard:

- `NEO4J_URI`: Your Neo4j connection URI
- `NEO4J_USER`: Your Neo4j username  
- `NEO4J_PASSWORD`: Your Neo4j password

### Other Platforms

For other platforms, ensure you set the required environment variables and use `gunicorn` for production:

```bash
gunicorn app:app
```

## 📊 API Endpoints

- `GET /` - Main application interface
- `GET /health` - Health check endpoint
- `GET /api/nodes/random` - Fetch random connected nodes
- `GET /api/neo4j/status` - Check Neo4j connection status

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEO4J_URI` | Neo4j database URI | Yes | - |
| `NEO4J_USER` | Neo4j username | Yes | - |
| `NEO4J_PASSWORD` | Neo4j password | Yes | - |
| `FLASK_ENV` | Flask environment | No | `production` |
| `PORT` | Application port | No | `5000` |

### Neo4j Requirements

Your Neo4j database should contain nodes with relationships. The application queries for:
- Nodes with any labels
- Relationships between connected nodes
- Node properties (especially `name`, `title`)

## 🛡️ Security Features

- **No credential exposure**: All sensitive data is handled server-side
- **Environment validation**: Application validates required environment variables on startup
- **Proper error handling**: Comprehensive error handling without exposing internal details
- **Connection management**: Proper Neo4j driver lifecycle management

## 🎨 Customization

### Adding New Visualizations

1. Create new API endpoints in `app.py`
2. Add corresponding JavaScript functions in `static/js/graph.js`
3. Extend the UI in `templates/index.html`

### Styling

Modify the CSS variables in `templates/index.html` or add styles to `static/css/styles.css`:

```css
:root {
    --accent-color: #your-color;
    --background-dark: #your-background;
    /* ... other variables */
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify Neo4j is running and accessible
   - Check your credentials in `.env`
   - Ensure firewall allows connections to Neo4j port

2. **Missing Environment Variables**
   - Check that `.env` file exists and contains all required variables
   - Verify environment variables are loaded correctly

3. **Graph Not Rendering**
   - Open browser developer tools to check for JavaScript errors
   - Verify the `/api/nodes/random` endpoint returns data

### Logs

Check application logs for detailed error information:
```bash
python run.py
```

## 📝 Development

### Code Structure

```
neurotome/
├── app.py              # Main Flask application
├── error_handling.py   # Error handling decorators
├── run.py             # Application runner
├── requirements.txt   # Python dependencies
├── render.yaml        # Render.com deployment config
├── static/
│   ├── css/
│   │   └── styles.css # Additional styles
│   └── js/
│       └── graph.js   # Graph visualization logic
└── templates/
    └── index.html     # Main UI template
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Neo4j for the graph database
- D3.js for visualization capabilities
- Flask for the web framework
