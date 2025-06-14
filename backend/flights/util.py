def flight_scrape_task(preferences, url):
    return f"""Follow these steps in order:
    Go to {url}
    1. Find and click the 'Search' button on the page

    2. For the outbound flight (first leg of the journey):
        - Identify the best outbound flight based on user preferences: {preferences}
        - Click on this outbound flight to select it
        - Store the outbound flight details including:
            * Departure time and date
            * Arrival time and date
            * Price
            * Number of stops
            * Stop Location and Time
            * Duration
            * Airlines
            * Origin and destination airports

    3. For the return flight (second leg of the journey):
        - After selecting the outbound flight, you'll see return flight options
        - Identify the best return flight based on user preferences: {preferences}
        - Store the return flight details including:
            * Departure time and date
            * Arrival time and date
            * Price
            * Number of stops
            *Stop Location and Time
            * Duration
            * Airlines
            * Origin and destination airports

    4. Create a structured JSON response with both flights:
        {{
            "outbound_flight": {{
                "start_time": "...",
                "end_time": "...",
                "origin": "...",
                "destination": "...",
                "price": "",
                "num_stops": 0,
                "duration": "...",
                "airline": "...",
                "stop_locations": "...",
            }},
            "return_flight": {{
                "start_time": "...",
                "end_time": "...",
                "origin": "...",
                "destination": "...",
                "price": "",
                "num_stops": 0,
                "duration": "...",
                "airline": "...",
                "stop_locations": "...",
            }}
        }}

    5. Important:
        - Make sure to capture BOTH outbound and return flight details
        - Each flight should have its own complete set of details
        - Store the duration in the format "Xh Ym" (e.g., "2h 15m")
        - Return the total price of the flight, which is the maximum of the two prices listed
    """