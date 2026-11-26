// Render the VALOR landing film in an isolated local Chromium session.
// Usage: node scripts/Render-LandingDemo.cjs <Chrome executable> <Command Center screenshot>
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { setTimeout: delay } = require('node:timers/promises');

const root = path.resolve(__dirname, '..');
const staticDir = path.join(root, 'src', 'aace', 'demo', 'static');
const artifacts = path.join(root, 'artifacts');

async function animate(heroSource, dashboardSource) {
  const load = async src => {
    const image = new Image();
    image.src = src;
    await image.decode();
    return image;
  };
  const [hero, dashboard] = await Promise.all([load(heroSource), load(dashboardSource)]);
  const width = 1280;
  const height = 720;
  const duration = 20;
  const gold = '#f2cc8d';
  const cream = '#f5eee4';
  const muted = '#c0b4a2';
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  document.body.append(canvas);
  const ctx = canvas.getContext('2d', { alpha: false });

  const clamp = x => Math.max(0, Math.min(1, x));
  const smooth = x => { const p = clamp(x); return p * p * (3 - 2 * p); };
  const reveal = (t, start, end) => smooth((t - start) / .48) * (1 - smooth((t - end + .38) / .38));

  function text(value, x, y, size, color, weight = 400) {
    ctx.font = `${weight} ${size}px "Segoe UI", sans-serif`;
    ctx.fillStyle = color;
    ctx.fillText(value, x, y);
  }

  function box(x, y, w, h, r, fill, stroke = '') {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1; ctx.stroke(); }
  }

  function line(x1, y1, x2, y2, color, width = 1) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
  }

  function wash(t) {
    const haze = ctx.createRadialGradient(965, 313, 0, 965, 313, 680);
    haze.addColorStop(0, '#2e221a');
    haze.addColorStop(.57, '#151211');
    haze.addColorStop(1, '#09090a');
    ctx.fillStyle = haze;
    ctx.fillRect(0, 0, width, height);
    for (let i = 0; i < 40; i++) {
      const x = (37 + i * 109.31 + t * (4 + i % 3)) % width;
      const y = 36 + ((i * 71.7 + Math.sin(t / 2 + i) * 16) % 650);
      ctx.fillStyle = i % 6 ? '#e9bc7537' : '#e9bc7565';
      ctx.fillRect(x, y, i % 8 ? 1 : 2, 1);
    }
  }

  function chamber(t) {
    const approach = smooth(t / 15);
    const imageWidth = 1000 + 64 * approach;
    const imageHeight = imageWidth * hero.height / hero.width;
    ctx.save();
    ctx.globalAlpha = .96 * (1 - smooth((t - 15.75) / .75));
    ctx.drawImage(hero, 286 - 25 * approach, 2 - 35 * approach, imageWidth, imageHeight);
    ctx.restore();
    const shadow = ctx.createLinearGradient(85, 0, 810, 0);
    shadow.addColorStop(0, '#0b0a0a');
    shadow.addColorStop(.48, '#0b0a0af3');
    shadow.addColorStop(.76, '#0b0a0a76');
    shadow.addColorStop(1, '#0b0a0a00');
    ctx.fillStyle = shadow;
    ctx.fillRect(0, 0, width, height);
    const floor = ctx.createLinearGradient(0, 490, 0, 680);
    floor.addColorStop(0, '#0b0a0a00');
    floor.addColorStop(1, '#0b0a0a');
    ctx.fillStyle = floor;
    ctx.fillRect(0, 490, width, 230);
  }

  function brand() {
    ctx.save();
    ctx.lineJoin = 'round';
    line(72, 47, 86, 61, gold, 2);
    line(86, 61, 100, 47, gold, 2);
    line(72, 54, 86, 68, gold, 2);
    line(86, 68, 100, 54, gold, 2);
    text('V A L O R', 116, 64, 21, cream, 600);
    text('SIMULATION REPLAY', 1023, 67, 16, gold, 600);
    ctx.restore();
  }

  function steps(t) {
    const locations = [296, 640, 984];
    const labels = ['Agent', 'VALOR', 'Work'];
    const stage = t < 7.4 ? 0 : t < 11.8 ? 1 : 2;
    const path = smooth((t - 7.1) / 1.12) + smooth((t - 11.5) / 1.12);
    const wave = locations[0] + (locations[1] - locations[0]) * path;
    line(locations[0], 574, locations[2], 574, '#75614466');
    line(locations[0], 574, wave, 574, '#d4a970aa');
    ctx.save();
    ctx.shadowBlur = 17;
    ctx.shadowColor = gold;
    ctx.fillStyle = cream;
    ctx.beginPath();
    ctx.arc(wave, 574, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    locations.forEach((x, index) => {
      const current = index === stage;
      ctx.save();
      ctx.textAlign = 'center';
      ctx.fillStyle = current ? gold : '#9c8a72';
      ctx.beginPath();
      ctx.arc(x, 574, current ? 4 : 2, 0, Math.PI * 2);
      ctx.fill();
      text(labels[index], x, 609, 16, current ? gold : muted, 600);
      ctx.restore();
    });
  }

  function sceneLine(t, start, end, eyebrow, lines, notes) {
    const alpha = reveal(t, start, end);
    if (alpha <= 0) return;
    const offset = (1 - smooth((t - start) / .63)) * 18;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(0, offset);
    text(eyebrow, 72, 232, 21, gold, 600);
    lines.forEach(([label, size, color], index) => text(label, 69, 315 + index * 75, size, color, 590));
    const noteY = lines.length > 1 ? 452 : 385;
    for (let i = 0; i < notes.length; i++) text(notes[i], 72, noteY + i * 32, 25, muted, 400);
    ctx.restore();
  }

  function commandCenter(t) {
    const drift = smooth((t - 15.45) / .8);
    if (drift <= 0) return;
    ctx.save();
    ctx.globalAlpha = drift;
    ctx.translate(0, (1 - drift) * 22);
    const imageWidth = 676;
    const imageHeight = imageWidth * dashboard.height / dashboard.width;
    const x = 532;
    const y = 125;
    ctx.save();
    ctx.shadowBlur = 40;
    ctx.shadowColor = '#b8863a48';
    box(x - 1, y - 1, imageWidth + 2, imageHeight + 2, 15, '#211913', '#b79259');
    ctx.restore();
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(x, y, imageWidth, imageHeight, 14);
    ctx.clip();
    ctx.drawImage(dashboard, x, y, imageWidth, imageHeight);
    ctx.restore();
    text('COMMAND CENTER', 72, 230, 21, gold, 600);
    text('Inspect the', 69, 315, 66, cream, 590);
    text('decision trace.', 69, 388, 66, gold, 590);
    text('Proposals, findings, and outcomes.', 72, 448, 25, muted);
    ctx.restore();
  }

  function frame(t) {
    wash(t);
    chamber(t);
    if (t < 15.7) {
      ctx.save();
      ctx.globalAlpha = smooth(t / .5) * (1 - smooth((t - 15.12) / .58));
      steps(t);
      ctx.restore();
    }
    sceneLine(t, -.02, 3.55, 'EXAMPLE SCENARIO', [['After damage.', 70, cream]], ['The simulated system starts', 'at 20% health.']);
    sceneLine(t, 3.2, 7.53, 'AGENT PROPOSAL', [['Four plans.', 70, cream]], ['The agent submits four options', 'for the next action.']);
    sceneLine(t, 7.15, 11.92, 'VALOR DECISION', [['Restore', 70, cream], ['capacity.', 70, gold]], ['VALOR selects the highest scoring', 'plan that passes its policy.']);
    sceneLine(t, 11.55, 15.75, 'OBSERVED RESULT', [['20%  →  50%', 77, gold]], ['System health increases after', 'the simulated recovery action.']);
    commandCenter(t);
    brand();
    line(72, 652, 1208, 652, '#8e75523e');
    line(72, 652, 72 + 1136 * clamp(t / duration), 652, '#d5b1759f');
    text('AFTER DAMAGE  /  SEED 42', 72, 688, 14, muted, 570);
  }

  const mimeType = 'video/webm;codecs=vp9';
  if (!MediaRecorder.isTypeSupported(mimeType)) throw new Error('Chromium cannot encode VP9.');
  const stream = canvas.captureStream(30);
  const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 1250000 });
  const chunks = [];
  recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
  const finished = new Promise((resolve, reject) => {
    recorder.onerror = event => reject(event.error);
    recorder.onstop = async () => {
      const reader = new FileReader();
      reader.onerror = () => reject(reader.error);
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.readAsDataURL(new Blob(chunks, { type: 'video/webm' }));
    };
  });
  frame(0);
  recorder.start();
  const start = performance.now();
  const advance = stamp => {
    const t = (stamp - start) / 1000;
    if (t >= duration) { recorder.stop(); return; }
    frame(Math.max(0, t));
    requestAnimationFrame(advance);
  };
  requestAnimationFrame(advance);
  return finished;
}

async function main() {
  const [chromePath, screenshot] = process.argv.slice(2);
  if (!chromePath || !screenshot) throw new Error('Provide the Chrome executable and a real Command Center screenshot.');
  await fs.mkdir(artifacts, { recursive: true });
  const profile = await fs.mkdtemp(path.join(artifacts, 'demo-render-'));
  const chrome = spawn(chromePath, [
    '--headless', '--disable-background-networking', '--no-first-run', '--disable-extensions',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
    '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank',
  ], { windowsHide: true, stdio: 'ignore' });
  let socket;
  try {
    const activePort = path.join(profile, 'DevToolsActivePort');
    let target;
    for (let attempt = 0; attempt < 100 && !target; attempt++) {
      const marker = await fs.readFile(activePort, 'utf8').catch(() => '');
      if (marker) {
        const port = Number(marker.split(/\r?\n/)[0]);
        const tabs = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => []);
        target = tabs.find(tab => tab.type === 'page' && tab.url === 'about:blank');
      }
      if (!target) await delay(100);
    }
    if (!target) throw new Error('The isolated Chromium recorder did not launch.');
    const dataUrl = async (file, mime) => `data:${mime};base64,${(await fs.readFile(file)).toString('base64')}`;
    const [hero, dashboard] = await Promise.all([
      dataUrl(path.join(staticDir, 'supervision-cell.webp'), 'image/webp'),
      dataUrl(screenshot, 'image/png'),
    ]);
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    });
    const expression = `(${animate.toString()})(${JSON.stringify(hero)}, ${JSON.stringify(dashboard)})`;
    const result = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Landing film exceeded 60 seconds while rendering.')), 60000);
      socket.addEventListener('message', event => {
        const response = JSON.parse(event.data);
        if (response.id !== 1) return;
        clearTimeout(timeout);
        if (response.error || response.result?.exceptionDetails) reject(new Error(JSON.stringify(response.error || response.result.exceptionDetails)));
        else resolve(response.result.result.value);
      });
      socket.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression, awaitPromise: true, returnByValue: true } }));
    });
    await fs.writeFile(path.join(artifacts, 'landing-demo-unindexed.webm'), Buffer.from(result, 'base64'));
    console.log('Rendered artifacts/landing-demo-unindexed.webm. Remux with ffmpeg to record the duration and seek index.');
  } finally {
    socket?.close();
    chrome.kill();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
