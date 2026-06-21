/**
 * Wumpus World Game - Frontend Controller
 * Rich animations: particles, confetti, screen shake, score floats,
 * cell reveal effects, gold shimmer, Wumpus sway, death flash
 */

let gameState = null;
let levelsData = null;
let revealMode = false;
let shootMode = false;
let autoPlaying = false;
let autoInterval = null;
let prevWumpusPos = null;
let prevScore = 0;
let prevAgentPos = null;
let prevVisitedCount = 0;
let prevHasGold = false;

// ===== API =====
async function apiCall(endpoint, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  return (await fetch(`/api/${endpoint}`, opts)).json();
}

async function fetchState() { gameState = await apiCall('state'); render(); }
async function fetchLevels() { levelsData = await apiCall('levels'); }

// ===== EFFECTS ENGINE =====
function spawnParticles(x, y, count, colors, sizeRange = [4,10], spread = 120) {
  const container = getParticleContainer();
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size = sizeRange[0] + Math.random() * (sizeRange[1] - sizeRange[0]);
    const color = colors[Math.floor(Math.random() * colors.length)];
    const angle = Math.random() * Math.PI * 2;
    const dist = 30 + Math.random() * spread;
    const dx = Math.cos(angle) * dist;
    const dy = Math.sin(angle) * dist;
    const dur = 600 + Math.random() * 600;
    p.style.cssText = `
      left:${x}px; top:${y}px; width:${size}px; height:${size}px;
      background:${color}; opacity:1;
      transition: all ${dur}ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
    `;
    container.appendChild(p);
    requestAnimationFrame(() => {
      p.style.transform = `translate(${dx}px, ${dy}px) scale(0)`;
      p.style.opacity = '0';
    });
    setTimeout(() => p.remove(), dur + 50);
  }
}

function spawnConfetti(count = 60) {
  const container = getParticleContainer();
  const colors = ['#818cf8','#34d399','#fbbf24','#f87171','#22d3ee','#a78bfa','#fb923c','#4ade80'];
  for (let i = 0; i < count; i++) {
    const piece = document.createElement('div');
    piece.className = 'confetti-piece';
    const color = colors[Math.floor(Math.random() * colors.length)];
    const x = Math.random() * window.innerWidth;
    const dur = 2000 + Math.random() * 3000;
    const delay = Math.random() * 1500;
    const w = 6 + Math.random() * 10;
    const h = 6 + Math.random() * 10;
    piece.style.cssText = `
      left:${x}px; top:-20px; width:${w}px; height:${h}px;
      background:${color}; opacity:0.9;
      animation-duration:${dur}ms; animation-delay:${delay}ms;
      border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
    `;
    container.appendChild(piece);
    setTimeout(() => piece.remove(), dur + delay + 100);
  }
}

function spawnScoreFloat(text, positive, x, y) {
  const el = document.createElement('div');
  el.className = `score-float ${positive ? 'positive' : 'negative'}`;
  el.textContent = text;
  el.style.left = x + 'px';
  el.style.top = y + 'px';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1300);
}

function screenShake() {
  document.body.classList.add('screen-shake');
  setTimeout(() => document.body.classList.remove('screen-shake'), 600);
}

function deathFlashEffect() {
  const overlay = document.createElement('div');
  overlay.className = 'death-overlay';
  document.body.appendChild(overlay);
  screenShake();
  setTimeout(() => overlay.remove(), 900);
}

function getParticleContainer() {
  let c = document.querySelector('.particle-container');
  if (!c) { c = document.createElement('div'); c.className = 'particle-container'; document.body.appendChild(c); }
  return c;
}

function cellRipple(cellEl) {
  const r = document.createElement('div');
  r.className = 'ripple';
  r.style.cssText = 'width:20px;height:20px;left:50%;top:50%;transform:translate(-50%,-50%) scale(0);';
  cellEl.appendChild(r);
  setTimeout(() => r.remove(), 650);
}

// ===== LEVEL SELECT =====
function showLevelSelect() {
  stopAutoPlay();
  const overlay = document.getElementById('levelOverlay');
  const grid = document.getElementById('levelGrid');
  grid.innerHTML = '';
  if (!levelsData) { fetchLevels().then(() => showLevelSelect()); return; }
  for (const [id, lvl] of Object.entries(levelsData)) {
    const card = document.createElement('div');
    card.className = 'level-card';
    card.onclick = () => startLevel(parseInt(id));
    card.innerHTML = `
      <div class="level-icon">${lvl.icon}</div>
      <div class="level-info">
        <div class="level-name">Level ${id}: ${lvl.name}</div>
        <div class="level-desc">${lvl.description}</div>
        <div class="level-details">
          <span class="level-detail-tag">${lvl.grid_size}×${lvl.grid_size}</span>
          <span class="level-detail-tag">${lvl.max_pits} pit${lvl.max_pits > 1 ? 's' : ''}</span>
          ${lvl.wumpus_moves ? '<span class="level-detail-tag danger">Wumpus Moves!</span>' : '<span class="level-detail-tag">Static Wumpus</span>'}
          <span class="level-detail-tag">+${lvl.gold_reward} gold</span>
        </div>
      </div>
    `;
    grid.appendChild(card);
  }
  overlay.classList.remove('hidden');
}
function hideLevelSelect() { document.getElementById('levelOverlay').classList.add('hidden'); }

async function startLevel(level) {
  hideLevelSelect();
  document.getElementById('gameOverOverlay').classList.add('hidden');
  const result = await apiCall('new_game', 'POST', { level });
  gameState = result;
  if (!gameState.grid_size && gameState.state) gameState = gameState.state;
  prevWumpusPos = gameState.world?.wumpus ? `${gameState.world.wumpus[0]},${gameState.world.wumpus[1]}` : null;
  prevScore = 0; prevAgentPos = null; prevVisitedCount = 0; prevHasGold = false;
  render();
}

async function newGame() { showLevelSelect(); }

// ===== GAME ACTIONS WITH EFFECTS =====
async function doAction(direction) {
  if (gameState?.score?.game_over) return;
  const oldScore = gameState?.score?.score || 0;
  let result;
  if (shootMode) {
    result = await apiCall('shoot', 'POST', { direction });
    toggleShootMode();
    // Shoot effect
    const grid = document.getElementById('gameGrid');
    const rect = grid.getBoundingClientRect();
    spawnParticles(rect.left + rect.width/2, rect.top + rect.height/2, 8,
      ['#f87171','#ef4444','#fca5a5'], [3,7], 80);
  } else {
    result = await apiCall('move', 'POST', { direction });
  }
  if (result.state) gameState = result.state;
  else await fetchState();
  handlePostAction(oldScore);
}

async function grabGold() {
  if (gameState?.score?.game_over) return;
  const oldScore = gameState?.score?.score || 0;
  const result = await apiCall('grab', 'POST');
  if (result.state) gameState = result.state;
  else await fetchState();
  // Gold grab celebration
  if (result.action_result?.success) {
    const grid = document.getElementById('gameGrid');
    const rect = grid.getBoundingClientRect();
    spawnParticles(rect.left + rect.width/2, rect.top + rect.height/2, 35,
      ['#fbbf24','#fde047','#f59e0b','#eab308','#facc15'], [5,14], 180);
    spawnScoreFloat(`+${gameState.level_config?.gold_reward || 1000}`, true,
      rect.left + rect.width/2 - 40, rect.top + rect.height/2 - 30);
  }
  handlePostAction(oldScore);
}

async function climbOut() {
  if (gameState?.score?.game_over) return;
  const oldScore = gameState?.score?.score || 0;
  const result = await apiCall('climb', 'POST');
  if (result.state) gameState = result.state;
  else await fetchState();
  handlePostAction(oldScore);
}

async function autoStep() {
  if (gameState?.score?.game_over) return;
  const oldScore = gameState?.score?.score || 0;
  const result = await apiCall('auto', 'POST');
  if (result.state) gameState = result.state;
  else await fetchState();
  handlePostAction(oldScore);
}

function handlePostAction(oldScore) {
  checkWumpusMoved();
  detectAndAnimateChanges(oldScore);
  render();
  checkGameOver();
}

function detectAndAnimateChanges(oldScore) {
  if (!gameState) return;
  const newScore = gameState.score.score;
  // Score change float
  if (newScore !== oldScore) {
    const diff = newScore - oldScore;
    const scoreEl = document.getElementById('statScore');
    const rect = scoreEl.getBoundingClientRect();
    if (Math.abs(diff) > 5) {
      spawnScoreFloat(diff > 0 ? `+${diff}` : `${diff}`, diff > 0,
        rect.left + rect.width/2 - 20, rect.top - 10);
    }
    // Animate score stat
    scoreEl.classList.remove('anim-score-pos','anim-score-neg');
    void scoreEl.offsetWidth; // force reflow
    scoreEl.classList.add(diff > 0 ? 'anim-score-pos' : 'anim-score-neg');
  }

  // Death
  if (!gameState.agent.is_alive && gameState.score.game_over) {
    deathFlashEffect();
    const grid = document.getElementById('gameGrid');
    const rect = grid.getBoundingClientRect();
    spawnParticles(rect.left + rect.width/2, rect.top + rect.height/2, 25,
      ['#ef4444','#dc2626','#991b1b','#7f1d1d'], [4,12], 150);
  }

  // Gold pickup detection
  if (gameState.agent.has_gold && !prevHasGold) {
    prevHasGold = true;
  }
  prevScore = newScore;
}

function autoPlay() {
  if (autoPlaying) { stopAutoPlay(); return; }
  autoPlaying = true;
  document.getElementById('btnAutoPlay').textContent = '⏹️ Stop Auto';
  document.getElementById('btnAutoPlay').classList.add('btn-danger');
  autoInterval = setInterval(async () => {
    if (gameState?.score?.game_over) { stopAutoPlay(); return; }
    await autoStep();
  }, 600);
}

function stopAutoPlay() {
  autoPlaying = false; clearInterval(autoInterval);
  document.getElementById('btnAutoPlay').textContent = '🤖 Auto Play';
  document.getElementById('btnAutoPlay').classList.remove('btn-danger');
}

function toggleReveal() {
  revealMode = !revealMode;
  document.getElementById('btnToggleReveal').textContent = revealMode ? '🙈 Hide Map' : '👁️ Reveal Map';
  render();
}

function toggleShootMode() {
  shootMode = !shootMode;
  document.getElementById('shootModeBanner').classList.toggle('active', shootMode);
  document.getElementById('btnShoot').textContent = shootMode ? '❌ Cancel' : '🏹 Shoot';
}

// ===== WORLD SHIFT MOVEMENT =====
function checkWumpusMoved() {
  if (!gameState?.world?.wumpus) return;
  const newPos = `${gameState.world.wumpus[0]},${gameState.world.wumpus[1]}`;
  if (prevWumpusPos && newPos !== prevWumpusPos) {
    showEarthquakeAlert();
    screenShake();
  }
  prevWumpusPos = newPos;
}

function showEarthquakeAlert() {
  document.querySelectorAll('.wumpus-alert').forEach(e => e.remove());
  const alert = document.createElement('div');
  alert.className = 'wumpus-alert';
  alert.style.backgroundColor = 'rgba(220, 38, 38, 0.95)';
  alert.innerHTML = '🌍 <strong>EARTHQUAKE!</strong> The Wumpus, Gold, and Pits have changed locations!';
  document.body.appendChild(alert);
  setTimeout(() => alert.remove(), 4000);
}

// ===== RENDERING =====
function render() {
  if (!gameState) return;
  renderGoalBanner();
  renderGrid();
  renderStats();
  renderPercepts();
  renderKnowledge();
  renderLog();
}

function renderGoalBanner() {
  const lc = gameState.level_config || {};
  const level = gameState.level || 1;
  document.getElementById('goalLevel').textContent = `${lc.icon || '🌿'} Level ${level}: ${lc.name || 'Explorer'}`;
  document.getElementById('goalDesc').textContent = gameState.goal || 'Find the gold, grab it, escape!';
  const badge = document.getElementById('wumpusBadge');
  if (lc.wumpus_moves) {
    badge.innerHTML = '🌍 World: <strong>DYNAMIC</strong> (Earthquakes)';
    badge.className = 'goal-badge wumpus-badge moving';
  } else {
    badge.textContent = '🌍 World: Static';
    badge.className = 'goal-badge wumpus-badge';
  }
}

function renderGrid() {
  const grid = document.getElementById('gameGrid');
  const size = gameState.grid_size;
  const world = gameState.world;
  const agent = gameState.agent;
  const knowledge = gameState.knowledge;
  const visited = new Set((knowledge.visited || []).map(c => `${c[0]},${c[1]}`));
  const safeCells = new Set((knowledge.safe_cells || []).map(c => `${c[0]},${c[1]}`));
  const possWumpus = new Set((knowledge.possible_wumpus || []).map(c => `${c[0]},${c[1]}`));
  const possPits = new Set((knowledge.possible_pits || []).map(c => `${c[0]},${c[1]}`));
  const perceptHistory = knowledge.percept_history || {};
  const newVisitedCount = visited.size;
  const hasNewVisit = newVisitedCount > prevVisitedCount;
  prevVisitedCount = newVisitedCount;

  const cellSize = size <= 4 ? 120 : size <= 5 ? 100 : 85;
  grid.style.gridTemplateColumns = `repeat(${size}, ${cellSize}px)`;
  grid.innerHTML = '';

  for (let row = size - 1; row >= 0; row--) {
    for (let col = 0; col < size; col++) {
      const key = `${row},${col}`;
      const isAgent = agent.position[0] === row && agent.position[1] === col;
      const isVisited = visited.has(key);
      const isDanger = possWumpus.has(key) || possPits.has(key);
      const isNewAgent = isAgent && prevAgentPos && (prevAgentPos[0] !== row || prevAgentPos[1] !== col);

      const cell = document.createElement('div');
      cell.className = 'grid-cell';
      cell.style.width = cellSize + 'px';
      cell.style.height = cellSize + 'px';

      if (isAgent) {
        cell.classList.add('agent-here');
        if (isNewAgent) {
          cell.classList.add('anim-cell-visit-glow');
          // Ripple on new cell
          setTimeout(() => cellRipple(cell), 50);
        }
      } else if (isVisited) {
        cell.classList.add('visited');
      } else if (isDanger && !isVisited) {
        cell.classList.add('danger');
      }

      if (row === 0 && col === 0 && !isAgent) {
        cell.style.borderColor = 'rgba(34, 197, 94, 0.4)';
        cell.classList.add('anim-border-glow');
      }

      const coord = document.createElement('span');
      coord.className = 'cell-coord';
      coord.textContent = `${row},${col}`;
      cell.appendChild(coord);

      if (row === 0 && col === 0) {
        const exit = document.createElement('span');
        exit.style.cssText = 'position:absolute;top:3px;right:5px;font-size:0.55rem;color:var(--accent-emerald);font-weight:700;';
        exit.textContent = '🚪EXIT';
        cell.appendChild(exit);
      }

      const content = document.createElement('div');
      content.className = 'cell-content';

      if (isAgent) {
        const agentIcon = document.createElement('div');
        agentIcon.className = 'agent-icon';
        const sprite = document.createElement('span');
        sprite.className = 'agent-sprite';
        sprite.textContent = '🤖';
        agentIcon.appendChild(sprite);
        const arrow = document.createElement('span');
        arrow.className = `direction-arrow ${agent.direction}`;
        arrow.textContent = { up: '▲', down: '▼', left: '◄', right: '►' }[agent.direction];
        agentIcon.appendChild(arrow);
        content.appendChild(agentIcon);
      } else if (revealMode || isVisited) {
        const wPos = world.wumpus, gPos = world.gold, pits = world.pits || [];
        let html = '';
        if (wPos[0] === row && wPos[1] === col && world.wumpus_alive)
          html += '<span class="wumpus-emoji">👹</span>';
        if (wPos[0] === row && wPos[1] === col && !world.wumpus_alive)
          html += '💀';
        if (gPos[0] === row && gPos[1] === col && !world.gold_picked)
          html += '<span class="gold-emoji">💰</span>';
        if (pits.some(p => p[0] === row && p[1] === col))
          html += '🕳️';
        if (html) { content.innerHTML = html; }
        else { content.textContent = isVisited ? '✓' : ''; content.style.opacity = isVisited ? '0.3' : '1'; }
      } else {
        content.innerHTML = '<span style="opacity:0.2">?</span>';
      }

      cell.appendChild(content);

      // Percept badges
      if (isVisited || isAgent) {
        const percepts = perceptHistory[key] || [];
        if (percepts.length > 0) {
          const pDiv = document.createElement('div');
          pDiv.className = 'cell-percepts';
          percepts.forEach((p, i) => {
            const badge = document.createElement('span');
            badge.className = `percept-badge ${p.toLowerCase()}`;
            badge.textContent = p[0];
            if (isNewAgent && isAgent) badge.style.animationDelay = `${i * 0.1}s`;
            pDiv.appendChild(badge);
          });
          cell.appendChild(pDiv);
        }
      }

      // Danger / Safe labels
      if (!isVisited && !isAgent && !revealMode) {
        const labels = [];
        if (possWumpus.has(key)) labels.push('W?');
        if (possPits.has(key)) labels.push('P?');
        if (labels.length) {
          const lbl = document.createElement('div');
          lbl.className = 'cell-label';
          lbl.style.color = 'var(--accent-red)';
          lbl.textContent = labels.join(' ');
          cell.appendChild(lbl);
        } else if (safeCells.has(key)) {
          const lbl = document.createElement('div');
          lbl.className = 'cell-label';
          lbl.style.color = 'var(--accent-emerald)';
          lbl.textContent = 'Safe';
          cell.appendChild(lbl);
        }
      }

      grid.appendChild(cell);
    }
  }
  prevAgentPos = [...agent.position];
}

function renderStats() {
  const score = gameState.score, agent = gameState.agent;
  const currentLevel = gameState.level || 1;
  const bestKey = 'wumpus_best_L' + currentLevel;
  const bestScore = localStorage.getItem(bestKey) || 0;

  const el = id => document.getElementById(id);
  el('statScore').textContent = score.score;
  el('statScore').style.color = score.score >= 0 ? 'var(--accent-emerald)' : 'var(--accent-red)';
  
  if (el('statBestScore')) {
    el('statBestScore').textContent = bestScore;
    el('statBestScoreLabel').textContent = `Best (L${currentLevel})`;
  }

  el('statActions').textContent = score.actions_taken;
  el('statArrow').textContent = agent.has_arrow ? '✓' : '✗';
  el('statArrow').style.color = agent.has_arrow ? 'var(--accent-emerald)' : 'var(--accent-red)';
  el('statGold').textContent = agent.has_gold ? '✓' : '✗';
  el('statGold').style.color = agent.has_gold ? 'var(--accent-amber)' : 'var(--text-muted)';
}

function renderPercepts() {
  const display = document.getElementById('perceptDisplay');
  const percepts = gameState.current_percepts || [];
  display.innerHTML = '';
  if (!percepts.length) {
    display.innerHTML = '<span class="percept-tag none">✅ None — All Clear</span>';
    return;
  }
  const icons = { Stench: '💨', Breeze: '🌬️', Glitter: '✨', Bump: '🧱', Scream: '😱' };
  percepts.forEach((p, i) => {
    const tag = document.createElement('span');
    tag.className = `percept-tag ${p.toLowerCase()}`;
    tag.textContent = `${icons[p] || '❓'} ${p}`;
    tag.style.animationDelay = `${i * 0.08}s`;
    display.appendChild(tag);
  });
}

function renderKnowledge() {
  const log = document.getElementById('knowledgeLog');
  const inferences = gameState.inference_log || [];
  const knowledge = gameState.knowledge || {};
  log.innerHTML = '';
  addKI(log, `📍 Position: (${gameState.agent.position[0]}, ${gameState.agent.position[1]}) facing ${gameState.agent.direction}`);
  addKI(log, `🗺️ Visited: ${(knowledge.visited || []).length}/${gameState.grid_size * gameState.grid_size} cells`);
  if (gameState.agent.has_gold) addKI(log, '💰 Gold in hand! Head to (0,0) to escape!');
  else addKI(log, '🔍 Goal: Find and grab the gold, then escape!');
  inferences.forEach(inf => addKI(log, inf));
  if (!inferences.length) addKI(log, '🔍 Gathering information...');
}

function addKI(container, text) {
  const item = document.createElement('div');
  item.className = 'knowledge-item';
  item.textContent = text;
  container.appendChild(item);
}

function renderLog() {
  const logEl = document.getElementById('gameLog');
  const entries = gameState.game_log || [];
  logEl.innerHTML = '';
  entries.slice().reverse().forEach(entry => {
    const div = document.createElement('div');
    div.className = 'log-entry';
    const step = document.createElement('span');
    step.className = 'log-step';
    step.textContent = `#${entry.step}`;
    div.appendChild(step);
    const text = document.createElement('span');
    const data = entry.data || {};
    let msg = entry.type;
    if (data.position) msg += ` → (${data.position[0]},${data.position[1]})`;
    if (data.percepts?.length) msg += ` [${data.percepts.join(', ')}]`;
    if (data.message) msg += ` — ${data.message}`;
    text.textContent = msg;
    div.appendChild(text);
    logEl.appendChild(div);
  });
  logEl.scrollTop = 0;
}

function checkGameOver() {
  if (!gameState?.score?.game_over) return;
  stopAutoPlay();
  const won = gameState.score.won, score = gameState.score.score;
  const card = document.querySelector('.game-over-card');
  card.classList.remove('win','lose');
  card.classList.add(won ? 'win' : 'lose');

  let isNewHighScore = false;
  if (won) {
    const currentLevel = gameState.level || 1;
    const bestKey = 'wumpus_best_L' + currentLevel;
    const currentBest = parseInt(localStorage.getItem(bestKey) || -9999);
    if (score > currentBest) {
      localStorage.setItem(bestKey, score);
      isNewHighScore = true;
    }
  }

  const iconEl = document.getElementById('resultIcon');
  iconEl.textContent = won ? '🏆' : '💀';
  iconEl.classList.add('anim-victory');
  setTimeout(() => iconEl.classList.remove('anim-victory'), 900);

  document.getElementById('resultTitle').textContent = won 
    ? (isNewHighScore ? '🎉 NEW HIGH SCORE! 🎉' : 'Victory!') 
    : 'Game Over';
  
  document.getElementById('resultMessage').textContent = won
    ? `You escaped Level ${gameState.level} with the gold!`
    : `You died! Cause: ${gameState.score.death_cause || 'Unknown'}`;
  
  document.getElementById('finalScore').textContent = score >= 0 ? `+${score}` : score;
  document.getElementById('finalScore').className = `final-score ${score >= 0 ? 'positive' : 'negative'}`;
  document.getElementById('gameOverOverlay').classList.remove('hidden');

  if (won) {
    setTimeout(() => spawnConfetti(80), 300);
    setTimeout(() => spawnConfetti(40), 1200);
    if (isNewHighScore) setTimeout(() => spawnConfetti(60), 2000);
  }
}

// ===== KEYBOARD =====
document.addEventListener('keydown', (e) => {
  if (!document.getElementById('levelOverlay').classList.contains('hidden')) return;
  if (gameState?.score?.game_over && e.key !== 'r') return;
  switch (e.key.toLowerCase()) {
    case 'w': case 'arrowup': e.preventDefault(); doAction('up'); break;
    case 's': case 'arrowdown': e.preventDefault(); doAction('down'); break;
    case 'a': case 'arrowleft': e.preventDefault(); doAction('left'); break;
    case 'd': case 'arrowright': e.preventDefault(); doAction('right'); break;
    case 'g': grabGold(); break;
    case 'c': climbOut(); break;
    case 'f': toggleShootMode(); break;
    case ' ': e.preventDefault(); autoStep(); break;
    case 'r': showLevelSelect(); break;
  }
});

// ===== INIT =====
(async () => {
  await fetchLevels();
  await fetchState();
  showLevelSelect();
})();
