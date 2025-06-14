travel_preferences_schema = {
    "title": "TravelPlan",
    "description": "A schema for a travel plan including destination, dates, budget, accommodation, flight, activities, and food preferences.",
    "type": "object",
    "properties": {
        "origin_airport_code": {"type": "string"},
        "destination_airport_code": {"type": "string"},
        "destination_city_name": {"type": "string"},
        "num_guests": {"type": "integer"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "budget": {"type": "integer"},
        "accommodation": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "max_price_per_night": {"type": "integer"},
                "amenities": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "flight": {
            "type": "object",
            "properties": {
                "class": {"type": "string"},
                "direct": {"type": "boolean"}
            }
        },
        "activities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "food_preferences": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["destination", "dates", "budget", "accommodation", "flight", "activities", "food_preferences"]
}