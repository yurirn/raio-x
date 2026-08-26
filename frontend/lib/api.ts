const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export function getToken() {
  return typeof window === "undefined" ? null : window.localStorage.getItem("raiox_token");
}

export function setToken(token: string) {
  window.localStorage.setItem("raiox_token", token);
}

export function clearToken() {
  window.localStorage.removeItem("raiox_token");
}

function errorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => item?.msg).filter(Boolean).join(". ");
  }
  return fallback;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (response.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
  }
  if (!response.ok) {
    let payload: unknown;
    try { payload = await response.json(); } catch { payload = null; }
    throw new Error(errorMessage(payload, "Não foi possível concluir a solicitação."));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function download(path: string, filename: string) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!response.ok) throw new Error("Não foi possível gerar o arquivo.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
