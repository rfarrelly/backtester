import { apiFetch, setAccessToken, clearAccessToken } from "./client";
import type { LoginResponse } from "../../../src/types/api";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form.toString(),
    }
  );

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail ?? message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  const data = (await response.json()) as LoginResponse;
  setAccessToken(data.access_token);
  return data;
}

export function logout(): void {
  clearAccessToken();
}