import { useEffect, useState } from "react";

import { getSession, logout, type AuthSession, type LoginResponse } from "../../lib/api/auth";
import TransferForm from "../transfers/TransferForm";
import ContactVerification from "./ContactVerification";
import PasswordResetForm from "./PasswordResetForm";
import RegistrationForm from "./RegistrationForm";
import SignInForm from "./SignInForm";

type View = "sign-in" | "register" | "reset-password";

export default function AuthApplication() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [view, setView] = useState<View>("sign-in");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let active = true;
    getSession()
      .then((current) => {
        if (active) setSession(current);
      })
      .catch(() => {
        if (active) setLoadError("Sign-in is currently unavailable.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleSignOut() {
    try {
      await logout();
    } finally {
      setSession({ authenticated: false, csrf_token: "", transfer_eligible: false });
      setView("sign-in");
    }
  }

  function handleSignIn(result: LoginResponse) {
    setSession({ ...result });
    setView("sign-in");
  }

  async function handleContactVerified() {
    const current = await getSession();
    setSession(current);
  }

  return (
    <>
      <header className="bank-header">
        <a className="bank-mark" href="/" aria-label="Simple Bank home">
          <span className="bank-mark__symbol" aria-hidden="true">S</span>
          <span>Simple Bank</span>
        </a>
        <span className="bank-header__section">Customer access</span>
      </header>
      <main className="page-shell">
        <div className="page-heading">
          <p className="eyebrow">SIMPLE BANK <span> / </span> SECURE ACCESS</p>
          <h1>{session?.authenticated ? "Your account" : "Welcome"}</h1>
        </div>
        {loading ? (
          <p role="status">Checking your session...</p>
        ) : loadError ? (
          <p className="outcome__error" role="alert">{loadError}</p>
        ) : session?.authenticated ? (
          session.transfer_eligible ? (
            <div className="authenticated-shell">
              <div className="account-toolbar">
                <span>Signed in{session.display_name ? ` as ${session.display_name}` : ""}</span>
                <button className="text-button" onClick={handleSignOut} type="button">Sign out</button>
              </div>
              <TransferForm
                onContactVerificationRequired={() =>
                  setSession({ ...session, transfer_eligible: false })
                }
                onUnauthenticated={() =>
                  setSession({ authenticated: false, csrf_token: "", transfer_eligible: false })
                }
              />
            </div>
          ) : (
            <ContactVerification onSignOut={handleSignOut} onVerified={handleContactVerified} />
          )
        ) : view === "register" ? (
          <RegistrationForm onSignIn={() => setView("sign-in")} />
        ) : view === "reset-password" ? (
          <PasswordResetForm onBack={() => setView("sign-in")} onDone={() => setView("sign-in")} />
        ) : (
          <SignInForm
            onForgotPassword={() => setView("reset-password")}
            onRegister={() => setView("register")}
            onSignedIn={handleSignIn}
          />
        )}
      </main>
    </>
  );
}