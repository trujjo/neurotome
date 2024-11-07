
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
import logging
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    # Example data - in a real application, this would pull from your database
    # without any limit
    nodes = []
    edges = []
    
    # Generate more test data
    for i in range(1, 501):  # Increased to 500 nodes for testing
        nodes.append({
            'id': str(i),
            'label': 'Node ' + str(i),
            'properties': {
                'location': 'Location ' + str((i % 5) + 1),  # 5 different locations
                'type': 'Type ' + str((i % 3) + 1)  # 3 different types
            }
        })
        
        # Create edges (connecting each node to several others)
        if i > 1:
            # Connect to previous node
            edges.append({
                'from': str(i),
                'to': str(i-1),
                'label': 'CONNECTS_TO'
            })
            # Connect to a random earlier node
            if i > 10:
                import random
                random_target = random.randint(1, i-2)
                edges.append({
                    'from': str(i),
                    'to': str(random_target),
                    'label': 'CONNECTS_TO'
                })
    
    # Return the response with properly formatted JSON
    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'graph_data': {
            'nodes': nodes,
            'edges': edges
        },
        'filters': {
            'locations': ['Location ' + str(i) for i in range(1, 6)],
            'types': ['Type ' + str(i) for i in range(1, 4)]
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
