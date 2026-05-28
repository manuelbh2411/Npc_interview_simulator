const token = localStorage.getItem("authToken");
const user = JSON.parse(localStorage.getItem("authUser") || "null");

if (!token) {
  window.location.href = "/";
}

const welcomeText = document.getElementById("welcomeText");
const historyList = document.getElementById("historyList");
const historyCount = document.getElementById("historyCount");
const reportTitle = document.getElementById("reportTitle");
const reportMeta = document.getElementById("reportMeta");
const reportContent = document.getElementById("reportContent");
const logoutBtn = document.getElementById("logoutBtn");
const playerName = document.getElementById("playerName");
const playerRank = document.getElementById("playerRank");
const playerLevel = document.getElementById("playerLevel");
const totalXp = document.getElementById("totalXp");
const xpToNext = document.getElementById("xpToNext");
const xpFill = document.getElementById("xpFill");
const completedCount = document.getElementById("completedCount");
const averageScore = document.getElementById("averageScore");
const bestScore = document.getElementById("bestScore");
const achievementList = document.getElementById("achievementList");
const leaderboardList = document.getElementById("leaderboardList");
const avatarUnlockList = document.getElementById("avatarUnlockList");
const playerAvatar = document.querySelector(".player-avatar span");
const avatarStorageKey = `profileAvatar:${user?.id || user?.email || "local"}`;

const personalityXp = {
  Amable: 80,
  RRHH: 100,
  "Startup informal": 115,
  Técnico: 135,
  Agresivo: 155,
};

function authHeaders() {
  return { Authorization: `Bearer ${token}` };
}

function formatDuration(seconds) {
  if (!seconds) {
    return "Sin duracion";
  }
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes > 0 ? `${minutes}m ${rest}s` : `${rest}s`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function statusLabel(status) {
  const labels = {
    completed: "Completada",
    in_progress: "En curso",
    cancelled: "Cancelada",
    failed: "Fallida",
  };
  return labels[status] || status;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (response.status === 401) {
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");
    window.location.href = "/";
    return null;
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "No se pudo cargar la informacion");
  }
  return data;
}

function renderEmptyHistory() {
  historyList.innerHTML = `
    <div class="empty-state">
      <strong>Aun no hay entrevistas guardadas.</strong>
      <span>Inicia una nueva entrevista y genera el informe para verla aqui.</span>
    </div>
  `;
}

function renderHistory(interviews) {
  historyCount.textContent = interviews.length;
  if (!interviews.length) {
    renderEmptyHistory();
    return;
  }

  historyList.innerHTML = "";
  for (const interview of interviews) {
    const item = document.createElement("button");
    item.className = "history-item";
    item.type = "button";
    item.innerHTML = `
      <span>
        <em>${missionName(interview.job_type)}</em>
        <strong>${interview.title}</strong>
        <small>${interview.job_type} · ${interview.personality}</small>
      </span>
      <span class="history-metrics">
        <small>${formatDate(interview.date)}</small>
        <small>${formatDuration(interview.duration_seconds)} · ${interview.message_count} mensajes</small>
        <b>${interview.has_report ? `${interview.overall_score}/10` : statusLabel(interview.status)}</b>
      </span>
    `;
    item.addEventListener("click", () => showInterview(interview));
    historyList.appendChild(item);
  }
}

function missionName(job) {
  const names = {
    Ingeniería: "Desafio tecnico",
    ADE: "Gestion y estrategia",
    Empresa: "Gestion y estrategia",
    Derecho: "Argumentacion juridica",
    Magisterio: "Comunicacion pedagogica",
    Marketing: "Creatividad y persuasion",
  };
  return names[job] || "Simulacion";
}

function renderReport(report, personality) {
  const rank = rankForScore(report.overall_score);
  reportContent.className = "report-content";
  reportContent.innerHTML = `
    <div class="score-row">
      <div class="score-ring">${report.overall_score}<small>/10</small></div>
      <div>
        <p class="badge">Rango obtenido</p>
        <h3>${rank}</h3>
        <small>+${xpForScore(report.overall_score, personality)} XP</small>
      </div>
    </div>
    <div class="mini-bars">
      ${skillBar("Comunicacion", report.communication_score)}
      ${skillBar("Coherencia", report.coherence_score)}
      ${skillBar("Adecuacion", report.job_fit_score)}
      ${skillBar("Confianza", report.confidence_score)}
    </div>
    <p>${report.summary_report}</p>
    <p>${report.final_feedback}</p>
    <h3>Fortalezas</h3>
    <ul>${report.strengths.map((item) => `<li>${item}</li>`).join("")}</ul>
    <h3>Mejoras</h3>
    <ul>${report.recommendations.map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
}

function rankForScore(score) {
  if (score >= 9) return "Perfil excelente";
  if (score >= 7.5) return "Profesional solido";
  if (score >= 6) return "Candidato prometedor";
  return "Novato";
}

function xpForScore(score, personality) {
  return Math.round(score * 100) + (personalityXp[personality] || 75);
}

function skillBar(label, value) {
  const percent = Math.min(100, Math.max(0, value * 10));
  return `<div class="mini-bar"><span>${label}</span><b>${value}/10</b><i style="--value:${percent}%"></i></div>`;
}

function renderPlayerStats(stats) {
  playerName.textContent = stats.name;
  playerRank.textContent = stats.rank;
  playerLevel.textContent = stats.level;
  totalXp.textContent = `${stats.total_xp} XP`;
  xpToNext.textContent = `${stats.current_level_xp} / ${stats.next_level_xp}`;
  xpFill.style.width = `${stats.progress_percent}%`;
  completedCount.textContent = stats.completed_interviews;
  averageScore.textContent = stats.average_score ?? "--";
  bestScore.textContent = stats.best_score ?? "--";
}

function renderAvatarUnlocks(icons) {
  const unlockedIcons = icons.filter((icon) => icon.unlocked);
  const savedCode = localStorage.getItem(avatarStorageKey);
  const activeIcon =
    unlockedIcons.find((icon) => icon.code === savedCode) ||
    unlockedIcons.at(-1) ||
    icons[0];

  if (activeIcon) {
    setProfileAvatar(activeIcon);
  }

  avatarUnlockList.innerHTML = icons.map((icon) => `
    <button
      class="avatar-token ${icon.unlocked ? "unlocked" : "locked"} ${activeIcon?.code === icon.code ? "selected" : ""}"
      type="button"
      data-code="${icon.code}"
      ${icon.unlocked ? "" : "disabled"}
      title="${icon.unlocked ? `Usar ${icon.title}` : `Se desbloquea en nivel ${icon.required_level}`}"
    >
      <span>${icon.symbol}</span>
      <small>Nv. ${icon.required_level}</small>
    </button>
  `).join("");

  for (const button of avatarUnlockList.querySelectorAll(".avatar-token.unlocked")) {
    button.addEventListener("click", () => {
      const icon = icons.find((item) => item.code === button.dataset.code);
      if (!icon) {
        return;
      }
      localStorage.setItem(avatarStorageKey, icon.code);
      setProfileAvatar(icon);
      for (const item of avatarUnlockList.querySelectorAll(".avatar-token")) {
        item.classList.toggle("selected", item.dataset.code === icon.code);
      }
    });
  }
}

function setProfileAvatar(icon) {
  playerAvatar.textContent = icon.symbol;
  playerAvatar.dataset.avatar = icon.code;
}

function renderAchievements(achievements) {
  achievementList.innerHTML = achievements.map((achievement) => `
    <div class="achievement ${achievement.unlocked ? "unlocked" : "locked"}">
      <span>${achievement.unlocked ? "✓" : "·"}</span>
      <div>
        <strong>${achievement.title}</strong>
        <small>${achievement.description}</small>
      </div>
    </div>
  `).join("");
}

function renderRanking(entries) {
  leaderboardList.innerHTML = entries.map((entry) => `
    <div class="rank-entry">
      <span>#${entry.position}</span>
      <strong>${entry.name}</strong>
      <small>Nv. ${entry.level} · ${entry.total_xp} XP</small>
      <b>${entry.average_score ?? "--"}</b>
    </div>
  `).join("");
}

async function showInterview(interview) {
  reportTitle.textContent = interview.title;
  reportMeta.textContent = `${interview.job_type} · ${interview.personality} · ${formatDuration(interview.duration_seconds)} · ${statusLabel(interview.status)}`;

  if (!interview.has_report) {
    reportContent.className = "report-content empty-state";
    reportContent.textContent = "Esta entrevista todavia no tiene informe generado.";
    return;
  }

  try {
    const report = await fetchJson(`/interviews/${interview.id}/report`);
    renderReport(report, interview.personality);
  } catch (error) {
    reportContent.className = "report-content empty-state";
    reportContent.textContent = error.message;
  }
}

async function loadDashboard() {
  if (user?.name) {
    welcomeText.textContent = `Bienvenido, ${user.name}. Tu perfil de candidato esta listo para entrenar.`;
  }
  const [interviews, stats, ranking] = await Promise.all([
    fetchJson("/interviews"),
    fetchJson("/game/profile"),
    fetchJson("/game/ranking"),
  ]);
  renderHistory(interviews || []);
  renderPlayerStats(stats);
  renderAvatarUnlocks(stats.avatar_icons || []);
  renderAchievements(stats.achievements);
  renderRanking(ranking || []);
}

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("authToken");
  localStorage.removeItem("authUser");
  window.location.href = "/";
});

loadDashboard().catch((error) => {
  historyList.innerHTML = `<div class="empty-state">${error.message}</div>`;
});
