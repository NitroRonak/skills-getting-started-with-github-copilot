"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    initial_state = {
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
        },
        "Basketball Team": {
            "description": "Competitive basketball practices and inter-school games",
            "schedule": "Mondays, Wednesdays, Fridays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["noah@mergington.edu", "ava@mergington.edu"]
        },
        "Soccer Club": {
            "description": "Casual and competitive soccer training and matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": ["liam@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore drawing, painting, and mixed media projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["mia@mergington.edu"]
        },
        "Choir": {
            "description": "Vocal training and performances for school events",
            "schedule": "Mondays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 30,
            "participants": ["isabella@mergington.edu"]
        },
        "Science Club": {
            "description": "Hands-on experiments, science fairs, and guest lectures",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["oliver@mergington.edu"]
        },
        "Debate Team": {
            "description": "Practice debating, public speaking, and competitions",
            "schedule": "Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 12,
            "participants": ["charlotte@mergington.edu", "ethan@mergington.edu"]
        }
    }
    
    # Clear existing activities and repopulate
    activities.clear()
    activities.update(initial_state)
    
    yield
    
    # Clean up after test
    activities.clear()
    activities.update(initial_state)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that get activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
        
    def test_get_activities_preserves_participants(self, client, reset_activities):
        """Test that participants are correctly returned"""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student(self, client, reset_activities):
        """Test successful signup for a new student"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up newstudent@mergington.edu" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test signup fails for a student already registered"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_full_activity(self, client, reset_activities):
        """Test signup fails when activity is full"""
        from app import activities
        
        # Create a full activity
        activities["Full Activity"] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 1,
            "participants": ["existing@mergington.edu"]
        }
        
        response = client.post(
            "/activities/Full%20Activity/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test multiple students can sign up"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Soccer%20Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        soccer_participants = activities_data["Soccer Club"]["participants"]
        
        for email in emails:
            assert email in soccer_participants


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test successful unregistration of an existing participant"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu" in data["message"]
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Test unregister fails for non-registered student"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregister fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        email = "michael@mergington.edu"
        
        # First, unregister
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Then, sign up again
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify the student is registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants from the same activity"""
        # Unregister all participants from Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        response2 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "daniel@mergington.edu"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Chess Club"]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_full_signup_and_unregister_workflow(self, client, reset_activities):
        """Test a complete workflow: signup and unregister"""
        email = "integration@mergington.edu"
        activity_name = "Programming%20Class"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert len(response.json()["Programming Class"]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert len(response.json()["Programming Class"]["participants"]) == initial_count
    
    def test_activity_capacity_management(self, client, reset_activities):
        """Test that activity capacity is properly managed"""
        from app import activities
        
        # Create a small activity
        activities["Small Workshop"] = {
            "description": "Limited workshop",
            "schedule": "Monday",
            "max_participants": 2,
            "participants": ["user1@mergington.edu"]
        }
        
        # Fill the activity
        response = client.post(
            "/activities/Small%20Workshop/signup",
            params={"email": "user2@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Try to exceed capacity
        response = client.post(
            "/activities/Small%20Workshop/signup",
            params={"email": "user3@mergington.edu"}
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
        
        # Unregister one and try again
        response = client.post(
            "/activities/Small%20Workshop/unregister",
            params={"email": "user1@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Now signup should succeed
        response = client.post(
            "/activities/Small%20Workshop/signup",
            params={"email": "user3@mergington.edu"}
        )
        assert response.status_code == 200
