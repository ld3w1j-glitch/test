const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const ctx = overlay.getContext("2d");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const saveBtn = document.getElementById("saveBtn");
const countEl = document.getElementById("count");
const statusEl = document.getElementById("status");
const modeEl = document.getElementById("mode");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadResult = document.getElementById("uploadResult");

let stream = null;
let running = false;
let detecting = false;
let lastFrameData = null;
let lastBoxes = [];
let lastCount = 0;
let intervalId = null;

function setStatus(text) {
  statusEl.textContent = text;
}

function resizeOverlay() {
  const rect = video.getBoundingClientRect();
  overlay.width = video.videoWidth || rect.width;
  overlay.height = video.videoHeight || rect.height;
}

function drawBoxes(boxes) {
  resizeOverlay();
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  ctx.lineWidth = Math.max(3, overlay.width / 250);
  ctx.font = `${Math.max(18, overlay.width / 35)}px Arial`;
  ctx.strokeStyle = "#00ff66";
  ctx.fillStyle = "#00ff66";

  boxes.forEach((b, idx) => {
    ctx.strokeRect(b.x, b.y, b.w, b.h);
    ctx.fillText(`Pessoa ${idx + 1}`, b.x, Math.max(24, b.y - 8));
  });
}

function captureFrameData(quality = 0.72) {
  resizeOverlay();
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const c = canvas.getContext("2d");
  c.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", quality);
}

async function detectFrame() {
  if (!running || detecting || !video.videoWidth) return;
  detecting = true;

  try {
    const image = captureFrameData(0.65);
    lastFrameData = image;

    const resp = await fetch(`/api/detect_frame?mode=${encodeURIComponent(modeEl.value)}`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image})
    });

    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || "Erro na leitura.");

    lastBoxes = data.boxes || [];
    lastCount = data.count || 0;
    countEl.textContent = lastCount;
    drawBoxes(lastBoxes);
    setStatus(`Leitura atualizada. Pessoas detectadas: ${lastCount}`);
  } catch (err) {
    setStatus("Erro: " + err.message);
  } finally {
    detecting = false;
  }
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    });
    video.srcObject = stream;
    await video.play();

    running = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    saveBtn.disabled = false;
    setStatus("Câmera iniciada. Contando em tempo real...");

    intervalId = setInterval(detectFrame, 900);
    detectFrame();
  } catch (err) {
    setStatus("Não consegui abrir a câmera: " + err.message + ". Use HTTPS ou envie uma foto.");
  }
}

function stopCamera() {
  running = false;
  if (intervalId) clearInterval(intervalId);
  intervalId = null;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
  }
  stream = null;
  startBtn.disabled = false;
  stopBtn.disabled = true;
  saveBtn.disabled = true;
  setStatus("Câmera parada.");
}

async function saveCurrentReading() {
  if (!lastFrameData) {
    setStatus("Nenhum frame capturado ainda.");
    return;
  }

  try {
    setStatus("Salvando leitura no histórico...");
    const resp = await fetch("/api/upload_detect", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image: lastFrameData, mode: modeEl.value})
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || "Erro ao salvar.");

    setStatus(`Salvo no histórico. Pessoas: ${data.count}`);
    uploadResult.innerHTML = `
      <p><strong>Salvo.</strong> Pessoas detectadas: ${data.count}</p>
      <img src="${data.processed_url}" alt="Imagem processada">
    `;
  } catch (err) {
    setStatus("Erro ao salvar: " + err.message);
  }
}

async function uploadPhoto() {
  const file = fileInput.files[0];
  if (!file) {
    uploadResult.innerHTML = "<p>Selecione uma imagem primeiro.</p>";
    return;
  }

  const form = new FormData();
  form.append("image", file);
  form.append("mode", modeEl.value);

  uploadResult.innerHTML = "<p>Processando...</p>";

  try {
    const resp = await fetch("/api/upload_detect", { method: "POST", body: form });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || "Erro ao contar.");

    uploadResult.innerHTML = `
      <p><strong>Pessoas detectadas:</strong> ${data.count}</p>
      <img src="${data.processed_url}" alt="Imagem processada">
      <p><a href="/history">Ver histórico</a></p>
    `;
  } catch (err) {
    uploadResult.innerHTML = `<p>Erro: ${err.message}</p>`;
  }
}

startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);
saveBtn.addEventListener("click", saveCurrentReading);
uploadBtn.addEventListener("click", uploadPhoto);
window.addEventListener("resize", () => drawBoxes(lastBoxes));