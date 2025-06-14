import requests
import time

class TravelAPIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url

    def search_flights(self, origin, destination, start_date, end_date, preferences):
        """Send flight search request"""
        response = requests.post(
            f"{self.base_url}/search_flights",
            json={
                "origin": origin,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "preferences": preferences
            }
        )
        return response

    def search_hotels(self, location, check_in, check_out, occupancy, currency):
        """Send hotel search request"""
        response = requests.post(
            f"{self.base_url}/search_hotels",
            json={
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "occupancy": occupancy,
                "currency": currency
            }
        )
        return response

    def poll_task_status(self, task_id, task_type, progress_container):
        """Poll the task status endpoint until completion or failure"""
        
        
        while True:
            response = requests.get(f"{self.base_url}/task_status/{task_id}")
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                if status == "completed":
                    progress_container.success(f"{task_type.capitalize()} search completed!")
                    return result.get("data")
                elif status == "failed":
                    error_msg = result.get('error', 'Unknown error')
                    progress_container.error(f"{task_type.capitalize()} search failed: {error_msg}")
                    return None
                
                time.sleep(2)
            else:
                progress_container.error(f"Failed to get {task_type} search status")
                return None 