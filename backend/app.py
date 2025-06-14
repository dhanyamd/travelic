from flask import Flask, request, jsonify
from flights.google_flight_scraper import scrape_flights, get_flight_url
from flights.hotels import BrightDataAPI
import requests
import asyncio
import uuid
import threading
from enum import Enum
from collections import defaultdict
from waitress import serve

app = Flask(__name__)

# In-memory storage for task results
task_results = defaultdict(dict)
# Lock for thread-safe operations on task_results
task_lock = threading.Lock()

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def run_async(coro):
    """Helper function to run async code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def update_task_status(task_id, status, data=None, error=None):
    """Thread-safe update of task status"""
    with task_lock:
        if data is not None:
            task_results[task_id].update({
                'status': status,
                'data': data
            })
        elif error is not None:
            task_results[task_id].update({
                'status': status,
                'error': error
            })
        else:
            task_results[task_id]['status'] = status

def process_flight_search(task_id, origin, destination, start_date, end_date, preferences):
    try:
        # Update status to processing
        update_task_status(task_id, TaskStatus.PROCESSING.value)

        # Get flight search URL
        url = run_async(get_flight_url(origin, destination, start_date, end_date))
        if not url:
            raise Exception("Failed to generate flight search URL")

        # Scrape flight results
        flight_results = run_async(scrape_flights(url, preferences))
        
        # Store results
        update_task_status(
            task_id, 
            TaskStatus.COMPLETED.value,
            data=flight_results
        )

    except Exception as e:
        print(f"Error in flight search task: {str(e)}")
        update_task_status(
            task_id,
            TaskStatus.FAILED.value,
            error=str(e)
        )

def process_hotel_search(task_id, location, check_in, check_out, occupancy, currency):
    try:
        # Update status to processing
        update_task_status(task_id, TaskStatus.PROCESSING.value)

        # Create API instance and search for hotels
        api = BrightDataAPI()
        with requests.Session() as session:
            hotels = api.search_hotels(
                session=session,
                location=location,
                check_in=check_in,
                check_out=check_out,
                occupancy=occupancy,
                currency=currency
            )

        # Store results
        update_task_status(
            task_id,
            TaskStatus.COMPLETED.value,
            data=hotels
        )

    except Exception as e:
        print(f"Error in hotel search task: {str(e)}")
        update_task_status(
            task_id,
            TaskStatus.FAILED.value,
            error=str(e)
        )

@app.route('/search_flights', methods=['POST'])
def search_flights():
    try:
        data = request.get_json()
        
        # Extract required parameters
        origin = data.get('origin')
        destination = data.get('destination')
        start_date = data.get('start_date').replace(" 0", " ")
        end_date = data.get('end_date').replace(" 0", " ")
        preferences = data.get('preferences')

        # Validate required parameters
        if not all([origin, destination, start_date, end_date]):
            return jsonify({
                'error': 'Missing required parameters. Please provide origin, destination, start_date, and end_date'
            }), 400

        # Generate task ID and store initial status
        task_id = str(uuid.uuid4())
        with task_lock:
            task_results[task_id] = {'status': TaskStatus.PENDING.value}

        # Start background thread
        thread = threading.Thread(
            target=process_flight_search,
            args=(task_id, origin, destination, start_date, end_date, preferences),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': TaskStatus.PENDING.value
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_hotels', methods=['POST'])
def search_hotels():
    try:
        data = request.get_json()
        
        # Extract required parameters
        location = data.get('location')
        check_in = data.get('check_in').replace(" 0", " ")
        check_out = data.get('check_out').replace(" 0", " ")
        occupancy = data.get('occupancy', '2')
        currency = data.get('currency', 'USD')
        
        # Validate required parameters
        if not all([location, check_in, check_out]):
            return jsonify({
                'error': 'Missing required parameters. Please provide location, check_in, and check_out dates'
            }), 400

        # Generate task ID and store initial status
        task_id = str(uuid.uuid4())
        with task_lock:
            task_results[task_id] = {'status': TaskStatus.PENDING.value}

        # Start background thread
        thread = threading.Thread(
            target=process_hotel_search,
            args=(task_id, location, check_in, check_out, occupancy, currency),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': TaskStatus.PENDING.value
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task_status/<task_id>', methods=['GET'])
def get_status(task_id):
    try:
        with task_lock:
            result = task_results.get(task_id)
        if not result:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use waitress instead of Flask's development server
    serve(app, host='0.0.0.0', port=5000) 