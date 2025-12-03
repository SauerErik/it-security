import unittest
from unittest.mock import MagicMock, patch

from backend.services import UserService, User
from test_backend.test_services import FakeUser


class TestUserService(unittest.TestCase):

    def setUp(self):
        """Runs before each test"""
   
        self.mock_db_session = MagicMock()
        self.mock_keycloak_admin = MagicMock()

     
        self.user_service = UserService(self.mock_db_session, self.mock_keycloak_admin)


    def test_register_user_success(self):
        """Tests successful registration of user"""
      
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "a_very_secure_password",
            "keycloak_payload": {"username": "testuser", "email": "test@example.com"}
        }
 
        self.mock_keycloak_admin.create_user.return_value = "fake-user-id-123"

   
        self.user_service.register_user(user_data)

 
        self.mock_keycloak_admin.create_user.assert_called_once_with(user_data['keycloak_payload'])
  
        self.mock_keycloak_admin.set_user_password.assert_called_once_with("fake-user-id-123", user_data['password'], temporary=False)
   
        self.mock_db_session.add.assert_called_once()
        self.mock_db_session.commit.assert_called_once()


    def test_register_user_fails_with_short_password(self):
        """Tests registration fails with password that is too short"""
       
        user_data = {"password": "123"}

     
        with self.assertRaises(ValueError) as context:
            self.user_service.register_user(user_data)

        self.assertIn("at least 8 characters long", str(context.exception))

        self.mock_keycloak_admin.create_user.assert_not_called()
        self.mock_db_session.add.assert_not_called()

    def test_register_user_keycloak_creation_fails(self):
        """Tests registration fails if Keycloak user creation fails."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "a_very_secure_password",
            "keycloak_payload": {"username": "testuser", "email": "test@example.com"}
        }
        # Simulate Keycloak error
        self.mock_keycloak_admin.create_user.side_effect = Exception("Keycloak error")

        with self.assertRaisesRegex(Exception, "Keycloak error"):
            self.user_service.register_user(user_data)

        self.mock_keycloak_admin.create_user.assert_called_once()
        self.mock_keycloak_admin.set_user_password.assert_not_called()
        self.mock_db_session.add.assert_not_called()
        self.mock_db_session.commit.assert_not_called()

    def test_register_user_db_creation_fails(self):
        """Tests registration fails if local DB user creation fails."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "a_very_secure_password",
            "birthday": "2000-01-01",
            "keycloak_payload": {"username": "testuser", "email": "test@example.com"}
        }
        self.mock_keycloak_admin.create_user.return_value = "fake-user-id-123"
        # Simulate DB error during add/commit
        self.mock_db_session.add.side_effect = Exception("DB error")

        with self.assertRaisesRegex(Exception, "DB error"):
            self.user_service.register_user(user_data)

        self.mock_keycloak_admin.create_user.assert_called_once()
        self.mock_keycloak_admin.set_user_password.assert_called_once()
        self.mock_db_session.add.assert_called_once()
        self.mock_db_session.commit.assert_not_called() # Commit should not be called if add fails

    def test_get_or_create_user_from_keycloak_missing_id(self):
        """Tests that an exception is raised if Keycloak user info has no 'sub' ID."""
        keycloak_userinfo = {"email": "test@example.com"}
        with self.assertRaisesRegex(Exception, r"Missing Keycloak user ID \(sub\)"):
            self.user_service.get_or_create_user_from_keycloak(keycloak_userinfo)
        self.mock_db_session.get.assert_not_called()
        self.mock_db_session.add.assert_not_called()
        self.mock_db_session.commit.assert_not_called()

    @patch('backend.api.keycloak_openid') 
    def test_login_success(self, mock_keycloak_openid):
        """Tests successful login"""
        # Configure the mock to return a fake token
        expected_token = {"access_token": "a-fake-token"}
        mock_keycloak_openid.token.return_value = expected_token

        # Call the method on the service
        token = self.user_service.login("testuser", "correct_password")

        # Check the result and the interaction with the mock
        self.assertEqual(token, expected_token)
        mock_keycloak_openid.token.assert_called_with("testuser", "correct_password")


    @patch('backend.api.keycloak_openid')
    def test_login_failure(self, mock_keycloak_openid):
        """Tests failed login"""
        from keycloak.exceptions import KeycloakAuthenticationError
        # Configure the mock to raise an exception on login
        mock_keycloak_openid.token.side_effect = KeycloakAuthenticationError("Invalid credentials")

        # Check that the service correctly propagates the exception
        with self.assertRaises(KeycloakAuthenticationError):
            self.user_service.login("testuser", "wrong_password")

    def test_get_or_create_user_from_keycloak_user_exists(self):
        """Tests that an existing user is returned and no new user is created."""
        keycloak_userinfo = {"sub": "kc-user-id", "preferred_username": "kcuser", "email": "kc@example.com"}
        existing_user = FakeUser(id="kc-user-id", username="kcuser", email="kc@example.com")
        self.mock_db_session.get.return_value = existing_user

        user = self.user_service.get_or_create_user_from_keycloak(keycloak_userinfo)

        self.assertEqual(user, existing_user)
        self.mock_db_session.get.assert_called_once_with(FakeUser, "kc-user-id")
        self.mock_db_session.add.assert_not_called()
        self.mock_db_session.commit.assert_not_called()

    def test_get_or_create_user_from_keycloak_new_user_created(self):
        """Tests that a new user is created in the local DB if they don't exist."""
        keycloak_userinfo = {"sub": "new-kc-user-id", "preferred_username": "newkcuser", "email": "newkc@example.com"}
        self.mock_db_session.get.return_value = None # User does not exist

        # Mock the User constructor. autospec=True is removed to avoid the application context error.
        with patch('backend.services.User') as MockUser:
            # Configure the instance that the constructor will return
            mock_instance = MockUser.return_value
            mock_instance.id = "new-kc-user-id"
            mock_instance.username = "newkcuser"
            mock_instance.email = "newkc@example.com"

            user = self.user_service.get_or_create_user_from_keycloak(keycloak_userinfo)

            MockUser.assert_called_once_with(id="new-kc-user-id", username="newkcuser", email="newkc@example.com")
            self.mock_db_session.add.assert_called_once_with(mock_instance)
            self.assertEqual(user, mock_instance)

if __name__ == '__main__':
    unittest.main()