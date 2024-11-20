let activeTypes = new Set();

function openTab(evt, tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(button => button.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
}

function toggleNodesByType(type) {
    const button = Array.from(document.querySelectorAll('.type-button')).find(btn => btn.textContent.trim() === type);
    if (button) button.classList.toggle('active');

    if (activeTypes.has(type)) activeTypes.delete(type);
    else activeTypes.add(type);

    filterNodes();
}

function filterNodes() {
    console.log('Filtering nodes by:', [...activeTypes]);
    // Add code to update the graph here
}

function clearNodeTypes() {
    activeTypes.clear();
    document.querySelectorAll('.type-button').forEach(btn => btn.classList.remove('active'));
    filterNodes();
}

function showRandomNodesWithRelationships() {
    console.log('Fetching random connected nodes...');
    // Add Neo4j query logic here
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.option-button').forEach(button => {
        button.addEventListener('click', function () {
            document.querySelectorAll('.option-button').forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
            console.log('Detail level:', this.dataset.option);
        });
    });
});
