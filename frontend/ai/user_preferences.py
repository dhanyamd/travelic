from ai.schemas import travel_preferences_schema
from ai.models import model

user_input_model = model.with_structured_output(travel_preferences_schema)

def get_travel_details(requirements, **kwargs):
    prompt = f"""
        Read the following information from the user and extract the data into the structured output fields.
        {requirements} {kwargs}
        When providing dates give the format like this: May 2, 2025
        When providing airport codes give 3 uppercase letters
    """
    return user_input_model.invoke(prompt)