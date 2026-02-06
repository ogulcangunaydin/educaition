"""
Test script for device tracking API endpoints.
Run this after starting the backend server.
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'

def test_device_tracking():
    test_device_id = 'aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee'
    
    # Test 1: Check completion (should be false for new device)
    print('=== Test 1: Check completion for new device ===')
    response = requests.post(f'{BASE_URL}/device-tracking/check', json={
        'device_id': test_device_id,
        'test_type': 'dissonance_test',
        'room_id': 1
    })
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {result}')
    assert response.status_code == 200, "Expected 200 status"
    # Note: has_completed might be true if you ran this test before
    print(f'Has completed: {result.get("has_completed")}')

    # Test 2: Mark completion
    print('\n=== Test 2: Mark completion ===')
    response = requests.post(f'{BASE_URL}/device-tracking/mark', json={
        'device_id': test_device_id,
        'test_type': 'dissonance_test',
        'room_id': 1
    })
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    assert response.status_code == 200, "Expected 200 status"

    # Test 3: Check completion again (should be true now)
    print('\n=== Test 3: Check completion after marking ===')
    response = requests.post(f'{BASE_URL}/device-tracking/check', json={
        'device_id': test_device_id,
        'test_type': 'dissonance_test',
        'room_id': 1
    })
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {result}')
    assert response.status_code == 200, "Expected 200 status"
    assert result.get('has_completed') == True, "Expected has_completed to be True"

    # Test 4: Get all completions for device
    print('\n=== Test 4: Get all device completions ===')
    response = requests.get(f'{BASE_URL}/device-tracking/device/{test_device_id}')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    assert response.status_code == 200, "Expected 200 status"

    # Test 5: Check different room (should be false)
    print('\n=== Test 5: Check completion for different room ===')
    response = requests.post(f'{BASE_URL}/device-tracking/check', json={
        'device_id': test_device_id,
        'test_type': 'dissonance_test',
        'room_id': 999
    })
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {result}')
    assert response.status_code == 200, "Expected 200 status"
    assert result.get('has_completed') == False, "Expected has_completed to be False for different room"

    # Test 6: Check different test type (should be false)
    print('\n=== Test 6: Check completion for different test type ===')
    response = requests.post(f'{BASE_URL}/device-tracking/check', json={
        'device_id': test_device_id,
        'test_type': 'program_suggestion',
        'room_id': 1
    })
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Response: {result}')
    assert response.status_code == 200, "Expected 200 status"
    assert result.get('has_completed') == False, "Expected has_completed to be False for different test type"

    # Test 7: Validation - invalid device_id length
    print('\n=== Test 7: Validation - invalid device_id length ===')
    response = requests.post(f'{BASE_URL}/device-tracking/check', json={
        'device_id': 'short',
        'test_type': 'dissonance_test',
        'room_id': 1
    })
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    assert response.status_code == 422, "Expected 422 status for validation error"

    print('\n=== All tests passed! ===')


if __name__ == '__main__':
    test_device_tracking()
