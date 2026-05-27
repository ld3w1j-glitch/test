const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const btnStart = document.getElementById('btnStart');
const btnCapture = document.getElementById('btnCapture');
const uploadForm = document.getElementById('uploadForm');
const settingsForm = document.getElementById('settingsForm');
const statusBox = document.getElementById('status');
const countBox = document.getElementById('count');
const resultImg = document.getElementById('resultImg');
const maskImg = document.getElementById('maskImg');
const details = document.getElementById('details');

let stream = null;

function setStatus(message, kind = 'idle') {
  statusBox.textContent = message;
  statusBox.className = `status ${kind}`;
}

function appendSettings(formData) {
  const settings = new FormData(settingsForm);
  for (const [key, value] of settings.entries()) {
    formData.append(key, value);
  }
  return formData;
}

async function sendForm(formData) {
  setStatus('Analisando imagem...', 'idle');
  countBox.textContent = '0';
  try {
    const response = await fetch('/analisar', { method: 'POST', body: formData });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || 'Erro ao analisar.');
    countBox.textContent = data.count;
    resultImg.src = data.result_url + '?t=' + Date.now();
    maskImg.src = data.mask_url + '?t=' + Date.now();
    resultImg.style.display = 'block';
    maskImg.style.display = 'block';
    details.textContent = JSON.stringify(data.items, null, 2);
    setStatus(data.message, 'ok');
  } catch (err) {
    setStatus(err.message, 'error');
  }
}

btnStart.addEventListener('click', async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    video.srcObject = stream;
    btnCapture.disabled = false;
    setStatus('Câmera aberta. Aponte para os itens e clique em capturar.', 'ok');
  } catch (err) {
    setStatus('Não consegui abrir a câmera. No celular, use HTTPS ou selecione/tire foto pelo campo de arquivo.', 'error');
  }
});

btnCapture.addEventListener('click', async () => {
  if (!stream) return;
  canvas.width = video.videoWidth || 1280;
  canvas.height = video.videoHeight || 720;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
  const formData = appendSettings(new FormData());
  formData.append('image_base64', dataUrl);
  await sendForm(formData);
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = appendSettings(new FormData(uploadForm));
  await sendForm(formData);
});
