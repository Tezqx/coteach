/* CoTeach frontend — analyze, feedback cards, and progress. */

const I18N = {
  en: {
    tagline: "AI professional growth coach for teachers in Kazakhstan",
    tabAnalyze: "New analysis",
    tabProgress: "My progress",
    teacherName: "Your name",
    subject: "Subject",
    grade: "Grade",
    materialType: "Material type",
    materialText: "Paste a lesson plan, presentation text, transcript, or student work",
    upload: "Or upload a file (.txt, .docx, .pdf, .pptx)",
    submit: "Get coaching feedback",
    analyzing: "Analyzing your material…",
    demoBanner: "Demo mode — no API key configured. Showing sample feedback so you can try every screen.",
    types: {
      lesson_plan: "Lesson plan",
      presentation_text: "Presentation text",
      transcript: "Lesson transcript",
      student_work: "Student work",
    },
    summary: "Summary",
    rubric: "Rubric (1–4)",
    strengths: "Strengths",
    improvements: "Areas to grow",
    microActions: "Micro-actions for the next lesson",
    plan: "Two-week development plan",
    week1: "Week 1",
    week2: "Week 2",
    progressNote: "Progress note",
    scoreTrend: "Rubric scores over time",
    loadProgress: "Show progress",
    noHistory: "No saved analyses yet for this name. Submit a lesson first.",
    historyTitle: "Previous analyses",
    average: "Average",
    viewFeedback: "View feedback",
    evidence: "Evidence",
    footer: "CoTeach — a structured alternative to CritiSabaq. Feedback is coaching support, not an official evaluation.",
    errorGeneric: "Something went wrong. Please try again.",
    fileTooLarge: "This file is larger than 20 MB. Please upload a smaller file or paste the text.",
    priority: { high: "High", medium: "Medium", low: "Low" },
    meta: (d) => `${d.subject}, grade ${d.grade} · ${d.materialType} · ${d.when}`,
  },
  ru: {
    tagline: "ИИ-коуч профессионального роста для учителей Казахстана",
    tabAnalyze: "Новый разбор",
    tabProgress: "Мой прогресс",
    teacherName: "Ваше имя",
    subject: "Предмет",
    grade: "Класс",
    materialType: "Тип материала",
    materialText: "Вставьте план урока, текст презентации, транскрипт или работу ученика",
    upload: "Или загрузите файл (.txt, .docx, .pdf, .pptx)",
    submit: "Получить обратную связь",
    analyzing: "Анализируем материал…",
    demoBanner: "Демо-режим — ключ API не задан. Показана примерная обратная связь, чтобы можно было пройти все экраны.",
    types: {
      lesson_plan: "План урока",
      presentation_text: "Текст презентации",
      transcript: "Транскрипт урока",
      student_work: "Работа ученика",
    },
    summary: "Краткий обзор",
    rubric: "Рубрика (1–4)",
    strengths: "Сильные стороны",
    improvements: "Зоны роста",
    microActions: "Микродействия на следующий урок",
    plan: "План развития на две недели",
    week1: "Неделя 1",
    week2: "Неделя 2",
    progressNote: "Заметка о прогрессе",
    scoreTrend: "Динамика баллов по рубрике",
    loadProgress: "Показать прогресс",
    noHistory: "Для этого имени пока нет сохранённых разборов. Сначала отправьте материал.",
    historyTitle: "Предыдущие разборы",
    average: "Средний балл",
    viewFeedback: "Открыть обратную связь",
    evidence: "Свидетельство",
    footer: "CoTeach — структурированная альтернатива CritiSabaq. Это поддержка коуча, а не официальная оценка.",
    errorGeneric: "Что-то пошло не так. Попробуйте ещё раз.",
    fileTooLarge: "Файл больше 20 МБ. Загрузите файл поменьше или вставьте текст.",
    priority: { high: "Высокий", medium: "Средний", low: "Низкий" },
    meta: (d) => `${d.subject}, ${d.grade} класс · ${d.materialType} · ${d.when}`,
  },
  kk: {
    tagline: "Қазақстан мұғалімдеріне арналған кәсіби дамудың ЖИ-коучі",
    tabAnalyze: "Жаңа талдау",
    tabProgress: "Менің прогресім",
    teacherName: "Атыңыз",
    subject: "Пән",
    grade: "Сынып",
    materialType: "Материал түрі",
    materialText: "Сабақ жоспарын, презентация мәтінін, транскрипті немесе оқушы жұмысын қойыңыз",
    upload: "Немесе файл жүктеңіз (.txt, .docx, .pdf, .pptx)",
    submit: "Кері байланыс алу",
    analyzing: "Материал талданып жатыр…",
    demoBanner: "Демо-режим — API кілті берілмеген. Барлық экранды көру үшін үлгілік кері байланыс көрсетіледі.",
    types: {
      lesson_plan: "Сабақ жоспары",
      presentation_text: "Презентация мәтіні",
      transcript: "Сабақ транскрипті",
      student_work: "Оқушы жұмысы",
    },
    summary: "Қысқаша шолу",
    rubric: "Рубрика (1–4)",
    strengths: "Күшті жақтары",
    improvements: "Дамыту бағыттары",
    microActions: "Келесі сабаққа микроәрекеттер",
    plan: "Екі апталық даму жоспары",
    week1: "1-апта",
    week2: "2-апта",
    progressNote: "Прогресс туралы жазба",
    scoreTrend: "Рубрика ұпайларының динамикасы",
    loadProgress: "Прогресті көрсету",
    noHistory: "Бұл атпен сақталған талдау жоқ. Алдымен материал жіберіңіз.",
    historyTitle: "Алдыңғы талдаулар",
    average: "Орташа ұпай",
    viewFeedback: "Кері байланысты ашу",
    evidence: "Дәлел",
    footer: "CoTeach — CritiSabaq-қа балама құрылымды кері байланыс. Бұл ресми бағалау емес, коуч қолдауы.",
    errorGeneric: "Қате шықты. Қайта көріңіз.",
    fileTooLarge: "Файл 20 МБ-тан үлкен. Кішірек файл жүктеңіз немесе мәтінді қойыңыз.",
    priority: { high: "Жоғары", medium: "Орташа", low: "Төмен" },
    meta: (d) => `${d.subject}, ${d.grade}-сынып · ${d.materialType} · ${d.when}`,
  },
};

const CRITERION_ORDER = [
  "objectives",
  "structure_pacing",
  "explanation_practice",
  "differentiation",
  "engagement",
  "language_clarity",
];

const state = {
  lang: localStorage.getItem("coteach.lang") || "ru",
  demoMode: false,
  chart: null,
  lastResult: null,
};

const $ = (id) => document.getElementById(id);

function t() {
  return I18N[state.lang] || I18N.en;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function refreshIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons({ attrs: { "stroke-width": 2 } });
  }
}

function applyLanguage() {
  const i = t();
  document.documentElement.lang = state.lang;
  document.title = "CoTeach";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (i[key]) el.textContent = i[key];
  });
  $("tab-analyze").textContent = i.tabAnalyze;
  $("tab-progress").textContent = i.tabProgress;
  $("submit-btn").textContent = i.submit;
  $("progress-btn").textContent = i.loadProgress;
  $("demo-banner").textContent = i.demoBanner;

  const grade = $("grade");
  const currentGrade = grade.value;
  grade.innerHTML = "";
  for (let n = 1; n <= 11; n += 1) {
    const opt = document.createElement("option");
    opt.value = String(n);
    opt.textContent = String(n);
    grade.appendChild(opt);
  }
  if (currentGrade) grade.value = currentGrade;

  const typeSelect = $("material-type");
  const currentType = typeSelect.value;
  [...typeSelect.options].forEach((opt) => {
    opt.textContent = i.types[opt.value] || opt.value;
  });
  if (currentType) typeSelect.value = currentType;

  document.querySelectorAll("[data-set-lang]").forEach((btn) => {
    btn.classList.toggle("is-active", btn.getAttribute("data-set-lang") === state.lang);
  });

  if (state.lastResult) renderFeedback(state.lastResult);
  if (typeof applyProgramLanguage === "function") applyProgramLanguage();
  refreshIcons();
}

function setView(name) {
  ["analyze", "progress", "program"].forEach((view) => {
    $(`view-${view}`).classList.toggle("hidden", name !== view);
    $(`tab-${view}`).classList.toggle("is-active", name === view);
  });
  localStorage.setItem("coteach.view", name);
}

function showError(el, message) {
  if (!message) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.textContent = message;
  el.classList.remove("hidden");
}

function formatWhen(iso) {
  if (!iso) return "";
  const date = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  if (Number.isNaN(date.getTime())) return iso;
  const locale = { kk: "kk-KZ", ru: "ru-RU", en: "en-GB" }[state.lang] || "en-GB";
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Berlin",
  }).format(date);
}

function renderFeedback(result) {
  const i = t();
  const fb = result.feedback || {};
  const typeLabel = i.types[result.material_type] || result.material_type;
  const meta = i.meta({
    subject: result.subject,
    grade: result.grade,
    materialType: typeLabel,
    when: formatWhen(result.created_at),
  });
  const avg = result.average_score != null ? Number(result.average_score).toFixed(2) : "";

  const rubricHtml = (fb.rubric || []).map((item) => `
    <article class="rubric-item">
      <div class="rubric-head">
        <strong>${esc(item.label || item.id)}</strong>
        <div class="score s${esc(item.score)}">${esc(item.score)}</div>
      </div>
      <p class="evidence">${esc(item.evidence || "")}</p>
    </article>
  `).join("");

  const strengths = (fb.strengths || []).map((item) => `
    <li>
      <div class="item-head"><i data-lucide="sprout"></i><div>
        <div>${esc(item.text)}</div>
        ${item.evidence ? `<p class="quote">“${esc(item.evidence)}”</p>` : ""}
      </div></div>
    </li>
  `).join("");

  const improvements = (fb.improvements || []).map((item) => `
    <li>
      <span class="priority ${esc(item.priority || "medium")}">${esc(i.priority[item.priority] || item.priority)}</span>
      <div>${esc(item.text)}</div>
      ${item.evidence ? `<p class="quote">“${esc(item.evidence)}”</p>` : ""}
    </li>
  `).join("");

  const actions = (fb.micro_actions || []).map((item) => `
    <div class="action"><i data-lucide="zap"></i> ${esc(item)}</div>
  `).join("");

  const plan = fb.development_plan || {};
  const week = (label, data) => `
    <div class="plan-col">
      <h3>${esc(label)}</h3>
      <p><strong>${esc(data && data.focus ? data.focus : "")}</strong></p>
      <ol>${(data && data.actions ? data.actions : []).map((a) => `<li>${esc(a)}</li>`).join("")}</ol>
    </div>
  `;

  $("feedback").innerHTML = `
    <article class="card">
      <div class="accent-bar"></div>
      <h2 class="card-heading"><i data-lucide="clipboard-check"></i> ${esc(i.summary)}</h2>
      <p class="meta">${esc(meta)} · ${esc(i.average)}: <span class="average">${esc(avg)} / 4</span></p>
      <p class="summary">${esc(fb.summary || "")}</p>
    </article>
    <article class="card">
      <h2 class="card-heading"><i data-lucide="layout-grid"></i> ${esc(i.rubric)}</h2>
      <div class="rubric">${rubricHtml}</div>
    </article>
    <article class="card">
      <h2 class="card-heading"><i data-lucide="sprout" class="icon-gold"></i> ${esc(i.strengths)}</h2>
      <ul class="list">${strengths}</ul>
    </article>
    <article class="card">
      <h2 class="card-heading"><i data-lucide="trending-up"></i> ${esc(i.improvements)}</h2>
      <ul class="list">${improvements}</ul>
    </article>
    <article class="card">
      <h2 class="card-heading"><i data-lucide="zap" class="icon-gold"></i> ${esc(i.microActions)}</h2>
      <div class="actions">${actions}</div>
    </article>
    <article class="card">
      <h2 class="card-heading"><i data-lucide="calendar-days"></i> ${esc(i.plan)}</h2>
      <div class="plan">${week(i.week1, plan.week1)}${week(i.week2, plan.week2)}</div>
    </article>
    <article class="card progress-note">
      <h2 class="card-heading"><i data-lucide="route"></i> ${esc(i.progressNote)}</h2>
      <p>${esc(fb.progress_note || "")}</p>
    </article>
  `;
  $("feedback").classList.remove("hidden");
  refreshIcons();
}

async function analyze(event) {
  event.preventDefault();
  const i = t();
  showError($("form-error"), "");
  $("feedback").classList.add("hidden");
  $("status").textContent = i.analyzing;
  $("status").classList.remove("hidden");
  $("submit-btn").disabled = true;

  const name = $("teacher-name").value.trim();
  localStorage.setItem("coteach.teacherName", name);
  $("progress-name").value = name;

  const form = new FormData();
  form.append("teacher_name", name);
  form.append("language", state.lang);
  form.append("subject", $("subject").value.trim());
  form.append("grade", $("grade").value);
  form.append("material_type", $("material-type").value);
  form.append("text", $("material-text").value);
  const file = $("material-file").files[0];
  if (file && file.size > 20 * 1024 * 1024) {
    showError($("form-error"), i.fileTooLarge);
    $("status").classList.add("hidden");
    $("submit-btn").disabled = false;
    return;
  }
  if (file) form.append("file", file);

  try {
    const res = await fetch("/api/analyze", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || i.errorGeneric);
    state.lastResult = data;
    renderFeedback(data);
  } catch (err) {
    showError($("form-error"), err.message || i.errorGeneric);
  } finally {
    $("status").classList.add("hidden");
    $("submit-btn").disabled = false;
  }
}

function renderChart(analyses) {
  const canvas = $("score-chart");
  const labels = analyses.map((a, idx) => formatWhen(a.created_at) || `#${idx + 1}`);
  const colors = {
    objectives: "#0F766E",
    structure_pacing: "#F59E0B",
    explanation_practice: "#0369a1",
    differentiation: "#7c3aed",
    engagement: "#be123c",
    language_clarity: "#15803d",
    average: "#1c2a2a",
  };
  const i = t();
  const labelFor = (id) => {
    const first = analyses.map((a) => (a.feedback && a.feedback.rubric || []).find((r) => r.id === id)).find(Boolean);
    return (first && first.label) || id;
  };
  const datasets = CRITERION_ORDER.map((id) => ({
    label: labelFor(id),
    data: analyses.map((a) => (a.scores || {})[id] ?? null),
    borderColor: colors[id],
    backgroundColor: "transparent",
    tension: 0.25,
    pointRadius: 4,
  }));
  datasets.push({
    label: i.average,
    data: analyses.map((a) => a.average_score),
    borderColor: colors.average,
    borderDash: [5, 4],
    backgroundColor: "transparent",
    tension: 0.25,
    pointRadius: 4,
  });
  if (state.chart) state.chart.destroy();
  state.chart = new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      scales: { y: { min: 1, max: 4, ticks: { stepSize: 1 } } },
      plugins: { legend: { position: "bottom" } },
    },
  });
}

async function loadProgress(event) {
  if (event) event.preventDefault();
  const i = t();
  const name = $("progress-name").value.trim();
  showError($("progress-error"), "");
  $("progress-empty").classList.add("hidden");
  $("progress-panel").classList.add("hidden");
  if (!name) return;
  localStorage.setItem("coteach.teacherName", name);
  $("teacher-name").value = name;
  try {
    const res = await fetch(`/api/progress?teacher_name=${encodeURIComponent(name)}`);
    if (res.status === 404) {
      $("progress-empty").textContent = i.noHistory;
      $("progress-empty").classList.remove("hidden");
      return;
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || i.errorGeneric);
    const analyses = data.analyses || [];
    if (!analyses.length) {
      $("progress-empty").textContent = i.noHistory;
      $("progress-empty").classList.remove("hidden");
      return;
    }
    $("progress-panel").classList.remove("hidden");
    renderChart(analyses);
    $("history-list").innerHTML = `<h2 class="card-heading"><i data-lucide="history"></i> ${esc(i.historyTitle)}</h2>` +
      [...analyses].reverse().map((a) => `
        <button type="button" class="card history-item" data-analysis-id="${esc(a.id)}">
          <strong>${esc(a.subject)}, ${esc(a.grade)}</strong>
          <div class="meta">${esc(i.types[a.material_type] || a.material_type)} · ${esc(formatWhen(a.created_at))} · ${esc(i.average)} ${esc(Number(a.average_score).toFixed(2))}</div>
          <div>${esc(a.summary || "")}</div>
        </button>
      `).join("");
    $("history-list").querySelectorAll("[data-analysis-id]").forEach((btn) => {
      btn.addEventListener("click", () => openAnalysis(Number(btn.getAttribute("data-analysis-id"))));
    });
    refreshIcons();
  } catch (err) {
    showError($("progress-error"), err.message || i.errorGeneric);
  }
}

async function openAnalysis(id) {
  const i = t();
  try {
    const res = await fetch(`/api/analyses/${id}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || i.errorGeneric);
    state.lastResult = data;
    setView("analyze");
    renderFeedback(data);
    $("feedback").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showError($("progress-error"), err.message || i.errorGeneric);
  }
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    state.demoMode = Boolean(data.demo_mode);
    $("demo-banner").classList.toggle("hidden", !state.demoMode);
  } catch {
    $("demo-banner").classList.add("hidden");
  }
}

function init() {
  const savedName = localStorage.getItem("coteach.teacherName") || "";
  $("teacher-name").value = savedName;
  $("progress-name").value = savedName;
  if (!I18N[state.lang]) state.lang = "en";
  initProgram();
  applyLanguage();
  loadConfig();

  document.querySelectorAll("[data-set-lang]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.lang = btn.getAttribute("data-set-lang");
      localStorage.setItem("coteach.lang", state.lang);
      applyLanguage();
    });
  });
  $("tab-analyze").addEventListener("click", () => setView("analyze"));
  $("tab-progress").addEventListener("click", () => {
    setView("progress");
    if ($("progress-name").value.trim()) loadProgress();
  });
  $("tab-program").addEventListener("click", () => {
    setView("program");
    enterProgramView();
  });
  $("analyze-form").addEventListener("submit", analyze);
  $("progress-form").addEventListener("submit", loadProgress);
  if (localStorage.getItem("coteach.view") === "program") {
    setView("program");
    enterProgramView();
  }
}

init();
