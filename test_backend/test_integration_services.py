import pytest
from unittest.mock import MagicMock
from flask import Flask
from backend.models import db, User, Group, GroupMembership
from backend.services import UserService, get_user_service, get_groups_for_user

@pytest.fixture
def app():
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
def mock_keycloak():
    return MagicMock()

@pytest.fixture
def user_service(app, mock_keycloak):
    return UserService(db.session, mock_keycloak)

def test_register_user_integration(app, user_service, mock_keycloak):
    mock_keycloak.create_user.return_value = "kc-user-123"
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "birthday": "2000-01-01",
        "faculty": "CS",
        "keycloak_payload": {}
    }
    
    user = user_service.register_user(user_data)
    
    assert user.id == "kc-user-123"
    assert user.username == "testuser"
    
    in_db = db.session.get(User, "kc-user-123")
    assert in_db is not None
    assert in_db.email == "test@example.com"

def test_register_user_password_validation(app, user_service):
    user_data = {
        "username": "shortpass",
        "email": "short@test.com",
        "password": "short", # Too short
        "birthday": "2000-01-01",
        "faculty": "CS",
        "keycloak_payload": {}
    }
    
    with pytest.raises(ValueError) as excinfo:
        user_service.register_user(user_data)
    assert "at least 8 characters" in str(excinfo.value)

def test_get_user_by_id_integration(app):
    user = User(id="u1", username="existing", email="ex@test.com")
    db.session.add(user)
    db.session.commit()
    
    fetched = get_user_service("u1")
    
    assert fetched.id == "u1"
    assert fetched.username == "existing"

def test_get_user_by_id_not_found(app):
    with pytest.raises(Exception) as excinfo:
        get_user_service("nonexistent")
    assert "does not exist" in str(excinfo.value)

def test_update_user_integration(app, user_service):
    user = User(id="u2", username="old_name", email="old@test.com")
    db.session.add(user)
    db.session.commit()
    
    update_data = {"username": "new_name", "faculty": "Engineering"}
    
    updated = user_service.update_user("u2", update_data)
    
    assert updated.username == "new_name"
    assert updated.faculty == "Engineering"
    
    db.session.expire_all()
    in_db = db.session.get(User, "u2")
    assert in_db.username == "new_name"
    assert in_db.faculty == "Engineering"

def test_update_user_not_found(app, user_service):
    with pytest.raises(Exception) as excinfo:
        user_service.update_user("missing_id", {"username": "new"})
    assert "not found" in str(excinfo.value)

def test_get_or_create_user_creates_new(app, user_service):
    kc_info = {"sub": "new-sub", "email": "new@test.com", "preferred_username": "newuser"}
    
    user = user_service.get_or_create_user_from_keycloak(kc_info)
    
    assert user.id == "new-sub"
    
    in_db = db.session.get(User, "new-sub")
    assert in_db is not None
    assert in_db.email == "new@test.com"

def test_get_or_create_user_returns_existing(app, user_service):
    user = User(id="existing-sub", username="exists", email="exists@test.com")
    db.session.add(user)
    db.session.commit()
    
    kc_info = {"sub": "existing-sub", "email": "ignore@test.com"}
    
    result = user_service.get_or_create_user_from_keycloak(kc_info)
    
    assert result.id == "existing-sub"
    assert result.email == "exists@test.com"

def test_get_groups_for_user_integration(app):
    user = User(id="u_groups", username="grouper", email="g@test.com")
    group = Group(name="Test Group", group_number=1, invite_link="link")
    db.session.add(user)
    db.session.add(group)
    db.session.commit()
    
    membership = GroupMembership(user_id=user.id, group_id=group.id, role="member")
    db.session.add(membership)
    db.session.commit()
    
    groups = get_groups_for_user(user.id)
    
    assert len(groups) == 1
    assert groups[0].name == "Test Group"
