from flask import Flask, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    nodes = [
        {'id': '1', 'label': 'Node 1', 'properties': {'location': 'A', 'type': 'Type1'}},
        {'id': '2', 'label': 'Node 2', 'properties': {'location': 'B', 'type': 'Type2'}}
    ]
    edges = [{'from': '1', 'to': '2', 'label': 'CONNECTS_TO'}]
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'graph_data': {'nodes': nodes, 'edges': edges},
        'filters': {
            'locations': ['A', 'B'],
            'types': ['Type1', 'Type2']
        }
    })

html_template = '''
# Your HTML template string here
'''

if __name__ == '__main__':
    app.run(debug=True)
