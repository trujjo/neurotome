function openTab(evt, tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
}

function generateLocationButtons() {
    const locationContainer = document.getElementById('location-buttons-container');
    for (const region in locationData) {
        if (locationData.hasOwnProperty(region)) {
            const regionDiv = document.createElement('div');
            regionDiv.className = 'location-group';

            const regionTitle = document.createElement('div');
            regionTitle.className = 'location-group-title';
            regionTitle.textContent = region;
            regionDiv.appendChild(regionTitle);

            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'location-buttons';

            locationData[region].forEach(location => {
                const locationButton = document.createElement('button');
                locationButton.className = 'location-button';
                locationButton.textContent = location;
                locationButton.onclick = () => toggleButton(locationButton);
                buttonContainer.appendChild(locationButton);
            });

            regionDiv.appendChild(buttonContainer);
            locationContainer.appendChild(regionDiv);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners to tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Add event listeners to filter buttons
    document.querySelectorAll('.tissue-button, .location-button, .relationship-button').forEach(button => {
        button.addEventListener('click', () => {
            button.classList.toggle('active');
        });
    });
});

function toggleButton(button) {
    button.classList.toggle('active');
}
    
    initDriver();
    generateLocationButtons();
});