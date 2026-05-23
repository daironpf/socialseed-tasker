export function login() {
  window.location.href = (window.__TASKER_API_URL || "http://localhost:8000") + "/auth/login";
}

export function logout() {
  fetch((window.__TASKER_API_URL || "http://localhost:8000") + "/auth/logout", { method: "POST", credentials: "include" })
    .then(() => {
      window.location.reload();
    });
}

export async function whoami() {
  const r = await fetch((window.__TASKER_API_URL || "http://localhost:8000") + "/api/v1/whoami", { credentials: "include" });
  if (r.ok) {
    return r.json();
  }
  return null;
}
