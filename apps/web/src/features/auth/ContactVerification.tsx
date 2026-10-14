import { useState } from "react";

import {
  AuthApiError,
  confirmContactVerification,
  requestContactVerification,
} from "../../lib/api/auth";

interface ContactVerificationProps {
  onVerified: () => void;
  onSignOut: () => void;
}

export default function ContactVerification({ onVerified, onSignOut }: ContactVerificationProps) {
  const [channel, setChannel] = useState<"email" | "mobile">("email");
  const [code, setCode] = useState("");
  const [codeLength, setCodeLength] = useState<4 | 6>(6);
  const [codeRequested, setCodeRequested] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function sendCode() {
    setPending(true);
    setError("");
    try {
      const result = await requestContactVerification(channel);
      setMessage(result.message);
      setCodeLength(result.code_length);
      setCodeRequested(true);
    } catch (reason) {
      setError(reason instanceof AuthApiError ? reason.message : "Code delivery is unavailable.");
    } finally {
      setPending(false);
    }
  }

  async function verifyCode() {
    setPending(true);
    setError("");
    try {
      const result = await confirmContactVerification({ channel, code });
      if (result.transfer_eligible) onVerified();
    } catch (reason) {
      setError(reason instanceof AuthApiError ? reason.message : "The verification code could not be accepted.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="auth-panel">
      <p className="eyebrow">ACCOUNT SECURITY</p>
      <h1>Verify a contact</h1>
      <p>Verify either your email or mobile number before transferring.</p>
      {!codeRequested ? (
        <div className="form-section">
          <fieldset className="channel-choice">
            <legend>Choose a verification method</legend>
            <label><input checked={channel === "email"} name="channel" onChange={() => setChannel("email")} type="radio" /> Email</label>
            <label><input checked={channel === "mobile"} name="channel" onChange={() => setChannel("mobile")} type="radio" /> Mobile</label>
          </fieldset>
          <button className="primary-button" disabled={pending} onClick={sendCode} type="button">
            {pending ? "Sending..." : `Send ${channel} code`}
          </button>
        </div>
      ) : (
        <div className="form-section">
          <p role="status">{message}</p>
          <label className="field">
            <span>{codeLength}-digit verification code</span>
            <input aria-label={`${codeLength}-digit verification code`} inputMode="numeric" maxLength={codeLength} onChange={(event) => setCode(event.target.value)} pattern={`[0-9]{${codeLength}}`} required value={code} />
          </label>
          <button className="primary-button" disabled={pending || code.length !== codeLength} onClick={verifyCode} type="button">
            {pending ? "Verifying..." : "Verify contact"}
          </button>
        </div>
      )}
      <div aria-live="polite" className="outcome" role="status">
        {error && <p className="outcome__error" role="alert">{error}</p>}
      </div>
      <button className="text-button" onClick={onSignOut} type="button">Sign out</button>
    </section>
  );
}