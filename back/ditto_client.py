import requests
import json
from config import Config

class DittoClient:
    def __init__(self):
        self.base_url = Config.DITTO_API_URL
        self.api_key = Config.DITTO_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def upsert(self, collection, data):
        """
        Insert or Update a document in a collection.
        """
        url = f"{self.base_url}/api/v4/store/write"
        
        # Wrap the data in the Ditto command format
        payload = {
            "commands": [
                {
                    "method": "upsert",
                    "collection": collection,
                    "value": data
                }
            ]
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"🔴 Ditto Upsert Error: {e}")
            # Check if response variable exists (it might not if the request failed before assignment)
            if 'response' in locals() and response:
                 print(f"Response: {response.text}")
            return None

    def find(self, collection, query):
        """
        Find documents using a DQL (Ditto Query Language) query or simple find.
        For HTTP API v4, we often use /store/find.
        """
        url = f"{self.base_url}/api/v4/store/find"
        
        # Construct the query (simplified for this example)
        # In a real scenario, you might pass a full DQL query
        params = {
            "collection": collection,
            "query": query
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"🔴 Ditto Find Error: {e}")
            return None

    def execute_dql(self, query):
        """
        Execute a raw DQL query (if supported by the endpoint version).
        """
        url = f"{self.base_url}/api/v4/store/execute"
        payload = {
            "statement": query
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"🔴 Ditto DQL Error: {e}")
            return None

    def delete(self, collection, doc_id):
        """
        Delete a document by ID.
        """
        url = f"{self.base_url}/api/v4/store/write"
        
        payload = {
            "commands": [
                {
                    "method": "remove",
                    "collection": collection,
                    "query": f"_id == '{doc_id}'"
                }
            ]
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"🔴 Ditto Delete Error: {e}")
            if 'response' in locals() and response:
                 print(f"Response: {response.text}")
            return None

# Singleton instance
ditto = DittoClient()
