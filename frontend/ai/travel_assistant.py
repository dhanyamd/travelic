from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from dotenv import load_dotenv
from ai.models import model
from ai.context import generate_travel_context_memory

load_dotenv() 

class TravelAssistant: 
    def __init__(self, travel_context):
        self.context = travel_context 
        self.assistant = self.create_assistant() 

    def _create_assistant(self):
        """Create a travel assistant with context about the trip"""
        memory = ConversationBufferMemory()
        
        # Add travel context to memory
        memory.chat_memory.add_ai_message(
            generate_travel_context_memory(self.context)
        )
        
        return ConversationChain(
            llm=model,
            memory=memory,
            verbose=True
        )

    def get_response(self, prompt):
        """Get response from the assistant"""
        return self.assistant.predict(input=prompt)

    @staticmethod
    def get_suggested_prompts():
        """Return suggested prompts for the user"""
        return {
            "column1": [
                "Create a day-by-day itinerary for my trip",
                "What are the must-see attractions?",
                "Suggest some local restaurants"
            ],
            "column2": [
                "What should I pack for this trip?",
                "How do I get from the airport to my hotel?",
                "What's the weather like during my stay?"
            ]
        } 