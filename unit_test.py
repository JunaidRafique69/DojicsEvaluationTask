# test_app.py

from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app import app, TaskCreate

client = TestClient(app)

@patch("app.celery.send_task")
def test_create_task(mock_send_task):
    mock_send_task.return_value = None
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "due_date": "2024-03-20T12:00:00",
        "priority": "High",
        "assigned_to": "test@example.com"
    }
    with patch("app.SessionLocal") as mock_session:
        mock_add = Mock()
        mock_session.return_value.add = mock_add
        mock_commit = Mock()
        mock_session.return_value.commit = mock_commit
        mock_refresh = Mock()
        mock_session.return_value.refresh = mock_refresh

        response = client.post("/tasks/", json=task_data)

        assert response.status_code == 200
        assert response.json() == {"message": "Task created successfully"}

        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        mock_refresh.assert_called_once()
        mock_send_task.assert_called_once()

def test_get_tasks():
    with patch("app.SessionLocal") as mock_session:
        mock_query = Mock()
        mock_session.return_value.query.return_value.all.return_value = []
        mock_session.return_value.query = mock_query

        response = client.get("/tasks/")

        assert response.status_code == 200
        assert response.json() == []

def test_get_task():
    with patch("app.SessionLocal") as mock_session:
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock()
        mock_first.return_value = {"id": 1}
        mock_query.return_value.filter.return_value.first.return_value = mock_first
        mock_session.return_value.query = mock_query

        response = client.get("/tasks/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

def test_update_task():
    task_data = {
        "title": "Updated Task",
        "description": "Updated Description",
        "due_date": "2024-03-25T12:00:00",
        "priority": "Medium",
        "assigned_to": "test@example.com"
    }
    with patch("app.SessionLocal") as mock_session:
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock()
        mock_first.return_value = {"id": 1, "assigned_to": "test@example.com"}
        mock_query.return_value.filter.return_value.first.return_value = mock_first
        mock_session.return_value.query = mock_query
        mock_commit = Mock()
        mock_session.return_value.commit = mock_commit
        with patch("app.celery.send_task") as mock_send_task:
            mock_send_task.return_value = None

            response = client.put("/tasks/1", json=task_data)

            assert response.status_code == 200
            assert response.json() == {"message": "Task updated successfully"}
            mock_commit.assert_called_once()
            mock_send_task.assert_called_once()

@patch("app.celery.send_task")
def test_delete_task(mock_send_task):
    mock_send_task.return_value = None
    with patch("app.SessionLocal") as mock_session:
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock()
        mock_first.return_value = {"assigned_to": "test@example.com", "title": "Test Task"}
        mock_query.return_value.filter.return_value.first.return_value = mock_first
        mock_session.return_value.query = mock_query
        mock_delete = Mock()
        mock_session.return_value.delete = mock_delete
        mock_commit = Mock()
        mock_session.return_value.commit = mock_commit

        response = client.delete("/tasks/1")

        assert response.status_code == 200
        assert response.json() == {"message": "Task deleted successfully"}
        mock_delete.assert_called_once()
        mock_commit.assert_called_once()
        mock_send_task.assert_called_once()
