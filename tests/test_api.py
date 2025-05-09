import requests
import json
import sys

# Base URL
BASE_URL = 'http://127.0.0.1:8000/api'

# Test user credentials
USERNAME = 'testuser'
PASSWORD = 'testpass123'

def get_token():
    """Get JWT token for authentication"""
    print("Attempting to get token...")
    try:
        response = requests.post(
            f'{BASE_URL}/token/',
            json={'username': USERNAME, 'password': PASSWORD},
            timeout=5
        )
        print(f"Token response status: {response.status_code}")
        print(f"Token response text: {response.text}")
        
        if response.status_code == 200:
            return response.json()['access']
        else:
            print(f"Error getting token: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_endpoints(token):
    """Test various API endpoints"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test job categories endpoint
    print("\nTesting job categories endpoint:")
    try:
        response = requests.get(f'{BASE_URL}/job-categories/', headers=headers, timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Test skills endpoint
    print("\nTesting skills endpoint:")
    try:
        response = requests.get(f'{BASE_URL}/skills/', headers=headers, timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Test job postings endpoint
    print("\nTesting job postings endpoint:")
    try:
        response = requests.get(f'{BASE_URL}/job-postings/', headers=headers, timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    print("Starting API tests...")
    token = get_token()
    if token:
        print("Successfully obtained token")
        test_endpoints(token)
    else:
        print("Failed to get authentication token")
        sys.exit(1) 