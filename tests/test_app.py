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
    response = client.get("/activities")

    assert response.status_code == 200
    assert test_activity in response.json()


def test_signup_adds_participant(client, test_activity):
    email = "student@example.com"

    response = client.post(signup_url(test_activity), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {test_activity}"}
    assert email in app_module.activities[test_activity]["participants"]


def test_signup_rejects_duplicate_participant(client, test_activity):
    email = "student@example.com"
    app_module.activities[test_activity]["participants"].append(email)

    response = client.post(signup_url(test_activity), params={"email": email})

    assert response.status_code == 400
    assert app_module.activities[test_activity]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(signup_url("Unknown Activity"), params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client, test_activity):
    email = "student@example.com"
    app_module.activities[test_activity]["participants"].append(email)

    response = client.delete(signup_url(test_activity), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {test_activity}"}
    assert email not in app_module.activities[test_activity]["participants"]


def test_unregister_rejects_unregistered_participant(client, test_activity):
    response = client.delete(
        signup_url(test_activity),
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        signup_url("Unknown Activity"),
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
