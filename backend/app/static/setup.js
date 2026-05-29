const token = localStorage.getItem("authToken");
if (!token) {
  window.location.href = "/";
}

const jobSelect = document.getElementById("jobSelect");
const personalitySelect = document.getElementById("personalitySelect");
const startForm = document.getElementById("startForm");
const logoutBtn = document.getElementById("logoutBtn");
const missionGrid = document.getElementById("missionGrid");
const personalityGrid = document.getElementById("personalityGrid");
const previewText = document.getElementById("previewText");
let selectedJob = "Ingeniería";
let selectedPersonality = "Amable";
const interviewDurationLabel = "3 min 30 s";

const missionData = {
  Ingeniería: {
    title: "Desafio tecnico",
    icon: "⌬",
    difficulty: "Alta",
    skills: "Logica, precision, resolucion",
  },
  ADE: {
    title: "Gestion y estrategia",
    icon: "◈",
    difficulty: "Media",
    skills: "Negocio, decision, liderazgo",
  },
  Derecho: {
    title: "Argumentacion juridica",
    icon: "⚖",
    difficulty: "Alta",
    skills: "Argumentacion, rigor, claridad",
  },
  Magisterio: {
    title: "Comunicacion pedagogica",
    icon: "✦",
    difficulty: "Media",
    skills: "Empatia, didactica, expresion",
  },
  Marketing: {
    title: "Creatividad y persuasion",
    icon: "✺",
    difficulty: "Variable",
    skills: "Creatividad, persuasion, marca",
  },
};

const personalityData = {
  Amable: { description: "Apoyo constante y tono calmado.", xp: 80 },
  Agresivo: { description: "Presion alta y preguntas directas.", xp: 155 },
  Técnico: { description: "Profundiza en conocimiento y metodo.", xp: 135 },
  RRHH: { description: "Evalua encaje, actitud y comunicacion.", xp: 100 },
  "Startup informal": { description: "Ritmo rapido y conversacion cercana.", xp: 115 },
};

function fillSelect(select, values) {
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}

async function loadOptions() {
  const response = await fetch("/options");
  if (!response.ok) {
    throw new Error("No se pudo cargar el selector de entrevistas");
  }

  const data = await response.json();
  fillSelect(jobSelect, data.jobs);
  fillSelect(personalitySelect, data.personalities);
  renderMissionCards(data.jobs);
  renderPersonalityCards(data.personalities);
}

function renderMissionCards(jobs) {
  missionGrid.innerHTML = "";
  const uniqueJobs = [...new Set(jobs.map((job) => job === "Empresa" ? "ADE" : job))];
  for (const job of uniqueJobs) {
    const mission = missionData[job] || missionData.Ingeniería;
    const card = document.createElement("button");
    card.type = "button";
    card.className = "mission-card";
    card.dataset.value = job;
    card.innerHTML = `
      <span class="mission-icon">${mission.icon}</span>
      <strong>${mission.title}</strong>
      <small>${job}</small>
      <em>Dificultad ${mission.difficulty}</em>
      <em>Duracion aprox. ${interviewDurationLabel}</em>
      <p>${mission.skills}</p>
    `;
    card.addEventListener("click", () => selectMission(job));
    missionGrid.appendChild(card);
  }
  selectMission(uniqueJobs[0]);
}

function renderPersonalityCards(personalities) {
  personalityGrid.innerHTML = "";
  for (const personality of personalities) {
    const data = personalityData[personality] || { description: "", xp: 75 };
    const card = document.createElement("button");
    card.type = "button";
    card.className = "personality-card";
    card.dataset.value = personality;
    card.innerHTML = `
      <strong>${personality}</strong>
      <small>${data.description}</small>
      <small>Formato breve: ${interviewDurationLabel}</small>
      <em>Recompensa +${data.xp} XP</em>
    `;
    card.addEventListener("click", () => selectPersonality(personality));
    personalityGrid.appendChild(card);
  }
  selectPersonality(personalities[0]);
}

function selectMission(job) {
  selectedJob = job;
  jobSelect.value = job;
  for (const card of missionGrid.querySelectorAll(".mission-card")) {
    card.classList.toggle("selected", card.dataset.value === job);
  }
  updatePreview();
}

function selectPersonality(personality) {
  selectedPersonality = personality;
  personalitySelect.value = personality;
  for (const card of personalityGrid.querySelectorAll(".personality-card")) {
    card.classList.toggle("selected", card.dataset.value === personality);
  }
  updatePreview();
}

function updatePreview() {
  const mission = missionData[selectedJob] || missionData.Ingeniería;
  const personality = personalityData[selectedPersonality] || { xp: 75 };
  previewText.textContent = `${mission.title}: ${mission.skills}. Carolina ${selectedPersonality} · ${interviewDurationLabel} aprox. · +${personality.xp} XP base.`;
}

startForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const job = encodeURIComponent(jobSelect.value);
  const personality = encodeURIComponent(personalitySelect.value);
  window.location.href = `/realtime?job=${job}&personality=${personality}`;
});

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("authToken");
  localStorage.removeItem("authUser");
  window.location.href = "/";
});

loadOptions().catch((error) => {
  alert(error.message);
});
