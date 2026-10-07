import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  submitTransfer,
  TransferApiError,
  type TransferResponse,
} from "../../lib/api/transfers";
import TransferForm from "./TransferForm";

vi.mock("../../lib/api/transfers", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../lib/api/transfers")>(),
  submitTransfer: vi.fn(),
}));

const acceptedResponse: TransferResponse = {
  transaction_id: "txn_demo_001",
  request_id: "req_demo_001",
  from_account: "XXXX1001",
  to_account: "XXXX2002",
  amount: "25.00",
  status: "ACCEPTED",
  created_at: "2026-10-06T10:00:00+05:30",
};

async function fillTransfer(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/sender account/i), "000000001001");
  await user.type(screen.getByLabelText(/recipient account/i), "000000002002");
  await user.type(screen.getByLabelText(/amount/i), "25.00");
  await user.type(screen.getByLabelText(/verification proof/i), "synthetic-verification-proof");
}

describe("TransferForm response states", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(submitTransfer).mockReset();
  });

  it("shows a pending state until the server responds", async () => {
    let resolveTransfer!: (transfer: TransferResponse) => void;
    vi.mocked(submitTransfer).mockReturnValue(
      new Promise((resolve) => {
        resolveTransfer = resolve;
      }),
    );
    const user = userEvent.setup();
    render(<TransferForm />);
    await fillTransfer(user);
    await user.click(screen.getByRole("button", { name: /send transfer/i }));

    expect(screen.getByText("Submitting transfer...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /processing/i })).toBeDisabled();
    resolveTransfer(acceptedResponse);
    expect(await screen.findByText("txn_demo_001")).toBeInTheDocument();
  });

  it("shows the safe rejection message returned by the API", async () => {
    vi.mocked(submitTransfer).mockRejectedValue(
      new TransferApiError("The sender account does not have enough available balance.", "INSUFFICIENT_BALANCE", 422),
    );
    const user = userEvent.setup();
    render(<TransferForm />);
    await fillTransfer(user);
    await user.click(screen.getByRole("button", { name: /send transfer/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The sender account does not have enough available balance.",
    );
  });

  it("retries an uncertain result with the identical request ID and details", async () => {
    vi.mocked(submitTransfer)
      .mockRejectedValueOnce(new TypeError("network connection lost"))
      .mockResolvedValueOnce(acceptedResponse);
    const user = userEvent.setup();
    render(<TransferForm />);
    await fillTransfer(user);
    await user.click(screen.getByRole("button", { name: /send transfer/i }));
    expect(await screen.findByText(/could not confirm the result/i)).toBeInTheDocument();
    const originalRequest = vi.mocked(submitTransfer).mock.calls[0][0];

    await user.click(screen.getByRole("button", { name: /retry same transfer/i }));

    expect(vi.mocked(submitTransfer).mock.calls[1][0]).toEqual(originalRequest);
    expect(await screen.findByText("txn_demo_001")).toBeInTheDocument();
  });
});