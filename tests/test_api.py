from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities before each test."""
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield


def test_get_activities_returns_all():
    # Arrange
    # (fixture already reset activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "Chess Club" in result
    assert "Programming Class" in result
    assert isinstance(result["Chess Club"]["participants"], list)


def test_signup_adds_participant_and_prevents_duplicate():
    # Arrange
    email = "newstudent@example.com"
    activity_name = "Chess Club"

    # Act: first signup
    response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: created
    assert response1.status_code == 200
    assert email in activities[activity_name]["participants"]

    # Act: duplicate signup
    response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: duplicate blocked
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Student already signed up"
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_missing_activity_returns_404():
    # Arrange
    email = "noone@example.com"
    activity_name = "Nonexistent Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success_and_not_found():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    assert existing_email in activities[activity_name]["participants"]

    # Act: remove participant
    response1 = client.delete(f"/activities/{activity_name}/participant", params={"email": existing_email})

    # Assert: deleted
    assert response1.status_code == 200
    assert existing_email not in activities[activity_name]["participants"]

    # Act: remove again
    response2 = client.delete(f"/activities/{activity_name}/participant", params={"email": existing_email})

    # Assert: not found
    assert response2.status_code == 404
    assert response2.json()["detail"] == "Participant not found in activity"


def test_remove_from_missing_activity_returns_404():
    # Arrange
    activity_name = "Ghost Club"
    email = "nobody@nowhere.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participant", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
