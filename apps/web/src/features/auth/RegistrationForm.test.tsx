import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthApiError, registerCustomer } from "../../lib/api/auth";
import RegistrationForm from "./RegistrationForm";

vi.mock("../../lib/api/auth", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../lib/api/auth")>(),
  registerCustomer: vi.fn(),
}));

describe("RegistrationForm", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(registerCustomer).mockReset();
    vi.mocked(registerCustomer).mockResolvedValue({
      customer_id: "cust_demo_001",
      account_number: "XXXX3456",
      account_type: "SAVINGS",
      status: "ACTIVE",
      transfer_eligible: false,
    });
  });

  async function completeForm(user: ReturnType<typeof userEvent.setup>, suffix = "0000123456") {
    await user.type(screen.getByLabelText(/^Full name$/i), "Synthetic Customer");
    await user.type(screen.getByLabelText(/email/i), "customer@example.test");
    await user.type(screen.getByLabelText(/mobile/i), "+919876543210");
    await user.type(screen.getByLabelText(/username/i), "customer-demo");
    await user.type(screen.getByLabelText(/^password$/i), "long synthetic passphrase");
    await user.type(screen.getByLabelText(/10-digit account suffix/i), suffix);
  }

  it("registers the customer and displays only the masked account number", async () => {
    const user = userEvent.setup();
    render(<RegistrationForm />);
    await completeForm(user);
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(registerCustomer).toHaveBeenCalledWith({
      name: "Synthetic Customer",
      email: "customer@example.test",
      mobile_number: "+919876543210",
      username: "customer-demo",
      password: "long synthetic passphrase",
      account_number_suffix: "0000123456",
    });
    expect(await screen.findByText("XXXX3456")).toBeInTheDocument();
    expect(screen.queryByText("19910000123456")).not.toBeInTheDocument();
  });

  it("does not submit an account suffix that is not exactly 10 digits", async () => {
    const user = userEvent.setup();
    render(<RegistrationForm />);
    await completeForm(user, "123456789");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(registerCustomer).not.toHaveBeenCalled();
  });

  it("shows a safe server rejection without displaying submitted credentials", async () => {
    vi.mocked(registerCustomer).mockRejectedValueOnce(
      new AuthApiError(
        "One or more registration details are unavailable.",
        "REGISTRATION_CONFLICT",
        409,
      ),
    );
    const user = userEvent.setup();
    render(<RegistrationForm />);
    await completeForm(user);
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "One or more registration details are unavailable.",
    );
    expect(screen.queryByText("long synthetic passphrase")).not.toBeInTheDocument();
  });
});