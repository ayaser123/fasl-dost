const $ = (s) => document.querySelector(s);
const toast = (title, text) => {
  $('#toastTitle').textContent = title;
  $('#toastText').textContent = text;
  $('#toast').classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => $('#toast').classList.remove('show'), 3800);
};

const state = { sessionId: '', audio: null, image: null, recorder: null, chunks: [], last: null, player: null };
const isRtl = (t) => /[؀-ۿ]/.test(t);

// ---------- weather card ----------
const WMO = (c) => c === 0 ? 'Clear sky' : c <= 3 ? 'Partly cloudy' : c <= 48 ? 'Fog / haze' : c <= 67 ? 'Rain' : c <= 77 ? 'Snow' : c <= 82 ? 'Showers' : 'Thunderstorm';
async function loadWeather() {
  const loc = $('#locationInput').value.trim();
  if (!loc) return;
  try {
    const w = await (await fetch('/api/weather?location=' + encodeURIComponent(loc))).json();
    if (w.error) throw 0;
    $('#wPlace').textContent = w.place + ' · Now';
    $('#wTemp').textContent = Math.round(w.current.temperature_2m) + '°';
    $('#wDesc').textContent = WMO(w.current.weather_code);
    $('#wHum').textContent = w.current.relative_humidity_2m + '%';
    $('#wWind').textContent = Math.round(w.current.wind_speed_10m) + ' km/h';
  } catch {
    $('#wPlace').textContent = loc; $('#wTemp').textContent = '–'; $('#wDesc').textContent = 'Weather unavailable';
  }
}
let wTimer;
$('#locationInput').addEventListener('input', () => { clearTimeout(wTimer); wTimer = setTimeout(loadWeather, 800); });
loadWeather();

// ---------- voice recording ----------
const recordButton = $('#recordButton');
recordButton.addEventListener('click', async () => {
  if (state.recorder) { state.recorder.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.chunks = [];
    const rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => e.data.size && state.chunks.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      state.audio = new Blob(state.chunks, { type: rec.mimeType || 'audio/webm' });
      state.recorder = null;
      recordButton.classList.remove('active');
      $('#recordText').textContent = 'Voice note ready · tap to redo';
      toast('Voice note saved', 'Now press “Get my crop guidance”.');
    };
    rec.start();
    state.recorder = rec;
    recordButton.classList.add('active');
    $('#recordText').textContent = 'Recording… tap to stop';
  } catch {
    toast('Microphone blocked', 'Allow the microphone, or type your message instead.');
  }
});

// ---------- photo (downscaled before upload) ----------
$('#photoButton').addEventListener('click', () => $('#photoInput').click());
$('#photoInput').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  state.image = await downscale(file, 1280);
  $('.photo-card .input-label small').textContent = file.name;
  $('.photo-card').style.borderColor = '#7e9b78';
  toast('Photo added', 'It will be sent with your question.');
});
function downscale(file, max) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = img.width * k; c.height = img.height * k;
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      c.toBlob((b) => resolve(b || file), 'image/jpeg', 0.85);
    };
    img.onerror = () => resolve(file);
    img.src = URL.createObjectURL(file);
  });
}

// ---------- chat ----------
function bubble(cls, text) {
  const chat = $('#chat');
  chat.querySelector('.chat-empty')?.remove();
  const p = document.createElement('p');
  p.className = cls; p.textContent = text;
  p.dir = isRtl(text) ? 'rtl' : 'ltr';
  chat.appendChild(p); chat.scrollTop = chat.scrollHeight;
}

// ---------- submit ----------
$('#analyseButton').addEventListener('click', async () => {
  const button = $('#analyseButton');
  const typed = $('#textInput').value.trim();
  if (!state.audio && !typed && !state.image) {
    toast('Nothing to send yet', 'Record a voice note, type a message, or add a photo.');
    return;
  }
  const fd = new FormData();
  fd.append('session_id', state.sessionId);
  fd.append('crop', $('#cropSelect').value);
  fd.append('stage', $('#stageSelect').value);
  fd.append('location', $('#locationInput').value);
  if (typed) fd.append('text', typed);
  if (state.audio) fd.append('audio', state.audio, 'voice.webm');
  if (state.image) fd.append('image', state.image, 'photo.jpg');

  button.disabled = true; button.classList.add('loading');
  button.querySelector('span').textContent = 'Listening and checking guidance…';
  try {
    const r = await fetch('/api/advise', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Server error');
    state.sessionId = d.session_id;
    if (d.error) { toast('Could not process', d.message); return; }
    if (d.transcript) bubble('me', d.transcript);
    bubble('bot', d.spoken_summary);
    render(d);
    // follow-up turns: clear consumed inputs
    state.audio = null; state.image = null; $('#textInput').value = '';
    $('#recordText').textContent = 'Tap to record';
    if (d.action !== 'ask') toast('Guidance ready', 'Scroll down to read it, or press Listen.');
  } catch (e) {
    toast('Something went wrong', 'Please try again, or contact your agriculture extension worker.');
  } finally {
    button.disabled = false; button.classList.remove('loading');
    button.querySelector('span').textContent = 'Get my crop guidance';
  }
});

const KIND = {
  advise: ['02 · YOUR GUIDANCE', 'Here’s what we found', 'LIKELY ISSUE', '✓'],
  ask: ['02 · A FEW QUESTIONS', 'Help us understand better', 'PLEASE TELL US', '?'],
  refer: ['02 · NEXT STEP', 'Please see an extension worker', 'WE CANNOT BE SURE', '!'],
};
function render(d) {
  state.last = d;
  const [kick, title, kind, mark] = KIND[d.action];
  $('#advKicker').textContent = kick; $('#advisoryTitle').textContent = title;
  $('#diagKind').textContent = kind; $('#diagMark').textContent = mark;
  $('#diagBox').className = 'diagnosis ' + d.action;
  const h = $('#diagTitle'), p = $('#diagText');
  const headline = d.action === 'ask' ? '' : d.likely_issue || '';
  h.textContent = headline; h.style.display = headline ? '' : 'none';
  p.textContent = d.action === 'ask' ? (d.questions || []).join('\n') : d.spoken_summary;
  p.style.whiteSpace = 'pre-line';
  [h, p].forEach((el) => (el.dir = isRtl(el.textContent) ? 'rtl' : 'ltr'));
  $('#confBadge').textContent = d.action === 'advise' ? ({ high: 'High', medium: 'Medium' }[d.confidence] + ' confidence') : '';
  $('#confBadge').style.display = d.action === 'advise' ? '' : 'none';

  const list = $('#stepsList'); list.innerHTML = '';
  (d.steps || []).forEach((s, i) => {
    const li = document.createElement('li');
    li.innerHTML = '<b></b><span dir="auto"><strong></strong><small></small></span><em></em>';
    li.querySelector('b').textContent = i + 1;
    li.querySelector('strong').textContent = s.title;
    li.querySelector('small').textContent = s.detail;
    li.querySelector('em').textContent = s.when || '';
    if (!s.when) li.querySelector('em').remove();
    list.appendChild(li);
  });
  $('#stepsBox').style.display = (d.steps || []).length ? '' : 'none';
  $('#safetyBox').style.display = d.safety_note ? '' : 'none';
  $('#safetyText').textContent = d.safety_note || '';
  $('#sourcesLine').textContent = (d.sources || []).length ? 'Based on: ' + d.sources.join(', ') : '';

  const s = $('#advisorySection'); s.classList.add('show');
  s.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------- listen ----------
$('#listenButton').addEventListener('click', async () => {
  const d = state.last; if (!d) return;
  const label = $('#listenButton span');
  if (state.player) { state.player.pause(); state.player = null; label.textContent = 'Listen'; return; }
  label.textContent = 'Loading…';
  const text = d.action === 'ask' ? [d.spoken_summary, ...(d.questions || [])].join('۔ ') : d.spoken_summary;
  try {
    const fd = new FormData(); fd.append('text', text); fd.append('lang', d.language);
    const r = await fetch('/api/tts', { method: 'POST', body: fd });
    if (!r.ok) throw 0;
    const a = new Audio(URL.createObjectURL(await r.blob()));
    state.player = a; label.textContent = 'Stop';
    a.onended = () => { state.player = null; label.textContent = 'Listen'; };
    a.play();
  } catch {
    // browser fallback voice (may not exist for Urdu/Punjabi on every device)
    const u = new SpeechSynthesisUtterance(text); u.lang = 'ur-PK';
    speechSynthesis.speak(u); label.textContent = 'Listen';
    toast('Using device voice', 'Server voice unavailable.');
  }
});

$('#resetButton').addEventListener('click', () => {
  Object.assign(state, { sessionId: '', audio: null, image: null, last: null });
  $('#chat').innerHTML = '<p class="chat-empty">Your conversation will appear here. Speak in Urdu or Punjabi, or type below.</p>';
  $('#advisorySection').classList.remove('show');
  $('#recordText').textContent = 'Tap to record';
});

$('#languageButton').addEventListener('click', () => toast('Replies follow your language', 'Speak in Urdu or Punjabi and Fasl Dost answers in the same language.'));
$('#notificationButton').addEventListener('click', () => toast('No alerts', 'Alerts are not enabled yet.'));
