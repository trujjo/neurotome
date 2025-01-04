
document.addEventListener('DOMContentLoaded', function() {
    // Create neural network background
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    // Neuron class
    class Neuron {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.connections = [];
            this.radius = 2;
            this.pulseRadius = 2;
            this.pulseOpacity = 0.5;
        }

        connect(neurons) {
            for (let neuron of neurons) {
                if (neuron !== this && Math.random() < 0.3) {
                    this.connections.push(neuron);
                }
            }
        }

        pulse() {
            this.pulseRadius += 0.3;
            this.pulseOpacity -= 0.01;
            if (this.pulseOpacity <= 0) {
                this.pulseRadius = 2;
                this.pulseOpacity = 0.5;
            }
        }

        draw() {
            // Draw pulse
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.pulseRadius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(144, 205, 244, ${this.pulseOpacity})`;
            ctx.fill();

            // Draw neuron
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#4299e1';
            ctx.fill();

            // Draw connections
            for (let neuron of this.connections) {
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                ctx.lineTo(neuron.x, neuron.y);
                ctx.strokeStyle = 'rgba(144, 205, 244, 0.2)';
                ctx.stroke();
            }
        }
    }

    // Create neurons
    const neurons = Array.from({ length: 50 }, () => new Neuron());
    neurons.forEach(neuron => neuron.connect(neurons));

    // Animation loop
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        neurons.forEach(neuron => {
            neuron.pulse();
            neuron.draw();
        });

        requestAnimationFrame(animate);
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    animate();
});
