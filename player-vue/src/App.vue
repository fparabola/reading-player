<template>
  <div class="app-shell">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>

    <main class="player-page">
      <header class="top-bar panel">
        <div class="brand">
          <div class="brand-icon"><span></span><span></span></div>
          <span class="brand-text">书籍与章节</span>
        </div>

        <div class="top-center">
          <select v-model="currentChapter" class="chapter-select" @change="onChapterSelect">
            <option v-for="chapter in chapterOptions" :key="chapter" :value="chapter">{{ chapter }}</option>
          </select>
        </div>

        <div class="top-actions">
          <button class="pill-switch" type="button" @click="isPlaying ? pausePlayback() : startPlayback()">
            <span class="switch-track" :class="{ active: isPlaying }"><span class="switch-thumb"></span></span>
            <span>{{ isPlaying ? "朗读中" : "已暂停" }}</span>
          </button>
          <button class="ghost-button" type="button">设置</button>
          <button class="ghost-button" type="button">更多</button>
        </div>
      </header>

      <section class="progress-strip">
        <div class="progress-meta">
          <span>本章进度 {{ chapterProgress }}%</span>
          <span>·</span>
          <span>{{ currentSentenceIndex + 1 }} / {{ safeSentenceCount }} 句</span>
        </div>
        <div class="progress-line"><div class="progress-line-fill" :style="{ width: `${chapterProgress}%` }"></div></div>
      </section>

      <section class="workspace">
        <section class="main-stage panel">
          <div class="mode-badge">点击句子可单句播放</div>
          <div class="sentence-counter">{{ Math.min(currentSentenceIndex + 1, safeSentenceCount) }} / {{ safeSentenceCount }}</div>

          <button class="nav-arrow left" type="button" @click="previousPage">‹</button>
          <button class="nav-arrow right" type="button" @click="nextPage">›</button>

          <div class="sentence-stage">
            <p class="english-sentence">
              <template v-for="(segment, index) in highlightedSentence.segments" :key="`${segment.text}-${index}`">
                <span :class="{ accent: segment.highlight }">{{ segment.text }}</span>
              </template>
            </p>
            <p class="chinese-sentence">{{ highlightedSentence.translation }}</p>
          </div>

          <div class="sentence-actions">
            <button class="mini-button" type="button" @click="speakText(highlightedSentence.english)">单句播放</button>
            <button class="mini-button active" type="button" @click="toggleWord(highlightedSentence.keyword)">生词</button>
            <button class="mini-icon" type="button">☰</button>
          </div>

          <div class="transport">
            <button class="rate-chip" type="button" @click="cycleRate">
              <span class="rotate">⟳</span>
              <span>{{ playbackRate.toFixed(1) }}x</span>
              <span>语速</span>
            </button>

            <div class="transport-buttons">
              <button class="transport-button" type="button" @click="goToStart">|◀</button>
              <button class="transport-button primary" type="button" @click="isPlaying ? pausePlayback() : startPlayback()">
                {{ isPlaying ? "❚❚" : "▶" }}
              </button>
              <button class="transport-button" type="button" @click="goToEnd">▶|</button>
            </div>

            <button class="follow-button" type="button" @click="followMode = !followMode" :class="{ active: followMode }">跟读模式</button>
          </div>

          <div class="timeline">
            <input
              v-model="progressValue"
              class="timeline-range"
              type="range"
              min="0"
              :max="Math.max(safeSentenceCount - 1, 0)"
              step="1"
              @input="onSeek"
            />
            <div class="timeline-labels">
              <span>{{ elapsedLabel }}</span>
              <span>{{ durationLabel }}</span>
            </div>
          </div>
        </section>

        <aside class="settings panel">
          <div class="note-chip">生词本 <span>{{ vocabularyCount }}</span></div>

          <div class="settings-group">
            <h3>朗读设置</h3>
            <label class="setting-label">语速</label>
            <div class="rate-tabs">
              <button
                v-for="rate in rateOptions"
                :key="rate"
                type="button"
                class="rate-tab"
                :class="{ active: playbackRate === rate }"
                @click="playbackRate = rate"
              >
                {{ rate.toFixed(1) }}x
              </button>
            </div>
            <input v-model="playbackRate" class="speed-slider" type="range" min="0.8" max="1.4" step="0.1" />
            <div class="slider-legend"><span>慢</span><span>正常</span><span>快</span></div>

            <div class="toggle-row">
              <span>自动朗读下一句</span>
              <button class="inline-switch" :class="{ active: autoPlayNext }" type="button" @click="autoPlayNext = !autoPlayNext"></button>
            </div>
            <div class="toggle-row">
              <span>高亮当前句</span>
              <button class="inline-switch" :class="{ active: highlightCurrent }" type="button" @click="highlightCurrent = !highlightCurrent"></button>
            </div>
          </div>

          <div class="settings-group">
            <h3>解析设置</h3>
            <div class="toggle-row">
              <span>自动翻译</span>
              <button class="inline-switch" :class="{ active: autoTranslate }" type="button" @click="autoTranslate = !autoTranslate"></button>
            </div>
            <div class="toggle-row">
              <span>语法解析</span>
              <button class="inline-switch" :class="{ active: autoAnalyze }" type="button" @click="autoAnalyze = !autoAnalyze"></button>
            </div>
          </div>

          <div class="settings-group">
            <h3>外观</h3>
            <div class="theme-row">
              <span>主题</span>
              <div class="theme-toggle">
                <button type="button">☼</button>
                <button type="button" class="active">☾</button>
              </div>
            </div>
            <div class="font-row">
              <span>字体大小</span>
              <div class="font-scale">
                <button type="button">A-</button>
                <button type="button" class="active">A</button>
                <button type="button">A+</button>
              </div>
            </div>
          </div>

          <div class="settings-group">
            <h3>高级</h3>
            <div class="model-row">
              <span>模型</span>
              <button class="select-pill" type="button">{{ analysisModel }}</button>
            </div>
          </div>
        </aside>
      </section>

      <section class="insight-tabs panel">
        <button v-for="tab in tabs" :key="tab" type="button" class="tab-button" :class="{ active: activeTab === tab }" @click="activeTab = tab">
          {{ tab }}
          <span v-if="tab === '词汇'">{{ vocabularyCount }}</span>
        </button>
      </section>

      <section class="insight-grid">
        <article class="info-card panel">
          <h3>翻译</h3>
          <p>{{ highlightedSentence.translation }}</p>
          <p class="muted">这里的 “{{ highlightedSentence.keyword }}” 表示 “{{ highlightedSentence.keywordMeaning }}”。</p>
        </article>

        <article class="info-card panel">
          <h3>语法解析</h3>
          <p>{{ highlightedSentence.grammar }}</p>
          <ul class="bullet-list">
            <li v-for="point in highlightedSentence.grammarPoints" :key="point">{{ point }}</li>
          </ul>
        </article>

        <article class="info-card panel vocab-card">
          <div class="card-title-row">
            <h3>生词</h3>
            <button class="export-button" type="button">导出</button>
          </div>
          <div class="vocab-list">
            <div v-for="item in vocabularyItems" :key="item.word" class="vocab-item">
              <div>
                <strong>{{ item.word }}</strong>
                <span>{{ item.pos }}</span>
              </div>
              <p>{{ item.meaning }}</p>
              <button type="button" class="star" @click="toggleWord(item.word)">{{ item.saved ? "★" : "☆" }}</button>
            </div>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

const API_URL = "http://localhost:8000";
const DEFAULT_MIN_SIZE = 500;
const ANALYSIS_MODEL = "Qwen/Qwen3-14B";

const demoChapter = [
  {
    english: "They didn't think they could bear it if anyone found out about the Potters.",
    translation: "他们无法承受别人发现波特一家事情的后果。",
    keyword: "bear",
    keywordMeaning: "忍受，承受",
    grammar: "if 引导条件状语从句，主句使用 think + that 从句，表达对结果的担忧。",
    grammarPoints: [
      "think + that 从句：宾语从句。",
      "could bear it：情态动词 could 表达过去语境下的能力或承受度。",
      "found out about：固定短语，表示得知、发现某事。"
    ],
    vocabulary: [
      { word: "bear", pos: "v.", meaning: "忍受；承受" },
      { word: "found out", pos: "短语", meaning: "发现；查明" },
      { word: "Potters", pos: "n.", meaning: "波特一家（专有名词）" }
    ]
  },
  {
    english: "Mrs. Potter often kept the curtains drawn, as if daylight itself might gossip.",
    translation: "波特太太总把窗帘拉着，仿佛连白天都会泄露秘密。",
    keyword: "gossip",
    keywordMeaning: "说闲话；传播消息",
    grammar: "as if 引导方式状语从句，使用 might 表示带有想象色彩的推测。",
    grammarPoints: [
      "kept the curtains drawn：keep + 宾语 + 过去分词。",
      "as if：表示“仿佛，好像”。",
      "might gossip：弱化语气的假设。"
    ],
    vocabulary: [
      { word: "curtains", pos: "n.", meaning: "窗帘" },
      { word: "drawn", pos: "adj.", meaning: "拉上的" },
      { word: "gossip", pos: "v.", meaning: "传播流言" }
    ]
  },
  {
    english: "The whole house seemed to hold its breath whenever the mailbox rattled.",
    translation: "每当邮箱发出响动，整栋房子仿佛都屏住了呼吸。",
    keyword: "rattled",
    keywordMeaning: "发出咔嗒响声",
    grammar: "whenever 引导时间状语从句，主句使用 seemed to 表示主观感受。",
    grammarPoints: [
      "seemed to hold：seem to do 结构。",
      "its breath：固定搭配 hold one's breath。",
      "whenever：每当。"
    ],
    vocabulary: [
      { word: "seemed", pos: "v.", meaning: "似乎" },
      { word: "hold its breath", pos: "短语", meaning: "屏住呼吸" },
      { word: "mailbox", pos: "n.", meaning: "邮箱" }
    ]
  }
];

const bookOptions = ref([]);
const chapterOptions = ref(["Chapter 2. The Vanishing Glass"]);
const currentBook = ref("");
const currentChapter = ref("Chapter 2. The Vanishing Glass");
const chapterSentences = ref([...demoChapter]);
const currentSentenceIndex = ref(0);
const progressValue = ref(0);
const activeTab = ref("解析");
const tabs = ["解析", "词汇", "语法", "笔记"];
const autoPlayNext = ref(true);
const highlightCurrent = ref(true);
const autoTranslate = ref(true);
const autoAnalyze = ref(true);
const followMode = ref(false);
const isPlaying = ref(false);
const playbackRate = ref(1.0);
const rateOptions = [0.8, 1.0, 1.2, 1.4];
const analysisModel = ref(ANALYSIS_MODEL);

let playTimer = null;
let speechUtterance = null;

const savedWords = reactive(new Set(["bear", "found out"]));

const safeSentenceCount = computed(() => Math.max(chapterSentences.value.length, 1));
const vocabularyCount = computed(() => savedWords.size);
const chapterProgress = computed(() => {
  if (!chapterSentences.value.length) return 0;
  return Math.round(((currentSentenceIndex.value + 1) / chapterSentences.value.length) * 100);
});
const elapsedLabel = computed(() => formatTime((currentSentenceIndex.value + 1) * 6));
const durationLabel = computed(() => formatTime(Math.max(chapterSentences.value.length * 6, 6)));

const highlightedSentence = computed(() => {
  const sentence = chapterSentences.value[currentSentenceIndex.value] || demoChapter[0];
  const escaped = sentence.keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = sentence.english.split(new RegExp(`(${escaped})`, "i"));
  return {
    ...sentence,
    segments: parts.filter(Boolean).map((part) => ({
      text: part,
      highlight: highlightCurrent.value && part.toLowerCase() === sentence.keyword.toLowerCase()
    }))
  };
});

const vocabularyItems = computed(() =>
  (highlightedSentence.value.vocabulary || []).map((item) => ({
    ...item,
    saved: savedWords.has(item.word)
  }))
);

watch(currentSentenceIndex, (value) => {
  progressValue.value = value;
});

watch(playbackRate, () => {
  if (isPlaying.value) restartPlayback();
});

watch(currentBook, async () => {
  await loadChapters();
});

onMounted(async () => {
  await loadBooks();
  await loadChapter();
});

onBeforeUnmount(() => {
  clearPlaybackTimer();
  cancelSpeech();
});

async function loadBooks() {
  try {
    const response = await fetch(`${API_URL}/books/list`);
    if (!response.ok) throw new Error("books list failed");
    const data = await response.json();
    bookOptions.value = Array.isArray(data.books) ? data.books : [];
    if (bookOptions.value.length) currentBook.value = bookOptions.value[0];
  } catch {
    bookOptions.value = ["Harry Potter and the Philosopher's Stone"];
    currentBook.value = bookOptions.value[0];
  }
}

async function loadChapters() {
  if (!currentBook.value) return;
  try {
    const response = await fetch(`${API_URL}/chapter/${encodeURIComponent(currentBook.value)}`);
    if (!response.ok) throw new Error("chapters failed");
    const data = await response.json();
    const chapters = Array.isArray(data.chapters) ? data.chapters.map((item) => item.name || item) : [];
    chapterOptions.value = chapters.length ? chapters : chapterOptions.value;
    if (!chapterOptions.value.includes(currentChapter.value)) currentChapter.value = chapterOptions.value[0];
  } catch {
    chapterOptions.value = ["Chapter 2. The Vanishing Glass", "Chapter 3. The Letters From No One"];
  }
}

async function onChapterSelect() {
  pausePlayback();
  await loadChapter();
}

async function loadChapter() {
  try {
    if (currentBook.value) await loadChapters();
    const content = await fetchChapterContent();
    const sentences = await splitText(content);
    chapterSentences.value = sentences.length ? sentences : [...demoChapter];
  } catch {
    chapterSentences.value = [...demoChapter];
  }
  currentSentenceIndex.value = 0;
  progressValue.value = 0;
}

async function fetchChapterContent() {
  if (!currentBook.value || !currentChapter.value) return demoChapter.map((item) => item.english).join(" ");
  const url = `${API_URL}/chapter/${encodeURIComponent(currentBook.value)}/${encodeURIComponent(currentChapter.value)}?position=0&min_size=${DEFAULT_MIN_SIZE}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error("chapter content failed");
  const data = await response.json();
  return data.text || "";
}

async function splitText(text) {
  if (!text) return [];
  try {
    const response = await fetch(`${API_URL}/split`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!response.ok) throw new Error("split failed");
    const data = await response.json();
    const sentences = Array.isArray(data.sentences) ? data.sentences : [];
    return sentences.slice(0, 12).map((sentence) => sentenceToCard(sentence));
  } catch {
    return text.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 12).map((sentence) => sentenceToCard(sentence));
  }
}

function sentenceToCard(sentence) {
  const words = sentence.replace(/[^\w\s']/g, "").split(/\s+/).filter(Boolean);
  const keyword = (words.find((word) => word.length > 4) || words[0] || "word").replace(/[^a-zA-Z']/g, "");
  return {
    english: sentence,
    translation: "示例翻译：从后端拆句成功后，这里可接入真实翻译结果。",
    keyword: keyword || "word",
    keywordMeaning: "待补充释义",
    grammar: "示例语法解析：当前句子的真实解析可继续接入 analyze_stream。",
    grammarPoints: [
      "可沿用 player/player.html 的流式解析接口。",
      "这里先用占位内容保证界面完整。",
      "句子切换和播放控制已接入 Vue 状态。"
    ],
    vocabulary: [
      { word: keyword || "word", pos: "n.", meaning: "待补充释义" },
      { word: words[1] || "context", pos: "n.", meaning: "上下文词汇" },
      { word: words[2] || "phrase", pos: "短语", meaning: "扩展词组" }
    ]
  };
}

function nextPage() {
  if (currentSentenceIndex.value < chapterSentences.value.length - 1) currentSentenceIndex.value += 1;
  else pausePlayback();
}

function previousPage() {
  currentSentenceIndex.value = Math.max(currentSentenceIndex.value - 1, 0);
}

function goToStart() {
  currentSentenceIndex.value = 0;
}

function goToEnd() {
  currentSentenceIndex.value = Math.max(chapterSentences.value.length - 1, 0);
}

function onSeek() {
  currentSentenceIndex.value = Number(progressValue.value);
}

function startPlayback() {
  isPlaying.value = true;
  speakText(highlightedSentence.value.english);
  scheduleNext();
}

function pausePlayback() {
  isPlaying.value = false;
  clearPlaybackTimer();
  cancelSpeech();
}

function restartPlayback() {
  clearPlaybackTimer();
  if (isPlaying.value) scheduleNext();
}

function scheduleNext() {
  clearPlaybackTimer();
  playTimer = window.setTimeout(() => {
    if (!autoPlayNext.value) {
      pausePlayback();
      return;
    }
    nextPage();
    if (isPlaying.value) {
      speakText(highlightedSentence.value.english);
      scheduleNext();
    }
  }, 2800 / playbackRate.value);
}

function clearPlaybackTimer() {
  if (playTimer) {
    window.clearTimeout(playTimer);
    playTimer = null;
  }
}

function cycleRate() {
  const index = rateOptions.findIndex((item) => item === playbackRate.value);
  playbackRate.value = rateOptions[(index + 1) % rateOptions.length];
}

function speakText(text) {
  cancelSpeech();
  if (!("speechSynthesis" in window) || !text) return;
  speechUtterance = new SpeechSynthesisUtterance(text);
  speechUtterance.rate = playbackRate.value;
  speechUtterance.lang = /[\u4e00-\u9fa5]/.test(text) ? "zh-CN" : "en-US";
  window.speechSynthesis.speak(speechUtterance);
}

function cancelSpeech() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  speechUtterance = null;
}

function toggleWord(word) {
  if (!word) return;
  if (savedWords.has(word)) savedWords.delete(word);
  else savedWords.add(word);
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}
</script>
