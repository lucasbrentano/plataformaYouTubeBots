const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  username: string;
  role: string;
  created_at: string;
}

export interface UserCreate {
  username: string;
  password: string;
  role: "admin" | "user";
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string };
    throw new ApiError(body.detail ?? "Erro na requisição", res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const authApi = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  logout: (token: string) =>
    request<{ detail: string }>("/auth/logout", { method: "POST" }, token),

  listUsers: (token: string) => request<UserOut[]>("/users/", {}, token),

  createUser: (data: UserCreate, token: string) =>
    request<UserOut>("/users/", { method: "POST", body: JSON.stringify(data) }, token),

  deleteUser: (userId: string, token: string) =>
    request<void>(`/users/${userId}`, { method: "DELETE" }, token),
};
