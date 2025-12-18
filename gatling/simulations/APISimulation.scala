import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class ApiSimulation extends Simulation {

  // 1. HTTP Protocol Configuration
  val httpProtocol = http
    .baseUrl("http://localhost:5000") // Base URL of the Flask API
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")

  // 2. Data Feeder
  // Generates unique users for each virtual user to avoid conflicts
  val userFeeder = Iterator.continually(Map(
    "username" -> ("loaduser_" + scala.util.Random.alphanumeric.take(8).mkString),
    "email" -> ("load_" + scala.util.Random.alphanumeric.take(5).mkString + "@test.com"),
    "password" -> "testpass123"
  ))

  // 3. Scenario Definition
  val scn = scenario("StudyConnect Load Test")
    .feed(userFeeder)
    // Step A: Register a new user
    .exec(http("Register User")
      .post("/api/users/register")
      .body(StringBody("""{
        "firstName": "Load",
        "lastName": "Tester",
        "username": "#{username}",
        "email": "#{email}",
        "password": "#{password}",
        "birthday": "2000-01-01",
        "faculty": "Engineering"
      }""")).asJson
      .check(status.is(201))
    )
    .pause(1) // Think time
    // Step B: Login to get Token
    .exec(http("Login")
      .post("/api/login")
      .body(StringBody("""{
        "username": "#{username}",
        "password": "#{password}"
      }""")).asJson
      .check(status.is(200))
      .check(jsonPath("$.access_token").saveAs("authToken"))
    )
    .pause(1)
    // Step C: Perform Authenticated Actions
    .repeat(3) { // Repeat a few times per user
      exec(http("Get Tasks")
        .get("/api/tasks")
        .header("Authorization", "Bearer #{authToken}")
        .check(status.is(200))
      )
      .pause(1)
      .exec(http("Create Task")
        .post("/api/tasks")
        .header("Authorization", "Bearer #{authToken}")
        .body(StringBody("""{
          "title": "Load Test Task",
          "deadline": "2025-12-31",
          "kind": "Homework",
          "priority": "medium"
        }""")).asJson
        .check(status.is(201))
      )
      .pause(2)
    }

  // 4. Load Simulation Profile
  // Choose one of the profiles below by uncommenting it

  // Profile A: Ramp-up Load (Spike/Stress Test)
  setUp(
    scn.inject(
      nothingFor(2.seconds),
      atOnceUsers(2),             // Start with 2 users immediately
      rampUsers(10).during(20.seconds) // Ramp up to 10 users over 20 seconds
    ).protocols(httpProtocol)
  )

  // Profile B: Constant Load (Stability Test)
  /*
  setUp(
    scn.inject(
      constantUsersPerSec(2).during(30.seconds) // 2 users per second for 30 seconds
    ).protocols(httpProtocol)
  )
  */
}