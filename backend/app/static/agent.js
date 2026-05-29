import { Conversation } from "https://esm.sh/@elevenlabs/client@1.2.0?bundle";

const state = {
  conversation: null,
  sessionId: null,
  interviewId: null,
  job: null,
  personality: null,
  status: "disconnected",
  audioEnabled: true,
  lastUserMessage: "",
  everConnected: false,
  lastStatus: "disconnected",
  lastMode: "",
  authenticated: false,
};

const sessionTitle = document.getElementById("sessionTitle");
const messages = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const avatar = document.getElementById("avatar");
const avatarMouth = document.getElementById("avatarMouth");
const voiceStatus = document.getElementById("voiceStatus");
const startBtn = document.getElementById("startBtn");
const endInterviewBtn = document.getElementById("endInterviewBtn");
const reportBtn = document.getElementById("reportBtn");
const formatBtn = document.getElementById("formatBtn");
const reportPanel = document.getElementById("reportPanel");
const finalScore = document.getElementById("finalScore");
const reportSummary = document.getElementById("reportSummary");
const reportRecommendation = document.getElementById("reportRecommendation");
const scoreList = document.getElementById("scoreList");
const npcState = document.getElementById("npcState");
const connectionState = document.getElementById("connectionState");
const durationTimer = document.getElementById("durationTimer");
const performanceMeter = document.getElementById("performanceMeter");
const micIndicator = document.getElementById("micIndicator");
const resultRank = document.getElementById("resultRank");
const xpReward = document.getElementById("xpReward");
const skillBars = document.getElementById("skillBars");

let visemeTimer = null;
let connectionTimeout = null;
let durationInterval = null;
let startedAt = null;
let targetDurationNoticeSent = false;
const targetDurationSeconds = 210;
const targetDurationLabel = "03:30";

function getAuthToken() {
  return localStorage.getItem("authToken");
}

function authHeaders() {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function handleUnauthorized(response) {
  if (response.status === 401) {
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");
    window.location.href = "/";
    return true;
  }
  return false;
}

function safeId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `session-${Date.now()}`;
}

function addMessage(role, text) {
  if (!text) {
    return;
  }
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function setVoiceStatus(text) {
  voiceStatus.textContent = text;
}

function setNpcState(label) {
  npcState.textContent = label;
}

function setConnectionState(label) {
  connectionState.textContent = label;
}

function startTimer() {
  startedAt = Date.now();
  targetDurationNoticeSent = false;
  stopTimer();
  durationInterval = window.setInterval(() => {
    const elapsed = Math.floor((Date.now() - startedAt) / 1000);
    const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const seconds = String(elapsed % 60).padStart(2, "0");
    durationTimer.textContent = `${minutes}:${seconds} / ${targetDurationLabel}`;
    if (elapsed >= targetDurationSeconds && !targetDurationNoticeSent) {
      targetDurationNoticeSent = true;
      performanceMeter.textContent = "Cierre";
      setVoiceStatus("Tiempo objetivo alcanzado. Puedes cerrar con Carolina y generar el informe.");
    }
  }, 1000);
}

function stopTimer() {
  if (durationInterval) {
    window.clearInterval(durationInterval);
    durationInterval = null;
  }
}

async function updateBackendStatus(status, detail = null) {
  state.status = status;
  if (detail) {
    console.debug("Estado de entrevista", status, detail);
  }
}

async function requestMicrophoneAccess() {
  if (!window.isSecureContext && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    throw new Error("El microfono solo funciona en localhost/127.0.0.1 o HTTPS.");
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Este origen del navegador no permite acceso al microfono. Usa http://localhost:8000/.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  for (const track of stream.getTracks()) {
    track.stop();
  }
}

function describeElevenLabsError(error) {
  if (!error) {
    return "Error desconocido de ElevenLabs.";
  }
  if (typeof error === "string") {
    return error;
  }
  if (error.message) {
    return error.message;
  }
  try {
    return JSON.stringify(error);
  } catch {
    return "Error de ElevenLabs no serializable.";
  }
}

function setViseme(viseme) {
  avatarMouth.dataset.viseme = viseme;
}

function startVisemeLoop() {
  stopVisemeLoop();
  const visemes = ["rest", "open", "wide", "open", "rest"];
  visemeTimer = window.setInterval(() => {
    setViseme(visemes[Math.floor(Math.random() * visemes.length)]);
  }, 110);
}

function stopVisemeLoop() {
  if (visemeTimer) {
    window.clearInterval(visemeTimer);
    visemeTimer = null;
  }
  setViseme("rest");
}

function parseSessionConfig() {
  const params = new URLSearchParams(window.location.search);
  const job = params.get("job");
  const personality = params.get("personality");
  if (!job || !personality) {
    window.location.href = "/";
    return false;
  }

  state.job = job;
  state.personality = personality;
  sessionTitle.textContent = `${job} · ${personality}`;
  return true;
}

async function startInterviewSession() {
  const token = getAuthToken();
  if (!token) {
    window.location.href = "/";
    throw new Error("Debes iniciar sesion");
  }

  const response = await fetch("/interviews/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({
      title: `${state.job} · ${state.personality}`,
      job_type: state.job,
      interviewer_personality: state.personality,
    }),
  });
  if (handleUnauthorized(response)) {
    throw new Error("Sesion expirada");
  }
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const data = await response.json();
  state.authenticated = true;
  state.interviewId = data.id;
  return data;
}

async function storeTranscriptMessage(speaker, text) {
  if (!state.sessionId || !text) {
    return;
  }
  try {
    if (!state.interviewId) {
      return;
    }
    const response = await fetch(`/interviews/${state.interviewId}/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        speaker,
        message: text,
        timestamp: new Date().toISOString(),
      }),
    });
    handleUnauthorized(response);
  } catch (error) {
    console.error("No se pudo guardar transcripcion", error);
  }
}

async function startConversation() {
  startBtn.disabled = true;
  sendBtn.disabled = true;
  state.everConnected = false;
  state.status = "connecting";
  setNpcState("Cargando");
  setConnectionState("Conectando");
  micIndicator.textContent = "Solicitando permiso";
  setVoiceStatus("Solicitando permiso de microfono...");
  await requestMicrophoneAccess();

  setVoiceStatus("Conectando con Carolina...");
  const session = await startInterviewSession();
  state.sessionId = session.session_id || safeId();
  state.interviewId = session.id || state.interviewId;
  const elevenlabs = session.elevenlabs_session_data;
  const sessionOptions = {
    signedUrl: elevenlabs.signed_url,
    overrides: elevenlabs.conversation_overrides,
  };

  await updateBackendStatus("connecting");

  connectionTimeout = window.setTimeout(() => {
    if (!state.everConnected) {
      setVoiceStatus("ElevenLabs sigue conectando demasiado tiempo.");
      addMessage(
        "assistant",
        "La conexion con ElevenLabs no ha terminado de abrirse. Revisa que el agente este publicado, que no tenga errores en ElevenLabs y que la allowlist este vacia durante desarrollo local.",
      );
      void updateBackendStatus("error", "Timeout esperando conexion con ElevenLabs");
      startBtn.disabled = false;
    }
  }, 12000);

  state.conversation = await Conversation.startSession({
    ...sessionOptions,
    onConnect: () => {
      if (connectionTimeout) {
        window.clearTimeout(connectionTimeout);
        connectionTimeout = null;
      }
      state.status = "connected";
      state.everConnected = true;
      startTimer();
      void updateBackendStatus("connected");
      sendBtn.disabled = false;
      setConnectionState("Online");
      setNpcState("Escuchando");
      micIndicator.textContent = "Micro activo";
      setVoiceStatus("Carolina te escucha. Puedes interrumpirla hablando.");
    },
    onDisconnect: () => {
      if (connectionTimeout) {
        window.clearTimeout(connectionTimeout);
        connectionTimeout = null;
      }
      state.status = state.everConnected ? "stopped" : "disconnected";
      stopTimer();
      sendBtn.disabled = true;
      startBtn.disabled = false;
      avatar.classList.remove("speaking");
      avatar.classList.remove("listening");
      stopVisemeLoop();
      if (state.everConnected) {
        void updateBackendStatus("stopped");
        setConnectionState("Cerrada");
        setNpcState("Finalizada");
        micIndicator.textContent = "Micro detenido";
        setVoiceStatus(`Entrevista detenida. Estado anterior: ${state.lastStatus || "desconocido"}.`);
      } else {
        void updateBackendStatus("disconnected", "ElevenLabs cerro antes de conectar");
        setConnectionState("Error");
        setNpcState("Sin conexion");
        setVoiceStatus("ElevenLabs cerro la conexion antes de iniciar.");
        addMessage(
          "assistant",
          "No se pudo iniciar la llamada con Carolina. Revisa en ElevenLabs Security que esten habilitados los overrides de System prompt, First message y Language, y que el agente tenga una voz disponible para Conversational AI.",
        );
      }
    },
    onError: (error) => {
      if (connectionTimeout) {
        window.clearTimeout(connectionTimeout);
        connectionTimeout = null;
      }
      console.error("ElevenLabs error", error);
      const detail = describeElevenLabsError(error);
      addMessage("assistant", `Error de ElevenLabs: ${detail}`);
      void updateBackendStatus("error", detail);
      setConnectionState("Error");
      setNpcState("Incidencia");
      setVoiceStatus("Error en la entrevista.");
      startBtn.disabled = false;
    },
    onStatusChange: (status) => {
      const currentStatus = typeof status === "string" ? status : status?.status;
      state.lastStatus = currentStatus || state.lastStatus;
      if (currentStatus === "connecting") {
        void updateBackendStatus("connecting");
        setConnectionState("Conectando");
        setVoiceStatus("Conectando con Carolina...");
      } else if (currentStatus === "connected") {
        void updateBackendStatus("connected");
        setConnectionState("Online");
        setVoiceStatus("Conexion establecida con Carolina.");
      } else if (currentStatus === "disconnected") {
        setConnectionState("Offline");
        setVoiceStatus("Conexion con ElevenLabs desconectada.");
      }
    },
    onModeChange: (mode) => {
      const currentMode = typeof mode === "string" ? mode : mode?.mode;
      state.lastMode = currentMode || state.lastMode;
      if (currentMode === "speaking") {
        avatar.classList.add("speaking");
        avatar.classList.remove("listening");
        startVisemeLoop();
        setNpcState("Hablando");
        setVoiceStatus("Carolina esta hablando. Puedes interrumpirla.");
      } else if (currentMode === "listening") {
        avatar.classList.remove("speaking");
        avatar.classList.add("listening");
        stopVisemeLoop();
        setNpcState("Escuchando");
        setVoiceStatus("Carolina te escucha...");
      }
    },
    onMessage: (message) => {
      const source = message?.source || message?.role;
      const text = message?.message || message?.text || message?.content;
      if (!text) {
        return;
      }
      if (source === "user") {
        state.lastUserMessage = text;
        addMessage("user", text);
        performanceMeter.textContent = "Analizando";
        void storeTranscriptMessage("candidate", text);
      } else {
        addMessage("assistant", text);
        void storeTranscriptMessage("interviewer", text);
      }
    },
  });

  if (connectionTimeout) {
    window.clearTimeout(connectionTimeout);
    connectionTimeout = null;
  }
  state.status = "connected";
  state.everConnected = true;
  startTimer();
  void updateBackendStatus("connected");
  sendBtn.disabled = false;
  setConnectionState("Online");
  setNpcState("Escuchando");
  micIndicator.textContent = "Micro activo";
  console.log("ElevenLabs session started", state.conversation?.getId?.());
  setVoiceStatus("Carolina conectada. Puedes hablar o escribir.");
}

async function endConversation() {
  if (state.status !== "connected") {
    setVoiceStatus("No se puede detener: la entrevista no esta conectada.");
    return;
  }
  await updateBackendStatus("stopping");
  try {
    if (state.conversation) {
      await state.conversation.endSession();
      state.conversation = null;
    }
  } catch (error) {
    addMessage("assistant", `No se pudo detener la llamada: ${error.message}`);
  }
  state.status = "stopped";
  stopTimer();
  startBtn.disabled = false;
  sendBtn.disabled = true;
  avatar.classList.remove("speaking");
  avatar.classList.remove("listening");
  stopVisemeLoop();
  setConnectionState("Cerrada");
  setNpcState("Finalizada");
  micIndicator.textContent = "Micro detenido";
  setVoiceStatus("Entrevista detenida.");
}

function fillList(element, values) {
  element.innerHTML = "";
  for (const value of values) {
    const li = document.createElement("li");
    li.textContent = value;
    element.appendChild(li);
  }
}

function buildScoreItems(scores) {
  return [
    `Comunicacion: ${scores.communication_score}/10`,
    `Coherencia: ${scores.coherence_score}/10`,
    `Adecuacion al puesto: ${scores.job_fit_score}/10`,
    `Confianza: ${scores.confidence_score}/10`,
  ];
}

function rankForScore(score) {
  if (score >= 9) return "Perfil excelente";
  if (score >= 7.5) return "Profesional solido";
  if (score >= 6) return "Candidato prometedor";
  return "Novato";
}

function xpForScore(score) {
  const personalityXp = {
    Amable: 80,
    RRHH: 100,
    "Startup informal": 115,
    Técnico: 135,
    Agresivo: 155,
  };
  return Math.round(score * 100) + (personalityXp[state.personality] || 75);
}

function renderSkillBars(report) {
  const skills = [
    ["Comunicacion", report.communication_score],
    ["Coherencia", report.coherence_score],
    ["Adecuacion", report.job_fit_score],
    ["Confianza", report.confidence_score],
  ];
  skillBars.innerHTML = skills.map(([label, value]) => {
    const percent = Math.min(100, Math.max(0, value * 10));
    return `
      <div class="skill-bar">
        <span>${label}</span>
        <b>${value}/10</b>
        <i style="--value:${percent}%"></i>
      </div>
    `;
  }).join("");
}

async function generateReport() {
  if (!state.sessionId) {
    addMessage("assistant", "Primero inicia una entrevista para poder generar el informe.");
    return;
  }
  reportBtn.disabled = true;
  try {
    if (state.status === "connected") {
      await endConversation();
    }
    if (!state.interviewId) {
      throw new Error("No hay entrevista autenticada activa.");
    }
    const response = await fetch(`/interviews/${state.interviewId}/end`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (handleUnauthorized(response)) {
      return;
    }
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    const report = data.report;
    reportPanel.classList.remove("hidden");
    finalScore.textContent = `Nota final: ${report.overall_score}/10`;
    resultRank.textContent = `Rango obtenido: ${rankForScore(report.overall_score)}`;
    xpReward.textContent = `Recompensa: +${xpForScore(report.overall_score)} XP`;
    reportSummary.textContent = report.summary_report;
    reportRecommendation.textContent = report.final_feedback;
    performanceMeter.textContent = `${report.overall_score}/10`;
    renderSkillBars(report);
    fillList(scoreList, [
      ...buildScoreItems(report),
      ...report.strengths.map((item) => `Fortaleza: ${item}`),
      ...report.weaknesses.map((item) => `Debilidad: ${item}`),
      ...report.recommendations.map((item) => `Mejora: ${item}`),
    ]);
  } catch (error) {
    addMessage("assistant", `No se pudo generar informe: ${error.message}`);
  } finally {
    reportBtn.disabled = false;
  }
}

startBtn.addEventListener("click", () => {
  startConversation().catch((error) => {
    addMessage("assistant", `No se pudo iniciar ElevenLabs: ${error.message}`);
    setVoiceStatus("No se pudo iniciar la entrevista.");
    startBtn.disabled = false;
  });
});

endInterviewBtn.addEventListener("click", () => {
  endConversation();
});

formatBtn.addEventListener("click", async () => {
  state.audioEnabled = !state.audioEnabled;
  formatBtn.textContent = state.audioEnabled ? "Cambiar a texto" : "Cambiar a voz";
  if (state.conversation?.setVolume) {
    await state.conversation.setVolume({ volume: state.audioEnabled ? 1 : 0 });
  }
  setVoiceStatus(state.audioEnabled ? "Formato voz activo." : "Formato texto activo.");
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text || !state.conversation) {
    return;
  }
  messageInput.value = "";
  if (state.conversation.sendUserMessage) {
    state.conversation.sendUserMessage(text);
  }
});

reportBtn.addEventListener("click", () => {
  void generateReport();
});

sendBtn.disabled = true;
if (parseSessionConfig()) {
  setVoiceStatus("Pulsa iniciar entrevista para hablar con Carolina.");
}
