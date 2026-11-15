const $ = (s) => document.querySelector(s);
const toast = (title, text) => {
  $('#toastTitle').textContent = title;
  $('#toastText').textContent = text;
  $('#toast').classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => $('#toast').classList.remove('show'), 3200);
};

const recordButton = $('#recordButton');
let recording = false;
recordButton.addEventListener('click', () => {
  recording = !recording;
  recordButton.classList.toggle('active', recording);
  $('#recordText').textContent = recording ? 'Recording… tap to stop' : 'Voice note added';
  if (!recording) toast('Voice note saved', 'Your 12-second description is ready.');
});

$('#photoButton').addEventListener('click', () => $('#photoInput').click());
$('#photoInput').addEventListener('change', (event) => {
  if (!event.target.files.length) return;
  $('.photo-card .input-label small').textContent = event.target.files[0].name;
  $('.photo-card').style.borderColor = '#7e9b78';
  toast('Photo added', 'The leaf image is clear and ready to analyse.');
});

$('#analyseButton').addEventListener('click', () => {
  const button = $('#analyseButton');
  button.classList.add('loading');
  button.querySelector('span').textContent = 'Checking your crop…';
  setTimeout(() => {
    button.classList.remove('loading');
    button.querySelector('span').textContent = 'Guidance ready';
    $('#advisorySection').classList.add('show');
    $('#advisorySection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 1100);
});

$('#listenButton').addEventListener('click', () => {
  const button = $('#listenButton span');
  const speaking = button.textContent === 'Playing…';
  button.textContent = speaking ? 'Listen' : 'Playing…';
  toast(speaking ? 'Audio stopped' : 'Playing guidance', speaking ? 'Tap Listen to start again.' : 'Reading your crop guidance aloud.');
  if (!speaking) setTimeout(() => { button.textContent = 'Listen'; }, 3500);
});

$('#languageButton').addEventListener('click', () => toast('Urdu mode', 'Full Urdu guidance will be available in the live service.'));
$('#notificationButton').addEventListener('click', () => toast('No urgent alerts', 'Your field conditions look stable today.'));

document.querySelectorAll('select').forEach((select) => select.addEventListener('change', () => {
  if (select.id === 'cropSelect') toast('Crop updated', `Guidance will now be tailored for ${select.value.toLowerCase()}.`);
}));
