<template>
  <div class="app-shell">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>

    <audio ref="audioRef" preload="auto" @ended="onAudioEnded"></audio>

    <main class="player-page">
      <header class="top-bar panel">
        <div class="brand">
          <div class="brand-icon"><span></span><span></span></div>
          <span class="brand-text">书籍与章节</span>
        </div>

        <div class="top-center top-selects">
          <select v-model="currentBook" class="chapter-select" @change="onBookChange">
            <option value="" disabled>选择书籍</option>
            <option v-for="book in bookOptions" :key="book" :value="book">{{ book }}</option>
          </select>
          <select v-model="currentChapter" class="chapter-select" @change="onChapterSelect" :disabled="!chapterOptions.length">
            <option value="" disabled>选择章节</option>
            <option v-for="chapter in chapterOptions" :key="chapter" :value="chapter">{{ chapter }}</option>
          </select>
        </div>

        <div class="top-actions">
          <button class="pill-switch" type="button" @click="togglePlayback" :disabled="!hasSentence">
            <span class="switch-track" :class="{ active: isPlaying }"><span class="switch-thumb"></span></span>
            <span>{{ isPlaying ? "朗读中" : "已暂停" }}</span>
          </button>
          <button class="ghost-button" type="button" @click="reloadCurrentChapter">刷新</button>
          <button class="ghost-button" type="button" @click="jumpToNextChapter" :disabled="!hasNextChapter">下一章</button>
        </div>
      </header>

      <section class="progress-strip">
        <div class="progress-meta">
          <span>{{ currentBook || "未选择书籍" }}</span>
          <span>·</span>
          <span>{{ chapterProgress }}%</span>
          <span>·</span>
          <span>{{ currentSentenceIndex + 1 }} / {{ safeSentenceCount }} 句</span>
        </div>
        <div class="progress-line"><div class="progress-line-fill" :style="{ width: `${chapterProgress}%` }"></div></div>
      </section>

      <section class="workspace">
        <section class="main-stage panel" :style="fontScaleStyle">
          <div class="mode-badge">{{ statusText }}</div>
          <div class="sentence-counter">{{ currentSentenceIndex + 1 }} / {{ safeSentenceCount }}</div>

          <div class="sentence-stage">
            <template v-if="hasSentence">
              <p class="english-sentence">{{ currentSentence.english }}</p>
            </template>
            <template v-else>
              <p class="english-sentence empty-copy">选择书籍和章节后，将从 service 服务加载文本并拆句播放。</p>
            </template>
          </div>

          <div class="transport">
            <div ref="rateMenuRef" class="rate-menu-wrap">
              <button class="rate-chip" type="button" @click="toggleRateMenu" :class="{ active: isRateMenuOpen }">
                <span class="rotate">⟳</span>
                <span>{{ formattedPlaybackRate }}x</span>
                <span>语速</span>
              </button>
              <div v-if="isRateMenuOpen" class="rate-popover panel">
                <button
                  v-for="rate in rateMenuOptions"
                  :key="rate"
                  type="button"
                  class="rate-popover-item"
                  :class="{ active: numericPlaybackRate === rate }"
                  @click="selectPlaybackRate(rate)"
                >
                  {{ formatPlaybackRateLabel(rate) }}x
                </button>
              </div>
            </div>

            <div class="transport-buttons">
              <button class="transport-button" type="button" @click="goToStart" :disabled="!hasSentence">|◀</button>
              <button class="transport-button" type="button" @click="previousPage" :disabled="!canGoPrev">◀</button>
              <button class="transport-button primary" type="button" @click="togglePlayback" :disabled="!hasSentence">
                {{ isPlaying ? "❚❚" : "▶" }}
              </button>
              <button class="transport-button" type="button" @click="nextPage" :disabled="!hasSentence">▶</button>
              <button class="transport-button" type="button" @click="goToEnd" :disabled="!hasSentence">▶|</button>
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
              :disabled="!hasSentence"
              @input="onSeek"
            />
            <div class="timeline-labels">
              <span>{{ elapsedLabel }}</span>
              <span>{{ durationLabel }}</span>
            </div>
          </div>

          <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
        </section>

        <aside class="settings panel">
          <div class="note-chip">生词本 <span>{{ vocabularyCount }}</span></div>

          <div class="settings-group">
            <h3>朗读设置</h3>
            <label class="setting-label">语速（{{ formattedPlaybackRate }}x）</label>
            <input v-model.number="playbackRate" class="speed-slider" type="range" min="0.5" max="2" step="0.25" />
            <div class="slider-ticks" aria-hidden="true">
              <span v-for="rate in rateOptions" :key="rate" class="slider-tick" :class="{ active: numericPlaybackRate === rate }">
                <i></i>
                <em>{{ formatPlaybackRateLabel(rate) }}x</em>
              </span>
            </div>
            <div class="slider-legend"><span>慢</span><span>正常</span><span>快</span></div>

            <div class="toggle-row">
              <span>自动朗读下一句</span>
              <button class="inline-switch" :class="{ active: autoPlayNext }" type="button" @click="autoPlayNext = !autoPlayNext"></button>
            </div>
            <div class="toggle-row">
              <span>使用服务 TTS</span>
              <button class="inline-switch" :class="{ active: ttsEnabled }" type="button" @click="toggleTts"></button>
            </div>
          </div>

          <div class="settings-group">
            <h3>内容状态</h3>
            <div class="toggle-row"><span>已加载句子</span><strong>{{ loadedSentenceCount }}</strong></div>
            <div class="toggle-row"><span>章节游标</span><strong>{{ currentPosition }}</strong></div>
            <div class="toggle-row"><span>章节结束</span><strong>{{ chapterFinished ? "是" : "否" }}</strong></div>
            <div class="toggle-row"><span>加载更多</span><strong>{{ isLoadingMore ? "进行中" : "空闲" }}</strong></div>
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
                <button type="button" :class="{ active: fontScaleLevel === 'sm' }" @click="setFontScale('sm')">A-</button>
                <button type="button" :class="{ active: fontScaleLevel === 'md' }" @click="setFontScale('md')">A</button>
                <button type="button" :class="{ active: fontScaleLevel === 'lg' }" @click="setFontScale('lg')">A+</button>
              </div>
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
          <p>{{ currentSentence.translation }}</p>
          <p class="muted">当前先用本地占位翻译承接真实文本播放，后续可继续接入 `/analyze` 或翻译服务。</p>
        </article>

        <article class="info-card panel">
          <h3>语法解析</h3>
          <p>{{ currentSentence.grammar }}</p>
          <ul class="bullet-list">
            <li v-for="point in currentSentence.grammarPoints" :key="point">{{ point }}</li>
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

const DEFAULT_MIN_SIZE = 500;
const DEFAULT_BOOK = "哈利波特1-7英文原版";
const STORAGE_KEY = "player_vue_reading_state";
const API_CANDIDATES = process.env.NODE_ENV === "development"
  ? ["/api", "http://localhost:8000", "http://127.0.0.1:8000"]
  : [window.location.origin, "http://localhost:8000", "http://127.0.0.1:8000"];

const FONT_SCALE_MAP = {
  sm: { "--player-english-size": "14px", "--player-empty-size": "14px" },
  md: { "--player-english-size": "16px", "--player-empty-size": "16px" },
  lg: { "--player-english-size": "18px", "--player-empty-size": "18px" }
};

const bookOptions = ref([]);
const chapterOptions = ref([]);
const currentBook = ref("");
const currentChapter = ref("");
const chapterSentences = ref([]);
const currentSentenceIndex = ref(0);
const progressValue = ref(0);
const currentPosition = ref(0);
const chapterFinished = ref(false);
const isInitialLoading = ref(false);
const isLoadingMore = ref(false);
const errorMessage = ref("");
const activeTab = ref("解析");
const tabs = ["解析", "词汇", "语法", "笔记"];
const autoPlayNext = ref(true);
const fontScaleLevel = ref("md");
const followMode = ref(false);
const isPlaying = ref(false);
const ttsEnabled = ref(true);
const playbackRate = ref(1.0);
const rateOptions = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

const audioRef = ref(null);
const rateMenuRef = ref(null);
const savedWords = reactive(new Set(["bear", "Potters"]));
const resolvedApiBase = ref("");

let advanceTimer = null;
let currentAudioUrl = null;
let playToken = 0;
let isRestoringState = false;
const isRateMenuOpen = ref(false);

const emptySentence = {
  english: "",
  translation: "加载后将显示当前句子的翻译占位。",
  keyword: "word",
  keywordMeaning: "待补充释义",
  grammar: "加载后将显示当前句子的语法解析占位。",
  grammarPoints: ["等待文本加载。"],
  vocabulary: []
};

const hasSentence = computed(() => chapterSentences.value.length > 0);
const safeSentenceCount = computed(() => Math.max(chapterSentences.value.length, 1));
const loadedSentenceCount = computed(() => chapterSentences.value.length);
const canGoPrev = computed(() => currentSentenceIndex.value > 0);
const vocabularyCount = computed(() => savedWords.size);
const currentChapterIndex = computed(() => chapterOptions.value.findIndex((item) => item === currentChapter.value));
const hasNextChapter = computed(() => currentChapterIndex.value >= 0 && currentChapterIndex.value < chapterOptions.value.length - 1);
const chapterProgress = computed(() => {
  if (!chapterSentences.value.length) return 0;
  return Math.round(((currentSentenceIndex.value + 1) / chapterSentences.value.length) * 100);
});
const elapsedLabel = computed(() => formatTime((currentSentenceIndex.value + 1) * 6));
const durationLabel = computed(() => formatTime(Math.max(chapterSentences.value.length * 6, 6)));
const currentSentence = computed(() => chapterSentences.value[currentSentenceIndex.value] || emptySentence);
const fontScaleStyle = computed(() => FONT_SCALE_MAP[fontScaleLevel.value] || FONT_SCALE_MAP.md);
const numericPlaybackRate = computed(() => clampPlaybackRate(playbackRate.value));
const formattedPlaybackRate = computed(() => formatPlaybackRateLabel(numericPlaybackRate.value));
const rateMenuOptions = computed(() => [...rateOptions].sort((a, b) => b - a));
const vocabularyItems = computed(() =>
  (currentSentence.value.vocabulary || []).map((item) => ({
    ...item,
    saved: savedWords.has(item.word)
  }))
);
const statusText = computed(() => {
  if (isInitialLoading.value) return "正在加载章节文本";
  if (isLoadingMore.value) return "正在获取下一段内容";
  if (errorMessage.value) return "接口调用失败";
  if (isPlaying.value) return ttsEnabled.value ? "服务 TTS 播放中" : "计时播放中";
  if (chapterFinished.value) return "本章已加载完成";
  return "点击句子可单句播放";
});

watch(currentSentenceIndex, (value) => {
  progressValue.value = value;
});

watch(
  [
    currentBook,
    currentChapter,
    currentSentenceIndex,
    currentPosition,
    chapterFinished,
    playbackRate,
    ttsEnabled,
    autoPlayNext,
    fontScaleLevel,
    () => chapterSentences.value
  ],
  () => {
    persistReadingState();
  },
  { deep: true }
);

watch(playbackRate, async () => {
  playbackRate.value = clampPlaybackRate(playbackRate.value);
  if (!isPlaying.value) return;
  stopAudio();
  clearAdvanceTimer();
  await nextTick();
  await playCurrentSentence();
});

onMounted(async () => {
  window.addEventListener("pointerdown", onWindowPointerDown);
  try {
    await initializePlayer();
  } catch (error) {
    handleError(error);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("pointerdown", onWindowPointerDown);
  stopPlayback();
});

async function initializePlayer() {
  isInitialLoading.value = true;
  try {
    const savedState = loadReadingState();
    await loadBooks();
    if (savedState?.book && bookOptions.value.includes(savedState.book)) {
      currentBook.value = savedState.book;
    }
    if (currentBook.value) {
      await loadChapters(currentBook.value);
    }
    if (savedState?.chapter && chapterOptions.value.includes(savedState.chapter)) {
      currentChapter.value = savedState.chapter;
    }
    if (applySavedReadingState(savedState)) return;
    if (currentBook.value && currentChapter.value) {
      await loadChapter({ resetSentences: true });
    }
  } finally {
    isInitialLoading.value = false;
  }
}

async function loadBooks() {
  errorMessage.value = "";
  const response = await fetchJson("/books/list");
  const books = Array.isArray(response.books) ? response.books : [];
  bookOptions.value = books;
  if (!books.length) throw new Error("未找到可用书籍");
  currentBook.value = books.includes(DEFAULT_BOOK) ? DEFAULT_BOOK : books[0];
}

async function loadChapters(book) {
  errorMessage.value = "";
  const response = await fetchJson(`/chapter/${encodeURIComponent(book)}`);
  const chapters = Array.isArray(response.chapters) ? response.chapters.map((item) => item.name || item) : [];
  chapterOptions.value = chapters;
  currentChapter.value = chapters[0] || "";
}

async function onBookChange() {
  stopPlayback();
  if (!currentBook.value) return;
  isInitialLoading.value = true;
  try {
    await loadChapters(currentBook.value);
    await loadChapter({ resetSentences: true });
  } catch (error) {
    handleError(error);
  } finally {
    isInitialLoading.value = false;
  }
}

async function onChapterSelect() {
  stopPlayback();
  if (!currentChapter.value) return;
  await reloadCurrentChapter();
}

async function reloadCurrentChapter() {
  isInitialLoading.value = true;
  try {
    await loadChapter({ resetSentences: true });
  } catch (error) {
    handleError(error);
  } finally {
    isInitialLoading.value = false;
  }
}

async function loadChapter({ resetSentences }) {
  if (!currentBook.value || !currentChapter.value) return;
  errorMessage.value = "";
  currentPosition.value = 0;
  chapterFinished.value = false;
  currentSentenceIndex.value = 0;
  progressValue.value = 0;
  if (resetSentences) chapterSentences.value = [];
  await loadMoreContent(true);
}

async function loadMoreContent(force = false) {
  if ((!force && chapterFinished.value) || isLoadingMore.value || !currentBook.value || !currentChapter.value) return;
  isLoadingMore.value = true;
  errorMessage.value = "";

  try {
    const content = await fetchJson(
      `/chapter/${encodeURIComponent(currentBook.value)}/${encodeURIComponent(currentChapter.value)}?position=${currentPosition.value}&min_size=${DEFAULT_MIN_SIZE}`
    );

    currentPosition.value = Number(content.end_position || currentPosition.value);
    const reachedEnd = !content.text || Number(content.start_position) === Number(content.end_position);

    if (reachedEnd) {
      chapterFinished.value = true;
      if (!chapterSentences.value.length) throw new Error("章节内容为空");
      return;
    }

    const newCards = await splitIntoCards(content.text);
    if (!newCards.length) {
      chapterFinished.value = Boolean(content.paragraph_end);
      return;
    }

    chapterSentences.value = [...chapterSentences.value, ...newCards];
    chapterFinished.value = false;
  } catch (error) {
    handleError(error);
  } finally {
    isLoadingMore.value = false;
  }
}

async function splitIntoCards(text) {
  const response = await fetchJson("/split", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language: "en", method: "r" })
  });
  const sentences = Array.isArray(response.sentences) ? response.sentences : [];
  return sentences.filter(Boolean).map((sentence) => sentenceToCard(sentence));
}

function sentenceToCard(sentence) {
  const plain = sentence.replace(/\s+/g, " ").trim();
  const words = plain.replace(/[^\w\s']/g, "").split(/\s+/).filter(Boolean);
  const keyword = (words.find((word) => word.length >= 5) || words[0] || "word").replace(/[^a-zA-Z']/g, "") || "word";
  const preview = words.slice(0, 4).join(" ");
  return {
    english: plain,
    translation: `示例翻译：${plain.slice(0, 36)}${plain.length > 36 ? "..." : ""}`,
    keyword,
    keywordMeaning: "待补充释义",
    grammar: "句子已从 service 拆出。当前语法卡片使用占位内容，可继续对接 analyze_stream。",
    grammarPoints: [
      `来源章节：${currentChapter.value}`,
      `关键词候选：${keyword}`,
      `上下文片段：${preview || "N/A"}`
    ],
    vocabulary: [
      { word: keyword, pos: "n.", meaning: "待补充释义" },
      { word: words[1] || "context", pos: "n.", meaning: "上下文词汇" },
      { word: words[2] || "phrase", pos: "短语", meaning: "扩展词组" }
    ]
  };
}

function onSeek() {
  currentSentenceIndex.value = Number(progressValue.value);
  if (isPlaying.value) replayFromCurrent();
}

async function nextPage() {
  if (!hasSentence.value) return;
  if (currentSentenceIndex.value < chapterSentences.value.length - 1) {
    currentSentenceIndex.value += 1;
    if (isPlaying.value) await playCurrentSentence();
    maybePreloadMore();
    return;
  }

  if (!chapterFinished.value) {
    const previousLength = chapterSentences.value.length;
    await loadMoreContent();
    if (chapterSentences.value.length > previousLength) {
      currentSentenceIndex.value += 1;
      if (isPlaying.value) await playCurrentSentence();
      maybePreloadMore();
      return;
    }
  }

  if (autoPlayNext.value && hasNextChapter.value) {
    await jumpToNextChapter();
    if (isPlaying.value) await playCurrentSentence();
    return;
  }

  stopPlayback();
}

function previousPage() {
  if (!hasSentence.value) return;
  currentSentenceIndex.value = Math.max(currentSentenceIndex.value - 1, 0);
  if (isPlaying.value) replayFromCurrent();
}

function goToStart() {
  currentSentenceIndex.value = 0;
  if (isPlaying.value) replayFromCurrent();
}

function goToEnd() {
  currentSentenceIndex.value = Math.max(chapterSentences.value.length - 1, 0);
  if (isPlaying.value) replayFromCurrent();
}

async function jumpToNextChapter() {
  if (!hasNextChapter.value) return;
  currentChapter.value = chapterOptions.value[currentChapterIndex.value + 1];
  await reloadCurrentChapter();
}

function togglePlayback() {
  if (isPlaying.value) stopPlayback();
  else startPlayback();
}

async function startPlayback() {
  if (!hasSentence.value) return;
  isPlaying.value = true;
  await playCurrentSentence();
}

function stopPlayback() {
  isPlaying.value = false;
  playToken += 1;
  clearAdvanceTimer();
  stopAudio();
}

async function replayFromCurrent() {
  stopAudio();
  clearAdvanceTimer();
  await playCurrentSentence();
}

async function playCurrentSentence() {
  if (!isPlaying.value || !hasSentence.value) return;
  clearAdvanceTimer();
  stopAudio();

  const token = ++playToken;
  const text = currentSentence.value.english;

  if (ttsEnabled.value) {
    try {
      await requestTtsAudio(text, token);
      return;
    } catch (error) {
      handleError(error);
      ttsEnabled.value = false;
    }
  }

  scheduleTextAdvance(token);
}

async function requestTtsAudio(text, token) {
  const voice = detectLanguage(text) === "zh" ? "zh-CN-XiaoxiaoNeural" : "en-US-AriaNeural";
  const rate = formatTtsRate(playbackRate.value);
  const response = await fetch(buildApiUrl(`/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}`));
  if (!response.ok) throw new Error("TTS 服务调用失败");

  const blob = await response.blob();
  if (token !== playToken || !isPlaying.value) return;

  currentAudioUrl = URL.createObjectURL(blob);
  const audio = audioRef.value;
  audio.src = currentAudioUrl;
  audio.playbackRate = playbackRate.value;
  await audio.play();
}

function scheduleTextAdvance(token, autoNext = true) {
  const duration = Math.max(1800, currentSentence.value.english.length * 70) / playbackRate.value;
  advanceTimer = window.setTimeout(async () => {
    if (token !== playToken) return;
    if (isPlaying.value && autoPlayNext.value && autoNext) {
      await nextPage();
    }
  }, duration);
}

async function onAudioEnded() {
  if (!isPlaying.value || !autoPlayNext.value) return;
  await nextPage();
}

function clearAdvanceTimer() {
  if (advanceTimer) {
    window.clearTimeout(advanceTimer);
    advanceTimer = null;
  }
}

function stopAudio() {
  const audio = audioRef.value;
  if (audio) {
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
  }
  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = null;
  }
}

function maybePreloadMore() {
  if (chapterFinished.value || isLoadingMore.value) return;
  if (chapterSentences.value.length - currentSentenceIndex.value <= 3) {
    loadMoreContent();
  }
}

function toggleRateMenu() {
  isRateMenuOpen.value = !isRateMenuOpen.value;
}

function selectPlaybackRate(rate) {
  playbackRate.value = rate;
  isRateMenuOpen.value = false;
}

function onWindowPointerDown(event) {
  if (!isRateMenuOpen.value) return;
  if (rateMenuRef.value?.contains(event.target)) return;
  isRateMenuOpen.value = false;
}

function toggleTts() {
  ttsEnabled.value = !ttsEnabled.value;
  if (isPlaying.value) replayFromCurrent();
}

function toggleWord(word) {
  if (!word) return;
  if (savedWords.has(word)) savedWords.delete(word);
  else savedWords.add(word);
}

function detectLanguage(text) {
  return /[\u4e00-\u9fa5]/.test(text) ? "zh" : "en";
}

function formatTtsRate(rate) {
  const percent = Math.round((rate - 1) * 100);
  return `${percent >= 0 ? "+" : ""}${percent}%`;
}

function formatPlaybackRateLabel(rate) {
  const normalized = clampPlaybackRate(rate);
  return Number.isInteger(normalized) ? `${normalized}` : `${normalized}`.replace(/(\.\d*?[1-9])0+$/, "$1");
}

function loadReadingState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function applySavedReadingState(savedState) {
  if (!savedState) return false;
  if (!savedState.book || !savedState.chapter) return false;
  if (savedState.book !== currentBook.value || savedState.chapter !== currentChapter.value) return false;
  if (!Array.isArray(savedState.chapterSentences) || !savedState.chapterSentences.length) return false;

  isRestoringState = true;
  chapterSentences.value = savedState.chapterSentences;
  currentPosition.value = Number(savedState.currentPosition || 0);
  chapterFinished.value = Boolean(savedState.chapterFinished);
  currentSentenceIndex.value = clampIndex(savedState.currentSentenceIndex, chapterSentences.value.length);
  progressValue.value = currentSentenceIndex.value;
  playbackRate.value = clampPlaybackRate(savedState.playbackRate);
  ttsEnabled.value = typeof savedState.ttsEnabled === "boolean" ? savedState.ttsEnabled : ttsEnabled.value;
  autoPlayNext.value = typeof savedState.autoPlayNext === "boolean" ? savedState.autoPlayNext : autoPlayNext.value;
  fontScaleLevel.value = normalizeFontScaleLevel(savedState.fontScaleLevel);
  isRestoringState = false;
  return true;
}

function persistReadingState() {
  if (isRestoringState) return;
  const payload = {
    book: currentBook.value,
    chapter: currentChapter.value,
    currentSentenceIndex: currentSentenceIndex.value,
    currentPosition: currentPosition.value,
    chapterFinished: chapterFinished.value,
    chapterSentences: chapterSentences.value,
    playbackRate: playbackRate.value,
    ttsEnabled: ttsEnabled.value,
    autoPlayNext: autoPlayNext.value,
    fontScaleLevel: fontScaleLevel.value
  };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function clampIndex(index, length) {
  const normalized = Number(index);
  if (!Number.isFinite(normalized)) return 0;
  return Math.max(0, Math.min(length - 1, normalized));
}

function clampPlaybackRate(rate) {
  const normalized = Number(rate);
  if (!Number.isFinite(normalized)) return 1.0;
  return Math.max(0.5, Math.min(2.0, normalized));
}

function setFontScale(level) {
  fontScaleLevel.value = normalizeFontScaleLevel(level);
}

function normalizeFontScaleLevel(level) {
  return Object.hasOwn(FONT_SCALE_MAP, level) ? level : "md";
}

function buildApiUrl(path, base = resolvedApiBase.value) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!base) return normalizedPath;
  return `${base}${normalizedPath}`;
}

async function detectApiBase() {
  if (resolvedApiBase.value) return resolvedApiBase.value;

  for (const base of API_CANDIDATES) {
    const normalizedBase = base.endsWith("/") ? base.slice(0, -1) : base;
    try {
      const response = await fetch(`${normalizedBase}/health`);
      if (response.ok) {
        resolvedApiBase.value = normalizedBase;
        return normalizedBase;
      }
    } catch {
      continue;
    }
  }

  throw new Error("无法连接到 service 服务，请确认 http://localhost:8000 已启动");
}

async function fetchJson(path, options) {
  const base = await detectApiBase();
  const response = await fetch(buildApiUrl(path, base), options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `请求失败: ${response.status}`);
  }
  return response.json();
}

function handleError(error) {
  errorMessage.value = error instanceof Error ? error.message : String(error);
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}
</script>
