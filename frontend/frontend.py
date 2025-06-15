import streamlit as st
from datetime import datetime
from ai.travel_assistant import TravelAssistant
from ai.travel_summary import TravelSummary
from api.api_client import TravelAPIClient
from ai.research_assistant import ResearchAssistant
from ai.user_preferences import get_travel_details
from constants import *

def format_date(date_str):
    """Format date string for display and API calls"""
    if isinstance(date_str, datetime):
        return date_str.strftime("%B %d, %Y")
    return date_str

ResearchAssistant._initialize_vector_store()

def initialize_session_state():
    """Initialize all session state variables"""
    if 'search_requirements' not in st.session_state:
        st.session_state.search_requirements = ""
    if 'travel_assistant' not in st.session_state:
        st.session_state.travel_assistant = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'research_assistant' not in st.session_state:
        st.session_state.research_assistant = None
    if 'research_messages' not in st.session_state:
        st.session_state.research_messages = []
    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = None
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = None

def display_parsed_travel_details(parsed_data):
    """Display and validate parsed travel details"""
    with st.expander("Parsed Travel Details", expanded=True):
        st.markdown("### Here's what we understood:")
        details = {
            "From": parsed_data['origin_airport_code'] or "Not specified",
            "To": parsed_data['destination_airport_code'] or "Not specified",
            "Departure": format_date(parsed_data['start_date']) if parsed_data['start_date'] else "Not specified",
            "Return": format_date(parsed_data['end_date']) if parsed_data['end_date'] else "Not specified",
        }
        
        for key, value in details.items():
            st.write(f"**{key}:** {value}")
        
        # Validate required fields
        if not (parsed_data['origin_airport_code'] and parsed_data['destination_airport_code']):
            st.error(MISSING_AIRPORTS_ERROR)
            st.stop()
            
        if not (parsed_data['start_date'] and parsed_data['end_date']):
            st.error(MISSING_DATES_ERROR)
            st.stop()


def search_travel_options(parsed_data, travel_description, progress_container):
    """Search for flights and hotels based on parsed data"""
    with progress_container.status("✨ Finding the best options for you...",state="running", expanded=True):
        my_bar = st.progress(0)
        try:
            st.write(" - ✈️ Finding available flights for your dates..")
            flight_response = api_client.search_flights(
                parsed_data['origin_airport_code'],
                parsed_data['destination_airport_code'],
                parsed_data['start_date'],
                parsed_data['end_date'],
                travel_description
            )
            
            my_bar.progress(0.2)
            if flight_response.status_code != 200:
                st.error(SEARCH_FAILED)
                return False
                
            # Get flight results first
            st.write(" - ✈️ Analyzing flight options and prices...")
            
            flight_task_id = flight_response.json().get("task_id")
            flight_results = api_client.poll_task_status(flight_task_id, "flight", st)
            if not flight_results:
                st.error(SEARCH_INCOMPLETE)
                return False
            
            my_bar.progress(0.4)
            st.write(" - 🏨 Searching for hotels in your destination...")
            
            hotel_response = api_client.search_hotels(
                parsed_data['destination_city_name'],
                parsed_data['start_date'],
                parsed_data['end_date'],
                1,
                "USD"
            )
            my_bar.progress(0.6)
            if hotel_response.status_code != 200:
                st.error(SEARCH_FAILED)
                return False
                
            # Get hotel results
            st.write(" - 🏨 Finding the best room options for you...")
            
            hotel_task_id = hotel_response.json().get("task_id")
            hotel_results = api_client.poll_task_status(hotel_task_id, "hotel", st)
            if not hotel_results:
                st.error(SEARCH_INCOMPLETE)
                return False
            my_bar.progress(0.8)
            
            # Generate summary
            st.write(" - ✨ Putting together your perfect trip...")
            summary = travel_summary.get_summary(
                flight_results,
                hotel_results,
                travel_description,
                destination=parsed_data['destination_city_name'],
                origin=parsed_data['origin_airport_code'],
                check_in=parsed_data['start_date'],
                check_out=parsed_data['end_date'],
                occupancy=1
            )
            my_bar.progress(0.8)
            
            st.success(SEARCH_COMPLETED)
            
            # Update session state
            st.session_state.summary = summary
            travel_context = {
                'origin': parsed_data['origin_airport_code'],
                'destination': parsed_data['destination_airport_code'],
                'start_date': format_date(parsed_data['start_date']),
                'end_date': format_date(parsed_data['end_date']),
                "occupancy": 1,
                'flights': flight_results,
                'hotels': hotel_results,
                'preferences': travel_description
            }
            
            # Initialize assistants
            st.session_state.travel_assistant = TravelAssistant(travel_context)
            st.session_state.research_assistant = ResearchAssistant(travel_context)
            st.session_state.travel_context = travel_context
            
            # Set flag to switch to results tab
            st.session_state.switch_to_results = True
            return True
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False

def render_chat_interface(messages, assistant, input_placeholder, message_type="chat"):
    """Render a chat interface with message history and input"""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Show suggested prompts for empty chat
    if not messages:
        st.markdown("### Suggested Questions:")
        suggested_prompts = assistant.get_suggested_prompts()
        cols = st.columns(2)
        with cols[0]:
            for prompt in suggested_prompts["column1"]:
                st.markdown(f"- {prompt}")
        with cols[1]:
            for prompt in suggested_prompts["column2"]:
                st.markdown(f"- {prompt}")
    
    # Chat input
    if prompt := st.chat_input(input_placeholder):
        # Add user message
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display AI response
        with st.chat_message("assistant"):
            response = assistant.get_response(prompt)
            st.markdown(response)
            messages.append({"role": "assistant", "content": response})

def render_search_tab():
    """Render the search tab content"""
    st.header("Tell Us About Your Trip")
    
    travel_description = st.text_area(
        "Describe your travel plans in natural language",
        height=200,
        help=TRAVEL_DESCRIPTION_HELP,
        placeholder=TRAVEL_DESCRIPTION_PLACEHOLDER
    )

    if st.button("Plan My Trip"):
        if not travel_description:
            st.warning(MISSING_DESCRIPTION_ERROR)
            st.stop()
        
        # Parse and process travel details
        parsed_data = get_travel_details(travel_description)
        st.session_state.parsed_data = parsed_data
        
        # Display and validate parsed data
        display_parsed_travel_details(parsed_data)
        
        # Search for travel options
        progress_container = st.container()
        search_travel_options(parsed_data, travel_description, progress_container)

def render_results_tab():
    """Render the results tab content"""
    if not st.session_state.travel_assistant:
        st.info("👋 No trip details available yet!")
        st.markdown(NO_TRIP_DETAILS_MESSAGE)
        
        with st.expander("Preview what you'll get", expanded=False):
            st.markdown(PREVIEW_SUMMARY)
    else:
        with st.expander("Travel Summary", expanded=True):
            st.markdown("### Flight and Hotel Details")
            if 'summary' in st.session_state:
                st.markdown(st.session_state.summary)
            else:
                st.info(NO_SUMMARY_YET)
        
        with st.expander("Travel Planning Assistant", expanded=True):
            render_chat_interface(
                st.session_state.chat_messages,
                st.session_state.travel_assistant,
                "Ask me anything about your trip..."
            )

def render_research_tab():
    """Render the research tab content"""
    if not st.session_state.travel_assistant or not st.session_state.research_assistant:
        st.info("👋 Please complete your trip search first to access the research assistant.")
        st.markdown(RESEARCH_LOCKED_MESSAGE)
    else:
        st.header("Travel Research Assistant")
        st.markdown(
            RESEARCH_ASSISTANT_INTRO.format(
                destination=st.session_state.travel_context['destination']
            )
        )
        
        render_chat_interface(
            st.session_state.research_messages,
            st.session_state.research_assistant,
            "Ask about your destination...",
            "research"
        )

def main():
    """Main application entry point"""
    # Initialize services
    global api_client, travel_summary
    api_client = TravelAPIClient()
    travel_summary = TravelSummary()
    
    # Initialize session state
    initialize_session_state()
    
    # Main UI
    st.title("Travel Search")
    
    # Create main tabs
    search_tab, results_tab, research_tab = st.tabs(["Search", "Results & Planning", "Research"])
    
    # Render tab contents
    with search_tab:
        render_search_tab()
    
    with results_tab:
        render_results_tab()
    
    with research_tab:
        render_research_tab()
    
    # Handle tab switching after search
    if hasattr(st.session_state, 'switch_to_results') and st.session_state.switch_to_results:
        st.session_state.switch_to_results = False
        results_tab._active = True

if __name__ == "__main__":
    main()