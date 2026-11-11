/* CoTeach Growth Program — multi-week plan, weekly submissions, dashboard, final report.
   Loaded before app.js; uses its globals (state, esc, $, formatWhen, refreshIcons, showError). */

const PROGRAM_I18N = {
  en: {
    tabProgram: "Growth program",
    progIntro: "A multi-week coaching cycle: pick 1–2 focus areas, get one concrete task per week, submit your results at the end of each week, and watch your growth.",
    myPrograms: "My programs",
    loadPrograms: "Show my programs",
    noPrograms: "No programs yet for this name. Start one below.",
    startTitle: "Start a new program",
    weeksLabel: "Length (weeks)",
    focusLabel: "Focus areas (choose 1–2)",
    focusAuto: "Let the coach choose from my latest analysis",
    goalLabel: "Personal goal (optional)",
    goalPlaceholder: "e.g. I want weaker students to take part in every lesson",
    langHint: "The coach will write in the interface language selected above.",
    startBtn: "Create my program",
    creating: "The coach is designing your program…",
    focusRequired: "Choose 1–2 focus areas, or let the coach choose.",
    back: "All programs",
    statusActive: "In progress",
    statusCompleted: "Completed",
    weekN: (n) => `Week ${n}`,
    weekOf: (n, total) => `Week ${n} of ${total}`,
    currentTask: "This week's task",
    adjustedNote: "Adjusted by the coach after last week",
    evidenceToSubmit: "What to submit",
    timeline: "Timeline",
    st: { done: "Done", current: "Current", upcoming: "Upcoming" },
    focusChart: "Focus scores by week",
    chartEmpty: "The chart appears after your first weekly submission.",
    baseline: "Start",
    average: "Average",
    submitTitle: (n) => `Submit your week ${n} results`,
    weekMaterials: "Paste this week's materials (lesson plan, slide text, transcript, student work)",
    weekFiles: "Or upload files (.txt, .docx, .pdf, .pptx); you can pick several",
    reflectionLabel: "Reflection: what did you try, what worked, what didn't?",
    submitWeek: "Submit week",
    reviewing: "The coach is reviewing your week…",
    weekFeedback: "Weekly feedback",
    taskCheck: "Task check",
    taskStatus: { done: "Done", partial: "Partly done", not_done: "Not done" },
    nextTask: "Next week's task",
    yourReflection: "Your reflection",
    files: "Files",
    task: "Task",
    reportTitle: "Final growth report",
    growthSummary: "Growth summary",
    beforeAfter: "Before / after on focus areas",
    before: "Before",
    after: "After",
    achievements: "Achievements",
    recommendations: "Recommendations for the next program",
    nextFocus: "Suggested focus for the next program",
    weeksOverview: "Week by week",
    print: "Print / save as PDF",
    retryReport: "Generate final report",
    reportPending: "All weeks are submitted, but the final report has not been generated yet.",
    programMeta: (d) => `${d.subject}, grade ${d.grade} · ${d.weeks} weeks · started ${d.when}`,
    coachChose: "chosen by the coach",
    goal: "Personal goal",
    overview: "About this program",
    progressWeeks: (done, total) => `${done} / ${total} weeks`,
    open: "Open",
    nameRequired: "Enter your name first.",
    teacher: "Teacher",
    strengths: "Strengths",
    improvements: "Areas to grow",
    microActions: "Micro-actions",
    progressNote: "Progress note",
    rubric: "Rubric (1–4)",
  },
  ru: {
    tabProgram: "Программа роста",
    progIntro: "Многонедельный цикл коучинга: выберите 1–2 направления, каждую неделю получайте одно конкретное задание, в конце недели присылайте результаты и следите за своим ростом.",
    myPrograms: "Мои программы",
    loadPrograms: "Показать мои программы",
    noPrograms: "Для этого имени программ пока нет. Начните новую ниже.",
    startTitle: "Начать новую программу",
    weeksLabel: "Длительность (недель)",
    focusLabel: "Направления (выберите 1–2)",
    focusAuto: "Пусть коуч выберет по моему последнему разбору",
    goalLabel: "Личная цель (необязательно)",
    goalPlaceholder: "Например: хочу, чтобы слабые ученики участвовали в каждом уроке",
    langHint: "Коуч будет писать на языке интерфейса, выбранном вверху.",
    startBtn: "Создать программу",
    creating: "Коуч составляет вашу программу…",
    focusRequired: "Выберите 1–2 направления или доверьте выбор коучу.",
    back: "Все программы",
    statusActive: "В процессе",
    statusCompleted: "Завершена",
    weekN: (n) => `Неделя ${n}`,
    weekOf: (n, total) => `Неделя ${n} из ${total}`,
    currentTask: "Задание этой недели",
    adjustedNote: "Скорректировано коучем по итогам прошлой недели",
    evidenceToSubmit: "Что прислать",
    timeline: "Ход программы",
    st: { done: "Готово", current: "Сейчас", upcoming: "Впереди" },
    focusChart: "Баллы по направлениям по неделям",
    chartEmpty: "График появится после первой отправки недели.",
    baseline: "Старт",
    average: "Средний балл",
    submitTitle: (n) => `Отправить результаты ${n}-й недели`,
    weekMaterials: "Вставьте материалы недели (план урока, текст слайдов, транскрипт, работы учеников)",
    weekFiles: "Или загрузите файлы (.txt, .docx, .pdf, .pptx); можно выбрать несколько",
    reflectionLabel: "Рефлексия: что вы попробовали, что сработало, что нет?",
    submitWeek: "Отправить неделю",
    reviewing: "Коуч разбирает вашу неделю…",
    weekFeedback: "Обратная связь за неделю",
    taskCheck: "Выполнение задания",
    taskStatus: { done: "Выполнено", partial: "Частично", not_done: "Не выполнено" },
    nextTask: "Задание на следующую неделю",
    yourReflection: "Ваша рефлексия",
    files: "Файлы",
    task: "Задание",
    reportTitle: "Итоговый отчёт о росте",
    growthSummary: "Итоги роста",
    beforeAfter: "До / после по направлениям",
    before: "До",
    after: "После",
    achievements: "Достижения",
    recommendations: "Рекомендации для следующей программы",
    nextFocus: "Предлагаемые направления следующей программы",
    weeksOverview: "По неделям",
    print: "Печать / сохранить в PDF",
    retryReport: "Сформировать итоговый отчёт",
    reportPending: "Все недели сданы, но итоговый отчёт ещё не сформирован.",
    programMeta: (d) => `${d.subject}, ${d.grade} класс · ${d.weeks} нед. · начата ${d.when}`,
    coachChose: "выбрано коучем",
    goal: "Личная цель",
    overview: "О программе",
    progressWeeks: (done, total) => `${done} / ${total} нед.`,
    open: "Открыть",
    nameRequired: "Сначала введите имя.",
    teacher: "Учитель",
    strengths: "Сильные стороны",
    improvements: "Зоны роста",
    microActions: "Микродействия",
    progressNote: "Заметка о прогрессе",
    rubric: "Рубрика (1–4)",
  },
  kk: {
    tabProgram: "Даму бағдарламасы",
    progIntro: "Бірнеше апталық коучинг циклі: 1–2 бағыт таңдаңыз, әр апта бір нақты тапсырма алыңыз, апта соңында нәтижені жіберіп, өсуіңізді бақылаңыз.",
    myPrograms: "Менің бағдарламаларым",
    loadPrograms: "Бағдарламаларымды көрсету",
    noPrograms: "Бұл атпен бағдарлама әлі жоқ. Төменде жаңасын бастаңыз.",
    startTitle: "Жаңа бағдарлама бастау",
    weeksLabel: "Ұзақтығы (апта)",
    focusLabel: "Бағыттар (1–2 таңдаңыз)",
    focusAuto: "Соңғы талдауым бойынша коуч таңдасын",
    goalLabel: "Жеке мақсат (міндетті емес)",
    goalPlaceholder: "Мысалы: әлсіз оқушылар әр сабаққа қатысқанын қалаймын",
    langHint: "Коуч жоғарыда таңдалған интерфейс тілінде жазады.",
    startBtn: "Бағдарлама құру",
    creating: "Коуч бағдарламаңызды құрып жатыр…",
    focusRequired: "1–2 бағыт таңдаңыз немесе таңдауды коучқа қалдырыңыз.",
    back: "Барлық бағдарламалар",
    statusActive: "Жүріп жатыр",
    statusCompleted: "Аяқталды",
    weekN: (n) => `${n}-апта`,
    weekOf: (n, total) => `${total} аптаның ${n}-аптасы`,
    currentTask: "Осы аптаның тапсырмасы",
    adjustedNote: "Өткен апта нәтижесі бойынша коуч түзеткен",
    evidenceToSubmit: "Не жіберу керек",
    timeline: "Бағдарлама барысы",
    st: { done: "Дайын", current: "Қазір", upcoming: "Алда" },
    focusChart: "Бағыттар бойынша апталық ұпайлар",
    chartEmpty: "График алғашқы апта жіберілгеннен кейін пайда болады.",
    baseline: "Бастау",
    average: "Орташа ұпай",
    submitTitle: (n) => `${n}-апта нәтижесін жіберу`,
    weekMaterials: "Апта материалдарын қойыңыз (сабақ жоспары, слайд мәтіні, транскрипт, оқушы жұмыстары)",
    weekFiles: "Немесе файл жүктеңіз (.txt, .docx, .pdf, .pptx); бірнешеуін таңдауға болады",
    reflectionLabel: "Рефлексия: не сынадыңыз, не нәтиже берді, не бермеді?",
    submitWeek: "Аптаны жіберу",
    reviewing: "Коуч аптаңызды талдап жатыр…",
    weekFeedback: "Апталық кері байланыс",
    taskCheck: "Тапсырманың орындалуы",
    taskStatus: { done: "Орындалды", partial: "Ішінара", not_done: "Орындалмады" },
    nextTask: "Келесі аптаның тапсырмасы",
    yourReflection: "Сіздің рефлексияңыз",
    files: "Файлдар",
    task: "Тапсырма",
    reportTitle: "Даму туралы қорытынды есеп",
    growthSummary: "Даму қорытындысы",
    beforeAfter: "Бағыттар бойынша дейін / кейін",
    before: "Дейін",
    after: "Кейін",
    achievements: "Жетістіктер",
    recommendations: "Келесі бағдарламаға ұсыныстар",
    nextFocus: "Келесі бағдарламаға ұсынылатын бағыттар",
    weeksOverview: "Апта бойынша",
    print: "Басып шығару / PDF сақтау",
    retryReport: "Қорытынды есепті жасау",
    reportPending: "Барлық апта жіберілді, бірақ қорытынды есеп әлі жасалмады.",
    programMeta: (d) => `${d.subject}, ${d.grade}-сынып · ${d.weeks} апта · басталды ${d.when}`,
    coachChose: "коуч таңдады",
    goal: "Жеке мақсат",
    overview: "Бағдарлама туралы",
    progressWeeks: (done, total) => `${done} / ${total} апта`,
    open: "Ашу",
    nameRequired: "Алдымен атыңызды енгізіңіз.",
    teacher: "Мұғалім",
    strengths: "Күшті жақтары",
    improvements: "Дамыту бағыттары",
    microActions: "Микроәрекеттер",
    progressNote: "Прогресс туралы жазба",
    rubric: "Рубрика (1–4)",
  },
};

const FOCUS_COLORS = ["#0F766E", "#F59E0B"];

const prog = {
  rubric: [],
  view: null,
  chart: null,
};

function pt() {
  return PROGRAM_I18N[state.lang] || PROGRAM_I18N.en;
}

function criterionLabel(id, lang) {
  const item = prog.rubric.find((c) => c.id === id);
  if (!item) return id;
  return item[lang || state.lang] || item.en || id;
}

async function loadRubric() {
  try {
    const res = await fetch("/api/rubric");
    prog.rubric = await res.json();
  } catch {
    prog.rubric = [];
  }
  renderFocusOptions();
}

function renderFocusOptions() {
  const box = $("focus-options");
  if (!box) return;
  const checked = new Set([...box.querySelectorAll("input:checked")].map((el) => el.value));
  box.innerHTML = prog.rubric.map((c) => `
    <label class="chip-check">
      <input type="checkbox" name="focus" value="${esc(c.id)}" ${checked.has(c.id) ? "checked" : ""} />
      <span>${esc(criterionLabel(c.id))}</span>
    </label>
  `).join("");
  box.querySelectorAll("input").forEach((el) => el.addEventListener("change", onFocusChange));
  onFocusChange();
}

function onFocusChange(event) {
  const boxes = [...document.querySelectorAll("#focus-options input")];
  const picked = boxes.filter((el) => el.checked);
  if (picked.length > 2 && event && event.target) event.target.checked = false;
  const count = boxes.filter((el) => el.checked).length;
  boxes.forEach((el) => { el.disabled = !el.checked && count >= 2; });
  if (count > 0) $("focus-auto").checked = false;
}

function applyProgramLanguage() {
  const i = pt();
  document.querySelectorAll("[data-pi18n]").forEach((el) => {
    const key = el.getAttribute("data-pi18n");
    if (typeof i[key] === "string") el.textContent = i[key];
  });
  const goal = $("p-goal");
  if (goal) goal.placeholder = i.goalPlaceholder;
  const tab = $("tab-program");
  if (tab) tab.textContent = i.tabProgram;
  renderFocusOptions();
  if (prog.view) renderProgram(prog.view);
  else if ($("program-list") && $("program-list").dataset.loaded) loadPrograms();
}

function setProgramScreen(name) {
  $("program-home").classList.toggle("hidden", name !== "home");
  $("program-dashboard").classList.toggle("hidden", name !== "dashboard");
}

function programName() {
  return $("p-name").value.trim();
}

async function loadPrograms(event) {
  if (event) event.preventDefault();
  const i = pt();
  const name = programName();
  showError($("program-error"), "");
  if (!name) {
    showError($("program-error"), i.nameRequired);
    return;
  }
  localStorage.setItem("coteach.teacherName", name);
  try {
    const res = await fetch(`/api/programs?teacher_name=${encodeURIComponent(name)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || t().errorGeneric);
    const list = data.programs || [];
    const box = $("program-list");
    box.dataset.loaded = "1";
    $("program-list-card").classList.remove("hidden");
    if (!list.length) {
      box.innerHTML = `<p class="muted">${esc(i.noPrograms)}</p>`;
      return;
    }
    box.innerHTML = list.map((p) => `
      <button type="button" class="program-item" data-program-id="${esc(p.id)}">
        <div class="program-item-head">
          <strong>${esc(p.title || i.tabProgram)}</strong>
          <span class="pill ${p.status === "completed" ? "pill-done" : "pill-current"}">${esc(p.status === "completed" ? i.statusCompleted : i.statusActive)}</span>
        </div>
        <div class="meta">${esc(i.programMeta({ subject: p.subject, grade: p.grade, weeks: p.weeks, when: formatWhen(p.created_at) }))}</div>
        <div class="mini-progress"><span style="width:${Math.round((100 * p.submitted) / p.weeks)}%"></span></div>
        <div class="meta">${esc(i.progressWeeks(p.submitted, p.weeks))} · ${p.focus_criteria.map((c) => esc(criterionLabel(c, p.language))).join(" · ")}</div>
      </button>
    `).join("");
    box.querySelectorAll("[data-program-id]").forEach((btn) => {
      btn.addEventListener("click", () => openProgram(Number(btn.getAttribute("data-program-id"))));
    });
  } catch (err) {
    showError($("program-error"), err.message || t().errorGeneric);
  }
}

async function startProgram(event) {
  event.preventDefault();
  const i = pt();
  showError($("program-error"), "");
  const name = programName();
  if (!name) {
    showError($("program-error"), i.nameRequired);
    return;
  }
  const focus = [...document.querySelectorAll("#focus-options input:checked")].map((el) => el.value);
  const auto = $("focus-auto").checked;
  if (!focus.length && !auto) {
    showError($("program-error"), i.focusRequired);
    return;
  }
  localStorage.setItem("coteach.teacherName", name);
  const btn = $("p-start-btn");
  btn.disabled = true;
  $("program-status").textContent = i.creating;
  $("program-status").classList.remove("hidden");
  try {
    const res = await fetch("/api/programs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        teacher_name: name,
        language: state.lang,
        subject: $("p-subject").value.trim(),
        grade: $("p-grade").value,
        weeks: Number($("p-weeks").value),
        focus_criteria: auto ? [] : focus,
        goal: $("p-goal").value.trim(),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(formatDetail(data.detail) || t().errorGeneric);
    showProgram(data);
  } catch (err) {
    showError($("program-error"), err.message || t().errorGeneric);
  } finally {
    btn.disabled = false;
    $("program-status").classList.add("hidden");
  }
}

function formatDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  return JSON.stringify(detail);
}

async function openProgram(id, silent = false) {
  try {
    const res = await fetch(`/api/programs/${id}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || t().errorGeneric);
    showProgram(data);
  } catch (err) {
    if (!silent) showError($("program-error"), err.message || t().errorGeneric);
  }
}

function showProgram(view) {
  prog.view = view;
  localStorage.setItem("coteach.programId", String(view.id));
  setProgramScreen("dashboard");
  renderProgram(view);
  window.scrollTo({ top: $("program-dashboard").offsetTop - 12, behavior: "smooth" });
}

function scoreBadge(score) {
  return `<div class="score s${esc(score)}">${esc(score)}</div>`;
}

function renderWeekFeedback(item, i, open) {
  const sub = item.submission;
  const fb = sub.feedback || {};
  const focus = prog.view.focus_criteria;
  const check = fb.task_check || {};
  const rubric = (fb.rubric || []).map((r) => `
    <article class="rubric-item ${focus.includes(r.id) ? "is-focus" : ""}">
      <div class="rubric-head"><strong>${esc(r.label || r.id)}</strong>${scoreBadge(r.score)}</div>
      <p class="evidence">${esc(r.evidence || "")}</p>
    </article>
  `).join("");
  const strengths = (fb.strengths || []).map((s) => `
    <li><div class="item-head"><i data-lucide="sprout"></i><div><div>${esc(s.text)}</div>
    ${s.evidence ? `<p class="quote">“${esc(s.evidence)}”</p>` : ""}</div></div></li>`).join("");
  const improvements = (fb.improvements || []).map((s) => `
    <li><span class="priority ${esc(s.priority || "medium")}">${esc(t().priority[s.priority] || s.priority)}</span>
    <div>${esc(s.text)}</div>${s.evidence ? `<p class="quote">“${esc(s.evidence)}”</p>` : ""}</li>`).join("");
  const actions = (fb.micro_actions || []).map((a) => `<div class="action"><i data-lucide="zap"></i> ${esc(a)}</div>`).join("");
  const next = fb.next_task;
  return `
    <details class="card week-card" id="week-${item.week}" ${open ? "open" : ""}>
      <summary>
        <span class="week-dot done">${item.week}</span>
        <span class="week-sum-title"><strong>${esc(i.weekN(item.week))}</strong> · ${esc(sub.task.focus || "")}</span>
        <span class="pill pill-${esc(check.status || "done")}">${esc(i.taskStatus[check.status] || check.status || "")}</span>
        <span class="average">${esc(Number(sub.average_score).toFixed(2))} / 4</span>
      </summary>
      <div class="week-body">
        <p class="meta">${esc(formatWhen(sub.created_at))}${sub.filenames && sub.filenames.length ? ` · ${esc(i.files)}: ${sub.filenames.map(esc).join(", ")}` : ""}</p>
        <div class="task-recap"><strong>${esc(i.task)}:</strong> ${esc(sub.task.task || "")}</div>
        <p class="summary">${esc(fb.summary || "")}</p>
        <div class="check-box check-${esc(check.status || "done")}">
          <h3><i data-lucide="list-checks"></i> ${esc(i.taskCheck)}: ${esc(i.taskStatus[check.status] || "")}</h3>
          <p>${esc(check.comment || "")}</p>
        </div>
        ${sub.reflection ? `<div class="reflection"><h3>${esc(i.yourReflection)}</h3><p>${esc(sub.reflection)}</p></div>` : ""}
        <h3 class="card-heading"><i data-lucide="layout-grid"></i> ${esc(i.rubric)}</h3>
        <div class="rubric">${rubric}</div>
        <div class="two-col">
          <div><h3 class="card-heading"><i data-lucide="sprout" class="icon-gold"></i> ${esc(i.strengths)}</h3><ul class="list">${strengths}</ul></div>
          <div><h3 class="card-heading"><i data-lucide="trending-up"></i> ${esc(i.improvements)}</h3><ul class="list">${improvements}</ul></div>
        </div>
        <h3 class="card-heading"><i data-lucide="zap" class="icon-gold"></i> ${esc(i.microActions)}</h3>
        <div class="actions">${actions}</div>
        ${next ? `<div class="next-task"><h3><i data-lucide="arrow-right-circle"></i> ${esc(i.nextTask)}</h3>
          <p><strong>${esc(next.focus || "")}</strong></p><p>${esc(next.task || "")}</p>
          <p class="meta">${esc(i.evidenceToSubmit)}: ${esc(next.evidence || "")}</p></div>` : ""}
        <div class="progress-note-inline"><h3><i data-lucide="route"></i> ${esc(i.progressNote)}</h3><p>${esc(fb.progress_note || "")}</p></div>
      </div>
    </details>
  `;
}

function renderReport(view, i) {
  const r = view.report;
  if (!r) {
    if (view.submitted >= view.weeks) {
      return `<div class="card report-pending"><p>${esc(i.reportPending)}</p>
        ${view.report_error ? `<p class="error">${esc(view.report_error)}</p>` : ""}
        <button type="button" class="btn primary" id="p-report-btn">${esc(i.retryReport)}</button></div>`;
    }
    return "";
  }
  const rows = (r.focus_comparison || []).map((f) => {
    const pct = (v) => (v == null ? 0 : Math.round((Number(v) / 4) * 100));
    return `
      <div class="ba-row">
        <div class="ba-label"><strong>${esc(criterionLabel(f.id, view.language))}</strong><p class="evidence">${esc(f.comment || "")}</p></div>
        <div class="ba-bars">
          <div class="ba-bar"><span class="ba-name">${esc(i.before)}</span><div class="bar"><span class="bar-before" style="width:${pct(f.before)}%"></span></div><b>${f.before == null ? "—" : esc(Number(f.before).toFixed(1))}</b></div>
          <div class="ba-bar"><span class="ba-name">${esc(i.after)}</span><div class="bar"><span class="bar-after" style="width:${pct(f.after)}%"></span></div><b>${f.after == null ? "—" : esc(Number(f.after).toFixed(1))}</b></div>
        </div>
      </div>`;
  }).join("");
  const weeks = view.timeline.filter((w) => w.submission).map((w) => `
    <tr><td>${esc(i.weekN(w.week))}</td><td>${esc(w.submission.task.focus || "")}</td>
    <td>${esc(i.taskStatus[(w.submission.feedback.task_check || {}).status] || "")}</td>
    <td>${view.focus_criteria.map((c) => esc(w.submission.scores[c])).join(" / ")}</td>
    <td>${esc(Number(w.submission.average_score).toFixed(2))}</td></tr>`).join("");
  return `
    <article class="card report" id="program-report">
      <div class="report-head">
        <div>
          <div class="accent-bar"></div>
          <h2 class="card-heading"><i data-lucide="award" class="icon-gold"></i> ${esc(i.reportTitle)}</h2>
          <p class="meta">${esc(view.plan.title || "")} · ${esc(i.teacher)}: ${esc(view.teacher_name || "")} · ${esc(i.programMeta({ subject: view.subject, grade: view.grade, weeks: view.weeks, when: formatWhen(view.created_at) }))}</p>
        </div>
        <button type="button" class="btn ghost no-print" id="p-print-btn"><i data-lucide="printer"></i> ${esc(i.print)}</button>
      </div>
      <h3>${esc(i.growthSummary)}</h3>
      <p class="summary">${esc(r.growth_summary || "")}</p>
      <h3>${esc(i.beforeAfter)}</h3>
      <div class="ba">${rows}</div>
      <div class="two-col">
        <div><h3>${esc(i.achievements)}</h3><ul class="list">${(r.achievements || []).map((a) => `<li><div class="item-head"><i data-lucide="check-circle-2"></i><div>${esc(a)}</div></div></li>`).join("")}</ul></div>
        <div><h3>${esc(i.recommendations)}</h3><ul class="list">${(r.recommendations || []).map((a) => `<li><div class="item-head"><i data-lucide="compass"></i><div>${esc(a)}</div></div></li>`).join("")}</ul></div>
      </div>
      ${(r.next_focus || []).length ? `<h3>${esc(i.nextFocus)}</h3><div class="chips">${r.next_focus.map((c) => `<span class="chip">${esc(criterionLabel(c, view.language))}</span>`).join("")}</div>` : ""}
      <h3>${esc(i.weeksOverview)}</h3>
      <table class="report-table"><thead><tr><th>#</th><th>${esc(i.task)}</th><th>${esc(i.taskCheck)}</th>
        <th>${view.focus_criteria.map((c) => esc(criterionLabel(c, view.language))).join(" / ")}</th><th>${esc(i.average)}</th></tr></thead>
        <tbody>${weeks}</tbody></table>
    </article>`;
}

function renderProgram(view) {
  const i = pt();
  const plan = view.plan || {};
  const focusChips = view.focus_criteria.map((c, idx) => `
    <span class="chip" style="border-color:${FOCUS_COLORS[idx]}"><span class="dot" style="background:${FOCUS_COLORS[idx]}"></span>${esc(criterionLabel(c, view.language))}</span>`).join("");
  const timeline = view.timeline.map((w) => `
    <li class="tl-item ${w.status}">
      <a href="${w.submission ? `#week-${w.week}` : "#p-current"}" class="tl-link" data-week="${w.week}">
        <span class="week-dot ${w.status}">${w.status === "done" ? "✓" : w.week}</span>
        <span class="tl-text"><strong>${esc(i.weekN(w.week))}</strong><small>${esc((w.task && w.task.focus) || "")}</small></span>
        <span class="pill pill-${w.status}">${esc(i.st[w.status])}</span>
      </a>
    </li>`).join("");

  const cur = view.current_task;
  const currentHtml = cur ? `
    <article class="card current-task" id="p-current">
      <div class="current-head">
        <span class="eyebrow">${esc(i.weekOf(view.current_week, view.weeks))}</span>
        ${cur.adjusted ? `<span class="pill pill-adjusted"><i data-lucide="refresh-cw"></i> ${esc(i.adjustedNote)}</span>` : ""}
      </div>
      <h2 class="card-heading"><i data-lucide="target" class="icon-gold"></i> ${esc(i.currentTask)}</h2>
      <p class="current-focus">${esc(cur.focus || "")}</p>
      <p class="current-text">${esc(cur.task || "")}</p>
      <p class="current-evidence"><i data-lucide="paperclip"></i> <strong>${esc(i.evidenceToSubmit)}:</strong> ${esc(cur.evidence || "")}</p>
    </article>
    <form id="week-form" class="card form-card">
      <h2 class="card-heading"><i data-lucide="upload"></i> ${esc(i.submitTitle(view.current_week))}</h2>
      <label class="block"><span>${esc(i.weekMaterials)}</span>
        <textarea id="w-text" rows="8"></textarea></label>
      <label class="block file-label"><span>${esc(i.weekFiles)}</span>
        <input id="w-files" type="file" multiple accept=".txt,.md,.docx,.pdf,.pptx,text/plain" /></label>
      <label class="block"><span>${esc(i.reflectionLabel)}</span>
        <textarea id="w-reflection" rows="4" class="short"></textarea></label>
      <div class="form-actions">
        <button type="submit" class="btn primary" id="w-submit">${esc(i.submitWeek)}</button>
        <p id="week-error" class="error hidden"></p>
      </div>
    </form>
    <div id="week-status" class="status hidden"></div>` : "";

  const done = view.timeline.filter((w) => w.submission);
  const feedbackHtml = done.length ? `
    <h2 class="section-title"><i data-lucide="messages-square"></i> ${esc(i.weekFeedback)}</h2>
    ${[...done].reverse().map((w, idx) => renderWeekFeedback(w, i, idx === 0)).join("")}` : "";

  $("program-dashboard").innerHTML = `
    <button type="button" class="btn link no-print" id="p-back"><i data-lucide="arrow-left"></i> ${esc(i.back)}</button>
    <article class="card program-head">
      <div class="accent-bar"></div>
      <div class="program-title-row">
        <h2>${esc(plan.title || i.tabProgram)}</h2>
        <span class="pill ${view.status === "completed" ? "pill-done" : "pill-current"}">${esc(view.status === "completed" ? i.statusCompleted : i.statusActive)}</span>
      </div>
      <p class="meta">${esc(i.programMeta({ subject: view.subject, grade: view.grade, weeks: view.weeks, when: formatWhen(view.created_at) }))}</p>
      <div class="chips">${focusChips}${view.focus_source === "coach" ? `<span class="meta">(${esc(i.coachChose)})</span>` : ""}</div>
      <p>${esc(plan.overview || "")}</p>
      ${view.goal ? `<p class="goal"><strong>${esc(i.goal)}:</strong> ${esc(view.goal)}</p>` : ""}
      <div class="mini-progress big"><span style="width:${Math.round((100 * view.submitted) / view.weeks)}%"></span></div>
      <p class="meta">${esc(i.progressWeeks(view.submitted, view.weeks))}</p>
    </article>
    ${renderReport(view, i)}
    ${currentHtml}
    <div class="dash-grid">
      <article class="card">
        <h2 class="card-heading"><i data-lucide="milestone"></i> ${esc(i.timeline)}</h2>
        <ol class="timeline">${timeline}</ol>
      </article>
      <article class="card">
        <h2 class="card-heading"><i data-lucide="chart-line"></i> ${esc(i.focusChart)}</h2>
        ${view.chart.labels.length ? `<div class="chart-wrap"><canvas id="program-chart" height="230"></canvas></div>` : `<p class="muted">${esc(i.chartEmpty)}</p>`}
      </article>
    </div>
    ${feedbackHtml}
  `;
  $("p-back").addEventListener("click", () => {
    prog.view = null;
    localStorage.removeItem("coteach.programId");
    setProgramScreen("home");
    loadPrograms();
  });
  const form = $("week-form");
  if (form) form.addEventListener("submit", submitWeek);
  const printBtn = $("p-print-btn");
  if (printBtn) printBtn.addEventListener("click", printReport);
  const reportBtn = $("p-report-btn");
  if (reportBtn) reportBtn.addEventListener("click", regenerateReport);
  document.querySelectorAll(".tl-link").forEach((a) => a.addEventListener("click", (e) => {
    const target = document.querySelector(a.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    if (target.tagName === "DETAILS") target.open = true;
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }));
  renderProgramChart(view);
  refreshIcons();
}

function renderProgramChart(view) {
  if (prog.chart) {
    prog.chart.destroy();
    prog.chart = null;
  }
  const canvas = $("program-chart");
  if (!canvas || typeof Chart === "undefined") return;
  const i = pt();
  const labels = view.chart.labels.map((l) => (l === "baseline" ? i.baseline : i.weekN(Number(l.replace("week", "")))));
  const datasets = view.focus_criteria.map((cid, idx) => ({
    label: criterionLabel(cid, view.language),
    data: view.chart.series[cid] || [],
    borderColor: FOCUS_COLORS[idx],
    backgroundColor: FOCUS_COLORS[idx],
    tension: 0.25,
    pointRadius: 5,
    borderWidth: 3,
  }));
  datasets.push({
    label: i.average,
    data: view.chart.average,
    borderColor: "#1F2937",
    borderDash: [5, 4],
    backgroundColor: "transparent",
    tension: 0.25,
    pointRadius: 3,
    borderWidth: 1.5,
  });
  prog.chart = new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      animation: false,
      scales: { y: { min: 1, max: 4, ticks: { stepSize: 1 } } },
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12 } } },
    },
  });
}

async function submitWeek(event) {
  event.preventDefault();
  const i = pt();
  const view = prog.view;
  showError($("week-error"), "");
  const files = [...$("w-files").files];
  if (files.some((f) => f.size > 20 * 1024 * 1024)) {
    showError($("week-error"), t().fileTooLarge);
    return;
  }
  const form = new FormData();
  form.append("text", $("w-text").value);
  form.append("reflection", $("w-reflection").value);
  files.forEach((f) => form.append("files", f));
  $("w-submit").disabled = true;
  $("week-status").textContent = i.reviewing;
  $("week-status").classList.remove("hidden");
  try {
    const res = await fetch(`/api/programs/${view.id}/weeks`, { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(formatDetail(data.detail) || t().errorGeneric);
    prog.view = data;
    renderProgram(data);
    const target = data.report ? $("program-report") : $(`week-${data.submitted_week}`);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showError($("week-error"), err.message || t().errorGeneric);
    $("w-submit").disabled = false;
    $("week-status").classList.add("hidden");
  }
}

async function regenerateReport() {
  const btn = $("p-report-btn");
  btn.disabled = true;
  try {
    const res = await fetch(`/api/programs/${prog.view.id}/report`, { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(formatDetail(data.detail) || t().errorGeneric);
    prog.view = data;
    renderProgram(data);
  } catch (err) {
    btn.disabled = false;
    alert(err.message || t().errorGeneric);
  }
}

function printReport() {
  document.body.classList.add("print-report");
  window.print();
  setTimeout(() => document.body.classList.remove("print-report"), 500);
}

function initProgram() {
  const grade = $("p-grade");
  for (let n = 1; n <= 11; n += 1) {
    const opt = document.createElement("option");
    opt.value = String(n);
    opt.textContent = String(n);
    grade.appendChild(opt);
  }
  const weeks = $("p-weeks");
  for (let n = 2; n <= 8; n += 1) {
    const opt = document.createElement("option");
    opt.value = String(n);
    opt.textContent = String(n);
    if (n === 4) opt.selected = true;
    weeks.appendChild(opt);
  }
  $("p-name").value = localStorage.getItem("coteach.teacherName") || "";
  $("focus-auto").addEventListener("change", () => {
    if ($("focus-auto").checked) {
      document.querySelectorAll("#focus-options input").forEach((el) => { el.checked = false; });
      onFocusChange();
    }
  });
  $("program-load-btn").addEventListener("click", loadPrograms);
  $("program-form").addEventListener("submit", startProgram);
  window.addEventListener("afterprint", () => document.body.classList.remove("print-report"));
  loadRubric();
}

function enterProgramView() {
  if (prog.view) return;
  const saved = Number(localStorage.getItem("coteach.programId") || 0);
  if (saved) {
    openProgram(saved, true).then(() => {
      if (!prog.view) {
        localStorage.removeItem("coteach.programId");
        if (programName()) loadPrograms();
      }
    });
  } else if (programName()) {
    loadPrograms();
  }
}
