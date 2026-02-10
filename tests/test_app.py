"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Tennis Club": {
            "description": "Learn tennis skills and compete in matches",
            "schedule": "Wednesdays and Saturdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Train and play competitive basketball",
            "schedule": "Mondays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "tyler@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore painting, drawing, and mixed media techniques",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and improve acting skills",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 14,
            "participants": ["noah@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["ava@mergington.edu", "ethan@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and restore
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Clean up after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Tennis Club" in data
        assert "Basketball Team" in data
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include participant information"""
        response = client.get("/activities")
        data = response.json()
        tennis_club = data["Tennis Club"]
        assert "participants" in tennis_club
        assert "alex@mergington.edu" in tennis_club["participants"]
    
    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activities include all required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Art Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert activity["max_participants"] == 18


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds a participant to an activity"""
        response = client.post(
            "/activities/Art%20Club/signup?email=newstudent@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        assert "successfully signed up" in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        art_club = activities_response.json()["Art Club"]
        assert "newstudent@mergington.edu" in art_club["participants"]
    
    def test_signup_duplicate_email_fails(self, client, reset_activities):
        """Test that signing up with an email already registered fails"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_full_activity_fails(self, client, reset_activities):
        """Test that signing up for a full activity fails"""
        # First, fill up Chess Club (max 12 participants, currently has 2)
        for i in range(10):
            response = client.post(
                f"/activities/Chess%20Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to add one more when full
        response = client.post(
            "/activities/Chess%20Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """Test that signup correctly increments participant count"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Drama Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Drama%20Club/signup?email=newparticipant@mergington.edu"
        )
        
        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()["Drama Club"]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes a participant from an activity"""
        response = client.delete(
            "/activities/Tennis%20Club/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        assert "successfully unregistered" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        tennis_club = activities_response.json()["Tennis Club"]
        assert "alex@mergington.edu" not in tennis_club["participants"]
    
    def test_unregister_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_unregistered_student_fails(self, client, reset_activities):
        """Test that unregistering a student not in the activity fails"""
        response = client.delete(
            "/activities/Tennis%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_decrements_participant_count(self, client, reset_activities):
        """Test that unregister correctly decrements participant count"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Drama Club"]["participants"])
        
        # Unregister first participant
        client.delete(
            "/activities/Drama%20Club/unregister?email=lucas@mergington.edu"
        )
        
        # Verify count decreased
        response = client.get("/activities")
        new_count = len(response.json()["Drama Club"]["participants"])
        assert new_count == initial_count - 1
    
    def test_unregister_followed_by_signup(self, client, reset_activities):
        """Test that a student can sign up after unregistering"""
        # Unregister
        client.delete(
            "/activities/Tennis%20Club/unregister?email=alex@mergington.edu"
        )
        
        # Try to sign up again
        response = client.post(
            "/activities/Tennis%20Club/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        assert "successfully signed up" in response.json()["message"]
