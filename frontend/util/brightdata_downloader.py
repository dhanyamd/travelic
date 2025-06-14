import requests
import time
from typing import Dict, Optional
from dotenv import load_dotenv
import os

load_dotenv()

class BrightDataDownloader:
    def __init__(self):
        self.base_url = "https://api.brightdata.com"
        self.auth_token = os.getenv('BRIGHTDATA_API_KEY')
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    def filter_dataset(self, dataset_id: str, filter_params: Dict, records_limit: Optional[int] = None) -> Dict:
        """Initialize dataset filtering and get snapshot ID"""
        url = f"{self.base_url}/datasets/filter"
        payload = {
            "dataset_id": dataset_id,
            "filter": filter_params
        }
        if records_limit:
            payload["records_limit"] = records_limit

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error initiating filter request: {e}")
            raise

    def get_snapshot_status(self, snapshot_id: str) -> Dict:
        """Check the status of a specific snapshot"""
        url = f"{self.base_url}/datasets/snapshots/{snapshot_id}"
        try:
            response = requests.request("GET", url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error checking snapshot status: {e}")
            raise

    def download_snapshot(self, snapshot_id: str, output_file: str) -> None:
        """Download the snapshot data and save to file"""
        time.sleep(5)
        url = f"{self.base_url}/datasets/snapshots/{snapshot_id}/download"
        try:
            response = requests.request("GET", url, headers=self.headers)
            response.raise_for_status()
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Data successfully saved to {output_file}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading snapshot: {e}")
            raise

    def poll_and_download(self, dataset_id: str, filter_params: Dict, 
                         output_file: str, records_limit: Optional[int] = None, 
                         max_retries: int = 30, delay: int = 10) -> None:
        """Complete workflow: Filter dataset, poll for completion, and download results"""
        # Initialize the filter request
        print("Initiating dataset filter request...")
        filter_response = self.filter_dataset(dataset_id, filter_params, records_limit)
        snapshot_id = filter_response.get('snapshot_id')
        
        if not snapshot_id:
            raise ValueError("No snapshot ID received in response")
        
        print(f"Received snapshot ID: {snapshot_id}")
        
        # Poll for completion
        retries = 0
        while retries < max_retries:
            status_response = self.get_snapshot_status(snapshot_id)
            status = status_response.get('status')
            print(f"Current status: {status}")
            
            if status == 'ready':
                print("Snapshot is ready for download")
                break
            elif status == 'scheduled':
                print("Snapshot is scheduled for processing")
            elif status == 'processing':
                print("Snapshot is being processed")
            elif status in ['failed', 'error']:
                raise Exception(f"Snapshot failed with status: {status}")
            
            retries += 1
            print(f"Waiting {delay} seconds before next check... (Attempt {retries}/{max_retries})")
            time.sleep(delay)
        
        if retries >= max_retries:
            raise TimeoutError("Maximum retry attempts reached")
        
        # Download the data
        print("Downloading snapshot data...")
        self.download_snapshot(snapshot_id, output_file)

def main():
    # Example usage
    downloader = BrightDataDownloader()
    snapshot_id = "snap_m7ko88ve1syf4sbot3"
    downloader.download_snapshot(snapshot_id, "brightdata_results.json")

    # dataset_id = "gd_lrqeq7u3bil0pmelk"
    # filter_params = {
    #     "name": "is_un_member",
    #     "operator": "=",
    #     "value": True
    # }
    # output_file = "brightdata_results.json"
    
    # try:
    #     downloader.poll_and_download(
    #         dataset_id=dataset_id,
    #         filter_params=filter_params,
    #         output_file=output_file,
    #         records_limit=500,  # Optional: limit number of records
    #         max_retries=30,     # Maximum number of status checks
    #         delay=10            # Delay between status checks in seconds
    #     )
    # except Exception as e:
    #     print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 