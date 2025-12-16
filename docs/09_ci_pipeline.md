# Exercise 9: CI pipeline

## Exercise 9.1: CI setup

A GitHub Actions [workflow file](../.github/workflows/ci.yaml) was created to automate the test and build processes.

### Configuration and Decisions
For the basic pipeline configuration, we decided to trigger the workflow on every push to any branch. This ensures that developers receive immediate feedback on their changes. Additionally, pull requests targeting the main branch trigger the pipeline, acting as a quality gate before merges. We selected ubuntu-latest as the runner because it is the standard environment such CI tasks, and supports docker natively.

### Workflow Steps

The pipeline is divided into three main jobs. The backend test job begins by checking out the code using the standard checkout action. It then starts the necessary services, Keycloak and PostgreSQL, via Docker Compose, as the backend tests require real database and authentication services. After setting up Python 3.11 with pip caching enabled, the job installs the dependencies listed in requirements.txt and executes the tests using pytest.

Simultaneously, the frontend build job sets up Node.js 20, installs dependencies using npm ci, and verifies the build process. Finally, an integration check confirms that the entire stack can be successfully built as Docker containers.

Finally, a Pipeline badge was added to the top level Readme.md.

## Exercise 9.2: More GitHub Actions
After exploring the workflow integrations mentioned in the task and with the setup already present in our project, it was decided to expand the CI on Security & Dependency Management. This acts as a final "Quality Gate" that cannot be bypassed. Therefore, security audits are integrated for both parts of the application stack:
- *backend*: integrated pip-audit to scan the python environment for known vulnerabilities in dependencies from our requirements.txt
- *frontend*: added npm audit to detect security issues within node_modules

This adds another layer to the following measures:

- *caching*: dependencies caching was already implemented as part of the initial CI setup. This ensures that the workflows remain efficient and build times are kept to a minimum by reusing downloaded packages between runs.
- *linting*: since flake8 was already added via the pre-commit hook, and due to implementing a broader range of tools, it was decided not to add flake8 to the GitHub Action. Style was considered as a less important factor than security, therefore it can remain in the local scope.

And since code quality is handled locally, the CI expansion is thus focused on security management.
