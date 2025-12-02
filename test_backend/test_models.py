import pytest
from flask import Flask
from datetime import date
from backend.models import db, User, Group, Task, GroupMembership

# Fixture for a Flask app with an in-memory SQLite DB.
@pytest.fixture
def app():
    """Creates and configures a new app instance for each test."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def app_context(app):
    """Provides an app context for the duration of a test."""
    with app.app_context():
        yield


class TestModelCreation:
    """Tests for basic model object creation."""

    def test_create_user(self, app_context):
        """Test creating a User object with valid data."""
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            birthday=date(2000, 1, 15),
            faculty="Computer Science"
        )
        db.session.add(user)
        db.session.commit()

        retrieved_user = db.session.get(User, "user123")
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.faculty == "Computer Science"
        assert retrieved_user.group_memberships == []
        assert retrieved_user.tasks == []

    def test_create_group(self, app_context):
        """Test creating a Group object with valid data."""
        group = Group(
            name="Study Group Alpha",
            description="A group for testing.",
            group_number=101,
            invite_link="invite123"
        )
        db.session.add(group)
        db.session.commit()

        retrieved_group = db.session.get(Group, group.id)
        assert retrieved_group is not None
        assert retrieved_group.name == "Study Group Alpha"
        assert retrieved_group.group_number == 101
        assert retrieved_group.group_memberships == []
        assert retrieved_group.tasks == []

    def test_create_task(self, app_context):
        """Test creating a Task object and check default values."""
        task = Task(
            title="Implement Tests",
            deadline=date(2025, 12, 31),
            kind="Development",
            priority="high"
        )
        db.session.add(task)
        db.session.commit()

        retrieved_task = db.session.get(Task, task.id)
        assert retrieved_task is not None
        assert retrieved_task.title == "Implement Tests"
        assert retrieved_task.status == "todo"  # Test default value
        assert retrieved_task.progress == 0      # Test default value
        assert retrieved_task.user is None
        assert retrieved_task.group is None


class TestModelRelationships:
    """Tests for relationships between models."""

    def test_user_group_membership_relationship(self, app_context):
        """Test the many-to-many relationship between User and Group."""
        user = User(id="user-rel", username="rel_user", email="rel@test.com")
        group = Group(name="Related Group", group_number=202, invite_link="rel_link")
        db.session.add_all([user, group])
        db.session.commit()

        # Create the membership with a role
        membership = GroupMembership(user_id=user.id, group_id=group.id, role="admin")
        db.session.add(membership)
        db.session.commit()

        # Check relationship from the User's side
        assert len(user.group_memberships) == 1
        assert user.group_memberships[0].role == "admin"
        assert user.group_memberships[0].group == group

        # Check relationship from the Group's side
        assert len(group.group_memberships) == 1
        assert group.group_memberships[0].user == user

    def test_task_to_user_relationship(self, app_context):
        """Test the one-to-many relationship between User and Task."""
        user = User(id="user-task", username="task_user", email="task@user.com")
        task = Task(title="User's Task", deadline=date(2025, 1, 1), kind="chore", priority="low", user=user)
        db.session.add_all([user, task])
        db.session.commit()

        assert task.user == user
        assert len(user.tasks) == 1
        assert user.tasks[0].title == "User's Task"

    def test_task_to_group_relationship(self, app_context):
        """Test the one-to-many relationship between Group and Task."""
        group = Group(name="Task Group", group_number=303, invite_link="task_group_link")
        task = Task(title="Group's Task", deadline=date(2025, 1, 1), kind="project", priority="medium", group=group)
        db.session.add_all([group, task])
        db.session.commit()

        assert task.group == group
        assert len(group.tasks) == 1
        assert group.tasks[0].title == "Group's Task"

    def test_cascade_delete(self, app_context):
        """Test that deleting a user also deletes their memberships and tasks."""
        user = User(id="user-del", username="del_user", email="del@user.com")
        group = Group(name="Delete Group", group_number=404, invite_link="del_link")
        db.session.add_all([user, group])
        db.session.commit()

        membership = GroupMembership(user=user, group=group)
        task = Task(title="Task to be deleted", deadline=date(2025, 1, 1), kind="chore", priority="low", user=user)
        db.session.add_all([membership, task])
        db.session.commit()

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        assert db.session.get(User, "user-del") is None
        assert db.session.query(GroupMembership).count() == 0
        assert db.session.query(Task).filter_by(user_id="user-del").count() == 0