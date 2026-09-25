/* ============================================================
   QuizArc — Full Frontend Implementation
   Workflow: Login -> Dashboard -> Daily Challenge / Practice -> Quiz -> Streak + XP -> Result -> Review -> Leaderboard
   Features:
     - 10 Points Checklist Implemented
     - Responsive Layout (Mobile, Tablet, Desktop)
     - Desktop Right Panel (Profile, Rank/Quizzes, Recent Activity)
     - Clean Header Hierarchy
     - Strong Selection States (Category & Difficulty check badges)
     - Equal Height Cards & Fixed Spacing System
     - CTA Hierarchy (Primary Glow CTAs vs Secondary buttons)
     - Polished Quiz Screen & 4-Metric Result Screen
     - Full Loading, Error & Empty States
   ============================================================ */

const API = '';
const DIFF_TIME = { easy: 25, medium: 20, hard: 12 };
const AUTH_KEY  = 'quizarc_auth';

/* ── State Variables ────────────────────────────────────────── */
let authToken        = null;
let userProfile      = null;
let categories       = [];
let selectedCat      = null;
let selectedCatName  = '';
let selectedDiff     = 'medium';

let quizQuestions    = [];
let userAnswers      = [];
let sessionToken     = null;
let isDailyQuiz      = false;
let currentIndex     = 0;

let streak           = 0;
let liveXp           = 0;
let timeLeft         = 20;
let timerId          = null;
let answered         = false;

let quizStartTime    = 0;
let quizEndTime      = 0;

let lastSubmissionResult = null;
let lbActiveType     = 'xp';
let lbActiveCat      = 'general';

/* ── DOM References ─────────────────────────────────────────── */
const headerAuthBtn  = document.getElementById('headerAuthBtn');
const headerLbBtn    = document.getElementById('headerLbBtn');
const headerUserChip = document.getElementById('headerUserChip');
const brandBtn       = document.getElementById('brandBtn');

/* =============================================================
   BOOT & INITIALIZATION
   ============================================================= */
document.addEventListener('DOMContentLoaded', boot);

async function boot() {
  loadAuthFromStorage();

  brandBtn.addEventListener('click', () => {
    if (authToken) showScreen('dashboard');
    else showScreen('login');
  });

  headerAuthBtn.addEventListener('click', () => {
    if (authToken) {
      if (confirm(`Log out as ${userProfile ? userProfile.username : 'user'}?`)) {
        clearAuth();
      }
    } else {
      showScreen('login');
    }
  });

  headerLbBtn.addEventListener('click', () => openLeaderboard('xp'));

  // Auth tabs & forms
  setupAuthHandlers();

  // Mode selection & start buttons
  setupModeHandlers();

  // Next & Review buttons
  document.getElementById('nextBtn').addEventListener('click', nextQuestion);
  document.getElementById('reviewAnswersBtn').addEventListener('click', showReviewScreen);
  document.getElementById('dashReturnBtn').addEventListener('click', () => {
    loadUserProfile();
    showScreen('dashboard');
  });
  document.getElementById('resLbBtn').addEventListener('click', () => openLeaderboard('xp'));
  document.getElementById('reviewBackBtn').addEventListener('click', () => {
    loadUserProfile();
    showScreen('dashboard');
  });
  document.getElementById('lbBackBtn').addEventListener('click', () => {
    if (authToken) showScreen('dashboard');
    else showScreen('login');
  });

  // Check auth state
  if (authToken) {
    showScreen('loading');
    const ok = await loadUserProfile();
    if (ok) {
      await loadCategories();
      showScreen('dashboard');
    } else {
      clearAuth();
      showScreen('login');
    }
  } else {
    showScreen('login');
  }
}

/* =============================================================
   AUTH & USER PROFILE
   ============================================================= */
function loadAuthFromStorage() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return;
    const { token } = JSON.parse(raw);
    if (token) authToken = token;
  } catch (_) {}
}

function saveAuth(token) {
  authToken = token;
  localStorage.setItem(AUTH_KEY, JSON.stringify({ token }));
}

function clearAuth() {
  if (authToken) {
    fetch(`${API}/api/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Auth-Token': authToken },
    }).catch(() => {});
  }
  authToken   = null;
  userProfile = null;
  localStorage.removeItem(AUTH_KEY);
  updateHeaderUI();
  showScreen('login');
}

async function loadUserProfile() {
  if (!authToken) return false;
  try {
    const res = await fetch(`${API}/api/user/profile`, {
      headers: { 'X-Auth-Token': authToken }
    });
    if (!res.ok) return false;
    userProfile = await res.json();
    updateProfileUI();
    updateHeaderUI();
    return true;
  } catch (err) {
    return false;
  }
}

function updateHeaderUI() {
  if (authToken && userProfile) {
    headerAuthBtn.textContent = '🚪 Logout';
    headerAuthBtn.classList.add('logged-in');
    headerUserChip.style.display = 'flex';
    document.getElementById('headerLvl').textContent = `Lv. ${userProfile.level}`;
    document.getElementById('headerXp').textContent = `⚡ ${userProfile.xp} XP`;
    document.getElementById('headerStreak').textContent = `🔥 ${userProfile.current_streak}`;
  } else {
    headerAuthBtn.textContent = '🔐 Login';
    headerAuthBtn.classList.remove('logged-in');
    headerUserChip.style.display = 'none';
  }
}

function updateProfileUI() {
  if (!userProfile) return;
  document.getElementById('dashAvatar').textContent = userProfile.username[0].toUpperCase();
  document.getElementById('dashUsername').textContent = userProfile.username;
  document.getElementById('dashLvlBadge').textContent = `Lv. ${userProfile.level}`;
  document.getElementById('dashTotalXp').textContent = userProfile.xp;
  document.getElementById('dashStreak').textContent = `${userProfile.current_streak}d`;
  document.getElementById('dashBestStreak').textContent = `${userProfile.best_streak}d`;

  // Global Rank & Quizzes Played
  document.getElementById('dashGlobalRank').textContent = `#${userProfile.global_rank || 1}`;
  document.getElementById('dashQuizzesPlayed').textContent = userProfile.total_quizzes || 0;

  // XP Progress Fill
  const pct = Math.min(100, Math.max(0, (userProfile.xp_in_level / userProfile.xp_needed) * 100));
  document.getElementById('dashXpFill').style.width = `${pct}%`;
  document.getElementById('dashXpText').textContent = `${userProfile.xp_in_level} / ${userProfile.xp_needed} XP`;

  // Daily Button Status
  const dailyBtn = document.getElementById('startDailyBtn');
  if (userProfile.daily_completed) {
    dailyBtn.disabled = true;
    dailyBtn.textContent = 'Completed Today ✓';
  } else {
    dailyBtn.disabled = false;
    dailyBtn.textContent = '⚡ Play Daily Challenge';
  }

  // Recent Activity Panel
  const recentList = document.getElementById('recentActivityList');
  if (!userProfile.recent_activity || userProfile.recent_activity.length === 0) {
    recentList.innerHTML = '<p class="empty-text">No recent quizzes played yet.</p>';
  } else {
    recentList.innerHTML = userProfile.recent_activity.map(act => `
      <div class="recent-item">
        <div class="recent-left">
          <span>${act.category_icon}</span>
          <span class="recent-name">${act.category_name}</span>
        </div>
        <div>
          <span style="color:var(--text);font-weight:700;margin-right:6px;">${act.score}/${act.total_questions}</span>
          <span class="recent-xp">+${act.xp_earned} XP</span>
        </div>
      </div>
    `).join('');
  }
}

function setupAuthHandlers() {
  const tabLoginBtn = document.getElementById('tabLoginBtn');
  const tabRegBtn   = document.getElementById('tabRegBtn');
  const loginForm   = document.getElementById('loginForm');
  const regForm     = document.getElementById('regForm');

  tabLoginBtn.addEventListener('click', () => {
    tabLoginBtn.classList.add('active');
    tabRegBtn.classList.remove('active');
    loginForm.style.display = 'flex';
    regForm.style.display   = 'none';
  });

  tabRegBtn.addEventListener('click', () => {
    tabRegBtn.classList.add('active');
    tabLoginBtn.classList.remove('active');
    regForm.style.display   = 'flex';
    loginForm.style.display = 'none';
  });

  // Login submit
  document.getElementById('loginSubmitBtn').addEventListener('click', async () => {
    const username = document.getElementById('loginUsername').value.trim();
    const pin      = document.getElementById('loginPin').value.trim();
    const errEl    = document.getElementById('loginError');
    errEl.textContent = '';

    if (!username || !pin) { errEl.textContent = 'Please fill in all fields.'; return; }

    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, pin }),
      });
      const data = await res.json();
      if (!res.ok) { errEl.textContent = data.error || 'Login failed.'; return; }
      saveAuth(data.auth_token);
      showScreen('loading');
      await loadUserProfile();
      await loadCategories();
      showScreen('dashboard');
    } catch (err) {
      errEl.textContent = `Connection error: ${err.message}`;
    }
  });

  // Register submit
  document.getElementById('regSubmitBtn').addEventListener('click', async () => {
    const username = document.getElementById('regUsername').value.trim();
    const pin      = document.getElementById('regPin').value.trim();
    const errEl    = document.getElementById('regError');
    errEl.textContent = '';

    if (!username || !pin) { errEl.textContent = 'Please fill in all fields.'; return; }
    if (!/^\d{4,10}$/.test(pin)) { errEl.textContent = 'PIN must be 4–10 numbers.'; return; }

    try {
      const res = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, pin }),
      });
      const data = await res.json();
      if (!res.ok) { errEl.textContent = data.error || 'Registration failed.'; return; }
      saveAuth(data.auth_token);
      showScreen('loading');
      await loadUserProfile();
      await loadCategories();
      showScreen('dashboard');
    } catch (err) {
      errEl.textContent = `Connection error: ${err.message}`;
    }
  });
}

/* =============================================================
   CATEGORIES & PRACTICE SELECTION
   ============================================================= */
async function loadCategories() {
  try {
    const res = await fetch(`${API}/api/categories`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    categories = await res.json();
    renderCategoryCards();
  } catch (err) {
    showError("Could not load category list.", loadCategories);
  }
}

function renderCategoryCards() {
  const grid = document.getElementById('catGrid');
  grid.innerHTML = '';
  categories.forEach(cat => {
    const card = document.createElement('div');
    card.className = `cat-card ${selectedCat === cat.key ? 'selected' : ''}`;
    card.dataset.cat = cat.key;

    const byDiff = cat.by_difficulty || {};
    const pills  = ['easy','medium','hard']
      .filter(d => byDiff[d] > 0)
      .map(d => `<span class="cat-diff-pill ${d}">${d[0].toUpperCase()} ${byDiff[d]}</span>`)
      .join('');

    card.innerHTML = `
      <span class="cat-check-badge">✓ Selected</span>
      <div>
        <span class="cat-icon">${cat.icon}</span>
        <div class="cat-name">${cat.name}</div>
        <div class="cat-count">${cat.question_count} questions</div>
      </div>
      <div class="cat-diff-pills">${pills}</div>`;
    
    card.addEventListener('click', () => {
      document.querySelectorAll('.cat-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedCat     = cat.key;
      selectedCatName = cat.name;
      updateStartPracticeBtn();
    });
    grid.appendChild(card);
  });
}

function setupModeHandlers() {
  // Difficulty buttons
  document.querySelectorAll('#diffRow .diff-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#diffRow .diff-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedDiff = btn.dataset.d;
    });
  });

  // Daily Challenge Start
  document.getElementById('startDailyBtn').addEventListener('click', startDailyChallenge);

  // Practice Quiz Start
  document.getElementById('startPracticeBtn').addEventListener('click', startPracticeQuiz);
}

function updateStartPracticeBtn() {
  const btn = document.getElementById('startPracticeBtn');
  if (selectedCat) {
    btn.disabled    = false;
    btn.textContent = `🎯 Start ${selectedCatName} Practice Quiz`;
  } else {
    btn.disabled    = true;
    btn.textContent = 'Select a category to start practice';
  }
}

/* =============================================================
   START QUIZ (Daily Challenge & Practice)
   ============================================================= */
async function startDailyChallenge() {
  if (!authToken) { showScreen('login'); return; }
  const btn = document.getElementById('startDailyBtn');
  btn.disabled = true;
  btn.textContent = 'Loading Daily Challenge…';

  try {
    const res = await fetch(`${API}/api/questions/daily`, {
      headers: { 'X-Auth-Token': authToken }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(err.error || 'Could not start Daily Challenge');
      await loadUserProfile();
      return;
    }
    const data = await res.json();
    quizQuestions   = data.questions;
    sessionToken    = data.session_token;
    isDailyQuiz     = true;
    selectedCatName = 'Daily Challenge';
    selectedDiff    = 'medium';

    initQuizSession();
  } catch (err) {
    alert(`Failed to launch Daily Challenge: ${err.message}`);
    loadUserProfile();
  }
}

async function startPracticeQuiz() {
  if (!authToken) { showScreen('login'); return; }
  if (!selectedCat) return;

  const btn = document.getElementById('startPracticeBtn');
  btn.disabled = true;
  btn.textContent = 'Loading Questions…';

  try {
    const res = await fetch(
      `${API}/api/questions?category=${selectedCat}&difficulty=${selectedDiff}&count=10`,
      { headers: { 'X-Auth-Token': authToken } }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    const data = await res.json();
    quizQuestions   = data.questions;
    sessionToken    = data.session_token;
    isDailyQuiz     = false;

    initQuizSession();
  } catch (err) {
    showError(`Failed to load quiz questions.\n${err.message}`, () => showScreen('dashboard'));
  } finally {
    updateStartPracticeBtn();
  }
}

function initQuizSession() {
  userAnswers   = quizQuestions.map(q => ({ question_id: q.id, selected_index: null }));
  currentIndex  = 0;
  streak        = 0;
  liveXp        = 0;
  quizStartTime = Date.now();

  showScreen('quiz');
  renderQuestion();
}

/* =============================================================
   QUIZ EXECUTION & TIMER
   ============================================================= */
function renderQuestion() {
  const q = quizQuestions[currentIndex];
  answered = false;

  document.getElementById('qCounter').textContent = `Question ${currentIndex + 1} of ${quizQuestions.length}`;
  document.getElementById('qCategory').textContent = isDailyQuiz ? '🌟 Daily Challenge (+50% XP)' : selectedCatName;
  document.getElementById('qText').textContent = q.question;
  document.getElementById('liveXpPill').textContent = `✨ +${liveXp} XP`;
  document.getElementById('liveStreakPill').textContent = `🔥 ${streak} streak`;
  document.getElementById('feedbackLine').textContent = '';
  document.getElementById('nextBtn').classList.remove('show');

  const progressPct = (currentIndex / quizQuestions.length) * 100;
  document.getElementById('progressFill').style.width = `${progressPct}%`;

  const wrap = document.getElementById('optionsWrap');
  wrap.innerHTML = '';
  const letters = ['A', 'B', 'C', 'D'];

  q.options.forEach((optText, idx) => {
    const btn = document.createElement('button');
    btn.className = 'option';
    btn.innerHTML = `<span class="option-letter">${letters[idx]}</span><span>${optText}</span>`;
    btn.addEventListener('click', () => selectOption(idx));
    wrap.appendChild(btn);
  });

  startTimer();
}

function startTimer() {
  timeLeft = DIFF_TIME[selectedDiff] || 20;
  updateTimerUI();
  clearInterval(timerId);
  timerId = setInterval(() => {
    timeLeft--;
    updateTimerUI();
    if (timeLeft <= 0) {
      clearInterval(timerId);
      if (!answered) handleTimeout();
    }
  }, 1000);
}

function updateTimerUI() {
  document.getElementById('timerNum').textContent = `${timeLeft}s`;
  const pct  = Math.max(0, (timeLeft / DIFF_TIME[selectedDiff]) * 100);
  const fill = document.getElementById('timerFill');
  fill.style.width      = `${pct}%`;
  fill.style.background = pct < 30 ? 'var(--bad)' : pct < 60 ? 'var(--warn)' : 'var(--accent2)';
}

function selectOption(i) {
  if (answered) return;
  answered = true;
  clearInterval(timerId);
  userAnswers[currentIndex].selected_index = i;

  document.querySelectorAll('.option').forEach((el, idx) => {
    el.classList.add('locked');
    if (idx !== i) el.classList.add('dim');
    else el.classList.add('correct');
  });

  streak++;
  const xpGain = selectedDiff === 'hard' ? 25 : selectedDiff === 'medium' ? 15 : 10;
  liveXp += xpGain;

  document.getElementById('liveXpPill').textContent = `✨ +${liveXp} XP`;
  document.getElementById('liveStreakPill').textContent = `🔥 ${streak} streak`;
  document.getElementById('feedbackLine').textContent = 'Answer recorded ✓';
  document.getElementById('nextBtn').classList.add('show');
}

function handleTimeout() {
  answered = true;
  streak = 0;
  document.getElementById('liveStreakPill').textContent = `🔥 0 streak`;
  document.querySelectorAll('.option').forEach(el => el.classList.add('locked', 'dim'));
  document.getElementById('feedbackLine').textContent = "⏱ Time's up!";
  document.getElementById('nextBtn').classList.add('show');
}

function nextQuestion() {
  currentIndex++;
  if (currentIndex >= quizQuestions.length) {
    clearInterval(timerId);
    quizEndTime = Date.now();
    submitQuizAnswers();
  } else {
    renderQuestion();
  }
}

/* =============================================================
   SCORE SUBMISSION & RESULT SCREEN
   ============================================================= */
async function submitQuizAnswers() {
  showScreen('loading');

  try {
    const payload = {
      category:      selectedCat,
      difficulty:    selectedDiff,
      session_token: sessionToken,
      answers:       userAnswers,
    };

    const res = await fetch(`${API}/api/scores`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Token': authToken
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }

    lastSubmissionResult = await res.json();
    renderResultScreen(lastSubmissionResult);
  } catch (err) {
    showError(`Failed to submit quiz scores.\n${err.message}`, () => showScreen('dashboard'));
  }
}

function renderResultScreen(res) {
  showScreen('results');

  // Level Up Banner
  const lvlUpBanner = document.getElementById('levelUpBanner');
  if (res.leveled_up) {
    lvlUpBanner.style.display = 'flex';
    document.getElementById('levelUpText').textContent = `Congratulations! You reached Level ${res.level}! 🎉`;
  } else {
    lvlUpBanner.style.display = 'none';
  }

  // Score Ring & Accuracy
  document.getElementById('scoreNum').textContent = `${res.score}/${res.total}`;
  const pct = res.score / res.total;
  const strokeDash = 327;
  const offset = strokeDash - (pct * strokeDash);
  document.getElementById('ringFg').style.strokeDashoffset = offset;

  const pct100 = Math.round(pct * 100);
  const tag = pct100 === 100 ? '🏆 Perfect Score!' : pct100 >= 80 ? '🌟 Outstanding!' : pct100 >= 50 ? '👍 Good Job!' : '💪 Keep Practicing!';
  document.getElementById('resultTag').textContent = tag;
  document.getElementById('resultSub').textContent = `Accuracy: ${pct100}%`;

  // 4 Metrics Grid
  document.getElementById('resXpEarned').textContent = `+${res.xp_earned} XP`;
  document.getElementById('resXpBreakdown').textContent = res.is_daily ? `Base XP: ${res.base_xp} (+50% Bonus)` : `Base XP: ${res.base_xp}`;
  document.getElementById('resAccuracyVal').textContent = `${pct100}%`;
  document.getElementById('resStreakVal').textContent = `${res.current_streak} Days 🔥`;

  // Average Time Per Question
  const totalSecs = Math.max(1, Math.round((quizEndTime - quizStartTime) / 1000));
  const avgSecs   = (totalSecs / res.total).toFixed(1);
  document.getElementById('resAvgTimeVal').textContent = `${avgSecs}s / Q`;
}

/* =============================================================
   QUESTION REVIEW SCREEN
   ============================================================= */
function showReviewScreen() {
  if (!lastSubmissionResult || !lastSubmissionResult.breakdown) {
    showScreen('dashboard');
    return;
  }

  showScreen('review');
  const container = document.getElementById('reviewList');
  container.innerHTML = '';

  lastSubmissionResult.breakdown.forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'review-card';

    const statusBadge = item.correct
      ? '<span class="review-badge correct">CORRECT ✓</span>'
      : item.selected_index === null
      ? '<span class="review-badge timeout">TIME OUT ⏱</span>'
      : '<span class="review-badge wrong">INCORRECT ❌</span>';

    const letters = ['A', 'B', 'C', 'D'];
    const optionsHtml = item.options.map((opt, oIdx) => {
      let cls = 'review-opt';
      if (oIdx === item.correct_index) cls += ' correct-target';
      if (oIdx === item.selected_index) cls += item.correct ? ' user-correct' : ' user-wrong';

      const prefix = (oIdx === item.correct_index) ? '✔ ' : (oIdx === item.selected_index && !item.correct) ? '✖ ' : '';
      return `<div class="${cls}"><strong>${letters[oIdx]}.</strong> ${prefix}${opt}</div>`;
    }).join('');

    card.innerHTML = `
      <div class="review-top">
        <span class="review-num">Question ${idx + 1}</span>
        ${statusBadge}
      </div>
      <div class="review-qtext">${item.question}</div>
      <div class="review-options">${optionsHtml}</div>
    `;

    container.appendChild(card);
  });
}

/* =============================================================
   LEADERBOARD SCREEN
   ============================================================= */
async function openLeaderboard(type = 'xp') {
  lbActiveType = type;
  showScreen('leaderboard');

  const tabXp  = document.getElementById('lbTabXp');
  const tabCat = document.getElementById('lbTabCat');
  const catRow = document.getElementById('lbCatRow');

  tabXp.onclick  = () => openLeaderboard('xp');
  tabCat.onclick = () => openLeaderboard('category');

  if (type === 'xp') {
    tabXp.classList.add('active');
    tabCat.classList.remove('active');
    catRow.style.display = 'none';
    fetchLeaderboardData('xp');
  } else {
    tabCat.classList.add('active');
    tabXp.classList.remove('active');
    catRow.style.display = 'flex';
    renderLbCategoryRow();
    fetchLeaderboardData('category', lbActiveCat);
  }
}

function renderLbCategoryRow() {
  const catRow = document.getElementById('lbCatRow');
  catRow.innerHTML = '';
  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = `lb-cat-btn ${cat.key === lbActiveCat ? 'active' : ''}`;
    btn.textContent = `${cat.icon} ${cat.name}`;
    btn.onclick = () => {
      lbActiveCat = cat.key;
      renderLbCategoryRow();
      fetchLeaderboardData('category', cat.key);
    };
    catRow.appendChild(btn);
  });
}

async function fetchLeaderboardData(type, category = 'general') {
  const tableWrap = document.getElementById('lbTableWrap');
  tableWrap.innerHTML = '<div class="spinner" style="margin:40px auto;"></div>';

  try {
    const url = type === 'xp'
      ? `${API}/api/leaderboard?type=xp`
      : `${API}/api/leaderboard?type=category&category=${category}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data || data.length === 0) {
      tableWrap.innerHTML = '<p class="empty-text" style="padding:40px;">No leaderboard scores recorded yet.</p>';
      return;
    }

    const rowsHtml = data.map((item, idx) => {
      const isMe = userProfile && item.player_name.toLowerCase() === userProfile.username.toLowerCase();
      const rankMedal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}`;
      const rankCls   = idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : '';

      if (type === 'xp') {
        return `
          <div class="lb-row ${isMe ? 'me' : ''}">
            <div class="lb-left">
              <span class="lb-rank ${rankCls}">${rankMedal}</span>
              <span class="lb-name">${item.player_name} ${isMe ? '(You)' : ''}</span>
            </div>
            <div class="lb-right">
              <span class="lb-lvl">Lv. ${item.level}</span>
              <span class="lb-xp">⚡ ${item.xp} XP</span>
            </div>
          </div>`;
      } else {
        return `
          <div class="lb-row ${isMe ? 'me' : ''}">
            <div class="lb-left">
              <span class="lb-rank ${rankCls}">${rankMedal}</span>
              <span class="lb-name">${item.player_name} ${isMe ? '(You)' : ''}</span>
            </div>
            <div class="lb-right">
              <span style="color:var(--text);">${item.score}/${item.total_questions}</span>
              <span class="lb-xp">+${item.xp_earned} XP</span>
            </div>
          </div>`;
      }
    }).join('');

    tableWrap.innerHTML = rowsHtml;
  } catch (err) {
    tableWrap.innerHTML = `<p style="padding:40px;text-align:center;color:var(--bad);">Failed to load leaderboard.\n${err.message}</p>`;
  }
}

/* =============================================================
   SCREEN ROUTER & UTILS
   ============================================================= */
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(`screen-${name}`);
  if (el) el.classList.add('active');
}

function showError(msg, retryFn) {
  document.getElementById('errorText').textContent = msg;
  const btn = document.getElementById('retryLoadBtn');
  btn.onclick = () => {
    showScreen('loading');
    if (retryFn) retryFn();
  };
  showScreen('error');
}
