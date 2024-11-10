const nodeTypes = [
    'nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 'sense', 
    'vein', 'artery', 'cv', 'function', 'sensory', 'gland', 'lymph', 
    'head', 'organ', 'sensation', 'skin'
];

const locationData = {
    'head': ['brain', 'eye', 'face', 'ear', 'nose', 'skull', 'mouth', 'head'],
    'neck': ['cervical spine', 'visceral', 'vascular'],
    'upper limb': ['wrist', 'hand', 'fingers', 'arm', 'forearm', 'elbow', 'shoulder'],
    'thorax': ['thoracic spine', 'ribcage', 'heart', 'lung'],
    'abdomen': ['lumbar spine', 'right upper quadrant', 'left upper quadrant', 'right lower quadrant', 'left lower quadrant'],
    'spine': ['spinal cord', 'vertebral', 'tracts', 'sacral spine'],
    'pelvis': ['sacral spine', 'greater pelvis', 'lesser pelvis'],
    'lower limb': ['foot', 'thigh', 'knee', 'leg', 'ankle', 'toes']
};

const neo4jConfig = {
    serverUrl: "neo4j+s://4e5eeae5.databases.neo4j.io:7687",
    serverUser: "neo4j",
    serverPassword: "your-password-here"
};
