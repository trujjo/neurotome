from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import numpy as np
from backend.neural_network import NeuralNetwork

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Replace the simple initialization with layer sizes
nn = NeuralNetwork(layer_sizes=[2, 4, 1])  # Example: 2 inputs, 4 hidden neurons, 1 output

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/train', methods=['POST'])
def train():
    data = request.get_json()
    inputs = np.array(data['inputs'])
    targets = np.array(data['targets'])
    epochs = data.get('epochs', 1000)
    
    nn.train(inputs, targets, epochs)
    return jsonify({'status': 'success'})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    inputs = np.array(data['inputs'])
    
    prediction = nn.predict(inputs)
    return jsonify({'prediction': prediction.tolist()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)