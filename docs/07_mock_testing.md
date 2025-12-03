
# Exercise 6.1

This part of the document reviews the unit test implementations from lab 3. The decisions were made by using the different decision table technique. The feedback gained from using those was used to realize missing unit tests.

## 6.1.1. register user

| Password is valid | user creation is successful in keycloak | database user creation is successful | Result  |
|-------------------|-----------------------------------------|--------------------------------------|---------|
| N                 | -                                       | -                                    | Error   |
| Y                 | Y                                       | Y                                    | Success |
| Y                 | N                                       | -                                    | Error   |
| Y                 | Y                                       | N                                    | Error   |


## 6.1.2. get or create user

| user ID is present in Keycloak user info | User exists in DB | Result                         |
|------------------------------------------|-------------------|--------------------------------|
| N                                        | -                 | error                          |
| Y                                        | Y                 | success (user already existed) |
| Y                                        | N                 | success (new user created)     |

## 6.1.3. creating a task 

| Deadline is in the past     | duplicate task exists | Result      |
|-----------------------------|-----------------------|-------------|
| Y                           | -                     | error       |
| N                           | Y                     | no new task |
| N                           | N                     | new task    |


## 6.1.4. updating a task 

This function is complex due to several validation areas. Therefore several steps and design techniques are used.


### status transition validation

| status in data | status changing? | Transition valid? | past due date? | new status "in_progress"? | Result                         |
|----------------|------------------|-------------------|----------------|---------------------------|--------------------------------|
| Y              | N                | -                 | -              | -                         | success                        |
| Y              | Y                | Y                 | N              | -                         | success                        |
| Y              | Y                | N                 | -              | -                         | error (invalid transition)     |
| Y              | Y                | Y                 | Y              | Y                         | error (task start is past due) |


### field validation

For these fields, the equivalence partitioning analysis with boundary values (where) is considered more valuable than the decision table 

| parameter | equivalence class           | representative                        |
|-----------|-----------------------------|---------------------------------------|
| progress  | [0–100] -> valid            | 0, 1, 50, 100                         |
|           | ≤ 0 -> invalid              | 0,-1                                  |
|           | ≥ 100 -> invalid            | 101                                   |
|           | NaN -> invalid              | "abc"                                 |
|-----------|-----------------------------|---------------------------------------|
| priority  | allowed strings -> valid    | low, medium, high                     |
|           | incorrect strings -> invalid| "urgent", ""                          |
|           | invalid strings -> invalid  | "High", "MEDIUM"                      |
|           | incorrect type -> invalid   | null, true                            |
|-----------|-----------------------------|---------------------------------------|
| deadline  | future dates -> valid       | today, today + 1 day, today + 10 days |
|           | past dates -> invalid       | today - 1 day, today - 10 days        |
|-----------|-----------------------------|---------------------------------------|
| assignee  | ID of existing user         | "user-123"                            |
|           | ID not existing             | "user-999"                            |
|           | invalid ID format           | 123, "", null                         |

### permission validation

Here, the use case testing technique is used for group assignment testing

| Scenario Description (Use Case)                                           | User Role / Context                 | User Action                                                            | Expected Result                        |
|---------------------------------------------------------------------------|-------------------------------------|------------------------------------------------------------------------|----------------------------------------|
| A group member assigns a task to their own group                        | Alice is a member of group "Alpha".   | Alice edits a task and sets the `group_id` to the ID of "Alpha".       | success: task is assigned to the group |
| A user tries to assign a task to a group they are *not* a member of     | Bob is not a member of group "Alpha". | Bob edits a task and tries to set the `group_id` to the ID of "Alpha". | permission error                       |


## 6.1.5. leaving a group

The "leave group" feature was completely missing, therefore a user table was created to cover all test cases needed.
This table analyzes the logic for when a user leaves a group, especially the critical case involving the last administrator.

| User is member? | Role is admin? | Last admin in group? | Result           |
|-----------------|----------------|----------------------|------------------|
| Yes             | No             | -                    | member deleted   |
| Yes             | Yes            | No                   | member deleted   |
| Yes             | Yes            | Yes                  | group is deleted |
| No              | -              | -                    | exception        |

# 6.1.6. domain model unit tests

Following the feedback of lab 4, unit tests for domain models defined in[models.py](../backend/models.py) were added in the file [test_models.py](../test_backend/test_models.py).


# Exercise 6.2: Service Testing with Mocks

This document explains how the requirements for service testing were fulfilled by implementing a UserService and testing it in isolation using mocks.

## Goal

The main goal was to test the application's business logic (the "Service Layer") without relying on external systems like a real database or the Keycloak authentication server. This is achieved by creating "mock" (or fake) versions of these external systems during testing.

---

## Part 1: Implementing the UserService

To separate the business logic from the web layer (API routes), a UserService class was created. This class contains the core logic for user-related operations.

File:  ...backend/services.py

This class is initialized with its dependencies (the database session and the Keycloak client), which allows us to replace them with mocks during testing.

```python
# backend/services.py

class UserService:
    def __init__(self, db_session, keycloak_admin_client):
        self.db = db_session
        self.keycloak_admin = keycloak_admin_client
    
    def register_user(self, user_data):
        
```

The UserService fulfills the following requirements:

- User Registration: Implemented in the register_user method.
- Password Validation: A check if not password or len(password) < 8: is included in the register_user method.
- User Login/Rejection: This logic is handled by the /api/login route in backend/api.py, which calls the Keycloak client. The behavior is verified in the mock tests.
- User Role Assignment: The principle is demonstrated in the create_group_service function, where the group creator is automatically assigned the 'admin' role.

---

## Part 2: Creating the Mock Test Suite

A dedicated test suite was created to test the UserService in complete isolation.

File: .../test_backend/test_user_service_mock.py

This test suite follows the 5-step process required by the exercise for each scenario.

### Example: Testing Successful User Registration

The test test_register_user_success demonstrates the process perfectly:

1.  Set up mocks: In the setUp method, fake versions of the database and Keycloak client are created.
    ```python
    self.mock_db_session = MagicMock()
    self.mock_keycloak_admin = MagicMock()
    self.user_service = UserService(self.mock_db_session, self.mock_keycloak_admin)
    ```
2.  Configure mock behavior: We tell the fake Keycloak client what to return when a method is called.
    ```python
    self.mock_keycloak_admin.create_user.return_value = "fake-user-id-123"
    ```
3.  Execute the service method: We call the actual register_user method on our service instance.
    ```python
    self.user_service.register_user(user_data)
    ```
4.  Verify outcomes and interactions: We check if our service called the mock objects with the correct parameters. This proves our logic works as expected.
    ```python
    self.mock_keycloak_admin.create_user.assert_called_once_with(...)
    self.mock_db_session.add.assert_called_once()
    ```




    # Exercise 6.3

    To test our database we wrote tests for our UserService.
    We did not implement a separate UserRepository because we implemented all needed features directly in the service.

    A deleting user function was not implemented. Deleting a user could lead to problems: If we have an old task from a few months ago with 3 people, we would lose information if we delete the user or we would have problems with the database because of the foreign key violation in the task.

    The file can be found [here](../test_backend/test_integration_services.py)

# 6.4 REST API Controller

For Exercise 6.4 we implemented the required REST API endpoints that form the entry point of the StudyConnect backend. The implementation follows the scenarios listed in the task description from the exercise sheet (user registration, login, profile management, task management, error handling, and validation).

Instead of redefining all endpoints here, we reference the file **studyconnect_api_docs.md**, which is located in the same folder. This file contains the full API specification and documents every implemented endpoint, including:

- **User endpoints** (registration, login, retrieving and updating user profiles)
- **Task endpoints** (creating, updating, retrieving tasks)
- **Group endpoints** used in our application
- **Authentication requirements**
- **Expected request and response formats**
- **Error handling and validation rules**

All REST controllers were implemented according to the definitions in *studyconnect_api_docs.md*.  
This ensured that:

- each required route exists and behaves as documented,
- input validation follows the API specification,
- appropriate HTTP status codes are used,
- and the controllers correctly interact with the service layer from the previous exercises.

As stated in the task description, Exercise 6.4 does **not** require writing test cases.  
The goal was to implement the REST endpoints so they can be tested in the following week.
