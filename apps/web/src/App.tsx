import TransferForm from "./features/transfers/TransferForm";

export default function App() {
  return (
    <>
      <header className="bank-header">
        <a className="bank-mark" href="/" aria-label="Simple Bank home">
          <span className="bank-mark__symbol" aria-hidden="true">S</span>
          <span>Simple Bank</span>
        </a>
        <span className="bank-header__section">Payments</span>
      </header>
      <main className="page-shell">
        <div className="page-heading">
          <p className="eyebrow">ACCOUNT SERVICES <span> / </span> TRANSFERS</p>
          <h1>Move money</h1>
        </div>
        <TransferForm />
      </main>
    </>
  );
}