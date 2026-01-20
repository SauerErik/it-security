describe("Test basics", () => {
  beforeEach(() => {
    cy.visit("");
    cy.login();
  });

  const task = {
    title: "test Title",
    deadline: new Date().toISOString().split("T")[0],
    kind: "homework",
    priority: "medium",
  };

  const taskFail = {
    title: "",
    deadline: new Date("2000-01-01").toISOString().split("T")[0],
    kind: "homework",
    priority: "medium",
  };

  const newTaskElement =
    "#root > div > div.kanban-board > div:nth-child(1) > div > div > div";

  it("Create fail task", () => {
    cy.get(newTaskElement).should("not.exist");
    cy.createTask(taskFail, true);
    cy.get(
      "#root > div > div.modal-overlay > div > div > form > div.form-buttons.mt-4.flex.gap-2 > button.btn-cancel.flex-1",
    ).click();
    cy.get(newTaskElement).should("not.exist");
  });

  it("Create task", () => {
    cy.get(newTaskElement).should("not.exist");
    cy.createTask(task);
    cy.get(newTaskElement).should("be.visible");
  });

  it("Validate new task", () => {
    cy.get(newTaskElement).click();

    cy.get(
      "#root > div > div.modal-overlay > div > div:nth-child(2) > input",
    ).should("have.value", task.title);

    cy.get(
      "#root > div > div.modal-overlay > div > div:nth-child(3) > input",
    ).should("have.value", task.deadline);

    cy.get(
      "#root > div > div.modal-overlay > div > div:nth-child(4) > select",
    ).should("have.value", task.kind);

    cy.get(
      "#root > div > div.modal-overlay > div > div:nth-child(5) > select:nth-child(2)",
    ).should("have.value", task.priority);
  });
});
