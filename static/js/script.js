const nodeTypes = [
    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 
    'sense', 'vein', 'artery', 'cv', 'function', 'sensory', 
    'gland', 'lymph', 'head', 'organ', 'sensation', 'skin'
];

const locationData = {
    head: ['brain', 'eye', 'face', 'ear', 'nose', 'skull', 'mouth'],
    neck: ['cervical spine', 'visceral', 'vascular'],
    'upper limb': ['wrist', 'hand', 'fingers', 'arm', 'forearm', 'elbow', 'shoulder'],
    thorax: ['thoracic spine', 'ribcage', 'heart', 'lung'],
    abdomen: ['lumbar spine', 'right upper quadrant', 'left upper quadrant', 'right lower quadrant', 'left lower quadrant'],
    spine: ['spinal cord', 'vertebral', 'tracts', 'sacral spine'],
    pelvis: ['greater pelvis', 'lesser pelvis', 'sacral spine'],
    'lower limb': ['foot', 'thigh', 'knee', 'leg', 'ankle', 'toes']
};

const relationships = [
    'includes', 'perfuses', 'supplies_blood', 'branches', 
    'more_details', 'drains_into', 'lymph_drains', 
    'innervates', 'spinal_cord', 'exits_or_occupies', 
    'nerve_branches', 'spinothalamic_tract', 'pumps_blood', 
    'senses', 'motor_innervation', 'ant_spinothalamic', 
    'lat_spinothalamic', 'dorsal_column', 'controls', 
    'csf_flow', 'releases_hormones', 'sensory_input', 
    'thalamocortical', 'corticospinal_descending', 
    'innervated_by', 'spinothalamic_decussation', 
    'pyramidal_decussation', 'corticospinal_termination'
];

let activeTypes = new Set();

function generateButtons(containerId, data, callback) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear existing content

    Object.entries(data).forEach(([category, items]) => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'location-group';

        const title = document.createElement('div');
        title.className = 'location-group-title';
        title.textContent = category;

        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'location-buttons';

        items.forEach(item => {
            const button = document.createElement('button');
            button.className = 'type-button';
            button.textContent = item;
            button.addEventListener('click', () => {
                button.classList.toggle('active');
                callback(item);
            });
            buttonsDiv.appendChild(button);
        });

        groupDiv.appendChild(title);
        groupDiv.appendChild(buttonsDiv);
        container.appendChild(groupDiv);
    });
}

function toggleNodesByType(type) {
    if (activeTypes.has(type)) {
        activeTypes.delete(type);
    } else {
        activeTypes.add(type);
    }
    filterNodes();
}

function filterNodes() {
    console.log('Filtering nodes by active types:', Array.from(activeTypes));
    // Update D3 graph visualization (placeholder function).
}

function clearNodeTypes() {
    activeTypes.clear();
    document.querySelectorAll('.type-button').forEach(button => {
        button.classList.remove('active');
    });
    filterNodes();
}

document.addEventListener('DOMContentLoaded', () => {
    generateButtons('location-buttons-container', locationData, toggleNodesByType);
});
