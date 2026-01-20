# Cypress-Tests

## Setup

1. Start app and make sure the cypress user exists.
1. Make sure no task exist for cypress user.
1. Go into the cypress folder.
1. Install packages with `npm install`

## Start tests CLI/UI

To start tests in the consol only type `npx cypress run` while in the cypress folder.

For the UI mode type `npx cypress open`.

## Test output

Following setup and then running `npx cypress run` gave the following output:

```
npx cypress run

DevTools listening on ws://127.0.0.1:46236/devtools/browser/a3712081-be28-44f4-99d2-a8838f3ba4e8

====================================================================================================

  (Run Starting)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Cypress:        15.9.0                                                                         │
  │ Browser:        Electron 138 (headless)                                                        │
  │ Node Version:   v20.19.1 (/usr/bin/node)                                                       │
  │ Specs:          2 found (createTask.cy.js, login.cy.js)                                        │
  │ Searched:       cypress/e2e/**/*.cy.{js,jsx,ts,tsx}                                            │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  createTask.cy.js                                                                (1 of 2)


  Test basics
    ✓ Create fail task (2075ms)
    ✓ Create task (2094ms)
    ✓ Validate new task (1254ms)


  3 passing (6s)


  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        3                                                                                │
  │ Passing:      3                                                                                │
  │ Failing:      0                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  0                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     5 seconds                                                                        │
  │ Spec Ran:     createTask.cy.js                                                                 │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  login.cy.js                                                                     (2 of 2)


  Test basics
    ✓ Test visiting without login (165ms)
    ✓ Test login UI (98ms)
    ✓ Try login (1240ms)


  3 passing (2s)


  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        3                                                                                │
  │ Passing:      3                                                                                │
  │ Failing:      0                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  0                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     1 second                                                                         │
  │ Spec Ran:     login.cy.js                                                                      │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


====================================================================================================

  (Run Finished)


       Spec                                              Tests  Passing  Failing  Pending  Skipped  
  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ ✔  createTask.cy.js                         00:05        3        3        -        -        - │
  ├────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ ✔  login.cy.js                              00:01        3        3        -        -        - │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
    ✔  All specs passed!                        00:07        6        6        -        -        -  
```

As we can see all test ran successfully.

But if we run them again before cleaning up the existing task we will get errors:

```
DevTools listening on ws://127.0.0.1:45180/devtools/browser/5630715b-4e50-49fd-9451-680d9060921e

====================================================================================================

  (Run Starting)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Cypress:        15.9.0                                                                         │
  │ Browser:        Electron 138 (headless)                                                        │
  │ Node Version:   v20.19.1 (/usr/bin/node)                                                       │
  │ Specs:          2 found (createTask.cy.js, login.cy.js)                                        │
  │ Searched:       cypress/e2e/**/*.cy.{js,jsx,ts,tsx}                                            │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  createTask.cy.js                                                                (1 of 2)


  Test basics
    1) Create fail task
    2) Create task
    ✓ Validate new task (1243ms)


  1 passing (12s)
  2 failing

  1) Test basics
       Create fail task:
     AssertionError: Timed out retrying after 4000ms: Expected <div.task-card.> not to exist in the DOM, but it was continuously found.
      at Context.eval (webpack:///./cypress/e2e/createTask.cy.js:25:27)

  2) Test basics
       Create task:
     AssertionError: Timed out retrying after 4000ms: Expected <div.task-card.> not to exist in the DOM, but it was continuously found.
      at Context.eval (webpack:///./cypress/e2e/createTask.cy.js:34:27)




  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        3                                                                                │
  │ Passing:      1                                                                                │
  │ Failing:      2                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  2                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     12 seconds                                                                       │
  │ Spec Ran:     createTask.cy.js                                                                 │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


  (Screenshots)

  -  /home/luka/studyconnect/cypress/cypress/screenshots/createTask.cy.js/Test basics     (1280x720)
      -- Create fail task (failed).png                                                              
  -  /home/luka/studyconnect/cypress/cypress/screenshots/createTask.cy.js/Test basics     (1280x720)
      -- Create task (failed).png                                                                   


────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                                                    
  Running:  login.cy.js                                                                     (2 of 2)


  Test basics
    ✓ Test visiting without login (165ms)
    ✓ Test login UI (94ms)
    ✓ Try login (1204ms)


  3 passing (2s)


  (Results)

  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Tests:        3                                                                                │
  │ Passing:      3                                                                                │
  │ Failing:      0                                                                                │
  │ Pending:      0                                                                                │
  │ Skipped:      0                                                                                │
  │ Screenshots:  0                                                                                │
  │ Video:        false                                                                            │
  │ Duration:     1 second                                                                         │
  │ Spec Ran:     login.cy.js                                                                      │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘


====================================================================================================

  (Run Finished)


       Spec                                              Tests  Passing  Failing  Pending  Skipped  
  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ ✖  createTask.cy.js                         00:12        3        1        2        -        - │
  ├────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ ✔  login.cy.js                              00:01        3        3        -        -        - │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
    ✖  1 of 2 failed (50%)                      00:13        6        4        2        -        -  
```

We do not have the option to delete task in the UI. We could add this functionality and update to test to delete the task after completion.
