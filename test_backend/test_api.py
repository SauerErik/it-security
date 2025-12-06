import pytest
from backend.api import task_to_dict, group_to_dict, app, request
from unittest.mock import patch

class DummyTask:
    # Mock class for Task model
    def __init__(self):
        self.id = 1
        self.title = "Test Task"
        self.deadline = None
        self.kind = "Homework"
        self.priority = "High"
        self.status = "Open"
        self.progress = 50
        self.group = None
        self.assignee = "user1"

class DummyGroup:
    # Mock class for Group model
    def __init__(self):
        self.id = 1
        self.name = "Group 1"
        self.description = "Desc"
        self.group_number = "A1"
        self.invite_link = "abc123"
        self.group_memberships = [] # Geändert von self.members

class DummyUser:
    # Mock class for User model
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.birthday = kwargs.get('birthday')
        self.faculty = kwargs.get('faculty')

# Tests conversion of DummyTask to dictionary.
def test_task_to_dict_basic():
    task = DummyTask()
    result = task_to_dict(task)
    assert result["title"] == "Test Task"
    assert result["status"] == "Open"
    assert result["group"] is None

# Tests conversion of DummyGroup to dictionary.
def test_group_to_dict_basic():
    group = DummyGroup()
    result = group_to_dict(group)
    assert result["name"] == "Group 1"
    assert result["memberCount"] == 0

# Pytest fixture to configure and yield a Flask test client.
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# Tests the /api/login endpoint when required fields are missing.
def test_login_missing_fields(client):
    response = client.post("/api/login", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

# Tests the /api/refresh endpoint when the token is missing from the request body.
def test_refresh_missing_token(client):
    response = client.post("/api/refresh", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Missing refresh token"

# Tests the successful registration of a user via the API endpoint.
@patch('backend.api.user_service')
def test_register_user_endpoint_success(mock_user_service, client):
    """
    Tests the successful user registration through the /api/users/register endpoint.
    """
    # 1. Mock the UserService to avoid real DB and Keycloak calls
    # Define what the register_user method should return
    mock_user_service.register_user.return_value = DummyUser(id="new-user-123", username="testuser")

    # 2. Define the payload for the API call
    registration_data = {
        "firstName": "Test",
        "lastName": "User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "a-secure-password"
    }

    # 3. Call the API endpoint
    response = client.post("/api/users/register", json=registration_data)

    # 4. Assert the results
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully"
    assert data["id"] == "new-user-123"
    mock_user_service.register_user.assert_called_once()

# Tests the successful creation of a task via the API endpoint.
@patch('backend.auth.keycloak_openid') # Patch the underlying openid client
@patch('backend.api.create_task_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_create_task_endpoint_success(mock_get_or_create_user, mock_create_task, mock_keycloak_openid, client):
    """
    Tests the successful creation of a task via the POST /api/tasks endpoint.
    """
    # 1. Configure mocks
    # Mock the userinfo call to simulate a valid token, which allows the decorator to succeed.
    mock_user_info = {"sub": "user-abc", "name": "test"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info

    # Mock the service calls made by the endpoint
    mock_get_or_create_user.return_value = DummyUser(id="user-abc", username="test")
    mock_create_task.return_value = DummyTask() # The service returns a task object

    # 2. Define the payload for the API call
    task_data = {
        "title": "New API Task",
        "deadline": "2025-12-31",
        "kind": "Test",
        "priority": "medium"
    }

    # 3. Call the API endpoint. The client fixture handles the request context.
    # A dummy token is still needed to pass the decorator's initial header check.
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/tasks", json=task_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Task created"
    assert data["task"]["title"] == "Test Task" # from DummyTask
    # The endpoint adds 'user_id' to the data before calling the service
    expected_service_data = task_data.copy()
    expected_service_data['user_id'] = "user-abc"
    mock_create_task.assert_called_once_with(expected_service_data)

# Tests the successful retrieval of all groups via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_all_groups')
def test_get_all_groups_endpoint_success(mock_get_all_groups, mock_keycloak_openid, client):
    """
    Tests the successful retrieval of all groups via the GET /api/groups endpoint.
    """
    # 1. Configure mocks
    # Mock the userinfo call to simulate a valid token.
    mock_keycloak_openid.userinfo.return_value = {"sub": "user-abc", "name": "test"}

    # Mock the service call to return a list of dummy groups.
    mock_get_all_groups.return_value = [DummyGroup(), DummyGroup()]

    # 2. Call the API endpoint
    # A dummy token is needed to pass the decorator's initial header check.
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get("/api/groups", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['name'] == 'Group 1' # From DummyGroup
    mock_get_all_groups.assert_called_once()

# Tests the successful creation of a group via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.create_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_create_group_endpoint_success(mock_get_or_create_user, mock_create_group, mock_keycloak_openid, client):
    """
    Tests the successful creation of a group via the POST /api/groups endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_user_info = {"sub": "creator-user-id", "name": "test"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="creator-user-id", username="test")

    # Mock the service call to return a new dummy group
    mock_create_group.return_value = DummyGroup()

    # 2. Define the payload for the API call
    group_data = {
        "name": "New Test Group",
        "description": "A group created via API test.",
        "groupNumber": "B2",
        "inviteLink": "xyz789"
    }

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups", json=group_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Group created"
    assert data["group"]["name"] == "Group 1" # From DummyGroup
    mock_create_group.assert_called_once_with(group_data, creator_id="creator-user-id")

# Tests the successful joining of a group via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.join_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_join_group_endpoint_success(mock_get_or_create_user, mock_join_group, mock_keycloak_openid, client):
    """
    Tests successfully joining a group via the POST /api/groups/join endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_user_info = {"sub": "joining-user-id", "name": "joiner"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="joining-user-id", username="joiner")

    # Mock the service call
    mock_join_group.return_value = DummyGroup()

    # 2. Define the payload for the API call
    join_data = {"group_id": 1}

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/join", json=join_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert "joined group" in data["message"]
    assert data["group"]["id"] == 1
    mock_join_group.assert_called_once_with("joining-user-id", 1)

# Tests the successful retrieval of tasks for the logged-in user.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_tasks_for_user')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_get_tasks_for_user_endpoint_success(mock_get_or_create_user, mock_get_tasks, mock_keycloak_openid, client):
    """
    Tests the successful retrieval of tasks via the GET /api/tasks endpoint.
    """
    # 1. Configure mocks
    # Mock authentication to simulate a logged-in user
    mock_user_info = {"sub": "task-user-id", "name": "task-user"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="task-user-id", username="task-user")

    # Mock the service call to return a list of dummy tasks
    mock_get_tasks.return_value = [DummyTask(), DummyTask()]

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get("/api/tasks", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['title'] == 'Test Task'
    mock_get_tasks.assert_called_once_with("task-user-id")

# Tests the successful update of a task via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.update_task_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_update_task_endpoint_success(mock_get_or_create_user, mock_update_task, mock_keycloak_openid, client):
    """
    Tests the successful update of a task via the PUT /api/tasks/<task_id> endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_user_info = {"sub": "editor-user-id", "name": "editor"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="editor-user-id", username="editor")

    # Mock the service call to return an updated dummy task
    updated_dummy_task = DummyTask()
    updated_dummy_task.title = "Updated Title"
    mock_update_task.return_value = updated_dummy_task

    # 2. Define the payload for the API call
    update_data = {"title": "Updated Title", "status": "in_progress"}
    task_id_to_update = 42

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.put(f"/api/tasks/{task_id_to_update}", json=update_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Task updated"
    assert data["task"]["title"] == "Updated Title"
    mock_update_task.assert_called_once_with(task_id_to_update, update_data, editor_user_id="editor-user-id")

# Tests the successful leaving of a group via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.leave_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_leave_group_endpoint_success(mock_get_or_create_user, mock_leave_group, mock_keycloak_openid, client):
    """
    Tests successfully leaving a group via the POST /api/groups/<group_id>/leave endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_user_info = {"sub": "leaving-user-id", "name": "leaver"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="leaving-user-id", username="leaver")

    # Mock the service call to return None (or just not raise an error)
    mock_leave_group.return_value = None
    group_id_to_leave = 5

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post(f"/api/groups/{group_id_to_leave}/leave", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    assert "successfully left the group" in response.get_json()["message"]
    mock_leave_group.assert_called_once_with("leaving-user-id", group_id_to_leave)

# Tests promoting a user to admin via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.promote_to_admin_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_add_admin_endpoint_success(mock_get_or_create_user, mock_promote_service, mock_keycloak_openid, client):
    """
    Tests successfully promoting a user to admin via the POST /api/groups/<group_id>/add-admin endpoint.
    """
    # 1. Configure mocks
    # Mock authentication for the user performing the promotion (the promoter)
    mock_user_info = {"sub": "promoter-id", "name": "promoter"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="promoter-id", username="promoter")

    # Mock the service call
    mock_promote_service.return_value = None # Service doesn't need to return anything on success

    # 2. Define data for the API call
    group_id = 10
    user_to_promote_id = "user-to-promote"
    payload = {"user_id": user_to_promote_id}

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post(f"/api/groups/{group_id}/add-admin", json=payload, headers=headers)

    # 4. Assert the results
    assert response.status_code == 200
    assert "User promoted to admin successfully" in response.get_json()["message"]
    mock_promote_service.assert_called_once_with("promoter-id", user_to_promote_id, group_id)

# Tests kicking a user from a group via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.kick_user_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_kick_user_endpoint_success(mock_get_or_create_user, mock_kick_service, mock_keycloak_openid, client):
    """
    Tests successfully kicking a user from a group via the POST /api/groups/<group_id>/kick endpoint.
    """
    # 1. Configure mocks
    # Mock authentication for the user performing the action (the kicker)
    mock_user_info = {"sub": "kicker-id", "name": "kicker"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    mock_get_or_create_user.return_value = DummyUser(id="kicker-id", username="kicker")

    # Mock the service call
    mock_kick_service.return_value = None # Service doesn't need to return anything on success

    # 2. Define data for the API call
    group_id = 20
    user_to_kick_id = "user-to-kick"
    payload = {"user_id": user_to_kick_id}

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post(f"/api/groups/{group_id}/kick", json=payload, headers=headers)

    # 4. Assert the results
    assert response.status_code == 200
    assert "User kicked successfully" in response.get_json()["message"]
    mock_kick_service.assert_called_once_with("kicker-id", user_to_kick_id, group_id)

# Tests retrieving a user's profile via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_user_endpoint_success(mock_db_get, mock_keycloak_openid, client):
    """
    Tests successfully retrieving a user's profile via the GET /api/users/<user_id> endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the User model query to return a specific user
    user_to_find = DummyUser(id="profile-user-id", username="profile_user")
    user_to_find.email = "profile@example.com"
    user_to_find.faculty = "Engineering"
    user_to_find.birthday = None # Test case with no birthday
    mock_db_get.return_value = user_to_find

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/users/{user_to_find.id}", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "profile-user-id"
    assert data["name"] == "profile_user"
    assert data["email"] == "profile@example.com"
    assert data["faculty"] == "Engineering"
    mock_db_get.assert_called_once()

# Tests retrieving group members via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_group_members_endpoint_success(mock_db_get, mock_keycloak_openid, client):
    """
    Tests successfully retrieving group members via the GET /api/groups/<group_id>/members endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Create dummy data for a group with a member
    member_user = DummyUser(id="member-id-1", username="test_member")
    member_user.email = "member@test.com"
    
    group_to_find = DummyGroup()
    group_to_find.id = 15
    # Simulate the GroupMembership relationship
    membership = type('DummyMembership', (object,), {
        'user': member_user,
        'role': 'admin'
    })()
    group_to_find.group_memberships = [membership]

    # Mock the Group model query to return our dummy group
    mock_db_get.return_value = group_to_find

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/groups/{group_to_find.id}/members", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["members"]) == 1
    assert data["members"][0]["id"] == "member-id-1"
    assert data["members"][0]["username"] == "test_member"
    assert data["members"][0]["role"] == "admin"
    mock_db_get.assert_called_once()

# Tests updating a user's profile via the API endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.user_service')
def test_update_user_endpoint_success(mock_user_service, mock_keycloak_openid, client):
    """
    Tests successfully updating a user's profile via the PUT /api/users/<user_id> endpoint.
    """
    # 1. Configure mocks
    # Mock authentication for the user performing the update
    user_id_to_update = "user-to-update"
    mock_user_info = {"sub": user_id_to_update, "name": "updater"}
    mock_keycloak_openid.userinfo.return_value = mock_user_info
    
    mock_user_service.get_or_create_user_from_keycloak.return_value = DummyUser(id=user_id_to_update, username="updater")
    
    # Mock the return value of the update_user service call
    updated_user = DummyUser(
        id=user_id_to_update,
        username="new_username",
        email="new@example.com",
        birthday=None,
        faculty="New Faculty"
    )
    mock_user_service.update_user.return_value = updated_user

    # 2. Define the payload for the API call
    update_data = {"username": "new_username", "faculty": "New Faculty", "birthday": None}

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.put(f"/api/users/{user_id_to_update}", json=update_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "new_username"
    assert data["faculty"] == "New Faculty"
    mock_user_service.update_user.assert_called_once_with(user_id_to_update, update_data)