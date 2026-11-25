// Automated browser tests for SOUND PLAYGROUND sketch 0.2.
// Usage: node tests/run_tests.cjs [--long]   (--long adds the full 3-minute recording)
// Needs: Playwright + Chromium, ffmpeg/ffprobe on PATH. Writes into tests/out/.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');

const DEMO = path.resolve(__dirname, '..', '..', '..', 'index.html');
const OUT = path.resolve(__dirname, 'out'); fs.mkdirSync(OUT, { recursive: true });
const URL = 'file://' + DEMO;
const LONG = process.argv.includes('--long');
const results = []; let failures = 0;
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail }); if (!ok) failures++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? '  — ' + detail : '')); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const NAMES = ['pulse', 'breath', 'resonance', 'movement'];

function measure(file) {
  const r = require('child_process').spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'volumedetect', '-f', 'null', '-'], { encoding: 'utf8' });
  const err = r.stderr;
  const time = [...err.matchAll(/time=(\d+):(\d+):([\d.]+)/g)].pop();
  const frames = [...err.matchAll(/frame=\s*(\d+)/g)].pop();
  const mean = /mean_volume: ([-\d.]+) dB/.exec(err), max = /max_volume: ([-\d.]+) dB/.exec(err);
  return { seconds: time ? (+time[1]) * 3600 + (+time[2]) * 60 + (+time[3]) : 0, frames: frames ? +frames[1] : 0, meanDb: mean ? +mean[1] : null, maxDb: max ? +max[1] : null };
}

async function freshPage(browser, opts = {}) {
  const context = await browser.newContext({ viewport: { width: 1300, height: 980 }, acceptDownloads: true, ...opts });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.type() + ': ' + m.text()); });
  await page.goto(URL);
  return { context, page, errors };
}
const st = page => page.evaluate(() => window.SoundPlaygroundTest.state());
async function padCentre(page, n) { const l = page.locator(`.pad[data-station="${n}"]`); await l.scrollIntoViewIfNeeded(); const b = await l.boundingBox(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }

async function downloadBoth(page, tag) {
  await page.waitForSelector('#dl-video', { timeout: 20000 });
  const files = {};
  for (const [id, ext] of [['#dl-video', null], ['#dl-log', 'json']]) {
    const [dl] = await Promise.all([page.waitForEvent('download'), page.click(id)]);
    const name = tag + '_' + dl.suggestedFilename();
    const p = path.join(OUT, name); await dl.saveAs(p); files[ext || 'video'] = p;
  }
  return files;
}
function verifyRecording(files, label, expectSec, tol) {
  const info = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_streams', '-of', 'json', files.video]).toString());
  const v = info.streams.find(s => s.codec_type === 'video'), a = info.streams.find(s => s.codec_type === 'audio');
  check(`${label}: file has a video stream`, v, v ? `${v.codec_name} ${v.width}x${v.height}` : 'none');
  check(`${label}: file has a stereo audio stream`, a && a.channels === 2, a ? `${a.codec_name} ${a.channels} ch ${a.sample_rate} Hz` : 'none');
  const m = measure(files.video);
  check(`${label}: decoded length ≈ ${expectSec}s`, Math.abs(m.seconds - expectSec) <= tol, `${m.seconds.toFixed(2)} s, ${m.frames} video frames`);
  check(`${label}: audio is audible and not clipped`, m.meanDb !== null && m.meanDb > -50 && m.maxDb < 0, `mean ${m.meanDb} dB, peak ${m.maxDb} dB`);
  const log = JSON.parse(fs.readFileSync(files.json, 'utf8'));
  const ev = log.events, ts = ev.map(e => e.t);
  const mono = ts.every((t, i) => i === 0 || t >= ts[i - 1]);
  check(`${label}: gesture log has timestamped events in order`, ev.length > 3 && mono && ev[0].type === 'initial', `${ev.length} events, last t=${ts[ts.length - 1]}`);
  const downs = ev.filter(e => e.type === 'padDown').length, ups = ev.filter(e => e.type === 'padUp').length;
  return { m, log, downs, ups };
}

(async () => {
  const browser = await chromium.launch();
  // ---------- 1. load, layout, no errors ----------
  {
    const { context, page, errors } = await freshPage(browser);
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, 'desktop_initial.png'), fullPage: true });
    const s = await st(page);
    check('Page loads with no console errors', errors.length === 0, errors.join(' | '));
    check('No audio context before a user gesture', s.audio === 'none', s.audio);
    check('Four pads and four rotary dials present', (await page.locator('.pad').count()) === 4 && (await page.locator('[role=slider].dial').count()) === 4);
    await context.close();
  }
  for (const [w, h, name] of [[390, 844, 'mobile'], [820, 1180, 'tablet']]) {
    const { context, page } = await freshPage(browser, { viewport: { width: w, height: h }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 });
    await page.waitForTimeout(300);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(`No horizontal scroll at ${w}px (${name})`, overflow <= 0, `overflow ${overflow}px`);
    await page.screenshot({ path: path.join(OUT, name + '_initial.png'), fullPage: true });
    await context.close();
  }

  // ---------- 2. audio start + core interaction ----------
  const { context, page, errors } = await freshPage(browser, { hasTouch: true });
  await page.click('#start');
  await page.waitForFunction(() => window.SoundPlaygroundTest.state().audio === 'running', null, { timeout: 5000 }).catch(() => {});
  let s = await st(page);
  check('Enable sound starts the AudioContext', s.audio === 'running', s.audio);
  await page.click('#start'); await page.click('#start'); await page.waitForTimeout(200);
  s = await st(page);
  check('Pressing Enable again keeps one running context and correct status', s.audio === 'running' && (await page.textContent('#start')) === 'Sound on', await page.textContent('#status'));

  // mouse
  let c = await padCentre(page, 'pulse');
  await page.mouse.move(c.x, c.y); await page.mouse.down(); await page.waitForTimeout(1500);
  s = await st(page);
  check('Mouse hold activates PULSE and schedules sound', s.active.pulse && s.liveSources > 0, `liveSources ${s.liveSources}`);
  await page.mouse.up(); await page.waitForTimeout(50);
  s = await st(page);
  check('Mouse release stops PULSE', !s.active.pulse && s.held.pulse === 0);

  // keyboard, including auto-repeat
  await page.keyboard.down('Digit2'); await page.keyboard.down('Digit2'); await page.waitForTimeout(800);
  s = await st(page);
  check('Holding key 2 sustains BREATH (repeat ignored)', s.active.breath && s.breathVoice && s.held.breath === 1);
  await page.keyboard.up('Digit2'); await page.waitForTimeout(50);
  s = await st(page);
  check('Releasing key 2 releases BREATH', !s.active.breath && !s.breathVoice);
  for (const k of ['Digit1', 'Digit3', 'Digit4']) await page.keyboard.down(k);
  await page.waitForTimeout(600); s = await st(page);
  check('Keys 1, 3, 4 held together all play', s.active.pulse && s.active.resonance && s.active.movement);
  for (const k of ['Digit1', 'Digit3', 'Digit4']) await page.keyboard.up(k);
  // focused pad + space
  await page.focus('.pad[data-station="resonance"]'); await page.keyboard.down('Space'); await page.waitForTimeout(200);
  s = await st(page); const spaceOn = s.active.resonance;
  await page.keyboard.up('Space'); await page.waitForTimeout(50); s = await st(page);
  check('Focused pad plays with Space (keyboard accessibility)', spaceOn && !s.active.resonance);

  // multitouch: four simultaneous touch points through CDP
  const cdp = await context.newCDPSession(page);
  const pts = []; for (const [i, n] of NAMES.entries()) { const p = await padCentre(page, n); pts.push({ x: p.x, y: p.y, id: i + 1 }); }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [pts[0]] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts.slice(0, 2) });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts.slice(0, 3) });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts });
  await page.waitForTimeout(1500);
  s = await st(page);
  check('Four simultaneous touches: all four stations active', NAMES.every(n => s.active[n]), JSON.stringify(s.active));
  check('Players counter shows 4 of 4', (await page.textContent('#players')) === '4 of 4 playing');
  await page.screenshot({ path: path.join(OUT, 'desktop_four_players.png') });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: pts.slice(2) }); // CDP: listed points are the ones lifted (fingers 3 and 4)
  await page.waitForTimeout(100); s = await st(page);
  check('Lifting two fingers releases only those two stations', s.active.pulse && s.active.breath && !s.active.resonance && !s.active.movement, JSON.stringify(s.active));
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(100); s = await st(page);
  check('Lifting all fingers releases all stations', NAMES.every(n => !s.active[n]));

  // dials: mouse rotation, wheel, keys
  await page.locator('#dial-resonance').scrollIntoViewIfNeeded(); const d = await page.locator('#dial-resonance').boundingBox(); const dc = { x: d.x + d.width / 2, y: d.y + d.height / 2 };
  const before = (await st(page)).knobs.resonance;
  await page.mouse.move(dc.x - 30, dc.y); await page.mouse.down();
  for (let a = -90; a <= 0; a += 10) await page.mouse.move(dc.x + 30 * Math.sin(a * Math.PI / 180), dc.y - 30 * Math.cos(a * Math.PI / 180));
  await page.mouse.up();
  let after = (await st(page)).knobs.resonance;
  check('Dragging the RESONANCE dial clockwise 90° raises it by ~1/3', Math.abs(after - before - 1 / 3) < .05, `${before.toFixed(2)} → ${after.toFixed(2)}`);
  await page.focus('#dial-pulse'); await page.keyboard.press('End'); s = await st(page);
  const endOk = s.knobs.pulse === 1;
  await page.keyboard.press('ArrowDown'); s = await st(page);
  check('Dial keyboard control (End, ArrowDown) works', endOk && Math.abs(s.knobs.pulse - .98) < 1e-6 && (await page.getAttribute('#dial-pulse', 'aria-valuenow')) === '98');
  await page.mouse.move((await page.locator('#dial-movement').boundingBox()).x + 30, (await page.locator('#dial-movement').boundingBox()).y + 30);
  const mv0 = (await st(page)).knobs.movement; await page.mouse.wheel(0, -100); await page.waitForTimeout(50);
  check('Mouse wheel turns a dial', (await st(page)).knobs.movement > mv0);

  // ---------- 3. clipping: everything at maximum ----------
  await page.evaluate(() => { const v = document.getElementById('volume'); v.value = 100; v.dispatchEvent(new Event('input')); });
  for (const n of NAMES) { await page.focus('#dial-' + n); await page.keyboard.press('End'); }
  await page.focus('#dial-movement'); await page.keyboard.press('Home');
  await page.locator('body').click({ position: { x: 5, y: 5 } });
  await page.evaluate(() => window.SoundPlaygroundTest.resetPeaks());
  for (const k of ['Digit1', 'Digit2', 'Digit3', 'Digit4']) await page.keyboard.down(k);
  await page.waitForTimeout(12000);
  s = await st(page);
  check('All four voices at max volume and max dials: output never reaches full scale', s.peaks.post < .999 && s.peaks.clipped === 0, `post-limiter peak ${s.peaks.post.toFixed(3)} (${(20 * Math.log10(s.peaks.post)).toFixed(1)} dBFS), pre-limiter peak ${s.peaks.pre.toFixed(3)}, live sources ${s.liveSources}`);
  check('Voice count stays bounded under full load', s.liveSources < 220, `${s.liveSources} live sources`);
  for (const k of ['Digit1', 'Digit2', 'Digit3', 'Digit4']) await page.keyboard.up(k);
  await page.evaluate(() => { const v = document.getElementById('volume'); v.value = 70; v.dispatchEvent(new Event('input')); });
  await page.click('#reset');

  // ---------- 4. stuck-note stress ----------
  const centres = {}; for (const n of NAMES) centres[n] = await padCentre(page, n);
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 300; i++) {
    const n = NAMES[Math.floor(rnd() * 4)], id = 1 + Math.floor(rnd() * 6), kind = rnd();
    const ev = kind < .45 ? 'pointerdown' : kind < .8 ? 'pointerup' : kind < .9 ? 'lostpointercapture' : 'pointercancel';
    await page.locator(`.pad[data-station="${n}"]`).dispatchEvent(ev, { pointerId: id, pointerType: 'touch', isPrimary: id === 1, bubbles: true });
    if (rnd() < .2) await page.keyboard.down(['Digit1', 'Digit2', 'Digit3', 'Digit4'][Math.floor(rnd() * 4)]);
    if (rnd() < .25) for (const k of ['Digit1', 'Digit2', 'Digit3', 'Digit4']) await page.keyboard.up(k);
  }
  // end every pointer the stress test may have left down, then all keys
  for (const n of NAMES) for (let id = 1; id <= 6; id++) await page.locator(`.pad[data-station="${n}"]`).dispatchEvent('pointerup', { pointerId: id, pointerType: 'touch', bubbles: true });
  for (const k of ['Digit1', 'Digit2', 'Digit3', 'Digit4']) await page.keyboard.up(k);
  await page.waitForTimeout(4000);
  s = await st(page);
  check('After 300 random press/release/cancel events: no station stuck', NAMES.every(n => !s.active[n] && s.held[n] === 0) && !s.breathVoice, JSON.stringify(s.held));
  check('After release, every audio source has ended (no stuck notes)', s.liveSources === 0, `${s.liveSources} live sources`);
  // blur safety
  await page.keyboard.down('Digit2'); await page.waitForTimeout(200);
  await page.evaluate(() => window.dispatchEvent(new Event('blur'))); await page.waitForTimeout(3000);
  s = await st(page);
  check('Window blur while holding releases the note', !s.active.breath && !s.breathVoice && s.liveSources === 0, `live ${s.liveSources}`);
  await page.keyboard.up('Digit2');

  // ---------- 5. recording: stop early ----------
  await page.click('#rec30'); await page.waitForTimeout(300);
  check('Recording starts', (await st(page)).recording);
  await page.keyboard.down('Digit1'); await page.keyboard.down('Digit2'); await page.waitForTimeout(2500);
  await page.keyboard.down('Digit3'); await page.waitForTimeout(1500); await page.keyboard.up('Digit3');
  await page.keyboard.down('Digit4'); await page.waitForTimeout(1500);
  for (const k of ['Digit1', 'Digit2', 'Digit4']) await page.keyboard.up(k);
  await page.waitForTimeout(500);
  await page.click('#recstop');
  const early = await downloadBoth(page, 'stop_early');
  const r1 = verifyRecording(early, 'Stopped-early recording', 6.0, 1.0);
  check('Stopped-early: log has pad downs/ups for played stations and stopReason user', r1.downs >= 4 && r1.ups >= 4 && r1.log.stopReason === 'user', `${r1.downs} down / ${r1.ups} up`);

  // ---------- 6. full 30-second recording ----------
  await page.click('#rec30'); const t0 = Date.now();
  const score = [[0, 'Digit1', 1], [0, 'Digit2', 1], [4000, 'Digit3', 1], [8000, 'Digit4', 1], [12000, 'Digit3', 0], [16000, 'Digit2', 0], [20000, 'Digit4', 0], [26000, 'Digit1', 0]];
  for (const [at, k, down] of score) { const w = at - (Date.now() - t0); if (w > 0) await sleep(w); down ? await page.keyboard.down(k) : await page.keyboard.up(k); }
  await page.screenshot({ path: path.join(OUT, 'desktop_recording.png') });
  const full = await downloadBoth(page, 'full30');
  const r2 = verifyRecording(full, '30-second recording', 30.0, 1.2);
  check('30-second recording stops itself (stopReason timer)', r2.log.stopReason === 'timer' && Math.abs(r2.log.durationSeconds - 30) < .6, `durationSeconds ${r2.log.durationSeconds}`);
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-ss', '14', '-i', full.video, '-frames:v', '1', path.join(OUT, 'recording_frame_14s.png')]);

  check('No console errors during the whole interactive session', errors.length === 0, errors.join(' | '));
  await context.close();

  // ---------- 7. first gesture is a pad (no Enable click) ----------
  {
    const { context, page, errors } = await freshPage(browser);
    const p = await padCentre(page, 'resonance');
    await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.waitForTimeout(600);
    const s = await st(page); await page.mouse.up();
    check('Pressing a pad first starts audio and plays the note', s.audio === 'running' && s.liveSources > 0, `${s.audio}, ${s.liveSources} sources`);
    await context.close();
  }

  // ---------- 8. optional full 3-minute recording ----------
  if (LONG) {
    const { context, page, errors } = await freshPage(browser);
    await page.click('#start'); await page.click('#rec180'); const t0 = Date.now();
    const keys = ['Digit1', 'Digit2', 'Digit3', 'Digit4'];
    while (Date.now() - t0 < 178000) {        // rotate players on and off every ~7 s
      const i = Math.floor((Date.now() - t0) / 7000);
      for (const [j, k] of keys.entries()) { ((i + j) % 3 !== 0) ? await page.keyboard.down(k) : await page.keyboard.up(k); }
      await sleep(1000);
    }
    for (const k of keys) await page.keyboard.up(k);
    const long = await downloadBoth(page, 'full180');
    const r3 = verifyRecording(long, '3-minute recording', 180.0, 2.0);
    check('3-minute recording stops itself (stopReason timer)', r3.log.stopReason === 'timer', `durationSeconds ${r3.log.durationSeconds}, ${r3.log.events.length} events`);
    check('No console errors during the 3-minute session', errors.length === 0, errors.join(' | '));
    await context.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify({ when: new Date().toISOString(), long: LONG, failures, results }, null, 2));
  console.log(`\n${results.length - failures}/${results.length} checks passed`);
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
