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
