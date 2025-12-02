"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_success(self):
        """Test that GET /activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_contain_known_activities(self):
        """Test that the activities list contains expected activities"""
        response = client.get("/activities")
        activities = response.json()

        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Workshop",
            "Drama Club",
            "Math Olympiad",
            "Science Club"
        ]

        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self):
        """Test successful signup of a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_participant_fails(self):
        """Test that signing up the same participant twice fails"""
        email = "duplicate@mergington.edu"

        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_participant_added_to_activity(self):
        """Test that a participant is actually added to the activity"""
        email = "newuser@mergington.edu"
        activity = "Art Workshop"

        # Get initial count
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity]["participants"])

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Get updated count
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity]["participants"])

        assert count_after == count_before + 1
        assert email in response_after.json()[activity]["participants"]


class TestUnregisterEndpoint:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self):
        """Test successful unregistration of an existing participant"""
        email = "unregister@mergington.edu"
        activity = "Drama Club"

        # First, sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Then unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_participant_fails(self):
        """Test that unregistering a non-existent participant fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from a non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_participant_removed_from_activity(self):
        """Test that a participant is actually removed from the activity"""
        email = "removeuser@mergington.edu"
        activity = "Basketball Club"

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Get count before unregister
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity]["participants"])
        assert email in response_before.json()[activity]["participants"]

        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")

        # Get count after unregister
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity]["participants"])

        assert count_after == count_before - 1
        assert email not in response_after.json()[activity]["participants"]


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that the root endpoint redirects to the static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
