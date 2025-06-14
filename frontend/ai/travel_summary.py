from dotenv import load_dotenv
from ai.models import model

load_dotenv()

class TravelSummary:
    def __init__(self):
        self.model = model

    def get_summary(self, flights, hotels, requirements, **kwargs):
        """Get LLM summary of flights and hotels"""
        response = self.model.invoke(
            f"""Summarize the following flight and hotels, including the total price for the duration of the stay, and give me a nicely formatted output: 
            
            Given this information:
            Flights: {flights} (the price is PER night)
            Hotels: {hotels}
            
            Calculate the total price for the duration of the stay based on the provided information. The duration is from {kwargs.get('start_date', 'unknown start date')} to {kwargs.get('end_date', 'unknown end date')}.
            
            Make a recommendation for the best hotel and flight based on this: {requirements} {kwargs}
            
            Note: the price of the flight is the maximum of the two prices listed, NOT the combined price. The total price includes both the flight and hotel costs for the entire duration.
            
            Only used basic markdown formatting in your reply so it can be easily parsed by the frontend.
            """
        )
        return response.content 