from flask import Flask, render_template_string, jsonify
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    try:
        return render_template_string(html_template)
    except Exception as e:
        logging.error(f"Error rendering template: {str(e)}")
        return "An error occurred", 500

@app.route('/refresh-data')
def refresh_data():
    try:
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
    except Exception as e:
        logging.error(f"Error in refresh_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Your html_template string remains the same

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
