"""
Tests for API endpoints using AAA (Arrange-Act-Assert) pattern.
"""

import pytest


class TestRootEndpoint:
    def test_root_redirects_to_static_index_html(self, client):
        # Arrange (client fixture ready)
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    def test_get_all_activities_returns_success(self, client, clean_activities):
        # Arrange
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Tennis Club", "Drama Club",
            "Art Studio", "Debate Team", "Science Club"
        }

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == expected_activities
        assert len(data) == 9

    def test_activity_has_required_fields(self, client, clean_activities):
        # Arrange
        required = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        for _, activity in activities.items():
            assert required.issubset(set(activity.keys()))
            assert isinstance(activity["description"], str)
            assert isinstance(activity["schedule"], str)
            assert isinstance(activity["max_participants"], int)
            assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    def test_signup_successful_adds_student(self, client, clean_activities, sample_email):
        # Arrange
        activity = "Chess Club"
        before = client.get("/activities").json()[activity]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {sample_email} for {activity}"

        after = client.get("/activities").json()[activity]["participants"]
        assert sample_email in after
        assert len(after) == len(before) + 1

    def test_signup_duplicate_returns_conflict(self, client, clean_activities, existing_participant_email):
        # Arrange
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": existing_participant_email}
        )

        # Assert
        assert response.status_code == 409
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, clean_activities, sample_email):
        # Arrange
        activity = "Invalid Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 404

    def test_signup_full_activity_returns_400(self, client, clean_activities):
        # Arrange
        from app import activities
        activities["Full Activity"] = {
            "description": "Full activity",
            "schedule": "Test",
            "max_participants": 2,
            "participants": ["a@mergington.edu", "b@mergington.edu"]
        }

        # Act
        response = client.post(
            "/activities/Full Activity/signup",
            params={"email": "new@mergington.edu"}
        )

        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

        # Cleanup
        activities.pop("Full Activity", None)


class TestRemoveParticipantEndpoint:
    def test_remove_existing_participant(self, client, clean_activities):
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert f"Removed {email} from {activity}" in response.json()["message"]
        assert email not in client.get("/activities").json()[activity]["participants"]

    def test_remove_nonexistent_participant_returns_404(self, client, clean_activities):
        # Arrange
        activity = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": "nobody@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_nonexistent_activity_returns_404(self, client, clean_activities):
        # Arrange
        activity = "Invalid Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": "some@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
