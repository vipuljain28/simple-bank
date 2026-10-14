import { type FormEvent, useState } from "react";

import { AuthApiError, login, type LoginResponse } from "../../lib/api/auth";

interface SignInFormProps {
  onSignedIn: (session: LoginResponse) => void;
  onRegister: () => void;
  onForgotPassword: () => void;
}

export default function SignInForm({ onSignedIn, onRegister, onForgotPassword }: SignInFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const session = await login(username, password);
      setPassword("");
      onSignedIn(session);
    } catch (reason) {
      setError(
        reason instanceof AuthApiError
          ? reason.message
          : "The sign-in details could not be verified.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="auth-panel">
      <p className="eyebrow">CUSTOMER ACCESS</p>
      <h1>Sign in</h1>
      <form className="transfer-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <label className="field">
            <span>Username</span>
            <input aria-label="Username" autoComplete="username" onChange={(event) => setUsername(event.target.value)} required value={username} />
          </label>
          <label className="field">
            <span>Password</span>
            <input aria-label="Password" autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
        </div>
        <div className="form-actions">
          <button className="primary-button" disabled={pending} type="submit">
            {pending ? "Signing in..." : "Sign in"}
          </button>
          <button className="text-button" onClick={onForgotPassword} type="button">Forgot password</button>
          <button className="text-button" onClick={onRegister} type="button">Create account</button>
        </div>
        <div aria-live="polite" className="outcome" role="status">
          {error && <p className="outcome__error" role="alert">{error}</p>}
        </div>
      </form>
    </section>
  );
}