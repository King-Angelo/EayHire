document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements
    const filterForm = document.getElementById('filterForm');
    const locationInput = document.querySelector('input[name="location"]');
    const radiusInput = document.querySelector('input[name="radius"]');
    const latitudeInput = document.querySelector('input[name="latitude"]');
    const longitudeInput = document.querySelector('input[name="longitude"]');

    // Function to get user's location
    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    latitudeInput.value = position.coords.latitude;
                    longitudeInput.value = position.coords.longitude;
                    
                    // Reverse geocode to get address
                    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`)
                        .then(response => response.json())
                        .then(data => {
                            locationInput.value = data.display_name;
                        })
                        .catch(error => console.error('Error:', error));
                },
                function(error) {
                    console.error('Error getting location:', error);
                }
            );
        }
    }

    // Initialize location autocomplete
    function initLocationAutocomplete() {
        let timeout = null;
        
        locationInput.addEventListener('input', function() {
            clearTimeout(timeout);
            
            timeout = setTimeout(() => {
                const query = this.value;
                if (query.length > 2) {
                    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            const datalist = document.getElementById('locationSuggestions');
                            datalist.innerHTML = '';
                            
                            data.forEach(item => {
                                const option = document.createElement('option');
                                option.value = item.display_name;
                                option.dataset.lat = item.lat;
                                option.dataset.lon = item.lon;
                                datalist.appendChild(option);
                            });
                        })
                        .catch(error => console.error('Error:', error));
                }
            }, 300);
        });

        locationInput.addEventListener('change', function() {
            const selectedOption = document.querySelector(`#locationSuggestions option[value="${this.value}"]`);
            if (selectedOption) {
                latitudeInput.value = selectedOption.dataset.lat;
                longitudeInput.value = selectedOption.dataset.lon;
            }
        });
    }

    // Handle form submission
    filterForm.addEventListener('submit', function(e) {
        // Remove empty values to keep the URL clean
        const formData = new FormData(this);
        const searchParams = new URLSearchParams();

        for (const [key, value] of formData.entries()) {
            if (value) {
                searchParams.append(key, value);
            }
        }

        window.location.href = `${window.location.pathname}?${searchParams.toString()}`;
        e.preventDefault();
    });

    // Initialize location features if the inputs exist
    if (locationInput && latitudeInput && longitudeInput) {
        // Add datalist for location autocomplete
        const datalist = document.createElement('datalist');
        datalist.id = 'locationSuggestions';
        locationInput.setAttribute('list', 'locationSuggestions');
        locationInput.parentNode.appendChild(datalist);

        initLocationAutocomplete();

        // Add "Use My Location" button if it exists
        const useLocationBtn = document.getElementById('use-my-location');
        if (useLocationBtn) {
            useLocationBtn.addEventListener('click', getUserLocation);
        }
    }

    // Handle salary range inputs
    const salaryMinInput = document.querySelector('input[name="salary_min"]');
    const salaryMaxInput = document.querySelector('input[name="salary_max"]');

    if (salaryMinInput && salaryMaxInput) {
        salaryMinInput.addEventListener('change', function() {
            if (parseInt(this.value) > parseInt(salaryMaxInput.value)) {
                salaryMaxInput.value = this.value;
            }
        });

        salaryMaxInput.addEventListener('change', function() {
            if (parseInt(this.value) < parseInt(salaryMinInput.value)) {
                salaryMinInput.value = this.value;
            }
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 