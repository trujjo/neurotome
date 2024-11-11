from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('neo4j_explorer.html')

# Example additional route for API
@app.route('/api/graph-data')
def get_graph_data():
    # Add any backend logic here
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
