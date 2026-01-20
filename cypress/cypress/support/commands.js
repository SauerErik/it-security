// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add("login", () => {
  const usernameElement = "#root > div > form > input[type=text]:nth-child(2)";
  const passwordElement =
    "#root > div > form > input[type=password]:nth-child(4)";

  const loginButtonElement = "#root > div > form > button";

  cy.get(usernameElement).type(Cypress.env("login_name"));
  cy.get(passwordElement).type(Cypress.env("login_password"));
  cy.get(loginButtonElement).click();
  cy.wait(250);
});

Cypress.Commands.add("createTask", (task, shouldBeDisabled = false) => {
  const taskTitleElement =
    "#root > div > div.modal-overlay > div > div > form > div:nth-child(1) > input";
  const taskDeadlineElement =
    "#root > div > div.modal-overlay > div > div > form > div:nth-child(2) > input";
  const taskKindElement =
    "#root > div > div.modal-overlay > div > div > form > div:nth-child(3) > select";
  const taskPrioElement =
    "#root > div > div.modal-overlay > div > div > form > div:nth-child(4) > select";

  cy.get("#root > div > div.button-container > button:nth-child(1)").click();

  if (task.title) cy.get(taskTitleElement).type(task.title);

  if (task.deadline) cy.get(taskDeadlineElement).type(task.deadline);

  if (task.kind) cy.get(taskKindElement).select(task.kind);

  if (task.priority) cy.get(taskPrioElement).select(task.priority);

  if (shouldBeDisabled) {
    cy.get(
      "#root > div > div.modal-overlay > div > div > form > div.form-buttons.mt-4.flex.gap-2 > button.btn-primary.flex-1",
    ).should("be.disabled");
  } else {
    cy.get(
      "#root > div > div.modal-overlay > div > div > form > div.form-buttons.mt-4.flex.gap-2 > button.btn-primary.flex-1",
    ).click();
  }
});
