const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    baseUrl: "http://localhost:8080",
  },
  env: {
    login_name: "cypress_user",
    login_password: "super-secret_cypress_password123",
  },
});
