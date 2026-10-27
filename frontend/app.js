/* ─────────────────────────────────────────────────────────
   app.js — QFF 2026 Quantum Traffic Intelligence Demo v2
   Exact Mumbai road network (V1–V8, 11 forward edges)
   10 predefined scenarios · SVG dual graphs · Continuous loop
   ───────────────────────────────────────────────────────── */

// ══════════════════════════════════════════════════════════
// 1. BACKGROUND PARTICLE SYSTEM
// ══════════════════════════════════════════════════════════
(function initParticles() {
  const canvas = document.getElementById('bg-canvas');
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  function mkP() {
    return { x: Math.random()*W, y: Math.random()*H, r: Math.random()*2+0.5,
      vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
      a: Math.random()*0.35+0.08, hue: Math.random()*60+240 };
  }
  for (let i=0;i<110;i++) particles.push(mkP());

  function draw() {
    ctx.clearRect(0,0,W,H);
    const g = ctx.createRadialGradient(W*.5,H*.3,0,W*.5,H*.3,W*.8);
    g.addColorStop(0,'rgba(230,210,255,0.3)'); g.addColorStop(1,'rgba(200,180,255,0.04)');
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
    for (let i=0;i<particles.length;i++) {
      for (let j=i+1;j<particles.length;j++) {
        const dx=particles[i].x-particles[j].x, dy=particles[i].y-particles[j].y;
        const d=Math.sqrt(dx*dx+dy*dy);
        if (d<110) { ctx.beginPath(); ctx.moveTo(particles[i].x,particles[i].y);
          ctx.lineTo(particles[j].x,particles[j].y);
          ctx.strokeStyle=`hsla(270,70%,60%,${(1-d/110)*0.1})`; ctx.lineWidth=0.8; ctx.stroke(); }
      }
    }
    particles.forEach(p => {
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`hsla(${p.hue},80%,65%,${p.a})`; ctx.fill();
      p.x+=p.vx; p.y+=p.vy;
      if (p.x<0||p.x>W) p.vx*=-1; if (p.y<0||p.y>H) p.vy*=-1;
    });
    requestAnimationFrame(draw);
  }
  draw();
})();

// ══════════════════════════════════════════════════════════
// 2. FADE-UP OBSERVER
// ══════════════════════════════════════════════════════════
document.querySelectorAll('.step-card, .section-title, .section-desc, .loop-diagram, .circuit-container, .datacollect-grid, .feature-fusion-wrap, .network-graph-banner').forEach(el => el.classList.add('fade-up'));
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
}, { threshold: 0.12 });
document.querySelectorAll('.fade-up').forEach(el => io.observe(el));

// ══════════════════════════════════════════════════════════
// 2B. CCTV COMPUTER VISION SIMULATION & TRAFFIC MANAGER CONSOLE
// ══════════════════════════════════════════════════════════
const CAM_PROFILES = [
  { id: 'CAM-01', name: 'MUMBAI ARTERIAL V1→V2', lanes: 3, speedRange: [40, 58], flowBase: 1840, density: 14, edgeIdx: 0 },
  { id: 'CAM-02', name: 'SOUTH SPINE V4→V5',     lanes: 3, speedRange: [32, 48], flowBase: 2150, density: 16, edgeIdx: 6 },
  { id: 'CAM-03', name: 'V2 INTERSECTION HUB',    lanes: 4, speedRange: [20, 36], flowBase: 2420, density: 18, isHub: true, edgeIdx: 1 },
  { id: 'CAM-04', name: 'EXPRESSWAY LINK V6→V7',  lanes: 3, speedRange: [55, 78], flowBase: 1620, density: 10, edgeIdx: 9 },
];

let activeCamIdx = 0;
let cctvVehicles = [];
let cctvVehicleCounter = 0;
let lastTripwireFlash = 0;
let cctvNextId = 101;

function initCCTVAnimation() {
  const canvas = document.getElementById('cctv-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = 600, H = 340;

  function spawnVehicle(forceX) {
    const cam = CAM_PROFILES[activeCamIdx];
    const types = [
      { type: 'CAR',  w: 24, h: 14, col: '#38bdf8', prob: 0.55 },
      { type: 'SUV',  w: 26, h: 15, col: '#34d399', prob: 0.20 },
      { type: 'BUS',  w: 42, h: 17, col: '#fbbf24', prob: 0.12 },
      { type: '2W',   w: 14, h: 8,  col: '#f472b6', prob: 0.13 },
    ];
    const rand = Math.random();
    let cumulative = 0;
    let chosen = types[0];
    for (const t of types) {
      cumulative += t.prob;
      if (rand <= cumulative) { chosen = t; break; }
    }

    const laneIndex = Math.floor(Math.random() * cam.lanes);
    const speedKmh = cam.speedRange[0] + Math.random() * (cam.speedRange[1] - cam.speedRange[0]);
    const vx = (speedKmh / 60) * 1.6; // px per frame

    let y;
    if (cam.isHub) {
      // Junction cross roads
      const isVertical = Math.random() > 0.5;
      if (isVertical) {
        return {
          id: cctvNextId++,
          type: chosen.type,
          w: chosen.h,
          h: chosen.w,
          col: chosen.col,
          x: 270 + (Math.random() > 0.5 ? 20 : -20),
          y: forceX !== undefined ? forceX : -50,
          vx: 0,
          vy: (speedKmh / 60) * 1.5,
          speedKmh: Math.round(speedKmh),
          conf: Math.round(88 + Math.random() * 11),
          trail: [],
          crossedTripwire: false,
          isVertical: true
        };
      }
      y = 145 + (laneIndex - 1.5) * 26;
    } else {
      const roadTop = 80;
      const laneH = 44;
      y = roadTop + laneIndex * laneH + laneH / 2;
    }

    return {
      id: cctvNextId++,
      type: chosen.type,
      w: chosen.w,
      h: chosen.h,
      col: chosen.col,
      x: forceX !== undefined ? forceX : -60,
      y: y,
      vx: vx,
      vy: 0,
      speedKmh: Math.round(speedKmh),
      conf: Math.round(88 + Math.random() * 11),
      trail: [],
      crossedTripwire: false,
      isVertical: false
    };
  }

  // Prepopulate vehicles across canvas
  cctvVehicles = [];
  for (let i = 0; i < CAM_PROFILES[activeCamIdx].density; i++) {
    cctvVehicles.push(spawnVehicle(Math.random() * (W + 60) - 30));
  }

  const tripwireX = 380; // Virtual counting line

  function render() {
    ctx.clearRect(0, 0, W, H);
    const cam = CAM_PROFILES[activeCamIdx];

    // 1. Road Background & Markings
    ctx.fillStyle = '#12101e';
    ctx.fillRect(0, 0, W, H);

    if (cam.isHub) {
      // 4-Way Intersection
      ctx.fillStyle = '#1e1a2f';
      ctx.fillRect(0, 100, W, 140); // E-W road
      ctx.fillRect(220, 0, 160, H); // N-S road

      // Intersection Box
      ctx.strokeStyle = 'rgba(251,191,36,0.5)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 6]);
      ctx.strokeRect(220, 100, 160, 140);
      ctx.setLineDash([]);

      // Zebra Crossings
      ctx.fillStyle = 'rgba(255,255,255,0.2)';
      for (let i = 0; i < 7; i++) {
        ctx.fillRect(195, 105 + i * 18, 18, 10); // West zebra
        ctx.fillRect(387, 105 + i * 18, 18, 10); // East zebra
      }
    } else {
      // Arterial / Spine / Expressway Road
      const roadTop = 60, roadH = cam.lanes * 44 + 40;
      ctx.fillStyle = '#181528';
      ctx.fillRect(0, roadTop, W, roadH);

      // Curbs
      ctx.fillStyle = 'rgba(168,85,247,0.3)';
      ctx.fillRect(0, roadTop, W, 4);
      ctx.fillRect(0, roadTop + roadH - 4, W, 4);

      // Dashed lane lines
      ctx.strokeStyle = 'rgba(255,255,255,0.25)';
      ctx.lineWidth = 2;
      ctx.setLineDash([14, 12]);
      for (let l = 1; l < cam.lanes; l++) {
        const ly = roadTop + 20 + l * 44;
        ctx.beginPath(); ctx.moveTo(0, ly); ctx.lineTo(W, ly); ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    // 2. Tripwire Virtual Counting Line
    const isFlashing = (Date.now() - lastTripwireFlash) < 220;
    ctx.strokeStyle = isFlashing ? '#34d399' : 'rgba(56,189,248,0.6)';
    ctx.lineWidth = isFlashing ? 3.5 : 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(tripwireX, 30);
    ctx.lineTo(tripwireX, H - 30);
    ctx.stroke();
    ctx.setLineDash([]);

    // Tripwire tag
    ctx.fillStyle = isFlashing ? '#34d399' : '#38bdf8';
    ctx.font = '700 9px JetBrains Mono, monospace';
    ctx.fillText('TRIPWIRE [OPTICAL COUNT]', tripwireX - 65, 24);

    if (isFlashing) {
      ctx.fillStyle = 'rgba(52,211,153,0.15)';
      ctx.fillRect(tripwireX - 15, 30, 30, H - 60);
    }

    // 3. Vehicles & Computer Vision Bounding Boxes
    let currentInFrameCount = 0;
    let speedSum = 0;

    for (let i = cctvVehicles.length - 1; i >= 0; i--) {
      const v = cctvVehicles[i];
      if (v.isVertical) {
        v.y += v.vy;
      } else {
        v.x += v.vx;
      }

      // Check Tripwire crossing
      if (!v.crossedTripwire && v.x >= tripwireX && v.x - v.vx < tripwireX) {
        v.crossedTripwire = true;
        cctvVehicleCounter++;
        lastTripwireFlash = Date.now();
      }

      // Record trajectory trail
      if (Math.random() > 0.4) {
        v.trail.push({ x: v.x, y: v.y });
        if (v.trail.length > 8) v.trail.shift();
      }

      // Remove out of bounds & respawn
      if (v.x > W + 60 || v.y > H + 60) {
        cctvVehicles.splice(i, 1);
        cctvVehicles.push(spawnVehicle());
        continue;
      }

      // Draw Trajectory Trail
      if (v.trail.length > 1) {
        ctx.beginPath();
        ctx.moveTo(v.trail[0].x, v.trail[0].y);
        for (let t = 1; t < v.trail.length; t++) {
          ctx.lineTo(v.trail[t].x, v.trail[t].y);
        }
        ctx.strokeStyle = `rgba(56,189,248,0.2)`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Draw Vehicle Body
      ctx.save();
      ctx.translate(v.x, v.y);
      ctx.fillStyle = v.col;
      ctx.shadowColor = v.col;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.roundRect(-v.w/2, -v.h/2, v.w, v.h, 3);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Windshield / Cabin
      ctx.fillStyle = '#0a0515';
      if (!v.isVertical) {
        ctx.fillRect(-v.w * 0.2, -v.h * 0.35, v.w * 0.45, v.h * 0.7);
        // Headlights
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(v.w/2 - 1, -v.h/2 + 2, 2, 3);
        ctx.fillRect(v.w/2 - 1, v.h/2 - 5, 2, 3);
      } else {
        ctx.fillRect(-v.w * 0.35, -v.h * 0.2, v.w * 0.7, v.h * 0.45);
        // Headlights
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(-v.w/2 + 2, v.h/2 - 1, 3, 2);
        ctx.fillRect(v.w/2 - 5, v.h/2 - 1, 3, 2);
      }
      ctx.restore();

      // Draw Computer Vision YOLO Bounding Box
      const pad = 4;
      const bx = v.x - v.w/2 - pad;
      const by = v.y - v.h/2 - pad;
      const bw = v.w + pad * 2;
      const bh = v.h + pad * 2;

      ctx.strokeStyle = v.col;
      ctx.lineWidth = 1.2;
      ctx.strokeRect(bx, by, bw, bh);

      // Corner notch accents (YOLO visual cue)
      const notch = 3;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      // Top-Left
      ctx.moveTo(bx, by + notch); ctx.lineTo(bx, by); ctx.lineTo(bx + notch, by);
      // Top-Right
      ctx.moveTo(bx + bw - notch, by); ctx.lineTo(bx + bw, by); ctx.lineTo(bx + bw, by + notch);
      // Bottom-Left
      ctx.moveTo(bx, by + bh - notch); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + notch, by + bh);
      // Bottom-Right
      ctx.moveTo(bx + bw - notch, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.lineTo(bx + bw, by + bh - notch);
      ctx.stroke();

      // YOLO Tag Label: [CLASS #ID CONF% SPEED]
      ctx.fillStyle = 'rgba(10,5,25,0.88)';
      ctx.fillRect(bx, by - 12, bw + 18, 11);
      ctx.fillStyle = v.col;
      ctx.font = '700 7.5px JetBrains Mono, monospace';
      ctx.fillText(`${v.type} #${v.id} ${v.speedKmh}k`, bx + 2, by - 3);

      currentInFrameCount++;
      speedSum += v.speedKmh;
    }

    // 4. Update HUD Telemetry
    const avgSpeed = currentInFrameCount ? Math.round(speedSum / currentInFrameCount) : 45;
    const computedFlow = Math.round(cam.flowBase + (currentInFrameCount - 12) * 45 + (Math.random() - 0.5) * 30);

    const hudCountEl = document.getElementById('hud-veh-count');
    const hudFlowEl  = document.getElementById('hud-flow-val');
    const hudSpeedEl = document.getElementById('hud-speed-val');

    if (hudCountEl) hudCountEl.textContent = currentInFrameCount;
    if (hudFlowEl)  hudFlowEl.textContent  = `${computedFlow.toLocaleString()} v/h`;
    if (hudSpeedEl) hudSpeedEl.textContent = `${avgSpeed} km/h`;

    requestAnimationFrame(render);
  }

  render();

  // Camera switcher buttons
  const camBtns = document.querySelectorAll('.cam-btn');
  camBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      camBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCamIdx = parseInt(btn.dataset.cam);
      const cam = CAM_PROFILES[activeCamIdx];

      const hudCamId = document.getElementById('hud-cam-id');
      if (hudCamId) hudCamId.textContent = `${cam.id} · ${cam.name}`;

      // Reset and respawn vehicles for this camera
      cctvVehicles = [];
      for (let i = 0; i < cam.density; i++) {
        cctvVehicles.push(spawnVehicle(Math.random() * (W + 60) - 30));
      }

      // Sync Traffic Manager selector to corresponding edge
      const tmSelect = document.getElementById('tm-segment-select');
      if (tmSelect) {
        tmSelect.value = cam.edgeIdx;
        tmSelect.dispatchEvent(new Event('change'));
      }
    });
  });
}

// ══════════════════════════════════════════════════════════
// 2C. TRAFFIC MANAGER CONTROL CONSOLE LOGIC
// ══════════════════════════════════════════════════════════
// Edge infrastructure defaults
const EDGE_INFRA = [
  { len: 3500, cap: 4000, speed: 70, mu: 1.0 }, // V1->V2 (WEH Main)
  { len: 2800, cap: 3200, speed: 60, mu: 1.0 }, // V1->V4
  { len: 4500, cap: 3000, speed: 60, mu: 1.0 }, // V1->V5
  { len: 4000, cap: 3500, speed: 60, mu: 1.0 }, // V2->V3
  { len: 1800, cap: 2800, speed: 50, mu: 1.0 }, // V2->V5
  { len: 2500, cap: 4200, speed: 80, mu: 1.0 }, // V3->V8 (Sea Link Corridor)
  { len: 1500, cap: 2500, speed: 50, mu: 1.0 }, // V4->V5
  { len: 2000, cap: 3600, speed: 50, mu: 1.0 }, // V5->V6 (BKC-Sion Link)
  { len: 2200, cap: 2400, speed: 50, mu: 1.0 }, // V6->V2 (Loop)
  { len: 3000, cap: 2800, speed: 50, mu: 1.0 }, // V6->V7
  { len: 2100, cap: 3100, speed: 50, mu: 1.0 }, // V7->V3
];

let currentMu = 1.0;

function initTrafficManagerConsole() {
  const segSelect  = document.getElementById('tm-segment-select');
  const sliderLen  = document.getElementById('slider-road-length');
  const sliderCap  = document.getElementById('slider-capacity');
  const sliderSpd  = document.getElementById('slider-speed-limit');
  const valLen     = document.getElementById('val-road-length');
  const valCap     = document.getElementById('val-capacity');
  const valSpd     = document.getElementById('val-speed-limit');
  const satEl      = document.getElementById('tdb-sat');
  const timeEl     = document.getElementById('tdb-time');
  const densEl     = document.getElementById('tdb-dens');

  function updateDerived() {
    const L = parseInt(sliderLen.value);
    const C = parseInt(sliderCap.value);
    const V = parseInt(sliderSpd.value);
    const mu = currentMu;

    valLen.textContent = `${L.toLocaleString()} m`;
    valCap.textContent = `${C.toLocaleString()} veh/hr`;
    valSpd.textContent = `${V} km/h`;

    // Greenshields & fundamental diagram physics
    const satDensity = Math.round(C / (V * mu * 0.22));
    const travelTime = ((L / 1000) / (V * mu) * 3600).toFixed(1);
    const critDensity = (satDensity * 0.28).toFixed(1);

    if (satEl) satEl.textContent   = `${satDensity} veh/km`;
    if (timeEl) timeEl.textContent = `${travelTime} s`;
    if (densEl) densEl.textContent = `${critDensity} veh/km`;

    // Sync updated capacity into FORWARD_EDGES so live simulation reflects manager inputs!
    const edgeIdx = parseInt(segSelect.value);
    if (FORWARD_EDGES[edgeIdx]) {
      FORWARD_EDGES[edgeIdx][3] = C;
      EDGE_INFRA[edgeIdx] = { ...EDGE_INFRA[edgeIdx], len: L, cap: C, speed: V, mu };
    }
  }

  if (segSelect) {
    segSelect.addEventListener('change', () => {
      const idx = parseInt(segSelect.value);
      const infra = EDGE_INFRA[idx];
      sliderLen.value = infra.len;
      sliderCap.value = infra.cap;
      sliderSpd.value = infra.speed;
      updateDerived();
    });
  }

  if (sliderLen) sliderLen.addEventListener('input', updateDerived);
  if (sliderCap) sliderCap.addEventListener('input', updateDerived);
  if (sliderSpd) sliderSpd.addEventListener('input', updateDerived);

  // Weather pills
  const pills = document.querySelectorAll('.tm-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentMu = parseFloat(pill.dataset.mu);
      updateDerived();
    });
  });

  updateDerived();
}


// ══════════════════════════════════════════════════════════
// 3. EXACT NETWORK TOPOLOGY (from train_stqgcn.py)
// ══════════════════════════════════════════════════════════
// Nodes: 0=V1, 1=V2, 2=V3, 3=V4, 4=V5, 5=V6, 6=V7, 7=V8
// FORWARD_EDGES from codebase:
//   (0,1),(0,3),(0,4) → V1→V2, V1→V4, V1→V5
//   (1,2),(1,4)       → V2→V3, V2→V5
//   (2,7)             → V3→V8
//   (3,4)             → V4→V5
//   (4,5)             → V5→V6
//   (5,1),(5,6)       → V6→V2, V6→V7
//   (6,2)             → V7→V3

const NODES = [
  { id: 0, label: 'V1', x: 70,  y: 80  },
  { id: 1, label: 'V2', x: 210, y: 80  },
  { id: 2, label: 'V3', x: 350, y: 80  },
  { id: 3, label: 'V4', x: 70,  y: 200 },
  { id: 4, label: 'V5', x: 210, y: 200 },
  { id: 5, label: 'V6', x: 350, y: 200 },
  { id: 6, label: 'V7', x: 490, y: 200 },
  { id: 7, label: 'V8', x: 490, y: 80  },
];

const NODE_LABELS = ['North Hub', 'Central-North', 'East-North', 'West-South', 'Central-South', 'East-South', 'South-East', 'Far-East'];

// 11 forward directed edges [src, dst, road_name, capacity]
const FORWARD_EDGES = [
  [0, 1, 'V1→V2', 4000],
  [0, 3, 'V1→V4', 3200],
  [0, 4, 'V1→V5', 3000],
  [1, 2, 'V2→V3', 3500],
  [1, 4, 'V2→V5', 2800],
  [2, 7, 'V3→V8', 4200],
  [3, 4, 'V4→V5', 2500],
  [4, 5, 'V5→V6', 3600],
  [5, 1, 'V6→V2', 2400],
  [5, 6, 'V6→V7', 2800],
  [6, 2, 'V7→V3', 3100],
];

const API_BASE_URL = window.QFF_API_BASE_URL || (window.location.port === '80' ? '/api' : 'http://localhost:8000');
let backendNetwork = null;

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Backend request failed (${response.status})`);
  }
  return response.json();
}

function getCapacity(edgeName) {
  const local = FORWARD_EDGES.find(e => e[2] === edgeName || e[2].split('→').reverse().join('→') === edgeName);
  if (local) return local[3];
  return backendNetwork?.edges?.find(e => e.id === edgeName)?.capacity ?? 1800;
}

// Reverse edges (bidirectional)
const REVERSE_EDGES = FORWARD_EDGES.map(([s, d, name, cap]) => [d, s, name.split('→').reverse().join('→'), cap]);
const ALL_EDGES = [...FORWARD_EDGES, ...REVERSE_EDGES];

// ══════════════════════════════════════════════════════════
// 4. 10 PREDEFINED TRAFFIC SCENARIOS
// ══════════════════════════════════════════════════════════
// occupancy[i] is the base occupancy for forward edge i (0-10)
// >0.60 = congested, 0.45-0.60 = moderate, <0.45 = free
const TRAFFIC_SCENARIOS = [
  {
    id: 1, name: 'Single Arterial Bottleneck', pattern: 'Morning peak on V1→V2 main corridor',
    desc: 'Heavy inbound commute on the northern arterial',
    occ: [0.84, 0.35, 0.32, 0.38, 0.30, 0.28, 0.33, 0.36, 0.41, 0.38, 0.31],
  },
  {
    id: 2, name: 'Adjacent Dual Bottleneck', pattern: 'V4→V5 and V5→V6 surge',
    desc: 'Cascade congestion in the central-south spine',
    occ: [0.38, 0.32, 0.79, 0.35, 0.28, 0.29, 0.82, 0.78, 0.34, 0.36, 0.30],
  },
  {
    id: 3, name: 'Hub Junction Overload', pattern: 'V2 intersection overload',
    desc: 'Central-north hub saturated from multiple feeders',
    occ: [0.81, 0.34, 0.35, 0.85, 0.77, 0.31, 0.36, 0.34, 0.30, 0.32, 0.28],
  },
  {
    id: 4, name: 'Radial Inbound Commute', pattern: 'V1→V2 and V2→V3 peak',
    desc: 'Morning rush funnelling through north corridor',
    occ: [0.83, 0.36, 0.31, 0.80, 0.33, 0.29, 0.35, 0.34, 0.30, 0.31, 0.28],
  },
  {
    id: 5, name: 'Stadium Event Exit Rush', pattern: 'V5→V6 and V6→V7 exit surge',
    desc: 'Post-event mass egress through south-east corridor',
    occ: [0.30, 0.28, 0.31, 0.29, 0.33, 0.31, 0.32, 0.86, 0.34, 0.82, 0.77],
  },
  {
    id: 6, name: 'Commercial District Rush', pattern: 'V2→V5 and V6→V2 congestion',
    desc: 'Lunchtime commercial area peak with recirculation',
    occ: [0.38, 0.31, 0.34, 0.79, 0.75, 0.30, 0.35, 0.38, 0.82, 0.36, 0.31],
  },
  {
    id: 7, name: 'Cross-Town Transit Surge', pattern: 'V3→V8 and V7→V3 flow',
    desc: 'Long-distance cross-town movement peak',
    occ: [0.34, 0.29, 0.33, 0.36, 0.28, 0.86, 0.31, 0.33, 0.30, 0.29, 0.84],
  },
  {
    id: 8, name: 'Inclement Weather Slowdown', pattern: 'Network-wide moderate congestion',
    desc: 'Rain-induced speed reduction across all edges',
    occ: [0.64, 0.61, 0.63, 0.68, 0.65, 0.29, 0.66, 0.62, 0.28, 0.63, 0.30],
  },
  {
    id: 9, name: 'Freight Corridor Peak', pattern: 'V1→V4 and V4→V5 heavy vehicles',
    desc: 'Morning industrial zone freight movement',
    occ: [0.33, 0.85, 0.34, 0.30, 0.31, 0.29, 0.82, 0.36, 0.31, 0.34, 0.30],
  },
  {
    id: 10, name: 'Multi-Spine Peak Hour', pattern: 'V1→V2, V4→V5, V5→V6, V6→V7 surge',
    desc: 'Evening peak on all major spine edges simultaneously',
    occ: [0.80, 0.33, 0.37, 0.34, 0.31, 0.29, 0.83, 0.85, 0.34, 0.87, 0.30],
  },
];

// ══════════════════════════════════════════════════════════
// 5. SCENARIO GRID RENDER
// ══════════════════════════════════════════════════════════
let selectedScenario = 0;

function renderScenarioGrid() {
  const grid = document.getElementById('scenario-grid');
  grid.innerHTML = '';
  TRAFFIC_SCENARIOS.forEach((sc, i) => {
    const congestedEdges = FORWARD_EDGES.filter((_, ei) => sc.occ[ei] > 0.60);
    const card = document.createElement('button');
    card.className = 'sc-card' + (i === 0 ? ' active' : '');
    card.id = `sc-card-${i}`;
    card.innerHTML = `
      <div class="sc-card-num">S${sc.id}</div>
      <div class="sc-card-name">${sc.name}</div>
      <div class="sc-card-desc">${sc.desc}</div>
      <div class="sc-card-congested">
        ${congestedEdges.map(e => `<span class="sc-edge-tag">${e[2]}</span>`).join('')}
      </div>`;
    card.addEventListener('click', () => {
      if (isRunning) return;
      selectedScenario = i;
      document.querySelectorAll('.sc-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      // Draw idle graphs with scenario base state
      const flows = buildFlows(sc.occ, 0);
      renderSVGGraph(document.getElementById('svg-predicted'), flows, false);
      renderSVGGraph(document.getElementById('svg-optimised'), flows.map(f => ({ ...f, occ: Math.max(0.18, f.occ * 0.68) })), false);
      updateFeatureTable(flows, null);
      const peakOcc = (Math.max(...flows.slice(0, 11).map(f => f.occ)) * 100).toFixed(1);
      document.getElementById('gs-before').textContent = `${peakOcc}%`;
      document.getElementById('gs-after').textContent = '—';
      document.getElementById('gs-reduction').textContent = '—';
      document.getElementById('gs-bits').textContent = 'Ready';
      setBadge('badge-pred', 'Ready', '');
      setBadge('badge-opt', 'Ready', '');
    });
    grid.appendChild(card);
  });
}

// ══════════════════════════════════════════════════════════
// 6. FLOW STATE BUILDER
// ══════════════════════════════════════════════════════════
// drift: small random perturbation per cycle to simulate live sensor noise
function buildFlows(baseOcc, drift) {
  const flows = [];
  FORWARD_EDGES.forEach(([src, dst, name, cap], i) => {
    const capacity = getCapacity(name);
    const occ = Math.min(0.97, Math.max(0.12, baseOcc[i]));
    const flow = Math.round(capacity * occ);
    // Derived features (physics-based approximations)
    const speedFreeFlow = 60; // km/h free-flow
    const speed = Math.round(speedFreeFlow * Math.max(0.15, 1 - occ * 0.85));
    const density = occ > 0.01 ? Math.round(flow / Math.max(1, speed)) : 0;
    const capUtil = Math.round(occ * 100);
    const delay = Math.round(occ > 0.6 ? (occ - 0.5) * 180 + 8 : occ * 12);
    flows.push({ src, dst, name, cap: capacity, occ, flow, speed, density, capUtil, delay });
  });
  // Scenario inputs are mirrored to the reverse edge; optimization output comes from the API.
  FORWARD_EDGES.forEach(([src, dst, name, cap], i) => {
    const revName = name.split('→').reverse().join('→');
    const capacity = getCapacity(revName);
    const revOcc = Math.min(0.90, Math.max(0.12, baseOcc[i]));
    const flow = Math.round(capacity * revOcc);
    const speed = Math.round(60 * Math.max(0.15, 1 - revOcc * 0.85));
    const density = Math.round(flow / Math.max(1, speed));
    const capUtil = Math.round(revOcc * 100);
    const delay = Math.round(revOcc > 0.6 ? (revOcc - 0.5) * 180 + 8 : revOcc * 12);
    flows.push({ src: dst, dst: src, name: revName, cap: capacity, occ: revOcc, flow, speed, density, capUtil, delay });
  });
  return flows;
}

function getTemporalFeatures() {
  const now = new Date();
  const hour = now.getHours() + now.getMinutes() / 60;
  return [
    Math.sin(2 * Math.PI * hour / 24),
    Math.cos(2 * Math.PI * hour / 24),
    now.getDay() === 0 || now.getDay() === 6 ? 1 : 0,
    0,
  ];
}

// ══════════════════════════════════════════════════════════
// 7. SVG GRAPH RENDERER
// ══════════════════════════════════════════════════════════
// SVG viewBox: 0 0 560 280
// Node positions scaled to fit, matching the image layout:
// Top row: V1(70,70), V2(210,70), V3(360,70), V8(490,70)
// Bot row: V4(70,200), V5(210,200), V6(360,200), V7(490,200)

const SVG_NS = 'http://www.w3.org/2000/svg';
const NODE_R = 22;

const SVG_NODES = [
  { id: 0, label: 'V1', x: 70,  y: 75  },
  { id: 1, label: 'V2', x: 220, y: 75  },
  { id: 2, label: 'V3', x: 370, y: 75  },
  { id: 3, label: 'V4', x: 70,  y: 205 },
  { id: 4, label: 'V5', x: 220, y: 205 },
  { id: 5, label: 'V6', x: 370, y: 205 },
  { id: 6, label: 'V7', x: 490, y: 205 },
  { id: 7, label: 'V8', x: 490, y: 75  },
];

function edgeColor(occ) {
  if (occ > 0.60) return '#ef4444';
  if (occ > 0.45) return '#f59e0b';
  return '#10b981';
}

function edgeWidth(occ) {
  return occ > 0.60 ? 3.2 : occ > 0.45 ? 2.4 : 1.8;
}

function renderSVGGraph(svgEl, flows, showOptLabel) {
  // Clear
  while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);

  // Defs (arrowheads for each color)
  const defs = document.createElementNS(SVG_NS, 'defs');
  ['#ef4444', '#f59e0b', '#10b981'].forEach((color, i) => {
    const m = document.createElementNS(SVG_NS, 'marker');
    m.setAttribute('id', `arr-${svgEl.id}-${i}`);
    m.setAttribute('markerWidth', '8'); m.setAttribute('markerHeight', '6');
    m.setAttribute('refX', '7'); m.setAttribute('refY', '3');
    m.setAttribute('orient', 'auto');
    const poly = document.createElementNS(SVG_NS, 'polygon');
    poly.setAttribute('points', '0 0, 8 3, 0 6');
    poly.setAttribute('fill', color);
    m.appendChild(poly); defs.appendChild(m);
  });
  svgEl.appendChild(defs);

  // White/beige background rect
  const bg = document.createElementNS(SVG_NS, 'rect');
  bg.setAttribute('width', '560'); bg.setAttribute('height', '280');
  bg.setAttribute('fill', '#faf8f3'); bg.setAttribute('rx', '8');
  svgEl.appendChild(bg);

  // Subtle grid lines
  for (let x = 0; x <= 560; x += 70) {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('x1', x); line.setAttribute('y1', 0);
    line.setAttribute('x2', x); line.setAttribute('y2', 280);
    line.setAttribute('stroke', '#e8e0d0'); line.setAttribute('stroke-width', '0.5');
    svgEl.appendChild(line);
  }
  for (let y = 0; y <= 280; y += 70) {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('x1', 0); line.setAttribute('y1', y);
    line.setAttribute('x2', 560); line.setAttribute('y2', y);
    line.setAttribute('stroke', '#e8e0d0'); line.setAttribute('stroke-width', '0.5');
    svgEl.appendChild(line);
  }

  // Color index map
  const colorIdx = {'#ef4444': 0, '#f59e0b': 1, '#10b981': 2};

  // --- Draw FORWARD EDGES (first 11 flows) ---
  flows.slice(0, 11).forEach((f, i) => {
    const srcN = SVG_NODES[f.src];
    const dstN = SVG_NODES[f.dst];
    const color = edgeColor(f.occ);
    const width = edgeWidth(f.occ);
    const cidx = colorIdx[color] || 0;

    // Compute direction vector & offset for bidirectional
    const dx = dstN.x - srcN.x, dy = dstN.y - srcN.y;
    const len = Math.sqrt(dx*dx + dy*dy);
    const ux = dx/len, uy = dy/len;
    const perpX = -uy * 5, perpY = ux * 5; // lateral offset for forward edge

    // Start/end points (stop at node edge)
    const x1 = srcN.x + ux * NODE_R + perpX;
    const y1 = srcN.y + uy * NODE_R + perpY;
    const x2 = dstN.x - ux * (NODE_R + 4) + perpX;
    const y2 = dstN.y - uy * (NODE_R + 4) + perpY;

    // Draw edge line
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', width);
    line.setAttribute('marker-end', `url(#arr-${svgEl.id}-${cidx})`);
    line.setAttribute('stroke-linecap', 'round');
    if (f.occ > 0.60) {
      line.setAttribute('stroke-dasharray', '0');
    }
    svgEl.appendChild(line);

    // Occupancy label on edge midpoint
    const mx = (x1 + x2) / 2 - uy * 9;
    const my = (y1 + y2) / 2 + ux * 9;
    const bg2 = document.createElementNS(SVG_NS, 'rect');
    const label = `${Math.round(f.occ * 100)}%`;
    bg2.setAttribute('x', mx - 14); bg2.setAttribute('y', my - 8);
    bg2.setAttribute('width', 28); bg2.setAttribute('height', 13);
    bg2.setAttribute('fill', 'rgba(250,248,243,0.88)');
    bg2.setAttribute('rx', 3);
    svgEl.appendChild(bg2);

    const txt = document.createElementNS(SVG_NS, 'text');
    txt.setAttribute('x', mx); txt.setAttribute('y', my + 2);
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('font-size', '9');
    txt.setAttribute('font-family', 'JetBrains Mono, monospace');
    txt.setAttribute('font-weight', '700');
    txt.setAttribute('fill', color);
    txt.textContent = label;
    svgEl.appendChild(txt);
  });

  // --- Draw REVERSE EDGES (flows 11-21) ---
  flows.slice(11).forEach((f, i) => {
    const srcN = SVG_NODES[f.src];
    const dstN = SVG_NODES[f.dst];
    const color = edgeColor(f.occ);
    const width = edgeWidth(f.occ) * 0.85;
    const cidx = colorIdx[color] || 0;

    const dx = dstN.x - srcN.x, dy = dstN.y - srcN.y;
    const len = Math.sqrt(dx*dx + dy*dy);
    const ux = dx/len, uy = dy/len;
    const perpX = uy * 5, perpY = -ux * 5; // opposite lateral offset

    const x1 = srcN.x + ux * NODE_R + perpX;
    const y1 = srcN.y + uy * NODE_R + perpY;
    const x2 = dstN.x - ux * (NODE_R + 4) + perpX;
    const y2 = dstN.y - uy * (NODE_R + 4) + perpY;

    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', width);
    line.setAttribute('stroke-dasharray', '4,3');
    line.setAttribute('marker-end', `url(#arr-${svgEl.id}-${cidx})`);
    line.setAttribute('opacity', '0.65');
    svgEl.appendChild(line);
  });

  // --- Draw NODES ---
  SVG_NODES.forEach(n => {
    // Check if node is involved in any congested edge
    const congested = flows.slice(0, 11).some(f => (f.src === n.id || f.dst === n.id) && f.occ > 0.60);

    // Outer glow circle for congested nodes
    if (congested) {
      const glow = document.createElementNS(SVG_NS, 'circle');
      glow.setAttribute('cx', n.x); glow.setAttribute('cy', n.y);
      glow.setAttribute('r', NODE_R + 6);
      glow.setAttribute('fill', 'rgba(239,68,68,0.12)');
      glow.setAttribute('stroke', 'rgba(239,68,68,0.3)');
      glow.setAttribute('stroke-width', '1.5');
      svgEl.appendChild(glow);
    }

    // White fill circle
    const circle = document.createElementNS(SVG_NS, 'circle');
    circle.setAttribute('cx', n.x); circle.setAttribute('cy', n.y);
    circle.setAttribute('r', NODE_R);
    circle.setAttribute('fill', '#ffffff');
    circle.setAttribute('stroke', congested ? '#ef4444' : '#4b5563');
    circle.setAttribute('stroke-width', congested ? '2.5' : '2');
    circle.setAttribute('filter', 'drop-shadow(0 1px 3px rgba(0,0,0,0.12))');
    svgEl.appendChild(circle);

    // Node label
    const txt = document.createElementNS(SVG_NS, 'text');
    txt.setAttribute('x', n.x); txt.setAttribute('y', n.y + 5);
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('font-size', '13');
    txt.setAttribute('font-family', 'Space Grotesk, Inter, sans-serif');
    txt.setAttribute('font-weight', '800');
    txt.setAttribute('fill', congested ? '#b91c1c' : '#1e1030');
    txt.textContent = n.label;
    svgEl.appendChild(txt);
  });

  // Optional: "OPTIMISED" watermark label
  if (showOptLabel) {
    const lbl = document.createElementNS(SVG_NS, 'text');
    lbl.setAttribute('x', '555'); lbl.setAttribute('y', '275');
    lbl.setAttribute('text-anchor', 'end');
    lbl.setAttribute('font-size', '8');
    lbl.setAttribute('font-family', 'Inter, sans-serif');
    lbl.setAttribute('font-weight', '700');
    lbl.setAttribute('fill', '#059669');
    lbl.setAttribute('opacity', '0.7');
    lbl.textContent = '⚛ QAOA OPTIMISED';
    svgEl.appendChild(lbl);
  }
}

// ══════════════════════════════════════════════════════════
// 8. FEATURE TABLE UPDATE
// ══════════════════════════════════════════════════════════
let prevEdgeFlows = null;

function updateFeatureTable(flows, optFlows) {
  // --- Edge Table ---
  const tbody = document.getElementById('ft-edge-body');
  const displayFlows = optFlows || flows;
  displayFlows.forEach((f, i) => {
    const prevOcc = prevEdgeFlows ? prevEdgeFlows[i]?.occ : null;
    const changed = prevOcc !== null && Math.abs(f.occ - prevOcc) > 0.005;
    let row = document.getElementById(`ft-row-e-${i}`);
    if (!row) {
      row = document.createElement('tr');
      row.id = `ft-row-e-${i}`;
      tbody.appendChild(row);
    }
    const occClass = f.occ > 0.60 ? 'td-congested' : f.occ > 0.45 ? 'td-moderate' : 'td-free';
    const statusClass = f.occ > 0.60 ? 'sp-cong' : f.occ > 0.45 ? 'sp-mod' : 'sp-free';
    const statusText = f.occ > 0.60 ? 'Congested' : f.occ > 0.45 ? 'Moderate' : 'Free Flow';
    const isForward = i < 11;
    row.innerHTML = `
      <td class="td-mono">${f.name}</td>
      <td>${isForward ? '→ Forward' : '← Reverse'}</td>
      <td>${f.flow.toLocaleString()}</td>
      <td class="${occClass}">${Math.round(f.occ * 100)}%</td>
      <td>${f.speed}</td>
      <td>${f.density}</td>
      <td class="${occClass}">${f.capUtil}%</td>
      <td>${f.delay}</td>
      <td><span class="status-pill ${statusClass}">${statusText}</span></td>
    `;
    if (changed) {
      row.classList.remove('ft-flash');
      void row.offsetWidth; // reflow
      row.classList.add('ft-flash');
    }
  });
  prevEdgeFlows = displayFlows.map(f => ({ ...f }));

  // --- Node Table ---
  const nodeTbody = document.getElementById('ft-node-body');
  SVG_NODES.forEach((n, ni) => {
    // Aggregate node features from connected edges
    const connEdges = (optFlows || flows).slice(0, 22).filter(f => f.src === ni || f.dst === ni);
    const avgSpeed = connEdges.length ? Math.round(connEdges.reduce((s, f) => s + f.speed, 0) / connEdges.length) : 45;
    const totalFlow = connEdges.reduce((s, f) => s + f.flow, 0);
    const avgOcc = connEdges.length ? connEdges.reduce((s, f) => s + f.occ, 0) / connEdges.length : 0.3;
    const queueLen = Math.round(Math.max(0, avgOcc - 0.5) * 120 + Math.random() * 5);
    const phase = ['Green', 'Yellow', 'Red'][Math.min(2, Math.floor(avgOcc * 3))];
    const phaseColor = phase === 'Green' ? '#059669' : phase === 'Yellow' ? '#d97706' : '#dc2626';
    const waitTime = Math.round(avgOcc > 0.6 ? avgOcc * 45 : avgOcc * 22);

    let nrow = document.getElementById(`ft-row-n-${ni}`);
    if (!nrow) {
      nrow = document.createElement('tr');
      nrow.id = `ft-row-n-${ni}`;
      nodeTbody.appendChild(nrow);
    }
    nrow.innerHTML = `
      <td class="td-mono">${n.label}</td>
      <td>${NODE_LABELS[ni]}</td>
      <td>${avgOcc.toFixed(3)}</td>
      <td>${avgSpeed}</td>
      <td>${queueLen} veh</td>
      <td>${totalFlow.toLocaleString()}</td>
      <td style="color:${phaseColor};font-weight:700">${phase}</td>
      <td>${waitTime}s</td>
    `;
  });
}

// Tab switcher
function switchTab(tab) {
  document.getElementById('table-edge-wrap').style.display = tab === 'edge' ? '' : 'none';
  document.getElementById('table-node-wrap').style.display = tab === 'node' ? '' : 'none';
  document.getElementById('tab-edge').classList.toggle('active', tab === 'edge');
  document.getElementById('tab-node').classList.toggle('active', tab === 'node');
}

window.switchTab = switchTab;

// ══════════════════════════════════════════════════════════
// 9. CONTINUOUS PIPELINE LOOP
// ══════════════════════════════════════════════════════════
let isRunning = false;
let cycleCount = 0;
let loopHandle = null;
let currentOptFlows = null; // The state that feeds back

function setPhaseActive(phase) {
  [1, 2, 3].forEach(p => {
    const el = document.getElementById(`pi-${p}`);
    if (el) el.classList.toggle('pi-active', p === phase);
  });
}

function setBadge(id, text, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = 'gp-badge' + (id === 'badge-opt' ? ' gp-badge-2' : '') + (cls ? ' ' + cls : '');
}

async function runOneCycle() {
  if (!isRunning) return;
  cycleCount++;
  document.getElementById('cycle-count').textContent = cycleCount;
  const sc = TRAFFIC_SCENARIOS[selectedScenario];

  // ── Phase 1: STQGCN Prediction ─────────────────────────
  setPhaseActive(1);
  setBadge('badge-pred', 'STQGCN predicting…', 'running');
  setBadge('badge-opt', 'Waiting', '');
  document.getElementById('graph-predicted').classList.add('pulsing');
  document.getElementById('graph-optimised').classList.remove('pulsing');

  // Scenario loads are the selected inputs; prior backend output feeds the next cycle.
  let baseOcc;
  if (cycleCount === 1 || !currentOptFlows) {
    baseOcc = sc.occ.slice();
  } else {
    // Closed-loop dynamic feedback with realistic dissipation:
    // Bottlenecks stay relieved by QAOA signals/rerouting; detours clear transient load back to baseline
    baseOcc = sc.occ.map((orig, i) => {
      const optOcc = currentOptFlows[i]?.occ ?? orig;
      let nextOcc;
      if (orig > 0.55) {
        // Sustained relief on bottleneck edges
        nextOcc = orig * 0.35 + optOcc * 0.65;
      } else {
        // Transient detour packets dissipate back to baseline
        nextOcc = orig * 0.85 + optOcc * 0.15;
      }
      const jitter = (Math.random() - 0.5) * 0.02;
      return Math.min(0.95, Math.max(0.12, nextOcc + jitter));
    });
  }
  const scenarioFlows = buildFlows(baseOcc, 0);
  renderSVGGraph(document.getElementById('svg-predicted'), scenarioFlows, false);
  updateFeatureTable(scenarioFlows, null);

  if (!isRunning) return;

  let prediction;
  try {
    const capacities = Object.fromEntries(scenarioFlows.map(f => [f.name, f.cap]));
    const observations = Object.fromEntries(scenarioFlows.slice(0, 11).map(f => [f.name, f.flow]));
    const edgeOverrides = Object.fromEntries(FORWARD_EDGES.map((edge, index) => [edge[2], {
      length_m: EDGE_INFRA[index].len,
      speed_limit: EDGE_INFRA[index].speed,
      lanes: Math.max(1, Math.round(EDGE_INFRA[index].cap / 650)),
      friction_factor: EDGE_INFRA[index].mu,
    }]));
    prediction = await apiRequest('/predict', {
      method: 'POST',
      body: JSON.stringify({
        network_type: 'qff', capacities, observations, edge_overrides: edgeOverrides,
        temporal_features: getTemporalFeatures(),
      }),
    });
  } catch (error) {
    stopPipeline();
    setBadge('badge-pred', error.message || 'STQGCN unavailable', 'error');
    return;
  }

  const predFlows = scenarioFlows.map(f => {
    const flow = Number(prediction.predictions?.[f.name] ?? f.flow);
    const occ = f.cap > 0 ? flow / f.cap : 0;
    const speed = Math.round(60 * Math.max(0.15, 1 - occ * 0.85));
    return { ...f, flow, occ, speed, density: Math.round(flow / Math.max(1, speed)),
      capUtil: Math.round(occ * 100), delay: Math.round(occ > 0.6 ? (occ - 0.5) * 180 + 8 : occ * 12) };
  });
  renderSVGGraph(document.getElementById('svg-predicted'), predFlows, false);
  updateFeatureTable(predFlows, null);
  setBadge('badge-pred', `STQGCN ${Number(prediction.latency_ms).toFixed(0)} ms`, 'done');

  // ── Phase 2: QAOA Optimisation ─────────────────────────
  setPhaseActive(2);
  setBadge('badge-opt', 'Optimising…', 'running');
  document.getElementById('graph-predicted').classList.remove('pulsing');
  document.getElementById('graph-optimised').classList.add('pulsing');

  let result;
  try {
    const capacities = Object.fromEntries(predFlows.map(f => [f.name, f.cap]));
    const predictions = Object.fromEntries(predFlows.map(f => [f.name, f.flow]));
    result = await apiRequest('/qaoa-optimize', {
      method: 'POST',
      body: JSON.stringify({ network_type: 'qff', capacities, predictions }),
    });
  } catch (error) {
    stopPipeline();
    setBadge('badge-opt', error.message || 'Backend unavailable', 'error');
    return;
  }
  const optFlows = predFlows.map(f => {
    const flow = Number(result.after?.[f.name] ?? f.flow);
    const occ = f.cap > 0 ? flow / f.cap : 0;
    const speed = Math.round(60 * Math.max(0.15, 1 - occ * 0.85));
    return { ...f, flow, occ, speed, density: Math.round(flow / Math.max(1, speed)),
      capUtil: Math.round(occ * 100), delay: Math.round(occ > 0.6 ? (occ - 0.5) * 180 + 8 : occ * 12) };
  });
  currentOptFlows = optFlows;

  // Stats
  const peakBefore = Math.max(...predFlows.slice(0,11).map(f => f.occ)) * 100;
  const peakAfter  = Math.max(...optFlows.slice(0,11).map(f => f.occ)) * 100;
  const reduction  = ((peakBefore - peakAfter) / peakBefore * 100).toFixed(1);
  const runtimes = `STQGCN ${Number(prediction.latency_ms).toFixed(0)} ms · QAOA ${Number(result.latency_ms ?? 0).toFixed(0)} ms`;

  document.getElementById('gs-before').textContent    = `${peakBefore.toFixed(1)}%`;
  document.getElementById('gs-after').textContent     = `${peakAfter.toFixed(1)}%`;
  document.getElementById('gs-reduction').textContent = `↓${reduction}%`;
  document.getElementById('gs-bits').textContent      = runtimes;

  if (!isRunning) return;

  // ── Phase 3: Feedback ──────────────────────────────────
  setPhaseActive(3);
  await delay(500);
  renderSVGGraph(document.getElementById('svg-optimised'), optFlows, true);
  updateFeatureTable(predFlows, optFlows);
  setBadge('badge-opt', 'Done ✓', 'done');
  document.getElementById('graph-optimised').classList.remove('pulsing');

  await delay(900); // pause before next cycle
  if (isRunning) loopHandle = setTimeout(runOneCycle, 100);
}

function startPipeline() {
  isRunning = true;
  cycleCount = 0;
  currentOptFlows = null;
  prevEdgeFlows = null;
  document.getElementById('run-icon').textContent = '■';
  document.getElementById('run-label').textContent = 'Stop';
  runOneCycle();
}

function stopPipeline() {
  isRunning = false;
  clearTimeout(loopHandle);
  setPhaseActive(0);
  document.getElementById('run-icon').textContent = '▶';
  document.getElementById('run-label').textContent = 'Run Pipeline';
  setBadge('badge-pred', 'Stopped', '');
  setBadge('badge-opt', 'Stopped', '');
  [1, 2, 3].forEach(p => {
    const el = document.getElementById(`pi-${p}`);
    if (el) el.classList.remove('pi-active');
  });
  document.getElementById('graph-predicted').classList.remove('pulsing');
  document.getElementById('graph-optimised').classList.remove('pulsing');
}

document.getElementById('run-btn').addEventListener('click', () => {
  if (isRunning) stopPipeline();
  else startPipeline();
});

// ══════════════════════════════════════════════════════════
// 10. VQC CIRCUIT CANVAS
// ══════════════════════════════════════════════════════════
let currentK = 1;

function drawCircuit(k) {
  const canvas = document.getElementById('circuit-canvas');
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.parentElement.clientWidth - 64;
  const H = 320;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const NUM_QUBITS = 8;
  const LEFT_MARGIN = 80, RIGHT_MARGIN = 80, TOP_MARGIN = 30;
  const WIRE_SPACING = (H - TOP_MARGIN * 2) / (NUM_QUBITS - 1);
  const GATE_W = 28, GATE_H = 22;
  const COL_ENCODE = LEFT_MARGIN + 20;
  const layerWidth = (W - LEFT_MARGIN - RIGHT_MARGIN - 60) / (k + 1);
  const COL_LAYERS = Array.from({ length: k }, (_, i) => COL_ENCODE + 80 + i * layerWidth);
  const COL_MEAS = W - RIGHT_MARGIN + 20;

  ctx.fillStyle = 'rgba(10,5,30,0.97)';
  ctx.fillRect(0, 0, W, H);

  for (let q = 0; q < NUM_QUBITS; q++) {
    const y = TOP_MARGIN + q * WIRE_SPACING;
    ctx.beginPath(); ctx.moveTo(LEFT_MARGIN - 30, y); ctx.lineTo(COL_MEAS + 20, y);
    ctx.strokeStyle = 'rgba(168,85,247,0.25)'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = '#c084fc'; ctx.font = '700 11px JetBrains Mono, monospace';
    ctx.textAlign = 'right'; ctx.fillText(`|q${q}⟩`, LEFT_MARGIN - 34, y + 4);
  }

  for (let q = 0; q < NUM_QUBITS; q++) {
    const y = TOP_MARGIN + q * WIRE_SPACING;
    drawGate(ctx, COL_ENCODE, y, GATE_W, GATE_H, 'RY', '#a855f7', '#f3e8ff');
  }
  ctx.fillStyle = 'rgba(168,85,247,0.5)'; ctx.font = '500 9px Inter, sans-serif';
  ctx.textAlign = 'center'; ctx.fillText('Angle\nEncoding', COL_ENCODE, TOP_MARGIN - 14);

  COL_LAYERS.forEach((layerX, li) => {
    const rz1x = layerX, ryx = layerX + 33, rz2x = layerX + 66;
    for (let q = 0; q < NUM_QUBITS; q++) {
      const y = TOP_MARGIN + q * WIRE_SPACING;
      drawGate(ctx, rz1x, y, GATE_W-4, GATE_H-2, 'RZ', '#6366f1', '#e0e7ff');
      drawGate(ctx, ryx,  y, GATE_W-4, GATE_H-2, 'RY', '#38bdf8', '#e0f2fe');
      drawGate(ctx, rz2x, y, GATE_W-4, GATE_H-2, 'RZ', '#6366f1', '#e0e7ff');
    }
    const cnotX = layerX + 100;
    for (let q = 0; q < NUM_QUBITS; q++) {
      drawCNOT(ctx, cnotX, TOP_MARGIN + q * WIRE_SPACING, TOP_MARGIN + ((q+1)%NUM_QUBITS) * WIRE_SPACING);
    }
    ctx.fillStyle = 'rgba(99,102,241,0.5)'; ctx.font = '500 9px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText(`Layer ${li+1}`, layerX + 50, TOP_MARGIN - 14);
    ctx.strokeStyle = 'rgba(99,102,241,0.15)'; ctx.lineWidth = 1; ctx.setLineDash([4,3]);
    ctx.strokeRect(layerX - 8, TOP_MARGIN - 24, cnotX - layerX + 24, H - TOP_MARGIN * 0.6);
    ctx.setLineDash([]);
  });

  for (let q = 0; q < NUM_QUBITS; q++) {
    drawMeasure(ctx, COL_MEAS, TOP_MARGIN + q * WIRE_SPACING, GATE_W, GATE_H);
  }
  ctx.fillStyle = 'rgba(52,211,153,0.5)'; ctx.font = '500 9px Inter, sans-serif';
  ctx.textAlign = 'center'; ctx.fillText('⟨Z⟩\nMeasure', COL_MEAS, TOP_MARGIN - 14);
}

function drawGate(ctx, cx, cy, w, h, label, stroke, fill) {
  const x = cx - w/2, y = cy - h/2;
  ctx.fillStyle = fill + '22'; ctx.strokeStyle = stroke; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill(); ctx.stroke();
  ctx.fillStyle = stroke; ctx.font = `700 ${label.length>2?8:10}px JetBrains Mono, monospace`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, cx, cy);
}

function drawCNOT(ctx, cx, yCtrl, yTgt) {
  ctx.beginPath(); ctx.arc(cx, yCtrl, 4.5, 0, Math.PI*2); ctx.fillStyle = '#fbbf24'; ctx.fill();
  const yMin = Math.min(yCtrl, yTgt), yMax = Math.max(yCtrl, yTgt);
  ctx.beginPath(); ctx.moveTo(cx, yMin); ctx.lineTo(cx, yMax);
  ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, yTgt, 6, 0, Math.PI*2); ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx-6, yTgt); ctx.lineTo(cx+6, yTgt); ctx.moveTo(cx, yTgt-6); ctx.lineTo(cx, yTgt+6); ctx.stroke();
}

function drawMeasure(ctx, cx, cy, w, h) {
  const x = cx-w/2, y = cy-h/2;
  ctx.fillStyle = 'rgba(52,211,153,0.08)'; ctx.strokeStyle = '#34d399'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 4); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy+2, 5, Math.PI, 0); ctx.strokeStyle = '#34d399'; ctx.lineWidth = 1.2; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy+2); ctx.lineTo(cx+3, cy-2); ctx.stroke();
}

const layerBtns = document.getElementById('layer-btns');
if (layerBtns) {
  layerBtns.addEventListener('click', e => {
    const btn = e.target.closest('.lb'); if (!btn) return;
    document.querySelectorAll('.lb').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentK = parseInt(btn.dataset.k);
    drawCircuit(currentK);
  });
}

const circuitContainer = document.getElementById('circuit-container');
if (circuitContainer) {
  new ResizeObserver(() => drawCircuit(currentK)).observe(circuitContainer);
}

// ══════════════════════════════════════════════════════════
// 11. UTILITY
// ══════════════════════════════════════════════════════════
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ══════════════════════════════════════════════════════════
// 12. INIT
// ══════════════════════════════════════════════════════════
window.addEventListener('load', async () => {
  initCCTVAnimation();
  initTrafficManagerConsole();
  renderScenarioGrid();
  drawCircuit(currentK);
  try {
    let lastError;
    for (let attempt = 0; attempt < 15; attempt++) {
      try {
        backendNetwork = await apiRequest('/network?network_type=qff');
        lastError = null;
        break;
      } catch (error) {
        lastError = error;
        if (attempt < 14) await delay(1000);
      }
    }
    if (!backendNetwork) throw lastError || new Error('Backend unavailable');
    backendNetwork.edges.forEach(edge => {
      const forward = FORWARD_EDGES.find(e => e[2] === edge.id);
      if (forward) forward[3] = edge.capacity;
    });
    const sc0 = TRAFFIC_SCENARIOS[0];
    const initFlows = buildFlows(sc0.occ, 0).map(f => {
      const flow = Number(backendNetwork.predictions?.[f.name] ?? f.flow);
      const occ = f.cap > 0 ? flow / f.cap : 0;
      return { ...f, flow, occ, capUtil: Math.round(occ * 100) };
    });
    renderSVGGraph(document.getElementById('svg-predicted'), initFlows, false);
    renderSVGGraph(document.getElementById('svg-optimised'), initFlows, false);
    updateFeatureTable(initFlows, null);
    const status = document.getElementById('backend-status');
    if (status) status.textContent = `Backend connected · ${backendNetwork.prediction_model || 'QFF network ready'}`;
  } catch (error) {
    const status = document.getElementById('backend-status');
    if (status) status.textContent = `Backend unavailable · ${error.message}`;
    setBadge('badge-pred', 'Backend unavailable', 'error');
    setBadge('badge-opt', 'Disconnected', 'error');
    document.getElementById('run-btn').disabled = true;
  }
});
