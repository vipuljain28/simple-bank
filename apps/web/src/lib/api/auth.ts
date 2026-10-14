export interface RegistrationRequest {
  name: string;
  email: string;
  mobile_number: string;
  username: string;
  password: string;
  account_number_suffix: string;
}

export interface RegistrationResponse {
  customer_id: string;
  account_number: string;
  account_type: "SAVINGS";
  status: "ACTIVE";
  transfer_eligible: boolean;
}

export interface AuthSession {
  authenticated: boolean;
  csrf_token: string;
  customer_id?: string;
  display_name?: string;
  email_verified?: boolean;
  mobile_verified?: boolean;
  transfer_eligible: boolean;
}

export interface LoginResponse {
  authenticated: true;
  customer_id: string;
  csrf_token: string;
  transfer_eligible: boolean;
}

interface AuthErrorBody {
  error_code?: string;
  message?: string;
}

export class AuthApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "AuthApiError";
  }
}

let csrfToken: string | null = null;

export function getCsrfHeaders(): Record<string, string> {
  return csrfToken ? { "X-CSRF-Token": csrfToken } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(`/api/v1/auth/${path}`, {
    ...init,
    credentials: "same-origin",
    headers,
  });
  if (response.status === 204) return undefined as T;
  const body = (await response.json()) as T | AuthErrorBody;
  if (!response.ok) {
    const error = body as AuthErrorBody;
    throw new AuthApiError(
      error.message ?? "The authentication request could not be completed.",
      error.error_code ?? "AUTH_ERROR",
      response.status,
    );
  }
  return body as T;
}

export async function registerCustomer(
  payload: RegistrationRequest,
): Promise<RegistrationResponse> {
  return request<RegistrationResponse>("register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSession(): Promise<AuthSession> {
  const session = await request<AuthSession>("session");
  csrfToken = session.csrf_token;
  return session;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const result = await request<LoginResponse>("login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  csrfToken = result.csrf_token;
  return result;
}

export async function logout(): Promise<void> {
  await request<void>("logout", { method: "POST" });
  csrfToken = null;
}

export async function requestContactVerification(
  channel: "email" | "mobile",
): Promise<{ message: string; code_length: 4 | 6 }> {
  return request("contact-verification", {
    method: "POST",
    body: JSON.stringify({ channel }),
  });
}

export async function confirmContactVerification(payload: {
  channel: "email" | "mobile";
  code: string;
}): Promise<{ transfer_eligible: boolean }> {
  return request("contact-verification/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function requestPasswordReset(payload: {
  username: string;
  channel: "email" | "mobile";
}): Promise<{ message: string }> {
  return request("password-reset/request", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function confirmPasswordReset(payload: {
  reset_code: string;
  new_password: string;
}): Promise<void> {
  await request<void>("password-reset/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  csrfToken = null;
}