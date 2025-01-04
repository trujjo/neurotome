class BrainViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer();
        
        this.init();
        this.animate();
    }

    init() {
        // Setup renderer
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Setup camera
        this.camera.position.z = 5;

        // Add basic brain mesh (placeholder)
        const geometry = new THREE.SphereGeometry(2, 32, 32);
        const material = new THREE.MeshPhongMaterial({
            color: 0xcccccc,
            transparent: true,
            opacity: 0.8
        });
        this.brain = new THREE.Mesh(geometry, material);
        this.scene.add(this.brain);

        // Add lighting
        const light = new THREE.PointLight(0xffffff, 1, 100);
        light.position.set(10, 10, 10);
        this.scene.add(light);
        
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);

        // Add controls
        this.addControls();
    }

    addControls() {
        document.getElementById('rotate').addEventListener('click', () => {
            this.brain.rotation.y += Math.PI / 2;
        });

        document.getElementById('zoom').addEventListener('click', () => {
            this.camera.position.z = Math.max(3, this.camera.position.z - 1);
        });

        document.getElementById('reset').addEventListener('click', () => {
            this.brain.rotation.set(0, 0, 0);
            this.camera.position.z = 5;
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.brain.rotation.y += 0.005;
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize viewer when page loads
window.addEventListener('load', () => {
    const viewer = new BrainViewer('brain-viewer');
});