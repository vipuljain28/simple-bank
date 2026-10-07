export interface TransferRequest {
  request_id: string;
  verification_proof: string;
  from_account: string;
  to_account: string;
  amount: string;
}

export interface TransferResponse {
  transaction_id: string;
  request_id: string;
  from_account: string;
  to_account: string;
  amount: string;
  status: "ACCEPTED";
  created_at: string;
}

interface TransferErrorBody {
  error_code?: string;
  message?: string;
}

export class TransferApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "TransferApiError";
  }
}

export async function submitTransfer(payload: TransferRequest): Promise<TransferResponse> {
  const response = await fetch("/api/v1/transfers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = (await response.json()) as TransferResponse | TransferErrorBody;
  if (!response.ok) {
    const errorBody = body as TransferErrorBody;
    throw new TransferApiError(
      errorBody.message ?? "The transfer could not be completed.",
      errorBody.error_code ?? "TRANSFER_ERROR",
      response.status,
    );
  }
  return body as TransferResponse;
}