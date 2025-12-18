import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class ApiSimulation extends Simulation {

  val httpProtocol = http
    .baseUrl("http://app:8000") // Docker service name
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")

  val login = exec(
    http("Login")
      .post("/auth/login")
      .body(RawFileBody("bodies/login.json")).asJson
      .check(status.is(200))
      .check(jsonPath("$.access_token").saveAs("token"))
  )

  val getUsers = exec(
    http("Get Users")
      .get("/users")
      .header("Authorization", "Bearer ${token}")
      .check(status.is(200))
  )

  val scn = scenario("API Load Test")
    .exec(login)
    .pause(1)
    .repeat(5) {
      exec(getUsers)
    }

  setUp(
    scn.inject(
      rampUsers(50).during(60.seconds)
    )
  ).protocols(httpProtocol)
}
