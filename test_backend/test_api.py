import pytest
from backend.api import task_to_dict, group_to_dict, app, request, db
from backend.models import User, Group
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

# Tests retrieving groups where the user is an admin.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
@patch('backend.api.get_groups_for_user')
def test_get_admin_groups_for_user_endpoint(mock_get_groups, mock_db_get, mock_keycloak_openid, client):
    """
    Tests the GET /api/groups/user/admin/<user_id> endpoint.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the user lookup
    admin_user_id = "admin-user-1"
    admin_user = DummyUser(id=admin_user_id, username="admin_user")
    mock_db_get.return_value = admin_user

    # Mock the groups returned for this user
    group1 = DummyGroup()
    group1.id = 1
    group1.group_memberships = [type('DummyMembership', (object,), {'user_id': admin_user_id, 'role': 'admin'})()]

    group2 = DummyGroup()
    group2.id = 2
    group2.name = "Group 2"
    group2.group_memberships = [type('DummyMembership', (object,), {'user_id': admin_user_id, 'role': 'member'})()]

    mock_get_groups.return_value = [group1, group2]

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/groups/user/admin/{admin_user_id}", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1  # Should only return the group where the user is an admin
    assert data[0]['id'] == 1
    assert data[0]['name'] == 'Group 1'

# Tests retrieving tasks for a specific user ID.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_tasks_for_user')
def test_get_tasks_for_specific_user_endpoint(mock_get_tasks, mock_keycloak_openid, client):
    """
    Tests the GET /api/tasks/user/<user_id> endpoint.
    """
    # 1. Configure mocks
    # Mock authentication (the user making the request can be anyone)
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the service call to return a list of tasks for the target user
    target_user_id = "target-user-123"
    mock_get_tasks.return_value = [DummyTask(), DummyTask()]

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/tasks/user/{target_user_id}", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['title'] == 'Test Task'
    mock_get_tasks.assert_called_once_with(target_user_id)


@patch('backend.auth.keycloak_openid')
@patch('backend.api.keycloak_openid')
@patch('backend.api.db.session.get')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_get_user_creates_local_user_if_missing(mock_get_or_create, mock_db_get, mock_api_openid, mock_auth_openid, client):
    """
    Tests that the GET /api/users/<user_id> endpoint creates a local user if they only exist in Keycloak.
    """
    user_id = "missing-user-id"
    token = "valid-token"

    # 1. Mock authentication (Decorator)
    mock_auth_openid.userinfo.return_value = {"sub": user_id}

    # 2. Mock DB to return None (User not found locally)
    mock_db_get.return_value = None

    # 3. Mock API Keycloak client to return user info matching the requested ID
    mock_api_openid.userinfo.return_value = {"sub": user_id, "preferred_username": "new_user", "email": "new@test.com"}

    # 4. Mock service to return the created user
    mock_get_or_create.return_value = DummyUser(id=user_id, username="new_user", email="new@test.com")

    # 5. Call endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/api/users/{user_id}", headers=headers)

    # 6. Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user_id
    mock_get_or_create.assert_called_once()

@patch('backend.auth.keycloak_openid')
@patch('backend.api.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_user_not_found_in_db_or_keycloak(mock_db_get, mock_api_openid, mock_auth_openid, client):
    """
    Tests the 404 error path when a user is not found in the local DB and the authenticated user does not match the requested user_id.
    """
    user_id = "missing-user-id"
    token = "valid-token"

    # 1. Mock authentication (Decorator)
    mock_auth_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # 2. Mock DB to return None
    mock_db_get.return_value = None

    # 3. Mock API Keycloak client to return info for the requesting user (mismatching the requested user_id)
    mock_api_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # 4. Call endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/api/users/{user_id}", headers=headers)

    # 5. Assert
    assert response.status_code == 404
    assert "User not found" in response.get_json()["error"]

# New test to increase coverage
@patch('backend.auth.keycloak_openid')
@patch('backend.api.user_service')
@patch('backend.api.get_groups_for_user')
def test_get_groups_for_specific_user_endpoint(mock_get_groups, mock_user_service, mock_keycloak_openid, client):
    """
    Tests the GET /api/groups/user/<user_id> endpoint.
    """
    # 1. Configure mocks
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_user_service.get_or_create_user_from_keycloak.return_value = DummyUser(id="requesting-user-id")
    mock_get_groups.return_value = [DummyGroup(), DummyGroup()]

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    # NOTE: The endpoint logic currently uses the logged-in user's ID, not the one from the URL.
    # The test reflects this current behavior.
    response = client.get("/api/groups/user/some-other-user-id", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == 'Group 1'
    # The service is called with the ID of the *logged-in* user.
    mock_get_groups.assert_called_once_with("requesting-user-id")

# New test to cover the "Group not found" error path.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_group_members_group_not_found(mock_db_get, mock_keycloak_openid, client):
    """
    Tests that GET /api/groups/<group_id>/members returns a 404 if the group does not exist.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the DB lookup to return None, simulating a missing group
    mock_db_get.return_value = None

    # 2. Call the API endpoint with a non-existent group ID
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get("/api/groups/9999/members", headers=headers)

    # 3. Assert the results
    assert response.status_code == 404
    assert "Group not found" in response.get_json()["error"]

# New test to cover the "Cannot edit another user" error path.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.user_service')
def test_update_user_forbidden_for_different_user(mock_user_service, mock_keycloak_openid, client):
    """
    Tests that PUT /api/users/<user_id> returns a 403 if the logged-in user
    is different from the user being updated.
    """
    # 1. Configure mocks
    # Mock authentication for the logged-in user (the one making the request)
    logged_in_user_id = "logged-in-user"
    mock_keycloak_openid.userinfo.return_value = {"sub": logged_in_user_id}
    mock_user_service.get_or_create_user_from_keycloak.return_value = DummyUser(id=logged_in_user_id)

    # 2. Define the payload for the API call
    user_id_to_update = "another-user" # This is a different user
    update_data = {"username": "hacker_man"}

    # 3. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.put(f"/api/users/{user_id_to_update}", json=update_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 403
    assert "Cannot edit another user" in response.get_json()["error"]

# New test to cover a generic exception handler.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_all_groups')
def test_get_all_groups_endpoint_handles_exception(mock_get_all_groups, mock_keycloak_openid, client):
    """
    Tests that GET /api/groups returns a 500 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the service call to raise a generic exception
    mock_get_all_groups.side_effect = Exception("Database connection failed")

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get("/api/groups", headers=headers)

    # 3. Assert the results
    assert response.status_code == 500
    assert "Database connection failed" in response.get_json()["error"]

# New test to cover a generic exception handler in the create_group endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.create_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_create_group_endpoint_handles_exception(mock_get_or_create_user, mock_create_group, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups returns a 400 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # Mock the service call to raise a generic exception
    mock_create_group.side_effect = Exception("Invalid group data")

    # 2. Define a payload and call the API endpoint
    group_data = {"name": "A new group"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups", json=group_data, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "Invalid group data" in response.get_json()["error"]

# New test to cover a generic exception handler in the update_task endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.update_task_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_update_task_endpoint_handles_exception(mock_get_or_create_user, mock_update_task, mock_keycloak_openid, client):
    """
    Tests that PUT /api/tasks/<task_id> returns a 400 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # Mock the service call to raise a generic exception
    mock_update_task.side_effect = Exception("Invalid task data provided")

    # 2. Define a payload and call the API endpoint
    update_data = {"title": "A new title"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.put("/api/tasks/123", json=update_data, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "Invalid task data provided" in response.get_json()["error"]

# New test to cover a generic exception handler in the join_group endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.join_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_join_group_endpoint_handles_exception(mock_get_or_create_user, mock_join_group, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/join returns a 400 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # Mock the service call to raise a generic exception
    mock_join_group.side_effect = Exception("Group is full")

    # 2. Define a payload and call the API endpoint
    join_data = {"group_id": 999}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/join", json=join_data, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "Group is full" in response.get_json()["error"]

# New test to cover a permission error when kicking a user.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.kick_user_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_kick_user_permission_denied(mock_get_or_create_user, mock_kick_service, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/<group_id>/kick returns a 400/403 error
    if the kicker is not an admin.
    """
    # 1. Configure mocks
    # Mock authentication for a non-admin user
    mock_keycloak_openid.userinfo.return_value = {"sub": "non-admin-user"}
    mock_get_or_create_user.return_value = DummyUser(id="non-admin-user")

    # Mock the service call to raise a PermissionError
    mock_kick_service.side_effect = PermissionError("Only admins can kick members.")

    # 2. Define a payload and call the API endpoint
    payload = {"user_id": "user-to-kick"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/1/kick", json=payload, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400 # Or 403, depending on your desired API behavior
    assert "Only admins can kick members" in response.get_json()["error"]

# New test to cover a validation error (past deadline).
@patch('backend.auth.keycloak_openid')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_create_task_with_past_deadline(mock_get_or_create_user, mock_keycloak_openid, client):
    """
    Tests that POST /api/tasks returns a 400 error if the deadline is in the past.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # 2. Define a payload with a deadline in the past
    task_data = {
        "title": "A task from the past",
        "deadline": "2020-01-01",
        "kind": "Test",
        "priority": "low"
    }
    headers = {"Authorization": "Bearer dummy-token"}

    # 3. Call the API endpoint
    response = client.post("/api/tasks", json=task_data, headers=headers)

    # 4. Assert the results
    assert response.status_code == 400
    assert "Deadline cannot be in the past" in response.get_json()["error"]

# New test to cover the refresh token failure path.
@patch('backend.api.keycloak_openid')
def test_refresh_token_failure(mock_keycloak_openid, client):
    """
    Tests that POST /api/refresh returns a 401 error if the refresh token is invalid.
    """
    # 1. Configure mocks
    # Mock the keycloak client to raise an exception, simulating an invalid token.
    from keycloak.exceptions import KeycloakPostError
    mock_keycloak_openid.refresh_token.side_effect = KeycloakPostError(
        response_code=400, error_message='{"error": "invalid_grant"}'
    )

    # 2. Call the API endpoint with an invalid token
    response = client.post("/api/refresh", json={"refresh_token": "invalid-or-expired-token"})

    # 3. Assert the results
    assert response.status_code == 401
    assert "Failed to refresh token" in response.get_json()["error"]
    assert "invalid_grant" in response.get_json()["details"]

# New test to cover a generic exception handler in the leave_group endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.leave_group_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_leave_group_endpoint_handles_exception(mock_get_or_create_user, mock_leave_group, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/<group_id>/leave returns a 400 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # Mock the service call to raise an exception (e.g., user is not a member)
    mock_leave_group.side_effect = Exception("User is not a member of this group.")

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/123/leave", headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "User is not a member of this group" in response.get_json()["error"]

# New test to cover missing fields in user registration.
def test_register_user_missing_fields(client):
    """
    Tests that POST /api/users/register returns a 400 error if required fields are missing.
    """
    # 1. Define a payload that is missing required fields (e.g., password)
    incomplete_registration_data = {
        "firstName": "Test",
        "lastName": "User",
        "username": "incomplete_user",
        "email": "incomplete@example.com"
    }

    # 2. Call the API endpoint
    response = client.post("/api/users/register", json=incomplete_registration_data)

    # 3. Assert the results
    assert response.status_code == 400
    assert "are required" in response.get_json()["error"]

# New test to cover a generic exception handler in the add_admin_to_group endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.promote_to_admin_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_add_admin_endpoint_handles_exception(mock_get_or_create_user, mock_promote_service, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/<group_id>/add-admin returns a 400 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication for the promoter
    mock_keycloak_openid.userinfo.return_value = {"sub": "promoter-id"}
    mock_get_or_create_user.return_value = DummyUser(id="promoter-id")

    # Mock the service call to raise an exception
    mock_promote_service.side_effect = Exception("User to promote is not a member of this group.")

    # 2. Define a payload and call the API endpoint
    payload = {"user_id": "non-member-id"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/1/add-admin", json=payload, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "User to promote is not a member" in response.get_json()["error"]

# New test to cover a permission error when promoting a user.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.promote_to_admin_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_add_admin_permission_denied(mock_get_or_create_user, mock_promote_service, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/<group_id>/add-admin returns a 400/403 error
    if the promoter is not an admin.
    """
    # 1. Configure mocks
    # Mock authentication for a non-admin user
    mock_keycloak_openid.userinfo.return_value = {"sub": "non-admin-user"}
    mock_get_or_create_user.return_value = DummyUser(id="non-admin-user")

    # Mock the service call to raise a PermissionError
    mock_promote_service.side_effect = PermissionError("Only admins can promote other members.")

    # 2. Define a payload and call the API endpoint
    payload = {"user_id": "user-to-promote"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/1/add-admin", json=payload, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400 # Or 403, depending on your desired API behavior
    assert "Only admins can promote other members" in response.get_json()["error"]

# New test to cover a generic exception handler in the get_groups_for_specific_user endpoint.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_groups_for_user')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_get_groups_for_user_handles_exception(mock_get_or_create_user, mock_get_groups, mock_keycloak_openid, client):
    """
    Tests that GET /api/groups/user/<user_id> returns a 500 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}
    mock_get_or_create_user.return_value = DummyUser(id="requesting-user-id")

    # Mock the service call to raise an exception
    mock_get_groups.side_effect = Exception("Internal service error")

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get("/api/groups/user/some-user-id", headers=headers)

    # 3. Assert the results
    assert response.status_code == 500
    assert "Internal service error" in response.get_json()["error"]

# New test to cover an exception during user registration.
@patch('backend.api.user_service')
def test_register_user_service_exception(mock_user_service, client):
    """
    Tests that POST /api/users/register returns a 500 error if the service call fails.
    """
    # 1. Configure mocks
    # Mock the user service to raise an exception
    mock_user_service.register_user.side_effect = Exception("Username already exists")

    # 2. Define a payload for the API call
    registration_data = {
        "firstName": "Test",
        "lastName": "User",
        "username": "existing_user",
        "email": "test@example.com",
        "password": "a-secure-password"
    }

    # 3. Call the API endpoint
    response = client.post("/api/users/register", json=registration_data)

    # 4. Assert the results
    assert response.status_code == 500
    assert "Keycloak or internal error" in response.get_json()["error"]
    assert "Username already exists" in response.get_json()["details"]

# New test to cover the login failure path.
@patch('backend.api.keycloak_openid')
def test_login_failure(mock_keycloak_openid, client):
    """
    Tests that POST /api/login returns a 401 error if login fails.
    """
    # 1. Configure mocks
    # Mock the keycloak client to raise an exception, simulating invalid credentials.
    from keycloak.exceptions import KeycloakAuthenticationError
    mock_keycloak_openid.token.side_effect = KeycloakAuthenticationError(
        response_code=401, error_message='{"error": "invalid_grant"}'
    )

    # 2. Call the API endpoint with invalid credentials
    response = client.post("/api/login", json={"username": "testuser", "password": "wrong-password"})

    # 3. Assert the results
    assert response.status_code == 401
    assert "Login failed" in response.get_json()["error"]
    assert "invalid_grant" in response.get_json()["details"]

# New test to cover missing fields in login.
def test_login_endpoint_missing_fields(client):
    """
    Tests that POST /api/login returns a 400 error if username or password is missing.
    """
    # 1. Test with missing password
    response1 = client.post("/api/login", json={"username": "testuser"})
    assert response1.status_code == 400
    assert "Username and password required" in response1.get_json()["error"]

    # 2. Test with missing username
    response2 = client.post("/api/login", json={"password": "somepassword"})
    assert response2.status_code == 400
    assert "Username and password required" in response2.get_json()["error"]

# New test to cover the error path of get_tasks_for_specific_user
@patch('backend.auth.keycloak_openid')
@patch('backend.api.get_tasks_for_user')
def test_get_tasks_for_specific_user_not_found(mock_get_tasks, mock_keycloak_openid, client):
    """
    Tests that GET /api/tasks/user/<user_id> returns a 404 if the user does not exist.
    """
    # 1. Configure mocks
    # Mock authentication
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Mock the service call to raise an exception (user not found)
    target_user_id = "non-existent-user"
    mock_get_tasks.side_effect = Exception(f"User with id {target_user_id} does not exist")

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/tasks/user/{target_user_id}", headers=headers)

    # 3. Assert the results
    assert response.status_code == 404
    assert "does not exist" in response.get_json()["error"]

# New test to cover an admin trying to kick another admin.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.kick_user_service')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
def test_kick_user_cannot_kick_admin(mock_get_or_create_user, mock_kick_service, mock_keycloak_openid, client):
    """
    Tests that POST /api/groups/<group_id>/kick returns a 400 error
    if an admin tries to kick another admin.
    """
    # 1. Configure mocks
    # Mock authentication for the admin performing the action
    mock_keycloak_openid.userinfo.return_value = {"sub": "admin-kicker"}
    mock_get_or_create_user.return_value = DummyUser(id="admin-kicker")

    # Mock the service call to raise a PermissionError
    mock_kick_service.side_effect = PermissionError("Admins cannot kick other admins.")

    # 2. Define a payload and call the API endpoint
    payload = {"user_id": "admin-to-kick"}
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.post("/api/groups/1/kick", json=payload, headers=headers)

    # 3. Assert the results
    assert response.status_code == 400
    assert "Admins cannot kick other admins" in response.get_json()["error"]

# New test to cover an edge case where a member's user record is missing.
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_group_members_with_orphaned_membership(mock_db_get, mock_keycloak_openid, client):
    """
    Tests that GET /api/groups/<group_id>/members handles memberships
    for which the user record no longer exists.
    """
    # 1. Configure mocks
    mock_keycloak_openid.userinfo.return_value = {"sub": "requesting-user-id"}

    # Create a group with one valid member and one orphaned membership
    valid_member = DummyUser(id="valid-member", username="valid")
    
    # Simulate the GroupMembership relationship
    valid_membership = type('DummyMembership', (object,), {'user': valid_member, 'role': 'member'})()
    orphaned_membership = type('DummyMembership', (object,), {'user': None, 'role': 'member'})() # User is None

    group_to_find = DummyGroup()
    group_to_find.group_memberships = [valid_membership, orphaned_membership]
    mock_db_get.return_value = group_to_find

    # 2. Call the API endpoint
    headers = {"Authorization": "Bearer dummy-token"}
    response = client.get(f"/api/groups/{group_to_find.id}/members", headers=headers)

    # 3. Assert the results
    assert response.status_code == 200
    data = response.get_json()
    # Only the valid member should be in the list
    assert len(data["members"]) == 1
    assert data["members"][0]["id"] == "valid-member"

# Tests for populate_keycloak_users function
@patch('backend.api.keycloak_admin')
@patch('backend.api.UserService')
def test_populate_keycloak_users(mock_UserService, mock_keycloak_admin):
    """
    Tests the helper function that syncs Keycloak users to the local DB.
    """
    from backend.api import populate_keycloak_users
    
    # 1. Setup mocks
    mock_keycloak_admin.get_users.return_value = [
        {"id": "u1", "username": "user1", "email": "e1@test.com"},
        {"id": "u2", "sub": "u2_sub", "username": "user2", "email": "e2@test.com"}, # Test 'sub' fallback
        {"username": "no_id"} # Should be skipped
    ]
    
    mock_service_instance = mock_UserService.return_value
    
    # 2. Run function
    populate_keycloak_users()
    
    # 3. Assert
    assert mock_keycloak_admin.get_users.called
    assert mock_service_instance.get_or_create_user_from_keycloak.call_count == 2

# Tests fallback logic for get_groups_for_specific_admin_user
@patch('backend.auth.keycloak_openid')
@patch('backend.api.keycloak_openid')
@patch('backend.api.db.session.get')
@patch('backend.api.user_service.get_or_create_user_from_keycloak')
@patch('backend.api.get_groups_for_user')
def test_get_admin_groups_fallback(mock_get_groups, mock_get_or_create, mock_db_get, mock_api_openid, mock_auth_openid, client):
    """
    Tests GET /api/groups/user/admin/<user_id> when user is not in local DB but valid in Keycloak.
    """
    user_id = "admin-user"
    token = "token"
    
    # Mocks
    mock_auth_openid.userinfo.return_value = {"sub": user_id}
    mock_db_get.return_value = None # Not in DB
    mock_api_openid.userinfo.return_value = {"sub": user_id} # Token matches
    
    user = DummyUser(id=user_id)
    mock_get_or_create.return_value = user
    
    # Groups setup
    g1 = DummyGroup()
    g1.group_memberships = [type('DummyMembership', (object,), {'user_id': user_id, 'role': 'admin'})()]
    mock_get_groups.return_value = [g1]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/api/groups/user/admin/{user_id}", headers=headers)
    
    assert response.status_code == 200
    assert len(response.get_json()) == 1
    mock_get_or_create.assert_called()

# Tests exception handling for get_groups_for_specific_admin_user
@patch('backend.auth.keycloak_openid')
@patch('backend.api.db.session.get')
def test_get_admin_groups_exception(mock_db_get, mock_auth_openid, client):
    """
    Tests that GET /api/groups/user/admin/<user_id> handles exceptions correctly.
    """
    mock_auth_openid.userinfo.return_value = {"sub": "u1"}
    mock_db_get.side_effect = Exception("DB Error")
    
    headers = {"Authorization": "Bearer token"}
    response = client.get("/api/groups/user/admin/u1", headers=headers)
    
    assert response.status_code == 500
    assert "DB Error" in response.get_json()["error"]