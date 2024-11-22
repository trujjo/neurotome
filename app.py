from flask import Flask, request, jsonify
import numpy as np
from neural_network import NeuralNetwork
from error_handling import handle_neo4j_error

app = Flask(__name__)
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
