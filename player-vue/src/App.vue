<template>
  <div class="app-shell">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>

    <audio ref="audioRef" preload="auto" @ended="onAudioEnded"></audio>

    <main class="player-page">




      <section class="workspace">
        <section class="main-stage panel" :style="fontScaleStyle" ref="mainStageRef">

          <div class="sentence-stage content-stage">
            <template v-if="hasSentence">
              <div ref="contentViewportRef" class="content-viewport" @scroll.passive="onContentScroll">
                <div class="content-text">
                  <span
                    v-for="(item, index) in chapterSentences"
                    :key="index"
                    :ref="el => sentenceRefs[index] = el"
                    class="content-sentence"
                    :class="sentenceClass(index)"
                    v-html="item.english.replace(/\n/g, '<br/>')"
                  ></span>
                </div>
              </div>
            </template>
            <template v-else>
              <p class="english-sentence empty-copy">选择书籍和章节后，将从 service 服务加载文本并拆句播放。</p>
            </template>
          </div>

          <div class="transport">
            <div class="transport-top">
              <div ref="rateMenuRef" class="rate-menu-wrap">
                <button class="rate-chip" type="button" @click="toggleRateMenu" :class="{ active: isRateMenuOpen }">
                  <span class="rotate">⟳</span>
                  <span>{{ formattedPlaybackRate }}x</span>
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
              <div class="transport-controls">
                <button class="transport-button" type="button" @click="centerCurrentSentence(true)" :disabled="!hasSentence">◎</button>
                <button class="transport-button" type="button" @click="toggleFullscreen" :disabled="!hasSentence">⛶</button>
                <button class="transport-button" type="button" @click="isBookSidebarOpen = !isBookSidebarOpen">📚</button>
                <button class="transport-button" type="button" @click="isSettingsSidebarOpen = !isSettingsSidebarOpen">⚙️</button>
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
            <div class="timeline-meta">
              <div class="timeline-meta-left">
                <span>{{ currentBook || "未选择书籍" }}</span>
              </div>
              <div class="timeline-meta-right">
                <span>{{ chapterProgress }}%</span>
                <span>·</span>
                <span>{{ currentSentenceIndex + 1 }} / {{ safeSentenceCount }} 句</span>
              </div>
            </div>
          </div>

          <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
        </section>

        <section class="side-panel panel">
          <article class="info-card panel analyze-card" v-if="autoAnalyze || analyzeResult">
            <div class="loading-container" v-if="isAnalyzing">
              <div class="loading-spinner"></div>
            </div>
            <div v-if="analyzeResult" class="analyze-content">
              <div v-if="analyzeResult.error" class="analyze-error">
                {{ analyzeResult.error }}
              </div>
              <div v-else class="analyze-markdown" v-html="renderAnalyzeContent(analyzeResult.raw)"></div>
            </div>
            <p v-else-if="!isAnalyzing" class="muted">点击播放或切换句子后将自动解析。</p>
          </article>
        </section>
      </section>

      <!-- 侧边栏 -->
      <div class="sidebar-overlay" v-if="isBookSidebarOpen || isSettingsSidebarOpen" @click="closeSidebars"></div>
      
      <!-- 书籍侧边栏 -->
      <div class="sidebar book-sidebar" :class="{ open: isBookSidebarOpen }">
        <div class="sidebar-header">
          <h3>选择书籍与章节</h3>
          <button class="close-button" @click="isBookSidebarOpen = false">×</button>
        </div>
        <div class="sidebar-content">
          <div class="book-chapter-selector">
            <select v-model="currentBook" class="chapter-select" @change="onBookChange">
              <option value="" disabled>选择书籍</option>
              <option v-for="book in bookOptions" :key="book" :value="book">{{ book }}</option>
            </select>
            
            <div v-if="chapterOptions.length > 0" class="chapter-list">
              <h4>章节列表</h4>
              <div class="chapter-items">
                <button 
                  v-for="chapter in chapterOptions" 
                  :key="chapter" 
                  class="chapter-item" 
                  :class="{ active: currentChapter === chapter }"
                  :title="chapter"
                  @click="selectChapter(chapter)"
                >
                  {{ chapter }}
                </button>
              </div>
            </div>
            <div v-else-if="currentBook" class="no-chapters">
              正在加载章节...
            </div>
            <div v-else class="no-chapters">
              请先选择书籍
            </div>
          </div>
        </div>
      </div>
      
      <!-- 设置侧边栏 -->
      <div class="sidebar settings-sidebar" :class="{ open: isSettingsSidebarOpen }">
        <div class="sidebar-header">
          <h3>设置</h3>
          <button class="close-button" @click="isSettingsSidebarOpen = false">×</button>
        </div>
        <div class="sidebar-content">
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
            <h3>解析设置</h3>
            <div class="toggle-row">
              <span>自动解析</span>
              <button class="inline-switch" :class="{ active: autoAnalyze }" type="button" @click="toggleAutoAnalyze"></button>
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
                <button type="button" :class="{ active: fontScaleLevel === 'sm' }" @click="setFontScale('sm')">A-</button>
                <button type="button" :class="{ active: fontScaleLevel === 'md' }" @click="setFontScale('md')">A</button>
                <button type="button" :class="{ active: fontScaleLevel === 'lg' }" @click="setFontScale('lg')">A+</button>
              </div>
            </div>
          </div>
        </div>
      </div>


    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useFullscreen } from "@vueuse/core";
import { marked } from "marked";

const DEFAULT_MIN_SIZE = 500;
const DEFAULT_BOOK = "哈利波特1-7英文原版";
const STORAGE_KEY = "player_vue_reading_state";
const API_CANDIDATES = ["http://192.168.2.178:8000"];

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
const autoPlayNext = ref(true);
const autoAnalyze = ref(false);
const fontScaleLevel = ref("md");
const mainStageRef = ref(null);
const isPlaying = ref(false);
const ttsEnabled = ref(true);
const playbackRate = ref(1.0);
const rateOptions = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
const CONTENT_SCROLL_EDGE_THRESHOLD = 48;

const audioRef = ref(null);
const rateMenuRef = ref(null);
const contentViewportRef = ref(null);
const contentScrollTop = ref(0);
const contentViewportHeight = ref(360);
const savedWords = reactive(new Set(["bear", "Potters"]));
const resolvedApiBase = ref("");
const isBookSidebarOpen = ref(false);
const isSettingsSidebarOpen = ref(false);
const audioCurrentTime = ref(0);

// 控制body滚动
function updateBodyScroll() {
  if (isBookSidebarOpen.value || isSettingsSidebarOpen.value) {
    document.body.classList.add('sidebar-open');
  } else {
    document.body.classList.remove('sidebar-open');
  }
}

// 监听侧边栏状态变化
watch([isBookSidebarOpen, isSettingsSidebarOpen], updateBodyScroll);

// 初始化时检查
onMounted(() => {
  updateBodyScroll();
  // 其他初始化代码...
  
  // 添加键盘事件监听器
  window.addEventListener('keydown', handleKeyDown);
});

// 处理键盘事件
function handleKeyDown(event) {
  // 避免在输入框中触发快捷键
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return;
  }
  
  switch (event.key) {
    case ' ': // 空格键：暂停/播放
      event.preventDefault(); // 阻止页面滚动
      togglePlayback();
      break;
    case 'ArrowLeft': // 左方向键：上一句
      event.preventDefault();
      previousPage();
      break;
    case 'ArrowRight': // 右方向键：下一句
      event.preventDefault();
      nextPage();
      break;
    case 'ArrowUp': // 上方向键：语速快一档
      event.preventDefault();
      playbackRate.value = Math.min(playbackRate.value + 0.25, 2.0);
      break;
    case 'ArrowDown': // 下方向键：语速慢一档
      event.preventDefault();
      playbackRate.value = Math.max(playbackRate.value - 0.25, 0.5);
      break;
    case 'f': // F键：切换全屏
      event.preventDefault();
      toggleFullscreen();
      break;
  }
}

// 全屏功能
const { isFullscreen, toggle: toggleFullscreen } = useFullscreen(mainStageRef, {
  autoExit: false,
  onFullscreenChange: (isFull) => {
    // 强制更新样式
    if (isFull) {
      document.body.classList.add('fullscreen-mode');
    } else {
      document.body.classList.remove('fullscreen-mode');
    }
  }
});
const analyzeResult = ref(null);
const isAnalyzing = ref(false);

let advanceTimer = null;
let currentAudioUrl = null;
let nextAudioUrl = null;  // Preloaded next sentence audio
let preloadIndex = -1;    // Which sentence is preloaded
let playToken = 0;
let isRestoringState = false;
const isRateMenuOpen = ref(false);
const sentenceRefs = ref([]);

function closeSidebars() {
  isBookSidebarOpen.value = false;
  isSettingsSidebarOpen.value = false;
}

function selectChapter(chapter) {
  currentChapter.value = chapter;
  onChapterSelect();
  isBookSidebarOpen.value = false;
}

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

const currentSentence = computed(() => chapterSentences.value[currentSentenceIndex.value] || emptySentence);
const fontScaleStyle = computed(() => FONT_SCALE_MAP[fontScaleLevel.value] || FONT_SCALE_MAP.md);
const numericPlaybackRate = computed(() => clampPlaybackRate(playbackRate.value));
const formattedPlaybackRate = computed(() => formatPlaybackRateLabel(numericPlaybackRate.value));
const rateMenuOptions = computed(() => [...rateOptions].sort((a, b) => b - a));
// 移除虚拟滚动相关计算属性，直接显示所有句子
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
  return "";
});

watch(currentSentenceIndex, (value) => {
  // 在恢复状态时，不设置progressValue，避免覆盖applySavedReadingState中设置的值
  if (!isRestoringState) {
    progressValue.value = value;
  }
  centerCurrentSentence(true);
});

// 移除虚拟滚动相关的 watch 监听器

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
      autoAnalyze,
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
  clearPreloadAudio();
  if (!isPlaying.value) return;
  stopAudio();
  clearAdvanceTimer();
  await nextTick();
  await playCurrentSentence();
});

watch(fontScaleLevel, () => {
  nextTick(() => centerCurrentSentence(true));
});

watch(currentSentenceIndex, () => {
  if (autoAnalyze.value && hasSentence.value) {
    analyzeSentence();
  }
});

onMounted(async () => {
  window.addEventListener("pointerdown", onWindowPointerDown);
  window.addEventListener("resize", syncContentViewportMetrics);
  try {
    await initializePlayer();
  } catch (error) {
    handleError(error);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("pointerdown", onWindowPointerDown);
  window.removeEventListener("resize", syncContentViewportMetrics);
  window.removeEventListener('keydown', handleKeyDown);
  
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
    if (applySavedReadingState(savedState)) {
      isInitialLoading.value = false;
      return;
    }
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
  // 防止在页面初始化时被调用，导致进度条重置
  if (isInitialLoading.value) return;
  
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
  contentScrollTop.value = 0;
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
    console.log('chapterSentences:', chapterSentences.value);
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
  // 保留原始句子，包括换行符
  const plain = sentence;
  // 去除空白字符用于提取关键词和预览
  const trimmed = sentence.trim();
  const words = trimmed.replace(/[^\w\s']/g, "").split(/\s+/).filter(Boolean);
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
  nextTick(() => {
    centerCurrentSentence();
  });
  if (isPlaying.value) replayFromCurrent();
}

function jumpToSentence(index) {
  currentSentenceIndex.value = clampIndex(index, chapterSentences.value.length);
  nextTick(() => {
    centerCurrentSentence();
  });
  if (isPlaying.value) replayFromCurrent();
}

async function nextPage() {
  if (!hasSentence.value) return;
  if (currentSentenceIndex.value < chapterSentences.value.length - 1) {
    // 重置音频播放位置，避免继续播放的逻辑影响新句子
    audioCurrentTime.value = 0;
    currentSentenceIndex.value += 1;
    nextTick(() => {
      centerCurrentSentence();
    });
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
  nextTick(() => {
    centerCurrentSentence();
  });
  if (isPlaying.value) replayFromCurrent();
}

function goToStart() {
  currentSentenceIndex.value = 0;
  nextTick(() => {
    centerCurrentSentence();
  });
  if (isPlaying.value) replayFromCurrent();
}

function goToEnd() {
  currentSentenceIndex.value = Math.max(chapterSentences.value.length - 1, 0);
  nextTick(() => {
    centerCurrentSentence();
  });
  if (isPlaying.value) replayFromCurrent();
}

async function jumpToNextChapter() {
  if (!hasNextChapter.value) return;
  clearPreloadAudio();  // Clear preloaded audio when switching chapters
  // 重置音频播放位置，避免继续播放的逻辑影响新章节
  audioCurrentTime.value = 0;
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
  centerCurrentSentence(true);
  await playCurrentSentence();
}

function stopPlayback() {
  isPlaying.value = false;
  playToken += 1;
  clearAdvanceTimer();
  stopAudio();
  clearPreloadAudio();
}

async function replayFromCurrent() {
  clearPreloadAudio();  // Clear preloaded audio when seeking/jumping
  stopAudio();
  clearAdvanceTimer();
  await playCurrentSentence();
}

async function playCurrentSentence() {
  if (!isPlaying.value || !hasSentence.value) return;
  clearAdvanceTimer();
  
  const token = ++playToken;
  const text = currentSentence.value.english;

  if (ttsEnabled.value) {
    try {
      // 检查是否是继续播放（有保存的播放位置）
      const isResuming = audioCurrentTime.value > 0;
      
      await requestTtsAudio(text, token);
      
      // 如果是继续播放，从保存的位置开始
      if (isResuming) {
        const audio = audioRef.value;
        if (audio) {
          audio.currentTime = audioCurrentTime.value;
          audioCurrentTime.value = 0; // 重置保存的位置
        }
      }

      // Preload next sentence after current starts playing
      const nextIndex = currentSentenceIndex.value + 1;
      if (autoPlayNext.value && nextIndex < chapterSentences.value.length) {
        // Don't wait for preload to complete
        preloadNextSentenceAudio(nextIndex);
      }
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

  // 检查是否是继续播放（有保存的播放位置）
  const isResuming = audioCurrentTime.value > 0;
  
  // 如果是继续播放，且音频已经加载，且音频没有播放完毕，则直接播放
  const audio = audioRef.value;
  if (isResuming && audio && audio.src && !audio.ended) {
    if (token !== playToken || !isPlaying.value) return;
    await audio.play();
    return;
  }

  // Check if we have preloaded audio for current sentence
  if (preloadIndex === currentSentenceIndex.value && nextAudioUrl) {
    if (token !== playToken || !isPlaying.value) return;

    currentAudioUrl = nextAudioUrl;
    nextAudioUrl = null;  // Consume preloaded audio
    preloadIndex = -1;

    if (audio) {
      audio.src = currentAudioUrl;
      // TTS服务已经按照正确的速率生成了音频，不需要再调整playbackRate
      audio.playbackRate = 1.0;
      await audio.play();
    }
    return;
  }

  // No preloaded audio, fetch new
  const response = await fetch(buildApiUrl(`/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}`));
  if (!response.ok) throw new Error("TTS 服务调用失败");

  const blob = await response.blob();
  if (token !== playToken || !isPlaying.value) return;

  currentAudioUrl = URL.createObjectURL(blob);
  if (audio) {
    audio.src = currentAudioUrl;
    // TTS服务已经按照正确的速率生成了音频，不需要再调整playbackRate
    audio.playbackRate = 1.0;
    await audio.play();
  }
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
  // 重置音频播放位置
  audioCurrentTime.value = 0;
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
    // 只有当音频没有播放完毕时，才保存当前位置
    if (!audio.ended) {
      audioCurrentTime.value = audio.currentTime;
    } else {
      audioCurrentTime.value = 0;
    }
    audio.pause();
  }
  // 不要移除src属性，保留音频资源以便继续播放
}

function clearPreloadAudio() {
  if (nextAudioUrl) {
    URL.revokeObjectURL(nextAudioUrl);
    nextAudioUrl = null;
  }
  preloadIndex = -1;
}

async function preloadNextSentenceAudio(nextIndex) {
  // Don't preload if index is invalid
  if (nextIndex >= chapterSentences.value.length || nextIndex < 0) {
    clearPreloadAudio();
    return;
  }

  // Skip if already preloaded
  if (preloadIndex === nextIndex && nextAudioUrl) return;

  // Clear old preload
  clearPreloadAudio();

  try {
    const nextSentence = chapterSentences.value[nextIndex];
    if (!nextSentence) return;

    const voice = detectLanguage(nextSentence.english) === "zh" ? "zh-CN-XiaoxiaoNeural" : "en-US-AriaNeural";
    const rate = formatTtsRate(playbackRate.value);
    const response = await fetch(buildApiUrl(`/tts?text=${encodeURIComponent(nextSentence.english)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}`));
    if (!response.ok) return;

    const blob = await response.blob();
    preloadIndex = nextIndex;
    nextAudioUrl = URL.createObjectURL(blob);
  } catch (error) {
    // Preload failure is not critical, continue without preload
    clearPreloadAudio();
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



function centerCurrentSentence(smooth = true) {
  const viewport = contentViewportRef.value;
  if (!viewport) return;

  const currentEl = sentenceRefs.value[currentSentenceIndex.value];
  if (currentEl) {
    // 计算当前句子在视口中的位置
    const viewportRect = viewport.getBoundingClientRect();
    const elementRect = currentEl.getBoundingClientRect();
    
    // 计算相对于视口的位置（不考虑页面滚动）
    const relativeTop = elementRect.top - viewportRect.top;
    const elementHeight = elementRect.height;
    const viewportHeight = viewportRect.height;
    
    // 计算目标滚动位置，使句子居中
    const targetScrollTop = viewport.scrollTop + relativeTop - (viewportHeight / 2) + (elementHeight / 2);
    
    // 只滚动 content-viewport，不滚动整个页面
    if (smooth) {
      // 平滑滚动
      const startScrollTop = viewport.scrollTop;
      const distance = targetScrollTop - startScrollTop;
      const duration = 300; // 滚动持续时间
      let startTime = null;
      
      function animateScroll(currentTime) {
        if (!startTime) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / duration, 1);
        // 使用缓动函数
        const easeProgress = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
        viewport.scrollTop = startScrollTop + distance * easeProgress;
        
        if (timeElapsed < duration) {
          requestAnimationFrame(animateScroll);
        }
      }
      
      requestAnimationFrame(animateScroll);
    } else {
      // 直接滚动
      viewport.scrollTop = targetScrollTop;
    }
    
    // 更新滚动状态
    contentScrollTop.value = viewport.scrollTop;
  }
  syncContentViewportMetrics();
}

function maybeLoadMoreFromViewport() {
  const viewport = contentViewportRef.value;
  if (!viewport) return;
  const remaining = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
  if (remaining <= CONTENT_SCROLL_EDGE_THRESHOLD) {
    loadMoreContent();
  }
}

function onContentScroll(event) {
  const viewport = event.target;
  if (!viewport) return;
  contentScrollTop.value = viewport.scrollTop;
  contentViewportHeight.value = viewport.clientHeight || contentViewportHeight.value;
  maybeLoadMoreFromViewport();
}

function syncContentViewportMetrics() {
  const viewport = contentViewportRef.value;
  if (!viewport) return;
  contentViewportHeight.value = viewport.clientHeight || contentViewportHeight.value;
  contentScrollTop.value = viewport.scrollTop || 0;
}

function sentenceClass(index) {
  const distance = Math.abs(index - currentSentenceIndex.value);
  return {
    current: distance === 0,
    tier1: distance === 1,
    tier2: distance === 2,
    tier3: distance === 3,
    tier4: distance >= 4
  };
}

function hasNewline(text) {
  return text.includes('\n');
}

function toggleTts() {
  ttsEnabled.value = !ttsEnabled.value;
  clearPreloadAudio();
  if (isPlaying.value) replayFromCurrent();
}

function toggleAutoAnalyze() {
  autoAnalyze.value = !autoAnalyze.value;
  if (autoAnalyze.value && hasSentence.value) {
    analyzeSentence();
  }
}

async function analyzeSentence() {
  if (!hasSentence.value || isAnalyzing.value) return;
  isAnalyzing.value = true;
  analyzeResult.value = { raw: "" };

  try {
    const text = currentSentence.value.english;
    const response = await fetch(buildApiUrl("/analyze_stream"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!response.ok) throw new Error("解析服务调用失败");

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      if (buffer.trim().length > 0) {
        analyzeResult.value = { raw: buffer };
      }
    }
  } catch (error) {
    handleError(error);
    analyzeResult.value = { error: error.message };
  } finally {
    isAnalyzing.value = false;
  }
}

function renderAnalyzeContent(raw) {
  if (!raw) return "";
  return marked.parse(raw, { async: false });
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
  console.log('Applying saved state:', savedState);
  if (!savedState) return false;
  if (!savedState.book || !savedState.chapter) return false;
  console.log('Current book:', currentBook.value, 'Current chapter:', currentChapter.value);
  if (savedState.book !== currentBook.value || savedState.chapter !== currentChapter.value) {
    console.log('Book or chapter mismatch, not applying saved state');
    return false;
  }
  if (!Array.isArray(savedState.chapterSentences) || !savedState.chapterSentences.length) {
    console.log('No chapter sentences in saved state, not applying');
    return false;
  }

  isRestoringState = true;
  chapterSentences.value = savedState.chapterSentences;
  currentPosition.value = Number(savedState.currentPosition || 0);
  chapterFinished.value = Boolean(savedState.chapterFinished);
  const restoredIndex = clampIndex(savedState.currentSentenceIndex, chapterSentences.value.length);
  console.log('Restored currentSentenceIndex:', restoredIndex);
  console.log('chapterSentences.length:', chapterSentences.value.length);
  console.log('safeSentenceCount:', Math.max(chapterSentences.value.length, 1));
  
  // 先设置progressValue，再设置currentSentenceIndex，确保进度条正确显示
  progressValue.value = restoredIndex;
  currentSentenceIndex.value = restoredIndex;
  
  playbackRate.value = clampPlaybackRate(savedState.playbackRate);
  ttsEnabled.value = typeof savedState.ttsEnabled === "boolean" ? savedState.ttsEnabled : ttsEnabled.value;
  autoPlayNext.value = typeof savedState.autoPlayNext === "boolean" ? savedState.autoPlayNext : autoPlayNext.value;
  autoAnalyze.value = typeof savedState.autoAnalyze === "boolean" ? savedState.autoAnalyze : autoAnalyze.value;
  fontScaleLevel.value = normalizeFontScaleLevel(savedState.fontScaleLevel);
  contentScrollTop.value = Number(savedState.contentScrollTop || 0);
  isRestoringState = false;
  
  // 等待DOM更新完成后再滚动到保存的位置
  nextTick(() => {
    const viewport = contentViewportRef.value;
    if (viewport) {
      viewport.scrollTop = contentScrollTop.value;
      // 确保当前句子在视口内
      centerCurrentSentence(false);
    }
  });
  
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
    autoAnalyze: autoAnalyze.value,
    fontScaleLevel: fontScaleLevel.value,
    contentScrollTop: contentScrollTop.value
  };
  console.log('Saving reading state:', payload);
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
