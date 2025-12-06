# **Exercise 8.1 -- Linter Configuration (Python / Flake8)**

## *Static Code Analysis -- StudyConnect Project*

In this exercise, I configured and ran a static code analysis tool for
the Python component of the StudyConnect application. The goal is to
understand how linters help identify code quality issues, enforce style
guidelines, and support consistent development practices.

For the Python **notification-service**, I selected **Flake8**, a widely
used linter that checks compliance with PEP 8, detects unused imports,
prevents common coding mistakes, and enforces basic formatting rules.

------------------------------------------------------------------------

## **1. Installing Flake8**

Flake8 was installed inside the project's virtual environment:

``` bash
pip install flake8
```

To ensure consistent setup across environments, I added it to the
project's `requirements.txt`:

    flake8==7.3.0

This locks the linter version and guarantees reproducible results.

------------------------------------------------------------------------

## **2. Running Flake8**

To analyze the entire Python project, Flake8 can be executed from the
root directory of the `notification-service`:

``` bash
flake8 .
```

This recursively scans all `.py` files and prints the findings directly
in the console.\
Typical issues reported include:

-   style violations (e.g., missing blank lines)\
-   unused variables or imports\
-   overly long lines\
-   spacing and indentation issues\
-   potential logic mistakes

Flake8 output includes the file path, line number, error code, and short
description, for example:

    service/utils.py:12:5: F841 local variable 'result' is assigned but never used

------------------------------------------------------------------------

## **3. Generating a Flake8 Report File**

When a persistent record of all linter warnings is required---e.g., for
documentation, grading, or CI---it is possible to write the output to a
file:

``` bash
flake8 . --output-file flake8-report.txt
```

This creates **`flake8-report.txt`** in the project root containing all
issues found during the scan.

------------------------------------------------------------------------

## **4. Reflection**

Running Flake8 on the StudyConnect notification-service highlighted
several issues:

-   inconsistent formatting\
-   unused imports\
-   long lines exceeding recommended limits\
-   missing blank lines between functions\
-   occasional logical warnings

Fixing these issues improved readability, consistency, and overall code
quality.

### **Are linters useful?**

Yes. Linters like Flake8 offer several benefits:

-   enforce consistent coding standards\
-   catch mistakes early\
-   improve maintainability\
-   support teamwork by keeping code style uniform\
-   reduce the number of trivial issues during code reviews

Even though linters may initially produce many warnings, the resulting
improvements make them a valuable part of modern development workflows.

---

# **Exercise 8.2 -- Code Coverage Configuration (Python / pytest-cov)**

## *Code Coverage Analysis -- StudyConnect Project*

In this exercise, I configured a code coverage checker for the Python backend service. Code coverage is a metric that measures the percentage of code lines executed during automated testing. It is an essential tool for ensuring test thoroughness and maintaining code quality.

For the Python backend, I used **`pytest-cov`**, a plugin for the Pytest framework.

------------------------------------------------------------------------

## **1. Configuration Steps**

To integrate `pytest-cov`, two main configuration steps were performed:

### **a) Adding the Dependency**

First, the `pytest-cov` package was added as a dependency to the project's `requirements.txt` file. This ensures that the tool is installed alongside other project dependencies when setting up the environment.

File: `backend/requirements.txt`
```
...
pytest
behave
flake8==7.3.0
pytest-cov
```

After updating the file, the new dependency was installed using `pip`:
```bash
pip install -r requirements.txt
```

### **b) Creating the Configuration File**

Next, a configuration file named `.coveragerc` was created in the root of the `backend` directory. This file allows for fine-tuning the behavior of `pytest-cov`.

File: `backend/.coveragerc`
```ini
[run]
source = backend
omit = */venv/*, */tests/*, *test*.py

[report]
show_missing = True
fail_under = 80

[html]
directory = htmlcov
```

Key configurations include:
-   `source = backend`: Specifies that only code within the `backend` directory should be measured.
-   `omit = ...`: Excludes test files and virtual environments to avoid skewing the results.
-   `fail_under = 80`: Sets a quality gate. The test run will fail if the total coverage is below 80%.

------------------------------------------------------------------------

## **2. Running the Coverage Check**

To run the tests and generate a coverage report, I used the following command from the `studyconnect` directory:

```bash
pytest --cov
```

This command executes all tests and, upon completion, prints a coverage report to the console and generates a detailed HTML report in the `htmlcov/` directory.

### **a) Viewing the HTML Report**

In environments without a graphical user interface (like WSL or Docker), opening the HTML file directly can fail. A universal method to view the report is to start a temporary web server.

1.  **Navigate to the report directory:**
    From the project root, change into the `htmlcov` directory.
    ```bash
    cd htmlcov
    ```

2.  **Start a simple Python web server:**
    This command serves the files in the current directory.
    ```bash
    python3 -m http.server
    ```

3.  **Open the report in your browser:**
    On your main operating system (Windows, macOS), open a web browser and navigate to:
    ```
    http://localhost:8000
    ```
    This will display the interactive coverage report. To stop the server, return to the terminal and press `Ctrl + C`.

------------------------------------------------------------------------

## **3. Reflection on the Results**

After the initial run, the code coverage was below the 80% target. To meet the quality gate, we had to write several additional tests, particularly for the service and API layers. After these additions, the final run yielded a **total coverage of 89%**, which successfully meets the 80% target defined in the configuration.

-   **Strengths**: The core business logic in `services.py` and the data models in `models.py` are very well-tested. This is excellent, as these are critical components of the application.
-   **Weaknesses**: The API layer, defined in `api.py`, initially showed a very low coverage. This indicated that the HTTP endpoints themselves were not being sufficiently tested, as most existing tests were unit tests that called service functions directly, bypassing the API routes.

To improve this, we added several integration tests that simulate HTTP requests (e.g., using the Flask test client) for the endpoints in `api.py`.

------------------------------------------------------------------------

## **4. Reflection on the Code Coverage Metric**

### **What do I think about the code coverage metric?**

Code coverage is a highly valuable metric, but it must be interpreted with caution.

**Benefits:**
-   **It reveals untested code:** Its greatest strength is objectively identifying parts of the codebase that are not exercised by any tests. This provides a clear roadmap for where to add new tests.
-   **It serves as a quality gate:** By setting a minimum threshold (e.g., `fail_under = 80`), it prevents the introduction of untested code into the main branch, enforcing a baseline of quality in a CI/CD pipeline.

**Limitations:**
-   **It does not measure test quality:** 100% coverage does not guarantee that the code is bug-free. A test can execute a line of code without actually verifying its behavior (i.e., without meaningful assert statements).
-   **It can encourage bad practices:** If treated as the only goal, developers might write trivial tests just to increase the percentage, rather than writing tests that validate important functionality and edge cases.

**Conclusion:** Code coverage is an essential tool for maintaining and improving test suites. However, it should be used as a guide to find gaps, not as the ultimate measure of code quality. The focus should always remain on writing meaningful tests that verify the application's behavior correctly.
