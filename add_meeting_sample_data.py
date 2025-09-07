#!/usr/bin/env python3
"""
Script to add sample data to meeting tables:
- meetings
- meeting_participants  
- meeting_reminders

This script demonstrates the relationship between these tables and adds realistic sample data.
"""

import asyncio
import requests
import json
from datetime import datetime, timedelta, timezone

# API Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def register_user(username, email, password):
    """Register a new user"""
    url = f"{API_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ User registered: {username} ({email})")
            return response.json()
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"ℹ️  User already exists: {username} ({email})")
            return None
        else:
            print(f"❌ Failed to register user {username}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error registering user {username}: {e}")
        return None

def login_user(username, password):
    """Login user and get JWT token"""
    url = f"{API_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ User logged in: {username}")
            return token_data["access_token"]
        else:
            print(f"❌ Failed to login user {username}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error logging in user {username}: {e}")
        return None

def create_meeting(token, meeting_data):
    """Create a meeting"""
    url = f"{API_URL}/meetings/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=meeting_data, headers=headers)
        if response.status_code == 201:
            meeting = response.json()
            print(f"✅ Meeting created: {meeting['title']} (ID: {meeting['id']})")
            return meeting
        else:
            print(f"❌ Failed to create meeting: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating meeting: {e}")
        return None

def get_meetings(token):
    """Get all meetings for the user"""
    url = f"{API_URL}/meetings/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            meetings_data = response.json()
            print(f"✅ Retrieved {len(meetings_data['meetings'])} meetings")
            return meetings_data
        else:
            print(f"❌ Failed to get meetings: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting meetings: {e}")
        return None

def main():
    """Main function to add sample meeting data"""
    print("🚀 Starting Meeting Sample Data Creation")
    print("=" * 50)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    import time
    time.sleep(5)
    
    # Test server connection
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    print("\n📋 Step 1: Register Users")
    print("-" * 30)
    
    # Register users with the specified emails
    users = [
        {"username": "rajesh_primary", "email": "rajeshkh704435@gmail.com", "password": "password123"},
        {"username": "rajesh_secondary", "email": "rajeshkumarhalder083@gmail.com", "password": "password123"},
        {"username": "organizer", "email": "test@example.com", "password": "password123"}
    ]
    
    for user in users:
        register_user(user["username"], user["email"], user["password"])
    
    print("\n🔐 Step 2: Login Users")
    print("-" * 30)
    
    # Login as organizer (try both username and email)
    organizer_token = login_user("organizer", "password123")
    if not organizer_token:
        organizer_token = login_user("test@example.com", "password123")
    if not organizer_token:
        print("❌ Cannot proceed without organizer token")
        return
    
    print("\n📅 Step 3: Create Sample Meetings")
    print("-" * 30)
    
    # Create sample meetings with different scenarios
    meetings_data = [
        {
            "title": "Project Planning Meeting",
            "description": "Weekly project planning and review session",
            "meeting_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "duration_minutes": 90,
            "location": "Conference Room A",
            "meeting_url": "https://meet.google.com/project-planning",
            "reminder_minutes": 30,
            "meeting_type": "hybrid",
            "participant_emails": ["rajeshkh704435@gmail.com", "rajeshkumarhalder083@gmail.com"]
        },
        {
            "title": "Code Review Session",
            "description": "Review recent code changes and discuss improvements",
            "meeting_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "duration_minutes": 60,
            "location": "Virtual Meeting",
            "meeting_url": "https://meet.google.com/code-review",
            "reminder_minutes": 15,
            "meeting_type": "virtual",
            "participant_emails": ["rajeshkh704435@gmail.com"]
        },
        {
            "title": "Team Standup",
            "description": "Daily team standup meeting",
            "meeting_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "location": "Office Meeting Room",
            "reminder_minutes": 10,
            "meeting_type": "in_person",
            "participant_emails": ["rajeshkh704435@gmail.com", "rajeshkumarhalder083@gmail.com"]
        },
        {
            "title": "Client Presentation",
            "description": "Present project progress to client",
            "meeting_date": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "duration_minutes": 120,
            "location": "Client Office",
            "meeting_url": "https://meet.google.com/client-presentation",
            "reminder_minutes": 60,
            "meeting_type": "hybrid",
            "participant_emails": ["rajeshkh704435@gmail.com"]
        },
        {
            "title": "Sprint Retrospective",
            "description": "Review sprint performance and plan improvements",
            "meeting_date": (datetime.now(timezone.utc) + timedelta(days=21)).isoformat(),
            "duration_minutes": 75,
            "location": "Conference Room B",
            "reminder_minutes": 20,
            "meeting_type": "in_person",
            "participant_emails": ["rajeshkh704435@gmail.com", "rajeshkumarhalder083@gmail.com"]
        }
    ]
    
    created_meetings = []
    for meeting_data in meetings_data:
        meeting = create_meeting(organizer_token, meeting_data)
        if meeting:
            created_meetings.append(meeting)
    
    print(f"\n✅ Created {len(created_meetings)} meetings successfully!")
    
    print("\n📊 Step 4: Display Meeting Summary")
    print("-" * 30)
    
    # Get all meetings to show the complete data
    meetings_info = get_meetings(organizer_token)
    if meetings_info:
        print(f"\n📋 Meeting Summary:")
        print(f"Total meetings: {meetings_info['total']}")
        print(f"Current page: {meetings_info['page']}")
        print(f"Page size: {meetings_info['size']}")
        
        print(f"\n📅 Meeting Details:")
        for meeting in meetings_info['meetings']:
            print(f"\n🔹 Meeting: {meeting['title']}")
            print(f"   ID: {meeting['id']}")
            print(f"   Date: {meeting['meeting_date']}")
            print(f"   Duration: {meeting['duration_minutes']} minutes")
            print(f"   Location: {meeting['location']}")
            print(f"   Type: {meeting['meeting_type']}")
            print(f"   Participants: {len(meeting['participants'])}")
            for participant in meeting['participants']:
                print(f"     - {participant['user']['username']} ({participant['user']['email']}) - {participant['role']} - {participant['response_status']}")
    
    print("\n🎉 Sample Data Creation Complete!")
    print("=" * 50)
    print("\n📋 What was created:")
    print("1. ✅ Users with specified email addresses")
    print("2. ✅ Meetings with different types and scenarios")
    print("3. ✅ Meeting participants (automatically created)")
    print("4. ✅ Meeting reminders (will be sent by cron jobs)")
    
    print("\n🔍 Table Explanations:")
    print("• meetings: Main meeting information (title, date, location, etc.)")
    print("• meeting_participants: Who's invited and their response status")
    print("• meeting_reminders: Tracking of reminder emails sent to participants")
    
    print("\n🚀 Next Steps:")
    print("• Check the database to see the data")
    print("• Test meeting reminder emails")
    print("• Test Google Calendar sync")
    print("• Test meeting updates and deletions")

if __name__ == "__main__":
    main()
