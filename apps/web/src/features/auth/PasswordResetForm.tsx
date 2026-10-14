import { type FormEvent, useState } from "react";

import {
  AuthApiError,
  confirmPasswordReset,
  requestPasswordReset,
} from "../../lib/api/auth";

interface PasswordResetFormProps {
  onDone: () => void;
  onBack: () => void;
}

export default function PasswordResetForm({ onDone, onBack }: PasswordResetFormProps) {
  const [username, setUsername] = useState("");
  const [channel, setChannel] = useState<"email" | "mobile">("email");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [requested, setRequested] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleRequest() {
    setPending(true);
    setError("");
    try {
      const result = await requestPasswordReset({ username, channel });
      setMessage(result.message);
      setRequested(true);
    } catch (reason) {
      setError(reason instanceof AuthApiError ? reason.message : "The reset request could not be completed.");
    } finally {
      setPending(false);
    }
  }

  async function handleConfirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await confirmPasswordReset({ reset_code: code, new_password: newPassword });
      setNewPassword("");
      onDone();
    } catch (reason) {
      setError(reason instanceof AuthApiError ? reason.message : "The password could not be reset.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="auth-panel">
      <p className="eyebrow">ACCOUNT RECOVERY</p>
      <h1>Reset password</h1>
      {!requested ? (
        <div className="form-section">
          <label className="field">
            <span>Username</span>
            <input aria-label="Username" autoComplete="username" onChange={(event) => setUsername(event.target.value)} required value={username} />
          </label>
          <fieldset className="channel-choice">
            <legend>Verified contact</legend>
            <label><input checked={channel === "email"} name="reset-channel" onChange={() => setChannel("email")} type="radio" /> Email</label>
            <label><input checked={channel === "mobile"} name="reset-channel" onChange={() => setChannel("mobile")} type="radio" /> Mobile</label>
          </fieldset>
          <button className="primary-button" disabled={pending || !username} onClick={handleRequest} type="button">
            {pending ? "Sending..." : "Send reset code"}
          </button>
        </div>
      ) : (
        <form className="form-section" onSubmit={handleConfirm}>
          <p role="status">{message}</p>
          <label className="field">
            <span>Six-digit reset code</span>
            <input aria-label="Six-digit reset code" inputMode="numeric" maxLength={6} onChange={(event) => setCode(event.target.value)} pattern="[0-9]{6}" required value={code} />
          </label>
          <label className="field">
            <span>New password</span>
            <input aria-label="New password" autoComplete="new-password" minLength={12} maxLength={128} onChange={(event) => setNewPassword(event.target.value)} required type="password" value={newPassword} />
          </label>
          <button className="primary-button" disabled={pending} type="submit">
            {pending ? "Resetting..." : "Reset password"}
          </button>
        </form>
      )}
      <div aria-live="polite" className="outcome" role="status">
        {error && <p className="outcome__error" role="alert">{error}</p>}
      </div>
      <button className="text-button" onClick={onBack} type="button">Back to sign in</button>
    </section>
  );
}