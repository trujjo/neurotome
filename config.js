// Neo4j connection configuration
const NEO4J_URI = "neo4j+s://4e5eeae5.databases.neo4j.io:7687";
const NEO4J_USER = "neo4j";
const NEO4J_PASSWORD = "Poconoco16!";

// Filter data
const tissueTypes = ['nerve', 'bone', 'neuro', 'region', 'viscera', 'muscle', 'sense', 'vein', 'artery', 'cv', 'function', 'sensory', 'gland', 'lymph', 'head', 'organ', 'sensation', 'skin'];

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

const relationships = ['includes', 'perfuses', 'supplies_blood', 'branches', 'more_details', 'drains_into', 
    'lymph_drains', 'innervates', 'spinal_cord', 'exits_or_occupies', 'nerve_branches',
    'spinothalamic_tract', 'pumps_blood', 'senses', 'motor_innervation', 'ant_spinothalamic',
    'lat_spinothalamic', 'dorsal_column', 'controls', 'csf_flow', 'releases_hormones',
    'sensory_input', 'thalamocortical', 'corticospinal_descending', 'innervated_by',
    'spinothalamic_decussation', 'pyramidal_decussation', 'corticospinal_termination'];
