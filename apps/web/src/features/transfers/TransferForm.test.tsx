import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { submitTransfer, TransferApiError } from "../../lib/api/transfers";
import TransferForm from "./TransferForm";

vi.mock("../../lib/api/transfers", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../lib/api/transfers")>(),
  submitTransfer: vi.fn(),
}));

describe("TransferForm", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(submitTransfer).mockResolvedValue({
      transaction_id: "txn_demo_001",
      request_id: "req_demo_001",
      from_account: "XXXX1001",
      to_account: "XXXX2002",
      amount: "25.00",
      status: "ACCEPTED",
      created_at: "2026-10-06T10:00:00+05:30",
    });
  });

  it("submits the transfer and displays its accepted transaction ID", async () => {
    const user = userEvent.setup();
    render(<TransferForm />);
    await user.type(screen.getByLabelText(/sender account/i), "000000001001");
    await user.type(screen.getByLabelText(/recipient account/i), "000000002002");
    await user.type(screen.getByLabelText(/amount/i), "25.00");
    await user.clear(screen.getByLabelText(/request id/i));
    await user.type(screen.getByLabelText(/request id/i), "req_demo_001");
    await user.type(screen.getByLabelText(/verification proof/i), "synthetic-verification-proof");
    await user.click(screen.getByRole("button", { name: /send transfer/i }));

    expect(submitTransfer).toHaveBeenCalledWith({
      request_id: "req_demo_001",
      verification_proof: "synthetic-verification-proof",
      from_account: "000000001001",
      to_account: "000000002002",
      amount: "25.00",
    });
    expect(await screen.findByText("txn_demo_001")).toBeInTheDocument();
  });

  it("returns an expired session to the sign-in flow", async () => {
    const onUnauthenticated = vi.fn();
    vi.mocked(submitTransfer).mockRejectedValueOnce(
      new TransferApiError("Authentication is required.", "UNAUTHENTICATED", 401),
    );
    const user = userEvent.setup();
    render(<TransferForm onUnauthenticated={onUnauthenticated} />);
    await user.type(screen.getByLabelText(/sender account/i), "000000001001");
    await user.type(screen.getByLabelText(/recipient account/i), "000000002002");
    await user.type(screen.getByLabelText(/amount/i), "25.00");
    await user.type(screen.getByLabelText(/verification proof/i), "synthetic-verification-proof");
    await user.click(screen.getByRole("button", { name: /send transfer/i }));

    expect(onUnauthenticated).toHaveBeenCalledOnce();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});