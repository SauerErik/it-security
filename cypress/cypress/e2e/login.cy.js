describe("Test basics", () => {
  beforeEach(() => {
    cy.visit("");
  });

  const usernameElement = "#root > div > form > input[type=text]:nth-child(2)";
  const passwordElement =
    "#root > div > form > input[type=password]:nth-child(4)";

  const loginButtonElement = "#root > div > form > button";

  it("Test visiting without login", () => {
    cy.url().then((url) => {
      expect(url).to.equal("http://localhost:8080/");
    });
  });

  it("Test login UI", () => {
    cy.get(usernameElement).should("be.visible");

    cy.get(passwordElement).should("be.visible");

    cy.get(loginButtonElement).should("be.visible");
  });

  it("Try login", () => {
    const testElement = "#root > div > h1";

    cy.get(testElement).should("not.exist");
    cy.login();
    cy.get(loginButtonElement).should("not.exist");

    cy.get(testElement).should("be.visible");
  });
});
