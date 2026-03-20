import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);

    try {
      await register({ email, password });
      navigate("/login", {
        replace: true,
        state: { registered: true, email },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: 380,
          display: "grid",
          gap: 12,
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 24,
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          background: "#fff",
        }}
      >
        <h2 style={{ margin: 0 }}>Create account</h2>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Confirm password</span>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            style={{ padding: 8 }}
          />
        </label>

        {error && <div style={{ color: "#b00020", fontSize: 14 }}>{error}</div>}

        <button type="submit" disabled={submitting} style={{ padding: 10 }}>
          {submitting ? "Creating account..." : "Register"}
        </button>

        <div style={{ fontSize: 14 }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </form>
    </div>
  );
}