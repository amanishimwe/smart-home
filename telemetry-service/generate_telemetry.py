#!/usr/bin/env python3
"""
Telemetry Data Generator Script
Generates 24 hours of one-minute interval telemetry data for 5 devices
Now with proper user isolation and device management
"""

import requests
import random
import time
import uuid
from datetime import datetime, timedelta
import json

# Configuration
TELEMETRY_SERVICE_URL = "http://localhost:8003"  # Telemetry service port
AUTH_SERVICE_URL = "http://localhost:8001"       # Auth service port

# Test user credentials (you'll need to register this user first)
TEST_USERNAME = "string"
TEST_PASSWORD = "string"

def get_auth_token():
    """Get authentication token from auth service"""
    try:
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Failed to get auth token: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to auth service: {e}")
        return None

def create_user_devices(token, device_count=5):
    """Create devices for the user"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    devices = []
    device_names = [
        "Living Room TV", "Kitchen Refrigerator", "Home Office Computer", 
        "Bedroom Light", "Garage Door Opener"
    ]
    device_types = ["Entertainment", "Appliance", "Electronics", "Lighting", "Security"]
    locations = ["Living Room", "Kitchen", "Home Office", "Bedroom", "Garage"]
    
    print(f"📱 Creating {device_count} devices for user...")
    
    for i in range(device_count):
        device_id = str(uuid.uuid4())
        device_data = {
            "device_id": device_id,
            "device_name": device_names[i] if i < len(device_names) else f"Device {i+1}",
            "device_type": device_types[i] if i < len(device_types) else "Smart Device",
            "location": locations[i] if i < len(locations) else "Unknown Location"
        }
        
        try:
            response = requests.post(
                f"{TELEMETRY_SERVICE_URL}/devices",
                json=device_data,
                headers=headers
            )
            
            if response.status_code == 201:
                devices.append(device_id)
                print(f"   ✅ Created device: {device_data['device_name']} ({device_id[:8]}...)")
            else:
                print(f"   ❌ Failed to create device {i+1}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error creating device {i+1}: {e}")
    
    return devices

def generate_telemetry_data():
    """Generate 24 hours of telemetry data"""
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token. Please make sure:")
        print("   1. Auth service is running on port 8001")
        print("   2. Telemetry service is running on port 8003")
        print("   3. You have registered a user with username 'testuser' and password 'password123'")
        return
    
    print("✅ Authentication successful!")
    
    # Create user devices first
    devices = create_user_devices(token)
    
    if not devices:
        print("❌ No devices were created. Cannot generate telemetry data.")
        return
    
    print(f"📱 Using {len(devices)} devices for telemetry generation:")
    for i, device_id in enumerate(devices, 1):
        print(f"   Device {i}: {device_id}")
    
    # Set up time range (24 hours, one reading per minute)
    start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_minutes = 24 * 60
    successful_posts = 0
    failed_posts = 0
    
    print(f"⏰ Generating telemetry data from {start_of_today.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"📊 Will create {total_minutes} data points per device ({total_minutes * len(devices)} total)")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Generate telemetry data
    for minute in range(total_minutes):
        timestamp = (start_of_today + timedelta(minutes=minute)).isoformat() + "Z"
        
        for device_id in devices:
            # Generate realistic telemetry data
            payload = {
                "device_id": device_id,
                "energy_usage": round(random.uniform(0.1, 5.0), 3),  # kWh
                "voltage": round(random.uniform(110.0, 130.0), 1),    # V
                "current": round(random.uniform(0.5, 25.0), 2),      # A
                "power_factor": round(random.uniform(0.85, 0.99), 3), # Power factor
                "temperature": round(random.uniform(18.0, 30.0), 1),  # °C
                "humidity": round(random.uniform(30.0, 70.0), 1),    # %
                "status": "active"
            }
            
            try:
                response = requests.post(
                    f"{TELEMETRY_SERVICE_URL}/telemetry",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 201:
                    successful_posts += 1
                    if successful_posts % 100 == 0:
                        print(f"✅ Posted {successful_posts} telemetry records...")
                else:
                    failed_posts += 1
                    print(f"❌ Failed to post telemetry for device {device_id[:8]}...: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                failed_posts += 1
                print(f"❌ Error posting telemetry: {e}")
            
            # Small delay to avoid overwhelming the service
            time.sleep(0.01)
        
        # Progress indicator
        if (minute + 1) % 60 == 0:
            hours_completed = (minute + 1) // 60
            print(f"⏳ Completed {hours_completed} hours...")
    
    # Summary
    print("\n" + "="*50)
    print("📊 TELEMETRY GENERATION COMPLETE")
    print("="*50)
    print(f"✅ Successful posts: {successful_posts}")
    print(f"❌ Failed posts: {failed_posts}")
    print(f"📱 Devices: {len(devices)}")
    print(f"⏰ Time period: 24 hours")
    print(f"📈 Data points per device: {total_minutes}")
    print(f"🎯 Total expected: {total_minutes * len(devices)}")
    
    if successful_posts > 0:
        print(f"\n🎉 Successfully generated {successful_posts} telemetry records!")
        print("You can now view this data in your telemetry dashboard.")
        print("Each user will only see their own device data!")
    else:
        print("\n❌ No telemetry data was generated. Please check the errors above.")

if __name__ == "__main__":
    print("🚀 Starting Telemetry Data Generator with User Isolation...")
    print("="*50)
    
    try:
        generate_telemetry_data()
    except KeyboardInterrupt:
        print("\n⏹️  Generation interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    
    print("\n👋 Script completed!")
