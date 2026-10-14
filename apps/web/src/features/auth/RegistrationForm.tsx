import { type FormEvent, useState } from "react";

import {
  AuthApiError,
  registerCustomer,
  type RegistrationRequest,
  type RegistrationResponse,
} from "../../lib/api/auth";

interface RegistrationFormProps {
  onSignIn?: () => void;
}

export default function RegistrationForm({ onSignIn }: RegistrationFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [suffix, setSuffix] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [createdAccount, setCreatedAccount] = useState<RegistrationResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    const payload: RegistrationRequest = {
      name,
      email,
      mobile_number: mobileNumber,
      username,
      password,
      account_number_suffix: suffix,
    };

    try {
      const response = await registerCustomer(payload);
      setCreatedAccount(response);
      setPassword("");
    } catch (reason) {
      setError(
        reason instanceof AuthApiError
          ? reason.message
          : "Registration could not be completed. Please try again.",
      );
    } finally {
      setPending(false);
    }
  }

  if (createdAccount) {
    return (
      <section className="registration-result" aria-live="polite">
        <p className="registration-result__label">Account created</p>
        <h2>Your savings account is ready</h2>
        <p>Account number <strong>{createdAccount.account_number}</strong></p>
        <p>Sign in separately to continue. Transfers become available after verifying either your email or mobile number.</p>
        {onSignIn && <button className="primary-button" onClick={onSignIn} type="button">Sign in</button>}
      </section>
    );
  }

  return (
    <form className="transfer-form registration-form" onSubmit={handleSubmit}>
      <div className="form-section">
        <div className="section-heading">
          <span className="section-heading__index">01</span>
          <h2>Your details</h2>
        </div>
        <div className="field-grid">
          <label className="field">
            <span>Full name</span>
            <input aria-label="Name" autoComplete="name" maxLength={200} onChange={(event) => setName(event.target.value)} required value={name} />
          </label>
          <label className="field">
            <span>Email</span>
            <input aria-label="Email" autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </label>
          <label className="field">
            <span>Mobile number</span>
            <input aria-label="Mobile number" autoComplete="tel" inputMode="tel" onChange={(event) => setMobileNumber(event.target.value)} placeholder="+91 98765 43210" required type="tel" value={mobileNumber} />
          </label>
        </div>
      </div>

      <div className="form-section">
        <div className="section-heading">
          <span className="section-heading__index">02</span>
          <h2>Sign-in details</h2>
        </div>
        <div className="field-grid">
          <label className="field">
            <span>Username</span>
            <input aria-label="Username" autoComplete="username" maxLength={128} onChange={(event) => setUsername(event.target.value)} required value={username} />
          </label>
          <label className="field">
            <span>Password</span>
            <input aria-label="Password" autoComplete="new-password" maxLength={128} minLength={12} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
        </div>
      </div>

      <div className="form-section">
        <div className="section-heading">
          <span className="section-heading__index">03</span>
          <h2>Account number</h2>
        </div>
        <label className="field field--amount">
          <span>Choose the final 10 digits</span>
          <div className="amount-input">
            <span aria-hidden="true">1991</span>
            <input
              aria-label="10-digit account suffix"
              autoComplete="off"
              inputMode="numeric"
              maxLength={10}
              minLength={10}
              onChange={(event) => setSuffix(event.target.value)}
              pattern="[0-9]{10}"
              placeholder="0000123456"
              required
              type="text"
              value={suffix}
            />
          </div>
          <span className="field__hint">Your account number will contain 1991 followed by the 10 digits you choose.</span>
        </label>
      </div>

      <div className="form-actions">
        <button className="primary-button" disabled={pending} type="submit">
          {pending ? "Creating account..." : "Create account"}
        </button>
      </div>
      <div aria-live="polite" className="outcome" role="status">
        {pending && <p>Creating your account...</p>}
        {error && <p className="outcome__error" role="alert">{error}</p>}
      </div>
    </form>
  );
}