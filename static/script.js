const locateBtn = document.getElementById('locateBtn');
const searchBtn = document.getElementById('searchBtn');
const queryInput = document.getElementById('query');
const output = document.getElementById('output');
let currentPos = null;

locateBtn.addEventListener('click', () => {
  if (!navigator.geolocation) {
    alert('Geolocation not supported by this browser');
    return;
  }
  navigator.geolocation.getCurrentPosition(pos => {
    currentPos = pos.coords;
    output.textContent = `Location acquired (lat: ${currentPos.latitude.toFixed(5)}, lon: ${currentPos.longitude.toFixed(5)})`;
    searchBtn.disabled = false;
  }, err => {
    alert('Unable to retrieve location: ' + err.message);
  });
});

searchBtn.addEventListener('click', async () => {
  const q = queryInput.value.trim();
  if (!q) { alert('Enter a search term'); return; }
  if (!currentPos) { alert('Location not available'); return; }
  const params = new URLSearchParams({
    lat: currentPos.latitude,
    lon: currentPos.longitude,
    q,
    radius: 2000
  });
  output.textContent = 'Searching...';
  try {
    const resp = await fetch(`/search?${params}`);
    const data = await resp.json();
    if (data.error) {
      output.textContent = `Error: ${data.error}`;
      return;
    }
    const pretty = JSON.stringify(data, null, 2);
    output.textContent = pretty;
  } catch (e) {
    output.textContent = `Request failed: ${e}`;
  }
});
