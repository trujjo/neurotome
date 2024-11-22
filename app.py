from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import numpy as np
from backend.neural_network import NeuralNetwork
from error_handling import handle_neo4j_error

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

nn = NeuralNetwork()

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/train', methods=['POST'])
@handle_neo4j_error
def train():
    data = request.get_json()
    inputs = np.array(data['inputs'])
    targets = np.array(data['targets'])
    epochs = data.get('epochs', 1000)
    
    nn.train(inputs, targets, epochs)
    return jsonify({'status': 'success'})

@app.route('/predict', methods=['POST'])
@handle_neo4j_error
def predict():
    data = request.get_json()
    inputs = np.array(data['inputs'])
    
    prediction = nn.predict(inputs)
    return jsonify({'prediction': prediction.tolist()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)