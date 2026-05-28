const registerTab = document.getElementById("registerTab");
const loginTab = document.getElementById("loginTab");
const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");
const authMessage = document.getElementById("authMessage");
const authPanel = document.getElementById("authPanel");
const startSimulationBtn = document.getElementById("startSimulationBtn");
const progressBtn = document.getElementById("progressBtn");

function setMode(mode) {
  const isRegister = mode === "register";
  registerTab.classList.toggle("active", isRegister);
  loginTab.classList.toggle("active", !isRegister);
  registerForm.classList.toggle("hidden", !isRegister);
  loginForm.classList.toggle("hidden", isRegister);
  authMessage.textContent = "";
}

function saveSession(data) {
  localStorage.setItem("authToken", data.access_token);
  localStorage.setItem("authUser", JSON.stringify(data.user));
  window.location.href = "/dashboard";
}

async function submitAuth(endpoint, payload) {
  authMessage.textContent = "Procesando...";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "No se pudo completar el acceso";
    throw new Error(detail);
  }
  saveSession(data);
}

registerTab.addEventListener("click", () => setMode("register"));
loginTab.addEventListener("click", () => setMode("login"));

function focusAccess(mode) {
  setMode(mode);
  authPanel.scrollIntoView({ behavior: "smooth", block: "center" });
}

startSimulationBtn.addEventListener("click", () => focusAccess("register"));
progressBtn.addEventListener("click", () => {
  if (localStorage.getItem("authToken")) {
    window.location.href = "/dashboard";
    return;
  }
  focusAccess("login");
});

if (localStorage.getItem("authToken")) {
  window.location.href = "/dashboard";
}

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAuth("/auth/register", {
    name: document.getElementById("registerName").value.trim(),
    email: document.getElementById("registerEmail").value.trim(),
    password: document.getElementById("registerPassword").value,
  }).catch((error) => {
    authMessage.textContent = error.message;
  });
});

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAuth("/auth/login", {
    email: document.getElementById("loginEmail").value.trim(),
    password: document.getElementById("loginPassword").value,
  }).catch((error) => {
    authMessage.textContent = error.message;
  });
});
