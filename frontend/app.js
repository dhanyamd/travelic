// State management
let travelContext = null;

// API endpoints
const API_BASE_URL = 'http://localhost:5000';

// Helper functions
function formatDate(dateStr) {
    if (typeof dateStr === 'string') {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    }
    return dateStr;
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.card-body').prepend(alertDiv);
}

function showProgress(step, message) {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    progressContainer.innerHTML = `
        <div class="progress-step current">
            <i class="fas fa-spinner fa-spin"></i>
            ${message}
        </div>
    `;
    document.querySelector('.card-body').appendChild(progressContainer);
    return progressContainer;
}

function updateProgress(container, step, message, completed = false) {
    const stepDiv = container.querySelector('.progress-step');
    stepDiv.className = `progress-step ${completed ? 'completed' : 'current'}`;
    stepDiv.innerHTML = `
        <i class="fas fa-${completed ? 'check' : 'spinner fa-spin'}"></i>
        ${message}
    `;
}

function displayFlightResults(flights) {
    const container = document.getElementById('flightResults');
    container.innerHTML = '';

    if (!flights || flights.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No flights found matching your criteria.</div>';
        return;
    }

    const flightList = document.createElement('div');
    flightList.className = 'list-group';

    flights.forEach(flight => {
        const flightItem = document.createElement('div');
        flightItem.className = 'list-group-item';
        flightItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-1">${flight.airline}</h5>
                    <p class="mb-1">
                        ${flight.departure_time} - ${flight.arrival_time}<br>
                        ${flight.origin} → ${flight.destination}
                    </p>
                </div>
                <div class="text-end">
                    <h4 class="mb-0">$${flight.price}</h4>
                    <small class="text-muted">${flight.duration}</small>
                </div>
            </div>
        `;
        flightList.appendChild(flightItem);
    });

    container.appendChild(flightList);
}

function displayHotelResults(hotels) {
    const container = document.getElementById('hotelResults');
    container.innerHTML = '';

    if (!hotels || hotels.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No hotels found matching your criteria.</div>';
        return;
    }

    const hotelList = document.createElement('div');
    hotelList.className = 'list-group';

    hotels.forEach(hotel => {
        const hotelItem = document.createElement('div');
        hotelItem.className = 'list-group-item';
        hotelItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-1">${hotel.name}</h5>
                    <p class="mb-1">
                        ${hotel.location}<br>
                        Rating: ${hotel.rating} ⭐
                    </p>
                    <div class="amenities">
                        ${hotel.amenities.map(amenity => `<span class="badge bg-light text-dark me-1">${amenity}</span>`).join('')}
                    </div>
                </div>
                <div class="text-end">
                    <h4 class="mb-0">$${hotel.price_per_night}</h4>
                    <small class="text-muted">per night</small>
                </div>
            </div>
        `;
        hotelList.appendChild(hotelItem);
    });

    container.appendChild(hotelList);
}

// API calls
async function parseTravelDetails(description) {
    const response = await fetch(`${API_BASE_URL}/parse_travel_details`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
    });
    if (!response.ok) throw new Error('Failed to parse travel details');
    return response.json();
}

async function searchFlights(origin, destination, startDate, endDate, preferences) {
    const response = await fetch(`${API_BASE_URL}/search_flights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            origin,
            destination,
            start_date: startDate,
            end_date: endDate,
            preferences
        })
    });
    if (!response.ok) throw new Error('Failed to search flights');
    return response.json();
}

async function searchHotels(location, checkIn, checkOut, occupancy, currency) {
    const response = await fetch(`${API_BASE_URL}/search_hotels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            location,
            check_in: checkIn,
            check_out: checkOut,
            occupancy,
            currency
        })
    });
    if (!response.ok) throw new Error('Failed to search hotels');
    return response.json();
}

async function pollTaskStatus(taskId, taskType) {
    const maxAttempts = 30;
    let attempts = 0;

    while (attempts < maxAttempts) {
        const response = await fetch(`${API_BASE_URL}/task_status/${taskId}`);
        const result = await response.json();

        if (result.status === 'completed') {
            return result.data;
        }
        if (result.status === 'failed') {
            throw new Error(`Failed to get ${taskType} results: ${result.error || 'Unknown error'}`);
        }

        await new Promise(resolve => setTimeout(resolve, 2000));
        attempts++;
    }

    throw new Error(`Timeout waiting for ${taskType} results`);
}

// Main search function
async function planTrip() {
    const description = document.getElementById('travelDescription').value;
    if (!description) {
        showError('Please describe your travel plans');
        return;
    }

    try {
        // Parse travel details
        const parsedData = await parseTravelDetails(description);
        
        // Validate required fields
        if (!parsedData.origin_airport_code || !parsedData.destination_airport_code) {
            showError('Please specify both departure and destination airports in your description');
            return;
        }
        if (!parsedData.start_date || !parsedData.end_date) {
            showError('Please specify both departure and return dates in your description');
            return;
        }

        // Show progress container
        const progressContainer = showProgress(0, 'Finding available flights...');

        // Search for flights
        const flightResponse = await searchFlights(
            parsedData.origin_airport_code,
            parsedData.destination_airport_code,
            parsedData.start_date,
            parsedData.end_date,
            description
        );

        updateProgress(progressContainer, 1, 'Analyzing flight options...');
        const flightResults = await pollTaskStatus(flightResponse.task_id, 'flight');

        // Search for hotels
        updateProgress(progressContainer, 2, 'Searching for hotels...');
        const hotelResponse = await searchHotels(
            parsedData.destination_city_name,
            parsedData.start_date,
            parsedData.end_date,
            1,
            'USD'
        );

        updateProgress(progressContainer, 3, 'Finding the best room options...');
        const hotelResults = await pollTaskStatus(hotelResponse.task_id, 'hotel');

        // Update UI
        document.getElementById('noTripDetails').style.display = 'none';
        document.getElementById('tripResults').style.display = 'block';
        
        // Display results
        displayFlightResults(flightResults);
        displayHotelResults(hotelResults);

        // Update travel context
        travelContext = {
            origin: parsedData.origin_airport_code,
            destination: parsedData.destination_airport_code,
            startDate: formatDate(parsedData.start_date),
            endDate: formatDate(parsedData.end_date),
            occupancy: 1,
            flights: flightResults,
            hotels: hotelResults,
            preferences: description
        };

        // Switch to results tab
        const resultsTab = document.getElementById('results-tab');
        const tab = new bootstrap.Tab(resultsTab);
        tab.show();

    } catch (error) {
        showError(error.message);
    }
} 