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
