import { FormEvent, useState } from "react";

import {
  submitTransfer,
  TransferApiError,
  TransferRequest,
  TransferResponse,
} from "../../lib/api/transfers";

type Outcome =
  | { kind: "idle" }
  | { kind: "pending" }
  | { kind: "accepted"; transfer: TransferResponse }
  | { kind: "rejected"; message: string }
  | { kind: "uncertain" };

function createRequestId(): string {
  return `req-${globalThis.crypto.randomUUID()}`;
}

function maskedPreview(accountNumber: string): string {
  return accountNumber ? `XXXX${accountNumber.slice(-4)}` : "XXXX----";
}

export default function TransferForm() {
  const [requestId, setRequestId] = useState(createRequestId);
  const [senderAccount, setSenderAccount] = useState("");
  const [recipientAccount, setRecipientAccount] = useState("");
  const [amount, setAmount] = useState("");
  const [verificationProof, setVerificationProof] = useState("");
  const [outcome, setOutcome] = useState<Outcome>({ kind: "idle" });
  const [retryRequest, setRetryRequest] = useState<TransferRequest | null>(null);
  const isLocked = outcome.kind === "pending" || outcome.kind === "uncertain";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = retryRequest ?? {
      request_id: requestId,
      verification_proof: verificationProof,
      from_account: senderAccount,
      to_account: recipientAccount,
      amount,
    };
    setRetryRequest(payload);
    setOutcome({ kind: "pending" });
    try {
      const transfer = await submitTransfer(payload);
      setRetryRequest(null);
      setOutcome({ kind: "accepted", transfer });
    } catch (error) {
      if (error instanceof TransferApiError && error.status < 500) {
        setRetryRequest(null);
        setOutcome({ kind: "rejected", message: error.message });
      } else {
        setOutcome({ kind: "uncertain" });
      }
    }
  }

  function startNewTransfer() {
    setRequestId(createRequestId());
    setOutcome({ kind: "idle" });
    setRetryRequest(null);
    setVerificationProof("");
  }

  return (
    <div className="transfer-layout">
      <form className="transfer-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <div className="section-heading">
            <span className="section-heading__index">01</span>
            <h2>Accounts</h2>
          </div>
          <div className="field-grid">
            <label className="field">
              <span>Sender account</span>
              <input aria-label="Sender account" autoComplete="off" disabled={isLocked} inputMode="numeric" onChange={(event) => setSenderAccount(event.target.value)} required type="password" value={senderAccount} />
              <output className="field__hint">{maskedPreview(senderAccount)}</output>
            </label>
            <label className="field">
              <span>Recipient account</span>
              <input aria-label="Recipient account" autoComplete="off" disabled={isLocked} inputMode="numeric" onChange={(event) => setRecipientAccount(event.target.value)} required type="password" value={recipientAccount} />
              <output className="field__hint">{maskedPreview(recipientAccount)}</output>
            </label>
          </div>
        </div>

        <div className="form-section">
          <div className="section-heading">
            <span className="section-heading__index">02</span>
            <h2>Amount</h2>
          </div>
          <label className="field field--amount">
            <span>Amount in Rs</span>
            <div className="amount-input">
              <span aria-hidden="true">Rs</span>
              <input aria-label="Amount" autoComplete="off" disabled={isLocked} inputMode="decimal" onChange={(event) => setAmount(event.target.value)} pattern="[0-9]+\.[0-9]{2}" placeholder="0.00" required type="text" value={amount} />
            </div>
            <span className="field__hint">Daily transfer limit: Rs 1,00,000</span>
          </label>
        </div>

        <div className="form-section">
          <div className="section-heading">
            <span className="section-heading__index">03</span>
            <h2>Verification</h2>
          </div>
          <div className="field-grid">
            <label className="field">
              <span>Request ID</span>
              <input aria-label="Request ID" disabled={isLocked} maxLength={128} onChange={(event) => setRequestId(event.target.value)} required value={requestId} />
            </label>
            <label className="field">
              <span>Verification proof</span>
              <input aria-label="Verification proof" autoComplete="off" disabled={isLocked} onChange={(event) => setVerificationProof(event.target.value)} required type="password" value={verificationProof} />
            </label>
          </div>
        </div>

        <div className="form-actions">
          <button className="primary-button" disabled={outcome.kind === "pending"} type="submit">
            {outcome.kind === "pending" ? "Processing..." : outcome.kind === "uncertain" ? "Retry same transfer" : "Send transfer"}
          </button>
          {outcome.kind === "uncertain" && <button className="text-button" onClick={startNewTransfer} type="button">Start a new transfer</button>}
        </div>

        <div aria-live="polite" className="outcome" role="status">
          {outcome.kind === "pending" && <p>Submitting transfer...</p>}
          {outcome.kind === "accepted" && <div className="outcome__accepted"><span className="outcome__label">Transfer accepted</span><p>Transaction ID <strong>{outcome.transfer.transaction_id}</strong></p></div>}
          {outcome.kind === "rejected" && <p className="outcome__error" role="alert">{outcome.message}</p>}
          {outcome.kind === "uncertain" && <p className="outcome__warning">We could not confirm the result. Retry this transfer with the same details.</p>}
        </div>
      </form>

      <aside className="transfer-aside" aria-label="Transfer details">
        <span className="aside-mark" aria-hidden="true">↗</span>
        <h2>Transfer details</h2>
        <dl>
          <div><dt>From</dt><dd>{maskedPreview(senderAccount)}</dd></div>
          <div><dt>To</dt><dd>{maskedPreview(recipientAccount)}</dd></div>
          <div><dt>Amount</dt><dd>{amount ? `Rs ${amount}` : "Rs --"}</dd></div>
        </dl>
        <p className="aside-note">Your transfer is confirmed only after both account balances and the transaction record are saved.</p>
      </aside>
    </div>
  );
}