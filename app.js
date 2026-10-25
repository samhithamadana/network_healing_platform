let soundEnabled = true;
let audioContext = null;
let knownActiveAlarmIds = new Set();
let toastTimer;

function showToast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}
function playAlarm() {
  if (!soundEnabled) return;
  try {
    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === 'suspended') audioContext.resume();
    [0, 0.28, 0.56].forEach((delay, i) => {
      const osc = audioContext.createOscillator();
      const gain = audioContext.createGain();
      osc.type = 'sine'; osc.frequency.value = i % 2 ? 720 : 920;
      gain.gain.setValueAtTime(0.0001, audioContext.currentTime + delay);
      gain.gain.exponentialRampToValueAtTime(0.12, audioContext.currentTime + delay + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + delay + 0.18);
      osc.connect(gain); gain.connect(audioContext.destination);
      osc.start(audioContext.currentTime + delay); osc.stop(audioContext.currentTime + delay + 0.2);
    });
  } catch (e) { console.info('Browser sound is unavailable until user interaction.', e); }
}
function toggleSound() {
  soundEnabled = !soundEnabled;
  document.getElementById('soundBtn').textContent = soundEnabled ? '🔔 Sound: On' : '🔕 Sound: Off';
  if (soundEnabled) playAlarm();
}
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function fmtTime(value) {
  try { return new Date(value).toLocaleString(); } catch { return value; }
}
async function api(url, options = {}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || 'Request failed');
  return data;
}
function renderDevices(data) {
  document.getElementById('deviceRows').innerHTML = data.devices.map(d => `
    <tr><td><span class="device-name">${esc(d.name)}</span><span class="device-id">${esc(d.id)} · ${esc(d.interface)}</span></td>
    <td>${esc(d.type)}</td><td><span class="status ${esc(d.status)}">${esc(d.status)}</span></td>
    <td>${d.latency_ms} ms</td><td>${d.packet_loss}%</td><td>${d.cpu}%</td>
    <td><button class="fault-btn" onclick="injectFault('${esc(d.id)}','high_latency')">Latency</button>
    <button class="fault-btn" onclick="injectFault('${esc(d.id)}','packet_loss')">Loss</button>
    <button class="fault-btn" onclick="injectFault('${esc(d.id)}','device_down')">Down</button>
    <button class="fault-btn" onclick="injectFault('${esc(d.id)}','high_cpu')">CPU</button></td></tr>`).join('');
}
function renderAlarms(alarms) {
  const active = alarms.filter(a => a.status === 'Active');
  document.getElementById('alarmCount').textContent = `${active.length} active`;
  document.getElementById('alarms').innerHTML = active.length ? active.map(a => `
    <article class="alarm"><div><div class="alarm-title"><span class="severity">${esc(a.severity)}</span>${esc(a.device_name)} <span class="device-id">${esc(a.id)}</span></div>
    <p>${esc(a.description)}</p><p class="cause"><b>Likely root cause:</b> ${esc(a.root_cause)}</p>
    <p><b>Recommended recovery:</b> ${esc(a.recommended_action)}</p><p class="feed-time">Raised ${esc(fmtTime(a.created_at))}</p></div>
    <div class="alarm-actions"><button class="heal" onclick="healAlarm('${esc(a.id)}')">⚡ Auto-heal</button>
    <button class="ack" onclick="ackAlarm('${esc(a.id)}')">${a.acknowledged ? 'Acknowledged' : 'Acknowledge'}</button></div></article>`).join('') : '<div class="empty">No active alarms. Your simulated network is healthy.</div>';
}
function renderFeed(target, items, kind) {
  const el = document.getElementById(target);
  if (!items.length) { el.innerHTML = '<div class="empty">Nothing to show yet.</div>'; return; }
  el.innerHTML = items.slice(0, 12).map(item => {
    const title = kind === 'events' ? item.message : `${item.device_id}: ${item.action}`;
    const sub = kind === 'events' ? item.level : `${item.result} · ${item.mode}`;
    const level = kind === 'events' ? item.level : 'SUCCESS';
    return `<div class="feed-item"><div class="feed-time">${esc(fmtTime(item.time))}</div><div><span class="feed-level level-${esc(level)}">${esc(sub)}</span></div>${esc(title)}</div>`;
  }).join('');
}
async function refresh() {
  try {
    const data = await api('/api/status');
    document.getElementById('totalDevices').textContent = data.summary.total_devices;
    document.getElementById('healthyDevices').textContent = data.summary.healthy_devices;
    document.getElementById('activeAlarms').textContent = data.summary.active_alarms;
    document.getElementById('healedAlarms').textContent = data.summary.healed_alarms;
    renderDevices(data); renderAlarms(data.alarms);
    renderFeed('history', data.healing_history, 'history');
    renderFeed('events', data.events, 'events');
    const current = new Set(data.alarms.filter(a => a.status === 'Active').map(a => a.id));
    if ([...current].some(id => !knownActiveAlarmIds.has(id))) playAlarm();
    knownActiveAlarmIds = current;
  } catch (e) { showToast(`Connection error: ${e.message}`); }
}
async function injectFault(device_id, fault) {
  try { await api('/api/simulate', {method:'POST', body:JSON.stringify({device_id, fault})});
    showToast(`Demo fault injected: ${fault.replace('_',' ')}`); await refresh();
  } catch (e) { showToast(e.message); }
}
async function healAlarm(id) {
  try { await api(`/api/heal/${encodeURIComponent(id)}`, {method:'POST', body:'{}'});
    showToast('Simulated recovery completed successfully.'); await refresh();
  } catch (e) { showToast(e.message); }
}
async function ackAlarm(id) {
  try { await api(`/api/acknowledge/${encodeURIComponent(id)}`, {method:'POST', body:'{}'});
    showToast('Alarm acknowledged.'); await refresh();
  } catch (e) { showToast(e.message); }
}
async function healAll() {
  try { const result = await api('/api/heal-all', {method:'POST', body:'{}'});
    showToast(`Recovery complete: ${result.healed_count} alarm(s) processed.`); await refresh();
  } catch (e) { showToast(e.message); }
}
refresh();
setInterval(refresh, 5000);
