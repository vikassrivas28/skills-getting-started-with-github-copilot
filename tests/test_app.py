from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def test_activity():
    name = "Test Activity"
    app_module.activities[name] = {
        "description": "Activity used by API tests",
        "schedule": "Mondays, 3:00 PM",
        "max_participants": 10,
        "participants": [],
    }
    yield name
    app_module.activities.pop(name, None)


def signup_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_get_activities_returns_available_activities(client, test_activity):
    # Arrange
    expected_activity = test_activity

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert expected_activity in response.json()


def test_signup_adds_participant(client, test_activity):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.post(signup_url(test_activity), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {test_activity}"}
    assert email in app_module.activities[test_activity]["participants"]

    # Act
    refreshed_activities = client.get("/activities")

    # Assert
    assert email in refreshed_activities.json()[test_activity]["participants"]


def test_signup_rejects_duplicate_participant(client, test_activity):
    # Arrange
    email = "student@example.com"
    app_module.activities[test_activity]["participants"].append(email)

    # Act
    response = client.post(signup_url(test_activity), params={"email": email})

    # Assert
    assert response.status_code == 400
    assert app_module.activities[test_activity]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@example.com"

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client, test_activity):
    # Arrange
    email = "student@example.com"
    app_module.activities[test_activity]["participants"].append(email)

    # Act
    response = client.delete(signup_url(test_activity), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {test_activity}"}
    assert email not in app_module.activities[test_activity]["participants"]


def test_unregister_rejects_unregistered_participant(client, test_activity):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        signup_url(test_activity),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@example.com"

    # Act
    response = client.delete(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
