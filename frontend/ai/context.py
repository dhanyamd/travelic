def generate_travel_context_memory(travel_context):
    return f"""I am your travel assistant. I have access to your travel details:
            - Flight from {travel_context['origin']} to {travel_context['destination']}
            - Travel dates: {travel_context['start_date']} to {travel_context['end_date']}
            - Number of travelers: {travel_context['occupancy']}
            
            Flight Details: {travel_context['flights']}
            Hotel Details: {travel_context['hotels']}
            
            Your preferences: {travel_context['preferences']}"""