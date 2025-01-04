from flask import Flask, render_template_string, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)

# Neo4j database connection credentials
NEO4J_URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Query function to get dermatomes and myotomes
def get_dermatomes_and_myotomes():
    with driver.session() as session:
        query = """
        MATCH (d:Dermatome)-[:CONNECTED_TO]->(m:Myotome)
        RETURN d.level AS dermatome_level, d.name AS dermatome_name, 
               m.name AS myotome_name, m.level AS myotome_level
        """
        result = session.run(query)
        dermatomes = []
        myotomes = []
        for record in result:
            dermatomes.append({
                "level": record["dermatome_level"],
                "name": record["dermatome_name"]
            })
            myotomes.append({
                "level": record["myotome_level"],
                "name": record["myotome_name"]
            })
        return dermatomes, myotomes

@app.route("/")
def index():
    # Get dermatomes and myotomes data from Neo4j
    dermatomes, myotomes = get_dermatomes_and_myotomes()

    # Define the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spinal Lesion Locator</title>
        <style>
            :root {
                --primary-color: #2196F3;
                --hover-color: #1976D2;
                --background-color: #f5f5f5;
                --border-radius: 8px;
            }

            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background-color);
                margin: 0;
                padding: 0;
            }

            .container {
                display: flex;
                height: 100vh;
            }

            /* Sidebar */
            .sidebar {
                width: 250px;
                background-color: #fff;
                padding: 20px;
                box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
                border-right: 1px solid #ddd;
            }

            .sidebar h2 {
                text-align: center;
                color: var(--primary-color);
            }

            .spinal-level {
                margin: 10px 0;
                padding: 8px;
                background-color: #f5f5f5;
                cursor: pointer;
                border-radius: var(--border-radius);
                transition: background-color 0.3s;
            }

            .spinal-level:hover {
                background-color: var(--primary-color);
                color: white;
            }

            .selected {
                background-color: var(--primary-color);
                color: white;
            }

            /* Right Content Area */
            .content {
                flex-grow: 1;
                padding: 20px;
            }

            .interactive-body {
                height: 500px;
                background-color: #e0e0e0;
                position: relative;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
            }

            .interactive-body .highlight {
                position: absolute;
                width: 50px;
                height: 50px;
                background-color: rgba(33, 150, 243, 0.5);
                border-radius: 50%;
                transition: top 0.3s, left 0.3s;
            }

            /* Spinal Level Section */
            .level-section {
                display: none;
            }

            .level-section.active {
                display: block;
            }

            .modern-button {
                background-color: var(--primary-color);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: var(--border-radius);
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .modern-button:hover {
                background-color: var(--hover-color);
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Sidebar -->
            <div class="sidebar">
                <h2>Spinal Levels</h2>
                <div id="level-list">
                    {% for dermatome in dermatomes %}
                        <div class="spinal-level" data-level="{{ dermatome.level }}">{{ dermatome.level }}: {{ dermatome.name }}</div>
                    {% endfor %}
                </div>
            </div>

            <!-- Right Content Area -->
            <div class="content">
                <div class="interactive-body" id="body">
                    <div class="highlight" id="highlight"></div>
                </div>
                <div id="level-content"></div>
                <button class="modern-button" onclick="analyzeLesion()">Analyze Lesion Location</button>
                <div id="results" style="display:none;">
                    <h3>Analysis Results</h3>
                    <div id="result-content"></div>
                </div>
            </div>
        </div>

        <script>
            // Fetch dermatomes and myotomes data from the Flask API
            const dermatomes = {{ dermatomes | tojson }};
            const myotomes = {{ myotomes | tojson }};

            // Attach event listener for the levels
            document.querySelectorAll('.spinal-level').forEach(button => {
                button.addEventListener('click', function() {
                    document.querySelectorAll('.spinal-level').forEach(b => b.classList.remove('selected'));
                    this.classList.add('selected');
                    const level = this.dataset.level;
                    updateBodyVisualization(level);
                });
            });

            function updateBodyVisualization(level) {
                const body = document.getElementById('highlight');
                let position;

                // Define position based on spinal level (dummy positions for demo)
                switch(level) {
                    case 'c1':
                        position = { top: '10%', left: '50%' };
                        break;
                    case 'c2':
                        position = { top: '20%', left: '50%' };
                        break;
                    case 'c3':
                        position = { top: '30%', left: '50%' };
                        break;
                    case 'c4':
                        position = { top: '40%', left: '50%' };
                        break;
                    default:
                        position = { top: '50%', left: '50%' };
                        break;
                }

                body.style.top = position.top;
                body.style.left = position.left;
            }

            function analyzeLesion() {
                // Collect and display analysis
                const results = document.getElementById('results');
                const resultContent = document.getElementById('result-content');
                resultContent.innerHTML = '<p>Analysis based on selected lesions will appear here.</p>';
                results.style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

    return render_template_string(html_content, dermatomes=dermatomes, myotomes=myotomes)

if __name__ == "__main__":
    app.run(debug=True)