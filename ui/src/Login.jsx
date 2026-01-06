import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // Assuming react-router-dom v6

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed");

      // Decode userId from JWT
      const userId = JSON.parse(atob(data.access_token.split(".")[1])).sub;

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", userId);
      onLogin(data.access_token, userId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Login to StudyConnect</h2>
      <form onSubmit={handleSubmit}>
        <label>Username:</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <label>Password:</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
      <p>
        Don't have an account?{" "}
        <button onClick={() => navigate("/register")} className="link-button">
          Register
        </button>
      </p>
    </div>
  );
}
