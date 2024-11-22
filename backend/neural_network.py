import numpy as np

class NeuralNetwork:
    def __init__(self, layer_sizes):
        if not isinstance(layer_sizes, (list, tuple)) or len(layer_sizes) < 2:
            raise ValueError("layer_sizes must be a list/tuple with at least 2 elements")
        if not all(isinstance(size, int) and size > 0 for size in layer_sizes):
            raise ValueError("All layer sizes must be positive integers")
            
        self.layer_sizes = layer_sizes
        self.weights = []
        self.biases = []
        
        for i in range(len(layer_sizes) - 1):
            self.weights.append(np.random.randn(layer_sizes[i+1], layer_sizes[i]))
            self.biases.append(np.random.randn(layer_sizes[i+1], 1))
    
    def forward(self, input_data):
        if input_data.shape != (self.layer_sizes[0], 1):
            raise ValueError(f"Input shape {input_data.shape} does not match expected shape ({self.layer_sizes[0]}, 1)")
            
        activation = input_data
        for w, b in zip(self.weights, self.biases):
            z = np.dot(w, activation) + b
            # Using np.clip for numeric stability
            z_clipped = np.clip(z, -500, 500)  # prevent overflow
            activation = 1/(1 + np.exp(-z_clipped))
        return activation