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
        <section class="main-stage panel">
          <div class="mode-badge">{{ statusText }}</div>
          <div class="sentence-counter">{{ currentSentenceIndex + 1 }} / {{ safeSentenceCount }}</div>

          <button class="nav-arrow left" type="button" @click="previousPage" :disabled="!canGoPrev">‹</button>
          <button class="nav-arrow right" type="button" @click="nextPage" :disabled="!hasSentence">›</button>

          <div class="sentence-stage">
            <template v-if="hasSentence">
              <p class="english-sentence">
                <template v-for="(segment, index) in highlightedSentence.segments" :key="`${segment.text}-${index}`">
                  <span :class="{ accent: segment.highlight }">{{ segment.text }}</span>
                </template>
              </p>
              <p class="chinese-sentence">{{ highlightedSentence.translation }}</p>
            </template>
            <template v-else>
              <p class="english-sentence empty-copy">选择书籍和章节后，将从 service 服务加载文本并拆句播放。</p>
              <p class="chinese-sentence">当前未加载内容</p>
            </template>
          </div>

          <div class="sentence-actions">
            <button class="mini-button" type="button" @click="speakCurrentSentence" :disabled="!hasSentence">单句播放</button>
            <button class="mini-button active" type="button" @click="toggleWord(highlightedSentence.keyword)" :disabled="!hasSentence">生词</button>
            <button class="mini-icon" type="button" @click="loadMoreContent" :disabled="chapterFinished || isLoadingMore">+</button>
          </div>

          <div class="transport">
            <button class="rate-chip" type="button" @click="cycleRate">
              <span class="rotate">⟳</span>
              <span>{{ playbackRate.toFixed(1) }}x</span>
              <span>语速</span>
            </button>

            <div class="transport-buttons">
              <button class="transport-button" type="button" @click="goToStart" :disabled="!hasSentence">|◀</button>
              <button class="transport-button primary" type="button" @click="togglePlayback" :disabled="!hasSentence">
                {{ isPlaying ? "❚❚" : "▶" }}
              </button>
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
              <span>使用服务 TTS</span>
              <button class="inline-switch" :class="{ active: ttsEnabled }" type="button" @click="toggleTts"></button>
            </div>
            <div class="toggle-row">
              <span>高亮当前词</span>
              <button class="inline-switch" :class="{ active: highlightCurrent }" type="button" @click="highlightCurrent = !highlightCurrent"></button>
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
                <button type="button">A-</button>
                <button type="button" class="active">A</button>
                <button type="button">A+</button>
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
          <p>{{ highlightedSentence.translation }}</p>
          <p class="muted">当前先用本地占位翻译承接真实文本播放，后续可继续接入 `/analyze` 或翻译服务。</p>
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

const DEFAULT_MIN_SIZE = 500;
const DEFAULT_BOOK = "哈利波特1-7英文原版";
const ANALYSIS_MODEL = "Qwen/Qwen3-14B";
const API_CANDIDATES = process.env.NODE_ENV === "development"
  ? ["/api", "http://localhost:8000", "http://127.0.0.1:8000"]
  : [window.location.origin, "http://localhost:8000", "http://127.0.0.1:8000"];

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
const analysisModel = ref(ANALYSIS_MODEL);
const autoPlayNext = ref(true);
const highlightCurrent = ref(true);
const followMode = ref(false);
const isPlaying = ref(false);
const ttsEnabled = ref(true);
const playbackRate = ref(1.0);
const rateOptions = [0.8, 1.0, 1.2, 1.4];

const audioRef = ref(null);
const savedWords = reactive(new Set(["bear", "Potters"]));
let advanceTimer = null;
let currentAudioUrl = null;
let playToken = 0;
const resolvedApiBase = ref("");

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

const highlightedSentence = computed(() => {
  const sentence = currentSentence.value;
  const keyword = sentence.keyword || "";
  if (!sentence.english || !keyword) {
    return { ...sentence, segments: [{ text: sentence.english || "暂无内容", highlight: false }] };
  }
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = sentence.english.split(new RegExp(`(${escaped})`, "i"));
  return {
    ...sentence,
    segments: parts.filter(Boolean).map((part) => ({
      text: part,
      highlight: highlightCurrent.value && part.toLowerCase() === keyword.toLowerCase()
    }))
  };
});

const vocabularyItems = computed(() =>
  (highlightedSentence.value.vocabulary || []).map((item) => ({
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

watch(playbackRate, async () => {
  if (!isPlaying.value) return;
  stopAudio();
  clearAdvanceTimer();
  await nextTick();
  await playCurrentSentence();
});

onMounted(async () => {
  try {
    await initializePlayer();
  } catch (error) {
    handleError(error);
  }
});

onBeforeUnmount(() => {
  stopPlayback();
});

async function initializePlayer() {
  isInitialLoading.value = true;
  try {
    await loadBooks();
    if (currentBook.value) {
      await loadChapters(currentBook.value);
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
    grammar: `句子已从 service 拆出。当前语法卡片使用占位内容，可继续对接 analyze_stream。`,
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
  if (isPlaying.value) {
    replayFromCurrent();
  }
}

async function nextPage() {
  if (!hasSentence.value) return;
  if (currentSentenceIndex.value < chapterSentences.value.length - 1) {
    currentSentenceIndex.value += 1;
    if (isPlaying.value) {
      await playCurrentSentence();
    }
    maybePreloadMore();
    return;
  }

  if (!chapterFinished.value) {
    const previousLength = chapterSentences.value.length;
    await loadMoreContent();
    if (chapterSentences.value.length > previousLength) {
      currentSentenceIndex.value += 1;
      if (isPlaying.value) {
        await playCurrentSentence();
      }
      maybePreloadMore();
      return;
    }
  }

  if (autoPlayNext.value && hasNextChapter.value) {
    await jumpToNextChapter();
    if (isPlaying.value) {
      await playCurrentSentence();
    }
    return;
  }

  stopPlayback();
}

function previousPage() {
  if (!hasSentence.value) return;
  currentSentenceIndex.value = Math.max(currentSentenceIndex.value - 1, 0);
  if (isPlaying.value) {
    replayFromCurrent();
  }
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
  const nextChapter = chapterOptions.value[currentChapterIndex.value + 1];
  currentChapter.value = nextChapter;
  await reloadCurrentChapter();
}

function togglePlayback() {
  if (isPlaying.value) {
    stopPlayback();
  } else {
    startPlayback();
  }
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
  if (!response.ok) {
    throw new Error("TTS 服务调用失败");
  }

  const blob = await response.blob();
  if (token !== playToken || !isPlaying.value) return;

  currentAudioUrl = URL.createObjectURL(blob);
  const audio = audioRef.value;
  audio.src = currentAudioUrl;
  audio.playbackRate = playbackRate.value;
  await audio.play();
}

function speakCurrentSentence() {
  if (!hasSentence.value) return;
  if (isPlaying.value) {
    replayFromCurrent();
    return;
  }

  if (ttsEnabled.value) {
    const token = ++playToken;
    requestTtsAudio(currentSentence.value.english, token).catch((error) => {
      handleError(error);
      ttsEnabled.value = false;
    });
    return;
  }

  scheduleTextAdvance(++playToken, false);
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

function cycleRate() {
  const index = rateOptions.findIndex((item) => item === playbackRate.value);
  playbackRate.value = rateOptions[(index + 1) % rateOptions.length];
}

function toggleTts() {
  ttsEnabled.value = !ttsEnabled.value;
  if (isPlaying.value) {
    replayFromCurrent();
  }
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

function buildApiUrl(path, base = resolvedApiBase.value) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!base) return normalizedPath;
  return `${base}${normalizedPath}`;
}

async function detectApiBase() {
  if (resolvedApiBase.value) return resolvedApiBase.value;

  const candidates = [...API_CANDIDATES];
  for (const base of candidates) {
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
