import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  AuthApiError,
  confirmContactVerification,
  confirmPasswordReset,
  getSession,
  login,
  logout,
  requestContactVerification,
  requestPasswordReset,
} from "../../lib/api/auth";
import AuthApplication from "./AuthApplication";

vi.mock("../../lib/api/auth", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../lib/api/auth")>(),
  confirmContactVerification: vi.fn(),
  confirmPasswordReset: vi.fn(),
  getSession: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  requestContactVerification: vi.fn(),
  requestPasswordReset: vi.fn(),
}));

const anonymousSession = {
  authenticated: false,
  csrf_token: "synthetic-csrf-token",
  transfer_eligible: false,
};

describe("AuthApplication", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(getSession).mockResolvedValue(anonymousSession);
    vi.mocked(login).mockResolvedValue({
      authenticated: true,
      customer_id: "cust_demo_001",
      csrf_token: "synthetic-session-csrf",
      transfer_eligible: false,
    });
    vi.mocked(logout).mockResolvedValue(undefined);
    vi.mocked(requestContactVerification).mockResolvedValue({
      message: "Local mock email is ready. Enter verification code 1234.",
      code_length: 4,
    });
    vi.mocked(confirmContactVerification).mockResolvedValue({ transfer_eligible: true });
    vi.mocked(requestPasswordReset).mockResolvedValue({ message: "If the account is eligible, a reset code has been sent." });
    vi.mocked(confirmPasswordReset).mockResolvedValue(undefined);
  });

  it("shows sign-in from the signed-out application entry", async () => {
    render(<AuthApplication />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    expect(getSession).toHaveBeenCalledOnce();
  });

  it("shows a generic cooldown message after the temporary sign-in limit", async () => {
    vi.mocked(login).mockRejectedValueOnce(
      new AuthApiError("Sign-in is temporarily unavailable. Try again later.", "LOGIN_TEMPORARILY_THROTTLED", 429),
    );
    const user = userEvent.setup();
    render(<AuthApplication />);
    await user.type(await screen.findByLabelText(/username/i), "customer-demo");
    await user.type(screen.getByLabelText(/^password$/i), "wrong synthetic password");
    await user.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/temporarily unavailable/i);
  });

  it("requires contact verification before showing transfers", async () => {
    vi.mocked(getSession)
      .mockResolvedValueOnce(anonymousSession)
      .mockResolvedValueOnce({
        authenticated: true,
        csrf_token: "synthetic-session-csrf",
        customer_id: "cust_demo_001",
        email_verified: true,
        mobile_verified: false,
        transfer_eligible: true,
      });
    const user = userEvent.setup();
    render(<AuthApplication />);
    await user.type(await screen.findByLabelText(/username/i), "customer-demo");
    await user.type(screen.getByLabelText(/^password$/i), "long synthetic passphrase");
    await user.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(await screen.findByRole("heading", { name: /verify a contact/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /send email code/i }));
    await user.type(await screen.findByLabelText(/4-digit verification code/i), "1234");
    await user.click(screen.getByRole("button", { name: /verify contact/i }));

    expect(await screen.findByRole("heading", { name: /accounts/i })).toBeInTheDocument();
    expect(requestContactVerification).toHaveBeenCalledWith("email");
    expect(confirmContactVerification).toHaveBeenCalledWith({ channel: "email", code: "1234" });
  });

  it("supports password recovery through a previously verified contact", async () => {
    const user = userEvent.setup();
    render(<AuthApplication />);
    await user.click(await screen.findByRole("button", { name: /forgot password/i }));
    await user.type(screen.getByLabelText(/username/i), "customer-demo");
    await user.click(screen.getByRole("button", { name: /send reset code/i }));
    await user.type(await screen.findByLabelText(/six-digit reset code/i), "654321");
    await user.type(screen.getByLabelText(/new password/i), "replacement synthetic passphrase");
    await user.click(screen.getByRole("button", { name: /reset password/i }));

    expect(confirmPasswordReset).toHaveBeenCalledWith({
      reset_code: "654321",
      new_password: "replacement synthetic passphrase",
    });
    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("signs out and returns to the signed-out entry screen", async () => {
    vi.mocked(getSession).mockResolvedValueOnce({
      authenticated: true,
      csrf_token: "session-csrf",
      customer_id: "cust_demo_001",
      display_name: "Synthetic Customer",
      email_verified: true,
      mobile_verified: false,
      transfer_eligible: true,
    });
    const user = userEvent.setup();
    render(<AuthApplication />);
    await user.click(await screen.findByRole("button", { name: /sign out/i }));

    expect(logout).toHaveBeenCalledOnce();
    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });
});