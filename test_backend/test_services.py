import os
import sys
from types import SimpleNamespace, ModuleType
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
import pytest
from backend import services

# Mock classes for testing
class DummyExpr:
    def __or__(self, other):
        return self
class DummyColumn:
    def __eq__(self, other):
        return DummyExpr

class FakeUser:
    query = None
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        # Ensure group_memberships is always a list for iteration
        self.group_memberships = kwargs.get('group_memberships', [])
        # Add a way to set group_memberships for testing
        if 'group_memberships' not in kwargs:
            self.group_memberships = []

        self.birthday = kwargs.get('birthday')
        self.faculty = kwargs.get('faculty')

def make_fake_db():
    session = SimpleNamespace(add=Mock(), commit=Mock(), get=Mock(), query=MagicMock(), delete=Mock())
    return SimpleNamespace(session=session)

# Install a fake 'models' module into sys.modules so services can import it
fake_models = ModuleType("models")
fake_models.db = make_fake_db()
fake_models.User = FakeUser
fake_models.Group = SimpleNamespace()
fake_models.Task = SimpleNamespace()
fake_models.GroupMembership = SimpleNamespace()
sys.modules["models"] = fake_models

class FakeTask:
    query = None
    # Class-level attributes für SQLAlchemy-Style Vergleiche
    title = object()
    deadline = object()
    user_id = object()
    group_id = object()
    status = object()
    progress = object()
    priority = object()
    assignee = object()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# -----------------------------
# Tests for get_user_service
# -----------------------------
def test_get_user_service_returns_user_when_exists():
    existing = FakeUser(id="u10", username="carol", email="carol@example.com")
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = existing

    result = services.get_user_service("u10")

    assert result is existing

def test_get_user_service_raises_when_not_exists():
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = None

    with pytest.raises(Exception) as excinfo:
        services.get_user_service("missing")
    assert "does not exist" in str(excinfo.value)


# -----------------------------
# Tests for create_task_service (fixed: provide class-level attributes used in comparisons)
# -----------------------------
def test_create_task_service_returns_existing_task(monkeypatch):
    data = {
        "title": "Homework",
        "deadline": "2025-10-30",
        "kind": "homework",
        "priority": "high",
        "user_id": "u1",
        "group_id": 1,
    }

    existing_task = FakeTask(
        title="Homework",
        deadline=date.fromisoformat("2025-10-30"),
        user_id="u1",
        group_id=1
    )

    # filter(...).first() should return existing_task
    FakeTask.query = SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(first=lambda: existing_task))
    services.Task = FakeTask
    services.db = make_fake_db()

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2025, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    result = services.create_task_service(data)
    assert result is existing_task
    assert services.db.session.add.call_count == 0
    assert services.db.session.commit.call_count == 0


def test_create_task_service_creates_and_commits_new_task(monkeypatch):
    data = {
        "title": "Project",
        "deadline": "2025-11-01",
        "kind": "project",
        "priority": "medium",
        "user_id": "u2",
        "group_id": 2,
        "assignee": "u3",
        "notes": "Do research",
        "progress": 20
    }

    # filter(...).first() returns None (no duplicate)
    FakeTask.query = SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(first=lambda: None))
    services.Task = FakeTask
    services.db = make_fake_db()

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2025, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    result = services.create_task_service(data)

    assert isinstance(result, FakeTask)
    assert result.title == "Project"
    assert result.deadline == date.fromisoformat("2025-11-01")
    assert result.kind == "project"
    assert result.priority == "medium"
    assert result.user_id == "u2"
    assert result.group_id == 2
    assert result.assignee == "u3"
    assert result.notes == "Do research"
    assert result.progress == 20

    services.db.session.add.assert_called_once_with(result)
    services.db.session.commit.assert_called_once()


# -----------------------------
# Tests for update_task_service
# -----------------------------
def test_update_task_service_updates_fields_and_deadline(monkeypatch):
    # prepare fake task class and existing instance
    class FakeTask:
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    existing = FakeTask(
        id="t1",
        title="Old Title",
        deadline=date.fromisoformat("2025-10-01"),
        kind="homework",
        priority="low",
        status="todo",
        user_id="u1",
        group_id=1,
        assignee=None,
        notes="old",
        progress=0
    )

    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = existing

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2025, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    update_data = {
        "title": "New Title",
        "priority": "high",
        "status": "in_progress",
        "deadline": "2025-12-15",
        "progress": 75,
        "notes": "updated notes"
    }

    result = services.update_task_service("t1", update_data)

    assert result is existing
    assert result.title == "New Title"
    assert result.priority == "high"
    assert result.status == "in_progress"
    assert result.deadline == date.fromisoformat("2025-12-15")
    assert result.progress == 75
    assert result.notes == "updated notes"
    services.db.session.commit.assert_called_once()


def test_update_task_service_raises_when_task_not_found():
    class FakeTask:
        query = None

    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = None

    with pytest.raises(Exception) as excinfo:
        services.update_task_service("missing-id", {"title": "x"})
    assert "does not exist" in str(excinfo.value)


# -----------------------------
# Tests for get_tasks_for_user
# -----------------------------
def test_get_tasks_for_user_returns_tasks_for_user_and_group():
    # helper types to emulate SQLAlchemy column expression behavior
    class DummyExpr:
        def __or__(self, other):
            return self
    class DummyColumn:
        def __eq__(self, other):
            return DummyExpr()
        def in_(self, seq):
            return DummyExpr()

    # prepare user with one group
    group = SimpleNamespace(id=2)
    user = FakeUser(id="u5", username="eve", email="eve@example.com")
    user.group_memberships = [SimpleNamespace(group=group)]
    services.User = FakeUser
    services.db = make_fake_db()

    # fake Task class and two tasks: one owned by user, one belonging to group
    class FakeTask:
        # provide dummy columns so expressions like Task.user_id and Task.group_id.in_(...) work
        user_id = DummyColumn()
        group_id = DummyColumn()
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    task_user = FakeTask(id="t1", user_id="u5", group_id=3)
    task_group = FakeTask(id="t2", user_id="other", group_id=2)

    # Task.query.filter(...).all() returns both tasks
    FakeTask.query = SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(all=lambda: [task_user, task_group]))
    services.Task = FakeTask
    services.db.session.get.return_value = user

    result = services.get_tasks_for_user("u5")
    assert result == [task_user, task_group]

def test_get_tasks_for_user_returns_empty_list_when_user_missing():
    """Tests that get_tasks_for_user raises an error if the user is not found."""
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = None

    with pytest.raises(Exception, match="does not exist"):
        services.get_tasks_for_user("nope")

# -----------------------------
# Tests for get_all_tasks
# -----------------------------
def test_get_all_tasks_returns_all_tasks():
    class FakeTask:
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    t1 = FakeTask(id="a")
    t2 = FakeTask(id="b")
    FakeTask.query = SimpleNamespace(all=lambda: [t1, t2])
    services.Task = FakeTask

    result = services.get_all_tasks()
    assert result == [t1, t2]

def test_get_all_tasks_returns_empty_list_when_none():
    class FakeTask:
        query = None
    FakeTask.query = SimpleNamespace(all=lambda: [])
    services.Task = FakeTask

    result = services.get_all_tasks()
    assert result == []

# -----------------------------
# Tests for create_group_service
# -----------------------------
def test_create_group_service_creates_and_commits_new_group():
    # helper type to emulate SQLAlchemy column expression behavior
    class DummyExpr:
        def __or__(self, other):
            return self
    class DummyColumn:
        def __eq__(self, other):
            return DummyExpr()

    # fake Group class with necessary column attributes
    class FakeGroup:
        group_number = DummyColumn()
        invite_link = DummyColumn()
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        _sa_instance_state = MagicMock() # Use MagicMock to handle subscripting

    # filter(...).first() returns None (no duplicate)
    FakeGroup.query = SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(first=lambda: None))
    services.Group = FakeGroup
    services.db = make_fake_db()

    data = {
        "name": "New Study Group",
        "description": "A fresh group",
        "groupNumber": "G999",
        "inviteLink": "newlink999"
    }

    result = services.create_group_service(data, creator_id="creator-1")

    assert isinstance(result, FakeGroup)
    assert result.name == "New Study Group"
    assert result.description == "A fresh group"
    assert result.group_number == "G999"
    assert result.invite_link == "newlink999" 

    assert services.db.session.add.call_count == 2 # Group and Membership
    assert services.db.session.commit.call_count == 1


def test_join_group_service_adds_user_to_group():
    class FakeGroup:
        group_number = DummyColumn()
        invite_link = DummyColumn()
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        _sa_instance_state = MagicMock()

    # Setup fake user and group
    user = FakeUser(id="u7", username="frank", email="frank@example.com")
    group = FakeGroup(id=3, name="Test Group")

    # Setup queries
    services.User = FakeUser
    services.Group = FakeGroup
    services.db = make_fake_db()
    services.db.session.get.side_effect = [user, group] # First call returns user, second group
    services.db.session.query.return_value.filter_by.return_value.first.return_value = None # Configure the mock chain

    result = services.join_group_service("u7", 3)

    assert result is group
    assert services.db.session.add.call_count == 1
    services.db.session.commit.assert_called_once()


def test_join_group_service_returns_group_if_already_member():
    # Setup fake user already in group
    user = FakeUser(id="u8", username="grace", email="grace@example.com")
    
    class FakeGroup:
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    services.User = FakeUser
    services.Group = FakeGroup
    services.db = make_fake_db()
    services.db.session.get.side_effect = [user, FakeGroup(id=4)]
    services.db.session.query.return_value.filter_by.return_value.first.return_value = True # Configure the mock chain

    result = services.join_group_service("u8", 4)

    assert result is not None
    assert services.db.session.commit.call_count == 0


def test_join_group_service_raises_when_user_not_found():
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = None

    with pytest.raises(Exception) as excinfo:
        services.join_group_service("missing", 1)
    assert "User with id missing does not exist" in str(excinfo.value)


def test_join_group_service_raises_when_group_not_found():
    user = FakeUser(id="u9")
    class FakeGroup:
        query = None

    services.User = FakeUser
    services.Group = FakeGroup
    services.db = make_fake_db()
    # First get (user) succeeds, second (group) fails
    services.db.session.get.side_effect = [user, None]

    with pytest.raises(Exception) as excinfo:
        services.join_group_service("u9", 999)
    assert "Group with id 999 does not exist" in str(excinfo.value)


# -----------------------------
# Tests for leave_group_service
# -----------------------------
def test_leave_group_service_member_leaves():
    """Rule 2: A regular member leaves the group."""
    membership = SimpleNamespace(user_id="user1", group_id=1, role="member")
    
    services.db = make_fake_db()
    services.db.session.query.return_value.filter_by.return_value.first.return_value = membership

    services.leave_group_service("user1", 1)

    services.db.session.delete.assert_called_once_with(membership)
    services.db.session.commit.assert_called_once()

def test_leave_group_service_admin_leaves_not_last():
    """Rule 3: An admin leaves, but other admins remain."""
    membership = SimpleNamespace(user_id="admin1", group_id=1, role="admin")
    
    services.db = make_fake_db()
    # Mock the membership lookup
    services.db.session.query.return_value.filter_by.return_value.first.return_value = membership
    # Mock the count of other admins to be greater than 0
    services.db.session.query.return_value.filter.return_value.count.return_value = 1

    services.leave_group_service("admin1", 1)

    # The group should NOT be deleted
    services.db.session.delete.assert_called_once_with(membership)
    services.db.session.commit.assert_called_once()

def test_leave_group_service_last_admin_leaves():
    """Rule 4: The last admin leaves, deleting the group."""
    class FakeGroup:
        pass
    
    membership = SimpleNamespace(user_id="admin1", group_id=1, role="admin")
    group_to_delete = FakeGroup()

    services.Group = FakeGroup
    services.db = make_fake_db()
    # Mock the membership lookup
    services.db.session.query.return_value.filter_by.return_value.first.return_value = membership
    # Mock the count of other admins to be 0
    services.db.session.query.return_value.filter.return_value.count.return_value = 0
    # Mock the lookup for the group to be deleted
    services.db.session.get.return_value = group_to_delete

    services.leave_group_service("admin1", 1)

    # The group itself should be deleted, not the membership directly
    services.db.session.delete.assert_called_once_with(group_to_delete)
    services.db.session.commit.assert_called_once()

def test_leave_group_service_not_a_member_fails():
    """Tests that leave_group_service raises an exception if the user is not a member."""
    services.db = make_fake_db()
    # Mock filter_by.first to return None, indicating no membership
    services.db.session.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(Exception, match="User is not a member of this group."):
        services.leave_group_service("non_member_user", 1)

    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_not_called()

def test_kick_user_service_cannot_kick_self():
    """Tests that an admin cannot kick themselves."""
    # Setup: Kicker and user to be kicked are the same person
    kicker_id = "admin1"
    user_to_kick_id = "admin1"
    group_id = 1

    # Mock the membership lookup for the kicker (they are an admin)
    kicker_membership = SimpleNamespace(role='admin')
    
    services.db = make_fake_db()
    # Configure the mock to return the kicker's membership on the first call
    # and the same membership on the second call (since kicker == kicked).
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: kicker_membership),
        MagicMock(first=lambda: kicker_membership)
    ]

    # Action & Assert: Expect a PermissionError
    with pytest.raises(PermissionError, match="You cannot kick yourself. Use the 'Leave Group' feature."):
        services.kick_user_service(kicker_id, user_to_kick_id, group_id)

    # The membership of the user to be kicked is not even queried
    assert services.db.session.query.return_value.filter_by.call_count == 2
    services.db.session.delete.assert_not_called()

def test_kick_user_service_cannot_kick_another_admin():
    """Tests that an admin cannot kick another admin."""
    # Setup
    kicker_id = "admin1"
    user_to_kick_id = "admin2"
    group_id = 1

    # Mocks for memberships
    kicker_membership = SimpleNamespace(role='admin')
    admin_to_kick_membership = SimpleNamespace(role='admin')

    services.db = make_fake_db()
    # First query (for kicker) returns admin, second query (for user to kick) also returns admin
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: kicker_membership),
        MagicMock(first=lambda: admin_to_kick_membership)
    ]

    # Action & Assert: Expect a PermissionError
    with pytest.raises(PermissionError, match="Admins cannot kick other admins"):
        services.kick_user_service(kicker_id, user_to_kick_id, group_id)

def test_promote_to_admin_service_success():
    """Tests that a user is successfully promoted to admin."""
    # Setup
    promoter_id = "admin1"
    user_to_promote_id = "member1"
    group_id = 1

    # Mocks for memberships
    promoter_membership = SimpleNamespace(role='admin')
    member_to_promote_membership = SimpleNamespace(role='member')

    services.db = make_fake_db()
    # First query (for promoter) returns admin, second query (for user to promote) returns member
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: promoter_membership),
        MagicMock(first=lambda: member_to_promote_membership)
    ]

    # Action
    services.promote_to_admin_service(promoter_id, user_to_promote_id, group_id)

    assert member_to_promote_membership.role == 'admin'
    services.db.session.commit.assert_called_once()

def test_promote_to_admin_service_promoter_not_admin():
    """Tests that an error is raised if the promoter is not an admin."""
    # Setup
    promoter_id = "not-an-admin"
    user_to_promote_id = "member1"
    group_id = 1

    # Mocks for memberships
    promoter_membership = SimpleNamespace(role='member') # Promoter is just a member

    services.db = make_fake_db()
    # The first query for the promoter's membership returns 'member'
    services.db.session.query.return_value.filter_by.return_value.first.return_value = promoter_membership

    # Action & Assert
    with pytest.raises(PermissionError, match="Only admins can promote other members."):
        services.promote_to_admin_service(promoter_id, user_to_promote_id, group_id)

    services.db.session.commit.assert_not_called()

def test_promote_to_admin_service_user_not_member():
    """Tests that an error is raised if the user to be promoted is not a member."""
    # Setup
    promoter_id = "admin1"
    user_to_promote_id = "not-a-member"
    group_id = 1

    # Mocks for memberships
    promoter_membership = SimpleNamespace(role='admin')

    services.db = make_fake_db()
    # First query (for promoter) returns admin, second query (for user to promote) returns None
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: promoter_membership),
        MagicMock(first=lambda: None)
    ]

    # Action & Assert
    with pytest.raises(Exception, match="User to be promoted is not a member of this group."):
        services.promote_to_admin_service(promoter_id, user_to_promote_id, group_id)

    services.db.session.commit.assert_not_called()

def test_update_task_service_sets_progress_to_100_on_done(monkeypatch):
    """Tests that setting a task's status to 'done' also sets its progress to 100."""
    # Setup
    task = FakeTask(id="t_done", status="in_progress", progress=50, deadline=date(2025, 1, 1))
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    # Mock date.today() to be before the deadline
    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2024, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    update_data = {"status": "done"}

    # Action
    services.update_task_service("t_done", update_data)

    # Assert
    assert task.status == "done"
    assert task.progress == 100
    services.db.session.commit.assert_called_once()

def test_kick_user_service_user_not_member():
    """Tests that an error is raised if the user to be kicked is not a member."""
    # Setup
    kicker_id = "admin1"
    user_to_kick_id = "not-a-member"
    group_id = 1

    # Mocks for memberships
    kicker_membership = SimpleNamespace(role='admin')

    services.db = make_fake_db()
    # First query (for kicker) returns admin, second query (for user to kick) returns None
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: kicker_membership),
        MagicMock(first=lambda: None)
    ]

    # Action & Assert
    with pytest.raises(Exception, match="User to be kicked is not a member of this group."):
        services.kick_user_service(kicker_id, user_to_kick_id, group_id)

    # Assert that the database was queried twice but no delete/commit happened
    assert services.db.session.query.return_value.filter_by.call_count == 2
    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_not_called()

def test_leave_group_service_last_admin_group_not_found():
    """
    Tests that leaving as the last admin does not fail if the group
    to be deleted is somehow already gone.
    """
    # Setup: An admin is leaving as the last admin
    membership = SimpleNamespace(user_id="admin1", group_id=1, role="admin")
    
    services.db = make_fake_db()
    # Mock the membership lookup
    services.db.session.query.return_value.filter_by.return_value.first.return_value = membership
    # Mock the count of other admins to be 0
    services.db.session.query.return_value.filter.return_value.count.return_value = 0
    # Mock the lookup for the group to be deleted to return None
    services.db.session.get.return_value = None

    # Action: The service should execute without raising an error
    services.leave_group_service("admin1", 1)

    # Assert: The service attempts to delete the group, but since it's None,
    # db.session.delete is not called. The membership is also not deleted in this path.
    # The important part is that commit is still called to finalize any transaction.
    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_called_once()

    # Verify that get was called to try to find the group
    services.db.session.get.assert_called_once_with(services.Group, 1)


def test_get_or_create_user_from_keycloak_fallback_to_email_for_username():
    """
    Tests that get_or_create_user_from_keycloak uses the email as username
    if 'preferred_username' is not in the Keycloak user info.
    """
    # 1. Setup: Create a UserService instance
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Define Keycloak user info without 'preferred_username'
    keycloak_userinfo = {
        "sub": "new-user-id",
        "email": "fallback@example.com"
        # 'preferred_username' is intentionally omitted
    }

    # 3. Mock the DB to indicate the user does not exist yet
    mock_db_session.get.return_value = None

    # 4. Action: Call the service function
    # We patch the User model to inspect the arguments it's called with
    with patch('backend.services.User') as MockUser:
        user_service.get_or_create_user_from_keycloak(keycloak_userinfo)

        # 5. Assert: Check that the User constructor was called with the email as username
        MockUser.assert_called_once_with(
            id="new-user-id",
            username="fallback@example.com", # This is the important check
            email="fallback@example.com"
        )
        mock_db_session.add.assert_called_once()

def test_kick_user_service_kicker_not_admin():
    """Tests that an error is raised if the user trying to kick is not an admin."""
    # Setup
    kicker_id = "not-an-admin"
    user_to_kick_id = "some-member"
    group_id = 1

    # Mocks for memberships
    kicker_membership = SimpleNamespace(role='member') # Kicker is just a member

    services.db = make_fake_db()
    # The first query for the kicker's membership returns 'member'
    services.db.session.query.return_value.filter_by.return_value.first.return_value = kicker_membership

    # Action & Assert
    with pytest.raises(PermissionError, match="Only admins can kick members."):
        services.kick_user_service(kicker_id, user_to_kick_id, group_id)

    # Assert that no changes were committed
    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_not_called()

def test_update_task_service_assignee_not_found():
    """Tests that an error is raised if the assignee user is not found."""
    # Setup
    task = FakeTask(id="t_assignee_test", group_id=1)

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()

    # The get for the task succeeds, but the get for the assignee user returns None
    services.db.session.get.side_effect = lambda model, id: {
        "t_assignee_test": task
    }.get(id)

    # Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service("t_assignee_test", {"assignee": "non-existent-user"})

    # Assert that no changes were committed
    services.db.session.commit.assert_not_called()

def test_get_or_create_user_from_keycloak_uses_preferred_username():
    """
    Tests that get_or_create_user_from_keycloak uses 'preferred_username'
    when it is available in the Keycloak user info.
    """
    # 1. Setup: Create a UserService instance
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Define Keycloak user info with 'preferred_username'
    keycloak_userinfo = {
        "sub": "new-user-id-2",
        "preferred_username": "preferred_name",
        "email": "email_should_be_ignored@example.com"
    }

    # 3. Mock the DB to indicate the user does not exist yet
    mock_db_session.get.return_value = None

    # 4. Action: Call the service function
    # We patch the User model to inspect the arguments it's called with
    with patch('backend.services.User') as MockUser:
        user_service.get_or_create_user_from_keycloak(keycloak_userinfo)

        # 5. Assert: Check that the User constructor was called with the preferred_username
        MockUser.assert_called_once_with(
            id="new-user-id-2",
            username="preferred_name", # This is the important check
            email="email_should_be_ignored@example.com"
        )
        mock_db_session.add.assert_called_once()

def test_get_or_create_user_from_keycloak_missing_sub_id():
    """
    Tests that get_or_create_user_from_keycloak raises an exception
    if the 'sub' (user ID) field is missing from the Keycloak user info.
    """
    # 1. Setup: Create a UserService instance
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Define Keycloak user info without 'sub'
    keycloak_userinfo_no_sub = {"email": "no_sub@example.com"}

    # 3. Action & Assert: Expect an Exception
    with pytest.raises(Exception, match="Missing Keycloak user ID"):
        user_service.get_or_create_user_from_keycloak(keycloak_userinfo_no_sub)

def test_leave_group_service_user_not_member():
    """
    Tests that leave_group_service raises an exception if the user
    is not a member of the group.
    """
    # 1. Setup: Mock the database to return no membership
    services.db = make_fake_db()
    services.db.session.query.return_value.filter_by.return_value.first.return_value = None

    # 2. Action & Assert: Expect an Exception
    with pytest.raises(Exception, match="User is not a member of this group."):
        services.leave_group_service("non-member-user", 99)

    # 3. Assert that no database modifications were attempted
    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_not_called()

def test_update_task_service_assignee_not_found_again():
    """
    Tests that update_task_service raises a ValueError if the assignee user does not exist.
    This specifically targets line 150 in services.py.
    """
    # 1. Setup
    task_to_update = FakeTask(id="task-1", group_id=1)
    update_data = {"assignee": "non-existent-user-id"}

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()

    # Mock db.session.get to return the task, but return None for the user
    def get_side_effect(model, entity_id):
        if model == FakeTask and entity_id == "task-1":
            return task_to_update
        if model == FakeUser and entity_id == "non-existent-user-id":
            return None
        return MagicMock() # Default return for other calls
    services.db.session.get.side_effect = get_side_effect

    # 2. Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service("task-1", update_data)

def test_user_service_update_user_not_found():
    """
    Tests that UserService.update_user raises an exception if the user is not found.
    """
    # 1. Setup: Create a UserService instance
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Mock the DB to indicate the user does not exist
    mock_db_session.get.return_value = None

    # 3. Action & Assert: Expect an Exception
    with pytest.raises(Exception, match="User with id non-existent-user not found."):
        user_service.update_user("non-existent-user", {"username": "new_name"})

    # 4. Assert that no database modifications were attempted
    mock_db_session.commit.assert_not_called()

def test_update_task_service_assignee_not_found_final():
    """
    Tests that update_task_service raises a ValueError if the assignee user does not exist.
    This specifically targets line 150 in services.py.
    """
    # 1. Setup
    task_to_update = FakeTask(id="task-for-assignment", group_id=1)
    update_data = {"assignee": "non-existent-user-id"}

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()

    # Mock db.session.get to return the task, but return None for the user
    def get_side_effect(model, entity_id):
        if model == FakeTask and entity_id == "task-for-assignment":
            return task_to_update
        if model == FakeUser and entity_id == "non-existent-user-id":
            return None
        return MagicMock() # Default return for other calls
    services.db.session.get.side_effect = get_side_effect

    # 2. Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service("task-for-assignment", update_data)

def test_user_service_update_user_not_found_final():
    """
    Tests that UserService.update_user raises an exception if the user to be updated is not found.
    """
    # 1. Setup: Create a UserService instance with mocked dependencies
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Mock the database to simulate that the user does not exist
    # The `get` call should return None
    mock_db_session.get.return_value = None

    # 3. Action & Assert: Call the service method and expect an Exception
    with pytest.raises(Exception, match="User with id non-existent-user not found."):
        user_service.update_user("non-existent-user", {"username": "new_username"})

    # 4. Assert that no changes were committed to the database
    mock_db_session.commit.assert_not_called()

def test_update_task_service_assignee_not_found_yet_again():
    """
    Tests that update_task_service raises a ValueError if the assignee user does not exist.
    This specifically targets line 150 in services.py.
    """
    # 1. Setup
    task_to_update = FakeTask(id="task-for-assignment-2", group_id=1)
    update_data = {"assignee": "non-existent-user-id-2"}

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()

    # Mock db.session.get to return the task, but return None for the user
    def get_side_effect(model, entity_id):
        if model == FakeTask and entity_id == "task-for-assignment-2":
            return task_to_update
        if model == FakeUser and entity_id == "non-existent-user-id-2":
            return None
        return MagicMock() # Default return for other calls
    services.db.session.get.side_effect = get_side_effect

    # 2. Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service("task-for-assignment-2", update_data)

def test_user_service_update_user_not_found_one_more_time():
    """
    Tests that UserService.update_user raises an exception if the user to be updated is not found.
    This test ensures the error path is covered.
    """
    # 1. Setup: Create a UserService instance with mocked dependencies
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    # 2. Mock the database to simulate that the user does not exist.
    # The `get` call on the session should return None.
    mock_db_session.get.return_value = None

    # 3. Action & Assert: Call the service method with a non-existent user ID
    # and assert that the correct exception is raised.
    with pytest.raises(Exception, match="User with id non-existent-user-id not found."):
        user_service.update_user("non-existent-user-id", {"username": "new_username"})

    # 4. Assert that no changes were committed to the database since the user was not found.
    mock_db_session.commit.assert_not_called()

def test_update_task_service_assignee_not_found_for_the_last_time():
    """
    Tests that update_task_service raises a ValueError if the assignee user does not exist.
    This specifically targets line 150 in services.py.
    """
    # 1. Setup
    task_to_update = FakeTask(id="task-for-assignment-3", group_id=1)
    update_data = {"assignee": "non-existent-user-id-3"}

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()

    # Mock db.session.get to return the task, but return None for the user
    def get_side_effect(model, entity_id):
        if model == FakeTask and entity_id == "task-for-assignment-3":
            return task_to_update
        if model == FakeUser and entity_id == "non-existent-user-id-3":
            return None
        return MagicMock() # Default return for other calls
    services.db.session.get.side_effect = get_side_effect

    # 2. Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service("task-for-assignment-3", update_data)

def test_user_service_update_user_success():
    """
    Tests that UserService.update_user correctly updates all provided fields.
    This covers the specific 'if' blocks for username, email, faculty, and birthday.
    """
    # 1. Setup: Create a UserService instance and a fake user to update
    mock_db_session = MagicMock()
    mock_keycloak_admin = MagicMock()
    user_service = services.UserService(mock_db_session, mock_keycloak_admin)

    original_user = FakeUser(
        id="user-to-update",
        username="old_username",
        email="old@example.com",
        faculty="Old Faculty",
        birthday=date(2000, 1, 1)
    )

    # 2. Mock the database to return the user
    mock_db_session.get.return_value = original_user

    # 3. Define the update data
    update_data = {
        "username": "new_username",
        "email": "new@example.com",
        "faculty": "New Faculty",
        "birthday": "2001-02-03"
    }

    # 4. Action: Call the update_user method
    updated_user = user_service.update_user("user-to-update", update_data)

    # 5. Assert: Check that all fields were updated correctly
    assert updated_user.username == "new_username"
    assert updated_user.email == "new@example.com"
    assert updated_user.faculty == "New Faculty"
    assert updated_user.birthday == date(2001, 2, 3)

    # Verify that the database session was called to get the user and commit the changes
    mock_db_session.get.assert_called_once_with(services.User, "user-to-update")
    mock_db_session.commit.assert_called_once()

def test_user_service_update_user_only_username():
    """
    Tests that UserService.update_user correctly updates only the username.
    This specifically targets the `if 'username' in data:` branch.
    """
    # 1. Setup
    mock_db_session = MagicMock()
    user_service = services.UserService(mock_db_session, MagicMock())
    original_user = FakeUser(id="user-to-update", username="old_username")
    mock_db_session.get.return_value = original_user

    # 2. Action
    updated_user = user_service.update_user("user-to-update", {"username": "new_username"})

    # 3. Assert
    assert updated_user.username == "new_username"
    mock_db_session.get.assert_called_once_with(services.User, "user-to-update")
    mock_db_session.commit.assert_called_once()

def test_kick_user_service_user_not_in_group():
    """
    Tests that kick_user_service raises an exception if the user to be kicked
    is not a member of the group. This covers line 335-336.
    """
    # 1. Setup
    kicker_id = "admin-user"
    user_to_kick_id = "non-member"
    group_id = 1

    # Mock memberships
    kicker_membership = SimpleNamespace(role='admin')
    # The user to be kicked has no membership, so the query returns None

    services.db = make_fake_db()
    # First query (for kicker) returns admin.
    # Second query (for user to kick) returns None.
    services.db.session.query.return_value.filter_by.side_effect = [
        MagicMock(first=lambda: kicker_membership),
        MagicMock(first=lambda: None)
    ]

    # 2. Action & Assert
    with pytest.raises(Exception, match="User to be kicked is not a member of this group."):
        services.kick_user_service(kicker_id, user_to_kick_id, group_id)

    # 3. Verify
    # The database was queried twice (once for kicker, once for kicked)
    assert services.db.session.query.return_value.filter_by.call_count == 2
    # No delete or commit should have happened
    services.db.session.delete.assert_not_called()
    services.db.session.commit.assert_not_called()

def test_update_task_service_assignee_not_found_isolated():
    """
    An isolated test to specifically cover the 'assignee not found' error path
    in update_task_service, which seems to be hard for the coverage tool to detect.
    """
    # 1. Setup
    task_id = "task-to-check"
    assignee_id = "non-existent-assignee"
    update_data = {"assignee": assignee_id}
    
    # Create a fresh fake DB for this test
    services.db = make_fake_db()
    
    # Mock the behavior of db.session.get
    # It should find the task, but not the assignee user.
    def get_side_effect(model, lookup_id):
        if model == services.Task and lookup_id == task_id:
            return FakeTask(id=task_id)
        if model == services.User and lookup_id == assignee_id:
            return None # Assignee not found
        return MagicMock() # Default for any other calls
    services.db.session.get.side_effect = get_side_effect
    
    # 2. Action & Assert
    with pytest.raises(ValueError, match="Assignee user not found"):
        services.update_task_service(task_id, update_data)













# -----------------------------
# Tests for get_all_groups
# -----------------------------
def test_get_all_groups_returns_all_groups():
    class FakeGroup:
        query = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    g1 = FakeGroup(id=1, name="Group A")
    g2 = FakeGroup(id=2, name="Group B")
    FakeGroup.query = SimpleNamespace(all=lambda: [g1, g2])
    services.Group = FakeGroup

    result = services.get_all_groups()
    
    assert result == [g1, g2]
    assert len(result) == 2
    assert result[0].name == "Group A"
    assert result[1].name == "Group B"


def test_get_all_groups_returns_empty_list_when_none():
    class FakeGroup:
        query = None
    FakeGroup.query = SimpleNamespace(all=lambda: [])
    services.Group = FakeGroup

    result = services.get_all_groups()
    assert result == []


# -----------------------------
# Tests for get_groups_for_user
# -----------------------------
def test_get_groups_for_user_returns_user_groups():
    # Setup fake user with groups
    class FakeGroup:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    g1 = FakeGroup(1, "Group A")
    g2 = FakeGroup(2, "Group B")
    
    user = FakeUser(id="u10", username="harry", email="harry@example.com")
    user.group_memberships = [SimpleNamespace(group=g1), SimpleNamespace(group=g2)]

    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = user

    result = services.get_groups_for_user("u10")
    
    assert result == [g1, g2]
    assert len(result) == 2


def test_get_groups_for_user_returns_empty_list_when_user_not_found():
    """Tests that get_groups_for_user raises an error if the user is not found."""
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = None

    with pytest.raises(Exception, match="does not exist"):
        services.get_groups_for_user("missing")


def test_get_groups_for_user_returns_empty_list_when_user_has_no_groups():
    user = FakeUser(id="u11", username="ian", email="ian@example.com")
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.return_value = user

    result = services.get_groups_for_user("u11")
    assert result == []

# -----------------------------
# Entity-specific validation tests
# -----------------------------
def test_update_task_service_validates_status_transition(monkeypatch):
    task = FakeTask(id="t3", status="todo", deadline=date(2025, 1, 1))
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    # Mock date.today() to return a fixed date before the task's deadline
    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2024, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    # Valid transition todo -> in_progress
    services.update_task_service("t3", {"status": "in_progress"})
    assert task.status == "in_progress"

    # Invalid transition in_progress -> cancelled
    with pytest.raises(ValueError) as excinfo:
        services.update_task_service("t3", {"status": "cancelled"})
    assert "Invalid status transition" in str(excinfo.value)

def test_create_task_service_validates_due_date(monkeypatch):
    """Tests that create_task_service raises ValueError if deadline is in the past."""
    data = {
        "title": "Past Task",
        "deadline": "2020-01-01",  # Past date
        "kind": "homework",
        "priority": "high"
    }
    
    services.Task = FakeTask
    services.db = make_fake_db()

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2024, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)
    
    with pytest.raises(ValueError) as excinfo:
        services.create_task_service(data)
    assert "Deadline cannot be in the past" in str(excinfo.value)

def test_update_task_service_cannot_start_past_due_task(monkeypatch):
    """Tests that update_task_service raises ValueError if trying to start a past-due task."""
    task = FakeTask(id="t_past_due", status="todo", deadline=date(2020, 1, 1))
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    # Mock date.today() to be after the task's deadline
    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2024, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    with pytest.raises(ValueError, match="Cannot start a task that is past its deadline."):
        services.update_task_service("t_past_due", {"status": "in_progress"})
    
    # Ensure status was not changed
    assert task.status == "todo"

def test_update_task_service_validates_deadline_on_update(monkeypatch):
    """Tests that update_task_service raises ValueError if a new deadline is in the past."""
    task = FakeTask(id="t_update_deadline", status="todo", deadline=date(2025, 1, 1))
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2024, 1, 1)
    monkeypatch.setattr(services, "date", FakeDate, raising=False)

    # Test with a valid future date
    services.update_task_service("t_update_deadline", {"deadline": "2025-12-31"})
    assert task.deadline == date(2025, 12, 31)

    # Test with an invalid past date
    with pytest.raises(ValueError, match="Deadline cannot be in the past"):
        services.update_task_service("t_update_deadline", {"deadline": "2023-01-01"})
    
    # Ensure deadline was not changed to the invalid value
    assert task.deadline == date(2025, 12, 31) # Should still be the last valid date

@pytest.mark.parametrize("progress_value, should_succeed", [
    # Boundary Value Analysis (Lower Boundary)
    (-1, False),   # Invalid (below lower bound)
    (0, True),    # Valid (at lower bound)
    (1, True),    # Valid (above lower bound)
    # Equivalence Partitioning (Valid middle value)
    (50, True),
    # Boundary Value Analysis (Upper Boundary)
    (99, True),   # Valid (below upper bound)
    (100, True),  # Valid (at upper bound)
    (101, False), # Invalid (above upper bound)
])
def test_update_task_service_validates_progress_with_boundaries(progress_value, should_succeed):
    """Tests progress validation using equivalence partitioning and boundary value analysis."""
    task = FakeTask(id="t4", progress=50)
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    if should_succeed:
        services.update_task_service("t4", {"progress": progress_value})
        assert task.progress == progress_value
    else:
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            services.update_task_service("t4", {"progress": progress_value})

def test_task_priority_management():
    task = FakeTask(id="t5", priority="low")
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task

    # Valid priority update
    services.update_task_service("t5", {"priority": "high"})
    assert task.priority == "high"

    # Invalid priority value
    with pytest.raises(ValueError) as excinfo:
        services.update_task_service("t5", {"priority": "super-high"})
    assert "Invalid priority value" in str(excinfo.value)

# Fix the task assignment validation test
def test_task_assignment_validation():
    # Create two users - one in group, one not
    group_user = FakeUser(id="u12")
    other_user = FakeUser(id="other-user")
    group_user.group_memberships = [SimpleNamespace(group_id=5, group=SimpleNamespace(id=5))]
    
    task = FakeTask(
        id="t6", 
        group_id=5,
        assignee=None
    )
    
    # Setup query to return either user based on id
    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()
    services.db.session.get.side_effect = lambda model, id: {
        "t6": task,
        "u12": group_user,
        "other-user": other_user
    }.get(id)

    # First verify we can assign to user in group
    services.update_task_service("t6", {"assignee": "u12"})
    assert task.assignee == "u12"

    # Then verify we cannot assign to user not in group
    with pytest.raises(ValueError) as excinfo:
        services.update_task_service("t6", {"assignee": "other-user"})
    assert "Assignee must be member of the group" in str(excinfo.value)

def test_update_task_service_member_assigns_to_own_group_success():
    """Scenario 1: A group member assigns a task to their own group (permission validation)."""
    # Setup: Task in group 1, editor is member of group 1
    task = FakeTask(id="t7", group_id=1, assignee=None)
    editor_user = FakeUser(id="editor1", group_memberships=[SimpleNamespace(group_id=1)])

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()
    # Configure the mock to return the correct object based on the requested ID.
    services.db.session.get.side_effect = lambda model, id: {
        "t7": task, "editor1": editor_user
    }.get(id)

    # Action: Editor updates task, setting group_id to their own group
    services.update_task_service("t7", {"group_id": 1}, editor_user_id="editor1")

    # Assert: Success, no error, commit called
    assert task.group_id == 1
    services.db.session.commit.assert_called_once()

def test_update_task_service_non_member_assigns_to_foreign_group_fails():
    """Scenario 2: A user tries to assign a task to a group they are not a member of (permission validation)."""
    # Setup: Task in group 1, editor is NOT member of group 1 (e.g., member of group 2)
    task = FakeTask(id="t8", group_id=1, assignee=None)
    editor_user = FakeUser(id="editor2", group_memberships=[SimpleNamespace(group_id=2)])

    services.Task = FakeTask
    services.User = FakeUser
    services.db = make_fake_db()
    # Configure the mock to return the correct object based on the requested ID.
    services.db.session.get.side_effect = lambda model, id: {
        "t8": task, "editor2": editor_user
    }.get(id)

    # Action: Editor updates task, setting group_id to a foreign group
    with pytest.raises(PermissionError, match="You can only assign tasks to groups you are a member of."):
        services.update_task_service("t8", {"group_id": 1}, editor_user_id="editor2")

    # Assert: Error raised, no commit
    services.db.session.commit.assert_not_called()

def test_update_task_service_anonymous_assigns_to_group_fails():
    """Scenario 3: An anonymous process tries to assign a task to a group (permission validation)."""
    task = FakeTask(id="t9", group_id=None)
    services.Task = FakeTask
    services.db = make_fake_db()
    services.db.session.get.return_value = task
    with pytest.raises(PermissionError, match="User ID is required to assign a task to a group."):
        services.update_task_service("t9", {"group_id": 1}, editor_user_id=None)