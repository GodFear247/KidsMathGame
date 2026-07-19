/* ===================================================
   Kids Math Game - Web Logic & Engine (app.js)
   Integrated with High-Reliability Online Burmese & English TTS
   =================================================== */

// State Object
const state = {
  currentScreen: 'MENU',
  difficulty: 'EASY',
  allowedOps: ['+'],
  questions: [],
  currentIndex: 0,
  score: 0,
  combo: 0,
  earnedCoins: 0,
  voiceEnabled: true,
  lang: 'EN', // 'EN' or 'MM'
  coins: 0,
  unlockedAvatars: ['smile'],
  equippedAvatar: 'smile'
};

// Shop Catalog
const SHOP_ITEMS = [
  { id: 'dog', name: 'Dog', price: 20 },
  { id: 'cat', name: 'Cat', price: 50 },
  { id: 'panda', name: 'Panda', price: 100 },
  { id: 'unicorn', name: 'Unicorn', price: 200 }
];

// Dialogue Dictionary
const DIALOGUE = {
  WELCOME: { EN: "Choose a game mode to start!", MM: "ကစားမယ့်ပုံစံကို ရွေးချယ်ပေးပါ!" },
  SELECT_DIFF: { EN: "Select a difficulty level.", MM: "အခက်အခဲ အဆင့်ကို ရွေးချယ်ပေးပါ!" },
  CORRECT: { EN: "Correct! Great job!", MM: "မှန်ပါတယ်။ အရမ်းတော်တာပဲ!" },
  WRONG: { EN: "Oops! Try again.", MM: "မှားနေပါတယ်။ ထပ်ကြိုးစားကြည့်ပါဦးနော်။" },
  GREET_EN: { EN: "English voice activated.", MM: "Hello!" },
  GREET_MM: { EN: "Burmese voice activated.", MM: "မြန်မာအသံ ပြောင်းလိုက်ပါပြီ။" }
};

// ===================================================
// Reliable Online Speech Engine (Burmese & English)
// ===================================================
class EdgeTTSManager {
  constructor() {
    this.voices = {
      MM: 'my-MM-NilarNeural',
      EN: 'en-US-AriaNeural'
    };
    this.currentAudio = null;
  }

  speak(text, lang = 'EN') {
    if (!state.voiceEnabled) return;

    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    const ttsLang = lang === 'MM' ? 'my' : 'en';

    // Primary Stream: High-compatibility HTTPS endpoint for GitHub Pages
    const streamUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text)}&tl=${ttsLang}&client=gtx`;
    
    const audio = new Audio();
    audio.crossOrigin = "anonymous";
    audio.src = streamUrl;
    audio.playbackRate = lang === 'MM' ? 1.25 : 1.0;
    this.currentAudio = audio;

    audio.play().catch(err => {
      console.warn("Primary Audio Stream failed, switching fallback:", err);
      const altUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text)}&tl=${ttsLang}&client=tw-ob`;
      const altAudio = new Audio(altUrl);
      altAudio.playbackRate = lang === 'MM' ? 1.25 : 1.0;
      this.currentAudio = altAudio;
      
      altAudio.play().catch(e => {
        console.warn("SpeechSynthesis Fallback:", e);
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = lang === 'MM' ? 'my-MM' : 'en-US';
          utterance.rate = lang === 'MM' ? 1.22 : 0.95;
          window.speechSynthesis.speak(utterance);
        }
      });
    });
  }
}

const edgeTTS = new EdgeTTSManager();

function speakText(text) {
  edgeTTS.speak(text, state.lang);
}

function speakDialogue(key) {
  if (state.voiceEnabled && DIALOGUE[key]) {
    speakText(DIALOGUE[key][state.lang]);
  }
}

// ===================================================
// LocalStorage Save System
// ===================================================
function loadGameData() {
  try {
    const saved = localStorage.getItem('kids_math_save_data');
    if (saved) {
      const data = JSON.parse(saved);
      state.coins = data.coins || 0;
      state.unlockedAvatars = data.unlockedAvatars || ['smile'];
      state.equippedAvatar = data.equippedAvatar || 'smile';
    }
  } catch (e) {
    console.error("Load save data error:", e);
  }
}

function saveGameData() {
  try {
    const data = {
      coins: state.coins,
      unlockedAvatars: state.unlockedAvatars,
      equippedAvatar: state.equippedAvatar
    };
    localStorage.setItem('kids_math_save_data', JSON.stringify(data));
  } catch (e) {
    console.error("Save game data error:", e);
  }
}

// ===================================================
// Web Audio Synthesizer (Upbeat Kids Marimba BGM & SFX)
// ===================================================
class SoundEngine {
  constructor() {
    this.ctx = null;
    this.masterBGMGain = null;
    this.bgmPlaying = false;
    this.bgmTimer = null;
    
    // Playful 8-bar Kids Nursery Melody (Twinkle / Playground Style)
    this.melody = [
      261.63, 261.63, 392.00, 392.00, 440.00, 440.00, 392.00, 0,
      349.23, 349.23, 329.63, 329.63, 293.66, 293.66, 261.63, 0,
      392.00, 392.00, 349.23, 349.23, 329.63, 329.63, 293.66, 0,
      392.00, 392.00, 349.23, 349.23, 329.63, 329.63, 293.66, 0,
      261.63, 261.63, 392.00, 392.00, 440.00, 440.00, 392.00, 0,
      349.23, 349.23, 329.63, 329.63, 293.66, 293.66, 261.63, 0
    ];
    this.bass = [
      130.81, 196.00, 130.81, 196.00, 174.61, 220.00, 130.81, 196.00,
      174.61, 130.81, 164.81, 130.81, 196.00, 146.83, 130.81, 196.00,
      130.81, 196.00, 174.61, 220.00, 130.81, 196.00, 196.00, 146.83,
      130.81, 196.00, 174.61, 220.00, 130.81, 196.00, 196.00, 146.83,
      130.81, 196.00, 130.81, 196.00, 174.61, 220.00, 130.81, 196.00,
      174.61, 130.81, 164.81, 130.81, 196.00, 146.83, 130.81, 196.00
    ];
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterBGMGain = this.ctx.createGain();
      this.masterBGMGain.gain.value = 0.15; // 15% default volume
      this.masterBGMGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  setBGMVolume(val) {
    this.init();
    if (this.masterBGMGain) {
      const gainVal = parseFloat(val) * 0.35;
      this.masterBGMGain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
    }
  }

  startBGM() {
    this.init();
    if (this.bgmPlaying) return;
    this.bgmPlaying = true;
    let step = 0;

    this.bgmTimer = setInterval(() => {
      if (!this.bgmPlaying || !this.ctx) return;
      const now = this.ctx.currentTime;
      
      const mFreq = this.melody[step % this.melody.length];
      const bFreq = this.bass[step % this.bass.length];
      step++;

      // Playful Marimba Lead
      if (mFreq > 0) {
        const osc1 = this.ctx.createOscillator();
        const osc2 = this.ctx.createOscillator();
        const leadGain = this.ctx.createGain();

        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(mFreq, now);
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(mFreq * 2, now);

        leadGain.gain.setValueAtTime(0.12, now);
        leadGain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

        osc1.connect(leadGain);
        osc2.connect(leadGain);
        leadGain.connect(this.masterBGMGain);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.25);
        osc2.stop(now + 0.25);
      }

      // Bouncy Bass
      if (bFreq > 0) {
        const bassOsc = this.ctx.createOscillator();
        const bassGain = this.ctx.createGain();

        bassOsc.type = 'sine';
        bassOsc.frequency.setValueAtTime(bFreq, now);

        bassGain.gain.setValueAtTime(0.08, now);
        bassGain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

        bassOsc.connect(bassGain);
        bassGain.connect(this.masterBGMGain);

        bassOsc.start(now);
        bassOsc.stop(now + 0.22);
      }
    }, 280); // Upbeat 280ms tempo
  }

  stopBGM() {
    this.bgmPlaying = false;
    if (this.bgmTimer) {
      clearInterval(this.bgmTimer);
      this.bgmTimer = null;
    }
  }

  playCorrectSFX() {
    this.init();
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(523.25, now);
    osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.1);
    osc.frequency.exponentialRampToValueAtTime(783.99, now + 0.2);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.4);
  }

  playWrongSFX() {
    this.init();
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(160, now);
    osc.frequency.exponentialRampToValueAtTime(100, now + 0.25);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  }

  playUnlockSFX() {
    this.init();
    const now = this.ctx.currentTime;
    [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, now + idx * 0.08);

      gain.gain.setValueAtTime(0.2, now + idx * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.08 + 0.25);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now + idx * 0.08);
      osc.stop(now + idx * 0.08 + 0.25);
    });
  }
}

const sounds = new SoundEngine();

// ===================================================
// Vector SVG Avatar Generator
// ===================================================
function getAvatarSVG(avatarId) {
  switch (avatarId) {
    case 'dog':
      return `
        <svg viewBox="0 0 100 100">
          <ellipse cx="25" cy="40" rx="14" ry="22" fill="#8C501E"/>
          <ellipse cx="75" cy="40" rx="14" ry="22" fill="#8C501E"/>
          <circle cx="50" cy="52" r="40" fill="#D7964B"/>
          <ellipse cx="50" cy="62" rx="22" ry="16" fill="#FFF5E6"/>
          <circle cx="50" cy="56" r="6" fill="#281E19"/>
          <ellipse cx="50" cy="72" rx="7" ry="9" fill="#FF7896"/>
          <circle cx="36" cy="44" r="5" fill="#1E1914"/>
          <circle cx="64" cy="44" r="5" fill="#1E1914"/>
          <circle cx="34" cy="42" r="2" fill="#FFF"/>
          <circle cx="62" cy="42" r="2" fill="#FFF"/>
        </svg>`;

    case 'cat':
      return `
        <svg viewBox="0 0 100 100">
          <polygon points="15,45 10,15 40,30" fill="#FFA050"/>
          <polygon points="85,45 90,15 60,30" fill="#FFA050"/>
          <polygon points="20,42 16,20 38,32" fill="#FFBEC8"/>
          <polygon points="80,42 84,20 62,32" fill="#FFBEC8"/>
          <circle cx="50" cy="54" r="38" fill="#FFAB5A"/>
          <ellipse cx="50" cy="64" rx="16" ry="11" fill="#FFF5EB"/>
          <polygon points="50,60 44,56 56,56" fill="#FF6E8C"/>
          <ellipse cx="36" cy="48" rx="7" ry="10" fill="#3CC882"/>
          <ellipse cx="64" cy="48" rx="7" ry="10" fill="#3CC882"/>
          <ellipse cx="36" cy="48" rx="2.5" ry="8" fill="#141414"/>
          <ellipse cx="64" cy="48" rx="2.5" ry="8" fill="#141414"/>
        </svg>`;

    case 'panda':
      return `
        <svg viewBox="0 0 100 100">
          <circle cx="22" cy="22" r="16" fill="#232328"/>
          <circle cx="78" cy="22" r="16" fill="#232328"/>
          <circle cx="50" cy="50" r="40" fill="#FAF7FC" stroke="#DCDCE1" stroke-width="2"/>
          <ellipse cx="36" cy="46" rx="12" ry="15" fill="#232328" transform="rotate(15 36 46)"/>
          <ellipse cx="64" cy="46" rx="12" ry="15" fill="#232328" transform="rotate(-15 64 46)"/>
          <circle cx="38" cy="44" r="3" fill="#FFF"/>
          <circle cx="62" cy="44" r="3" fill="#FFF"/>
          <ellipse cx="50" cy="60" rx="6" ry="4" fill="#232328"/>
          <path d="M 44 64 Q 50 72 56 64" fill="none" stroke="#232328" stroke-width="2.5" stroke-linecap="round"/>
        </svg>`;

    case 'unicorn':
      return `
        <svg viewBox="0 0 100 100">
          <circle cx="35" cy="35" r="16" fill="#FF8CC8"/>
          <circle cx="25" cy="50" r="18" fill="#8CE6FF"/>
          <circle cx="35" cy="65" r="16" fill="#C8A0FF"/>
          <circle cx="50" cy="52" r="38" fill="#FAF5FF"/>
          <polygon points="50,4 42,32 58,32" fill="#FFD700"/>
          <line x1="50" y1="4" x2="46" y2="32" stroke="#FFF5A0" stroke-width="2"/>
          <polygon points="68,30 82,10 80,30" fill="#FAF5FF"/>
          <polygon points="70,28 80,14 80,28" fill="#FFB4D2"/>
          <circle cx="62" cy="62" r="14" fill="#FFE1EC"/>
          <path d="M 40 46 Q 50 38 60 46" fill="none" stroke="#3C2846" stroke-width="3" stroke-linecap="round"/>
        </svg>`;

    case 'smile':
    default:
      return `
        <svg viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="44" fill="#FFD633" stroke="#E6B414" stroke-width="3"/>
          <circle cx="36" cy="40" r="6" fill="#282828"/>
          <circle cx="64" cy="40" r="6" fill="#282828"/>
          <path d="M 32 58 Q 50 78 68 58" fill="none" stroke="#282828" stroke-width="5" stroke-linecap="round"/>
        </svg>`;
  }
}

// ===================================================
// Question Generator Algorithm
// ===================================================
function generateQuestions(total = 10, allowedOps = ["+"], difficulty = "EASY") {
  const result = [];
  const used = new Set();

  while (result.length < total) {
    const op = allowedOps[Math.floor(Math.random() * allowedOps.length)];
    let a, b, ans, displayOp;

    if (op === "+") {
      if (difficulty === "EASY") { a = rand(1, 10); b = rand(1, 10); }
      else if (difficulty === "MEDIUM") { a = rand(10, 50); b = rand(10, 50); }
      else { a = rand(50, 100); b = rand(50, 100); }
      ans = a + b;
      displayOp = "+";
    } else if (op === "-") {
      if (difficulty === "EASY") { a = rand(1, 10); b = rand(1, 10); }
      else if (difficulty === "MEDIUM") { a = rand(10, 50); b = rand(10, 50); }
      else { a = rand(50, 100); b = rand(50, 100); }
      if (a < b) [a, b] = [b, a];
      ans = a - b;
      displayOp = "-";
    } else if (op === "*") {
      if (difficulty === "EASY") { a = rand(1, 5); b = rand(1, 5); }
      else if (difficulty === "MEDIUM") { a = rand(2, 10); b = rand(2, 10); }
      else { a = rand(5, 15); b = rand(5, 15); }
      ans = a * b;
      displayOp = "×";
    } else { // "/"
      if (difficulty === "EASY") { b = rand(1, 5); ans = rand(1, 5); }
      else if (difficulty === "MEDIUM") { b = rand(2, 10); ans = rand(2, 10); }
      else { b = rand(3, 12); ans = rand(5, 15); }
      a = b * ans;
      displayOp = "÷";
    }

    const key = `${a}${op}${b}`;
    if (used.has(key)) continue;
    used.add(key);

    const wrong = new Set();
    while (wrong.size < 3) {
      let offset;
      if (op === "*" || op === "/") {
        offset = [ -2, -1, 1, 2, b, -b ][Math.floor(Math.random() * 6)] || 1;
      } else {
        const span = difficulty === "EASY" ? 4 : difficulty === "MEDIUM" ? 10 : 20;
        offset = rand(-span, span);
      }
      if (offset === 0) offset = 2;
      const x = ans + offset;
      if (x >= 0 && x !== ans) wrong.add(x);
    }

    const options = Array.from(wrong);
    options.push(ans);
    shuffle(options);

    result.push({ a, b, op, displayOp, qStr: `${a} ${displayOp} ${b}`, answer: ans, options });
  }

  return result;
}

function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

// ===================================================
// Confetti Animation Engine
// ===================================================
class ConfettiEngine {
  constructor() {
    this.canvas = document.getElementById('confetti-canvas');
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.animId = null;

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = this.canvas.parentElement.clientHeight;
  }

  spawn(x, y, count = 40) {
    const colors = ['#FF6384', '#63D180', '#63A8FF', '#FFDD59', '#FF9F1C', '#C681FF'];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: x || this.canvas.width / 2,
        y: y || this.canvas.height / 2,
        vx: (Math.random() - 0.5) * 14,
        vy: Math.random() * -12 - 4,
        size: Math.random() * 8 + 6,
        color: colors[Math.floor(Math.random() * colors.length)],
        timer: 80,
        maxTimer: 80
      });
    }
    if (!this.animId) this.loop();
  }

  loop() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.5;
      p.timer--;

      const alpha = Math.max(0, p.timer / p.maxTimer);
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = alpha;
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size / 2, 0, Math.PI * 2);
      this.ctx.fill();

      if (p.timer <= 0) {
        this.particles.splice(i, 1);
      }
    }

    if (this.particles.length > 0) {
      this.animId = requestAnimationFrame(() => this.loop());
    } else {
      this.animId = null;
    }
  }
}

const confetti = new ConfettiEngine();

// ===================================================
// UI & Screen Controller
// ===================================================
function switchScreen(screenId) {
  state.currentScreen = screenId;
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(`screen-${screenId.toLowerCase()}`).classList.add('active');

  const btnHome = document.getElementById('btn-home');
  if (screenId === 'MENU') {
    btnHome.style.opacity = '0.4';
    updateMenuUI();
  } else {
    btnHome.style.opacity = '1';
  }

  if (screenId === 'SHOP') renderShop();
}

function updateMenuUI() {
  document.getElementById('equipped-avatar-display').innerHTML = getAvatarSVG(state.equippedAvatar);
  document.getElementById('menu-coin-count').innerText = state.coins;
}

function startMode(ops) {
  sounds.startBGM();
  state.allowedOps = ops === 'mix' ? ['+', '-', '*', '/'] : [ops];
  switchScreen('DIFFICULTY');
  speakDialogue('SELECT_DIFF');
}

function startGame(difficulty) {
  sounds.startBGM();
  state.difficulty = difficulty;
  state.questions = generateQuestions(10, state.allowedOps, difficulty);
  state.currentIndex = 0;
  state.score = 0;
  state.combo = 0;
  
  switchScreen('PLAYING');
  loadQuestion();

  if (state.lang === 'EN') {
    speakText(`Starting ${difficulty} mode! Let's go!`);
  } else {
    speakText("စတင်လိုက်ရအောင်!");
  }
}

function loadQuestion() {
  const q = state.questions[state.currentIndex];
  document.getElementById('q-current').innerText = state.currentIndex + 1;
  document.getElementById('q-total').innerText = state.questions.length;
  document.getElementById('current-score').innerText = state.score;

  const pct = (state.currentIndex / state.questions.length) * 100;
  document.getElementById('progress-bar-fill').style.width = `${pct}%`;

  document.getElementById('question-text').innerText = `${q.qStr} = ?`;

  const feedback = document.getElementById('msg-feedback');
  feedback.classList.add('hidden');
  feedback.innerText = '';

  const streakBanner = document.getElementById('streak-banner');
  if (state.combo > 1) {
    streakBanner.classList.remove('hidden');
    document.getElementById('streak-count').innerText = state.combo;
  } else {
    streakBanner.classList.add('hidden');
  }

  const optionBtns = document.querySelectorAll('.option-btn');
  optionBtns.forEach((btn, idx) => {
    btn.innerText = q.options[idx];
    btn.disabled = false;
    btn.className = 'option-btn';
  });
}

function readCurrentQuestion() {
  const q = state.questions[state.currentIndex];
  const opWordsEN = { "+": "plus", "-": "minus", "*": "times", "/": "divided by" };
  const opWordsMM = { "+": "အပေါင်း", "-": "အနုတ်", "*": "အမြှောက်", "/": "အစား" };

  let text = "";
  if (state.lang === 'EN') {
    text = `What is ${q.a} ${opWordsEN[q.op]} ${q.b}`;
  } else {
    text = `${q.a} ${opWordsMM[q.op]} ${q.b} ညီမျှခြင်း ဘယ်လောက်လဲ`;
  }
  speakText(text);
}

function selectAnswer(choiceIndex) {
  const q = state.questions[state.currentIndex];
  const selected = q.options[choiceIndex];
  const optionBtns = document.querySelectorAll('.option-btn');

  optionBtns.forEach(btn => btn.disabled = true);

  const feedback = document.getElementById('msg-feedback');
  feedback.classList.remove('hidden');

  if (selected === q.answer) {
    state.score++;
    state.combo++;
    optionBtns[choiceIndex].classList.add('correct');
    sounds.playCorrectSFX();

    let msg = "🌟 Awesome! Correct!";
    if (state.combo === 2) msg = "🚀 Double Correct! x2";
    else if (state.combo === 3) msg = "🔥 Combo x3! Amazing!";
    else if (state.combo > 3) msg = `🎇 On Fire! x${state.combo}!`;

    feedback.innerText = msg;
    feedback.style.color = "#2A9D8F";

    const rect = optionBtns[choiceIndex].getBoundingClientRect();
    confetti.spawn(rect.left + rect.width / 2, rect.top + rect.height / 2, 40 + state.combo * 10);
    speakDialogue('CORRECT');

  } else {
    state.combo = 0;
    optionBtns[choiceIndex].classList.add('wrong');
    sounds.playWrongSFX();

    document.getElementById('math-card').classList.add('shake');
    setTimeout(() => document.getElementById('math-card').classList.remove('shake'), 400);

    optionBtns.forEach((btn, idx) => {
      if (q.options[idx] === q.answer) btn.classList.add('correct');
    });

    feedback.innerText = "🤔 Oops! Try again.";
    feedback.style.color = "#D62828";
    speakDialogue('WRONG');
  }

  setTimeout(() => {
    state.currentIndex++;
    if (state.currentIndex >= state.questions.length) {
      showResult();
    } else {
      loadQuestion();
    }
  }, 1400);
}

function showResult() {
  switchScreen('RESULT');
  const pct = state.score / state.questions.length;
  let msg = "Keep practicing!";
  let stars = 0;

  if (pct === 1) { msg = "Perfect! Amazing Job!"; stars = 3; }
  else if (pct >= 0.7) { msg = "Great job!"; stars = 2; }
  else if (pct >= 0.4) { msg = "Good effort!"; stars = 1; }

  document.getElementById('final-score-display').innerText = `${state.score} / ${state.questions.length}`;
  document.getElementById('final-message').innerText = msg;

  [1, 2, 3].forEach(i => {
    const starEl = document.getElementById(`star-${i}`);
    if (i <= stars) {
      starEl.className = 'star-item earned';
    } else {
      starEl.className = 'star-item grey';
    }
  });

  state.earnedCoins = (state.score * 5) + (state.combo * 2);
  state.coins += state.earnedCoins;
  saveGameData();

  document.getElementById('coins-earned-display').innerText = `+${state.earnedCoins} 🪙 Earned!`;
  if (state.score > 0) confetti.spawn(null, null, 60);

  if (state.lang === 'EN') {
    speakText(`Game Finished! Your score is ${state.score}`);
  } else {
    speakText(`ဂိမ်းပြီးသွားပါပြီ။ သင့်ရမှတ်ကတော့ ${state.score} မှတ်ပါ။`);
  }
}

function renderShop() {
  document.getElementById('shop-coin-count').innerText = state.coins;
  const container = document.getElementById('shop-items-container');
  container.innerHTML = '';

  SHOP_ITEMS.forEach(item => {
    const isEquipped = state.equippedAvatar === item.id;
    const isUnlocked = state.unlockedAvatars.includes(item.id);

    const card = document.createElement('div');
    card.className = 'shop-item-card';

    card.innerHTML = `
      <div class="shop-item-info">
        <div class="shop-item-avatar">${getAvatarSVG(item.id)}</div>
        <div class="shop-item-details">
          <h4>${item.name}</h4>
          <p>${item.price} 🪙</p>
        </div>
      </div>
      <button class="shop-buy-btn ${isEquipped ? 'btn-easy' : isUnlocked ? 'btn-med' : 'btn-mul'}">
        ${isEquipped ? 'Equipped' : isUnlocked ? 'Equip' : 'Buy'}
      </button>
    `;

    const btn = card.querySelector('.shop-buy-btn');
    btn.addEventListener('click', () => {
      if (isUnlocked) {
        state.equippedAvatar = item.id;
        saveGameData();
        renderShop();
      } else {
        if (state.coins >= item.price) {
          state.coins -= item.price;
          state.unlockedAvatars.push(item.id);
          state.equippedAvatar = item.id;
          saveGameData();
          sounds.playUnlockSFX();
          speakText("Item unlocked!");
          renderShop();
        }
      }
    });

    container.appendChild(card);
  });
}

// ===================================================
// Event Listeners & Bootstrapping
// ===================================================
document.addEventListener('DOMContentLoaded', () => {
  loadGameData();
  updateMenuUI();

  // Initialize BGM on first user interaction
  const initAudioOnUserClick = () => {
    sounds.startBGM();
    document.removeEventListener('click', initAudioOnUserClick);
  };
  document.addEventListener('click', initAudioOnUserClick);

  // Music Volume Slider Listener
  document.getElementById('music-slider').addEventListener('input', (e) => {
    sounds.setBGMVolume(e.target.value);
  });

  // Mode Selection
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => startMode(btn.dataset.op));
  });

  // Difficulty Selection
  document.querySelectorAll('.diff-btn').forEach(btn => {
    btn.addEventListener('click', () => startGame(btn.dataset.diff));
  });

  // Navigation Controls
  document.getElementById('btn-home').addEventListener('click', () => switchScreen('MENU'));
  document.getElementById('btn-diff-back').addEventListener('click', () => switchScreen('MENU'));
  document.getElementById('btn-shop-trigger').addEventListener('click', () => switchScreen('SHOP'));
  document.getElementById('btn-shop-back').addEventListener('click', () => switchScreen('MENU'));
  document.getElementById('btn-result-menu').addEventListener('click', () => switchScreen('MENU'));
  document.getElementById('btn-play-again').addEventListener('click', () => startGame(state.difficulty));

  // Audio & Language Controls
  document.getElementById('btn-lang').addEventListener('click', () => {
    state.lang = state.lang === 'EN' ? 'MM' : 'EN';
    document.getElementById('btn-lang').innerText = state.lang;
    speakDialogue(state.lang === 'EN' ? 'GREET_EN' : 'GREET_MM');
  });

  document.getElementById('btn-voice').addEventListener('click', () => {
    state.voiceEnabled = !state.voiceEnabled;
    document.getElementById('btn-voice').innerText = state.voiceEnabled ? '🔊' : '🔇';
  });

  // Answer Choice Buttons
  document.querySelectorAll('.option-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.index);
      selectAnswer(idx);
    });
  });

  document.getElementById('btn-read-q').addEventListener('click', readCurrentQuestion);
});
