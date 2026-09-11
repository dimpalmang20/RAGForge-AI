const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const healthBadge = document.getElementById("healthBadge");
const ingestForm = document.getElementById("ingestForm");
const chatForm = document.getElementById("chatForm");
const ingestResult = document.getElementById("ingestResult");
const conversation = document.getElementById("conversation");
const emptyState = document.getElementById("emptyState");
const messageTemplate = document.getElementById("messageTemplate");
const checkHealthButton = document.getElementById("checkHealthButton");
const uploadButton = document.getElementById("uploadButton");
const resetMemoryButton = document.getElementById("resetMemoryButton");
const resetKnowledgeButton = document.getElementById("resetKnowledgeButton");
const ingestPathButton = document.getElementById("ingestPathButton");
const sendButton = document.getElementById("sendButton");
const newSessionButton = document.getElementById("newSessionButton");
const currentUserLabel = document.getElementById("currentUserLabel");
const currentSessionLabel = document.getElementById("currentSessionLabel");

const storageKeys = {
  apiBaseUrl: "hybrid-rag-ui-api-base-url",
  chatUserId: "hybrid-rag-ui-user-id",
  sessionId: "hybrid-rag-ui-session-id",
  ingestUserId: "hybrid-rag-ui-ingest-user-id",
};

function saveFieldValue(key, value) {
  window.localStorage.setItem(key, value);
}

function loadStoredValue(key, fallback = "") {
  return window.localStorage.getItem(key) || fallback;
}

function getApiBaseUrl() {
  return apiBaseUrlInput.value.replace(/\/$/, "");
}

function setHealthState(label, mode) {
  healthBadge.textContent = label;
  healthBadge.className = `badge ${mode}`;
}

function setButtonBusy(button, busy, idleLabel, busyLabel) {
  if (!button) {
    return;
  }
  button.disabled = busy;
  button.textContent = busy ? busyLabel : idleLabel;
}

function ensureDefaults() {
  const ingestUserId = document.getElementById("ingestUserId");
  const chatUserId = document.getElementById("chatUserId");
  const sessionId = document.getElementById("sessionId");

  if (!ingestUserId.value.trim()) {
    ingestUserId.value = "alice";
  }
  if (!chatUserId.value.trim()) {
    chatUserId.value = ingestUserId.value.trim() || "alice";
  }
  if (!sessionId.value.trim()) {
    sessionId.value = `session-${Date.now()}`;
  }
}

function syncWorkspaceLabels() {
  ensureDefaults();
  const userId = document.getElementById("chatUserId").value.trim() || document.getElementById("ingestUserId").value.trim() || "alice";
  const sessionId = document.getElementById("sessionId").value.trim() || `session-${Date.now()}`;

  document.getElementById("ingestUserId").value = userId;
  document.getElementById("chatUserId").value = userId;
  document.getElementById("sessionId").value = sessionId;
  currentUserLabel.textContent = userId;
  currentSessionLabel.textContent = sessionId;

  saveFieldValue(storageKeys.ingestUserId, userId);
  saveFieldValue(storageKeys.chatUserId, userId);
  saveFieldValue(storageKeys.sessionId, sessionId);
}

async function requestJson(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const body = options.body;
  if (!(body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers,
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "object" && payload?.detail ? payload.detail : payload;
    throw new Error(String(detail));
  }

  return payload;
}

async function checkHealth() {
  setHealthState("Checking", "badge-idle");
  setButtonBusy(checkHealthButton, true, "Check Connection", "Checking...");
  try {
    await requestJson("/health", { method: "GET", headers: {} });
    setHealthState("Healthy", "badge-ok");
  } catch (error) {
    setHealthState("Offline", "badge-error");
    console.error(error);
  } finally {
    setButtonBusy(checkHealthButton, false, "Check Connection", "Checking...");
  }
}

function addMessageCard(sessionId, answer, sources, role = "Grounded Answer", type = "assistant") {
  if (emptyState) {
    emptyState.remove();
  }

  const fragment = messageTemplate.content.cloneNode(true);
  const card = fragment.querySelector(".message-card");
  if (type === "system") {
    card.classList.add("system-card");
  }

  fragment.querySelector(".message-role").textContent = role;
  fragment.querySelector(".message-session").textContent = sessionId;
  fragment.querySelector(".message-body").textContent = answer;

  const sourcesList = fragment.querySelector(".sources-list");
  const sourcesBlock = fragment.querySelector(".sources-block");
  if (!sources || sources.length === 0) {
    if (type === "system") {
      sourcesBlock.remove();
    } else {
      const emptyItem = document.createElement("div");
      emptyItem.className = "source-item";
      emptyItem.textContent = "No sources returned.";
      sourcesList.appendChild(emptyItem);
    }
  } else {
    for (const source of sources) {
      const item = document.createElement("div");
      item.className = "source-item";

      const meta = document.createElement("span");
      meta.className = "source-meta";
      meta.textContent = `${source.source}:${source.chunk_id} | score=${Number(source.score).toFixed(3)}`;

      const text = document.createElement("div");
      text.textContent = source.text;

      item.append(meta, text);
      sourcesList.appendChild(item);
    }
  }

  conversation.prepend(fragment);
}

function addSystemCard(sessionId, text) {
  addMessageCard(sessionId, text, [], "System Notice", "system");
}

ingestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  syncWorkspaceLabels();

  const userId = document.getElementById("ingestUserId").value.trim();
  const filePath = document.getElementById("filePath").value.trim();

  if (!filePath) {
    ingestResult.textContent = "Add a backend local file path under Advanced Settings first.";
    return;
  }

  ingestResult.textContent = "Ingesting backend path...";
  setButtonBusy(ingestPathButton, true, "Ingest Backend Path", "Ingesting...");
  try {
    const payload = await requestJson("/ingest", {
      method: "POST",
      body: JSON.stringify({
        file_path: filePath,
        user_id: userId || null,
      }),
    });
    ingestResult.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    ingestResult.textContent = error.message;
  } finally {
    setButtonBusy(ingestPathButton, false, "Ingest Backend Path", "Ingesting...");
  }
});

uploadButton.addEventListener("click", async () => {
  syncWorkspaceLabels();
  const userId = document.getElementById("ingestUserId").value.trim();
  const fileInput = document.getElementById("uploadFile");
  const selectedFile = fileInput.files && fileInput.files[0];

  if (!selectedFile) {
    ingestResult.textContent = "Select a .txt or .md file first.";
    return;
  }

  ingestResult.textContent = "Uploading and ingesting...";
  setButtonBusy(uploadButton, true, "Upload and Ingest", "Uploading...");

  const formData = new FormData();
  formData.append("file", selectedFile);
  if (userId) {
    formData.append("user_id", userId);
  }

  try {
    const payload = await requestJson("/ingest/upload", {
      method: "POST",
      body: formData,
    });
    ingestResult.textContent = JSON.stringify(payload, null, 2);
    fileInput.value = "";
  } catch (error) {
    ingestResult.textContent = error.message;
  } finally {
    setButtonBusy(uploadButton, false, "Upload and Ingest", "Uploading...");
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  syncWorkspaceLabels();

  const userId = document.getElementById("chatUserId").value.trim();
  const sessionId = document.getElementById("sessionId").value.trim();
  const message = document.getElementById("message").value.trim();

  if (!message) {
    return;
  }

  setButtonBusy(sendButton, true, "Send Message", "Thinking...");
  try {
    const payload = await requestJson("/chat", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message,
      }),
    });
    addMessageCard(payload.session_id, payload.answer, payload.sources, "Grounded Answer", "assistant");
    document.getElementById("message").value = "";
  } catch (error) {
    addSystemCard(sessionId, `Error: ${error.message}`);
  } finally {
    setButtonBusy(sendButton, false, "Send Message", "Thinking...");
  }
});

resetMemoryButton.addEventListener("click", async () => {
  syncWorkspaceLabels();
  const userId = document.getElementById("chatUserId").value.trim();
  const sessionId = document.getElementById("sessionId").value.trim();

  setButtonBusy(resetMemoryButton, true, "Reset Session Memory", "Resetting...");
  try {
    const payload = await requestJson("/memory/reset", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
      }),
    });
    addSystemCard(sessionId, `Session memory reset for ${payload.user_id}:${payload.session_id}.`);
  } catch (error) {
    addSystemCard(sessionId, `Error resetting session memory: ${error.message}`);
  } finally {
    setButtonBusy(resetMemoryButton, false, "Reset Session Memory", "Resetting...");
  }
});

resetKnowledgeButton.addEventListener("click", async () => {
  syncWorkspaceLabels();
  const userId = document.getElementById("chatUserId").value.trim();

  setButtonBusy(resetKnowledgeButton, true, "Reset User Knowledge", "Resetting...");
  try {
    const payload = await requestJson("/knowledge/reset", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
      }),
    });
    ingestResult.textContent = JSON.stringify(payload, null, 2);
    addSystemCard("knowledge-reset", `Deleted ${payload.chunks_deleted} chunks and cleared ${payload.sessions_cleared} session histories for user ${payload.user_id}.`);
  } catch (error) {
    addSystemCard("knowledge-reset", `Error resetting knowledge base: ${error.message}`);
  } finally {
    setButtonBusy(resetKnowledgeButton, false, "Reset User Knowledge", "Resetting...");
  }
});

newSessionButton.addEventListener("click", () => {
  document.getElementById("sessionId").value = `session-${Date.now()}`;
  syncWorkspaceLabels();
  addSystemCard(document.getElementById("sessionId").value, "Started a new conversation session.");
});

checkHealthButton.addEventListener("click", checkHealth);
apiBaseUrlInput.addEventListener("change", () => {
  saveFieldValue(storageKeys.apiBaseUrl, apiBaseUrlInput.value);
  checkHealth();
});

document.getElementById("chatUserId").addEventListener("change", syncWorkspaceLabels);
document.getElementById("ingestUserId").addEventListener("change", syncWorkspaceLabels);
document.getElementById("sessionId").addEventListener("change", syncWorkspaceLabels);

function boot() {
  apiBaseUrlInput.value = loadStoredValue(storageKeys.apiBaseUrl, apiBaseUrlInput.value);
  document.getElementById("chatUserId").value = loadStoredValue(storageKeys.chatUserId, "alice");
  document.getElementById("sessionId").value = loadStoredValue(storageKeys.sessionId, "session-ui-1");
  document.getElementById("ingestUserId").value = loadStoredValue(storageKeys.ingestUserId, "alice");
  syncWorkspaceLabels();
  checkHealth();
}

boot();