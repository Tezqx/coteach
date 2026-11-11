"""Growth Program coaching: multi-week plan, weekly reviews, and final report.

Reuses the rubric, LLM client, JSON repair loop, and mock-mode switch from
coach.py so program output stays consistent with single-lesson analyses.
"""

from __future__ import annotations

import json
from typing import Any

from . import coach
from .schemas import (
    CRITERION_IDS,
    CRITERION_LABELS,
    RUBRIC_CRITERIA,
    FinalReport,
    FocusComparison,
    ProgramPlan,
    WeekFeedback,
    clean_criteria,
)

MAX_WEEK_MATERIAL_CHARS = 20000

SYSTEM_BASE = (
    "You are CoTeach, an experienced, supportive instructional coach running a "
    "multi-week professional growth program for a school teacher in Kazakhstan. "
    "You align loosely with the updated curriculum content (жаңартылған білім мазмұны) "
    "and criteria-based assessment (критериалды бағалау / критериальное оценивание). "
    "Be specific, kind, practical, and realistic for a busy teacher: one focused task per week. "
    "Do not invent evidence; quote or closely paraphrase what the teacher submitted. "
)


def _lang(language: str) -> str:
    return language if language in {"kk", "ru", "en"} else "en"


def _label(cid: str, language: str) -> str:
    return CRITERION_LABELS[cid][_lang(language)]


def _rubric_lines() -> str:
    return "\n".join(f"- {c['id']}: {c['en']} / {c['ru']} / {c['kk']}" for c in RUBRIC_CRITERIA)


def _system(language: str) -> str:
    lang_name = coach.LANGUAGE_NAMES.get(language, "English")
    return (
        SYSTEM_BASE
        + f"Write EVERY human-readable text field in {lang_name} ({language}) only. "
        "In prose, refer to rubric criteria by their names in that language, never by their ids "
        "(ids such as explanation_practice belong only in id/focus_criteria/next_focus fields). "
        "Return ONLY a single JSON object. No markdown fences, no preamble."
    )


def suggest_focus(latest_scores: dict[str, int] | None, exclude: list[str] | None = None) -> list[str]:
    """Pick the two lowest-scoring criteria (stable order), optionally skipping some."""
    if not latest_scores:
        return []
    pool = [cid for cid in CRITERION_IDS if cid not in (exclude or [])] or list(CRITERION_IDS)
    ranked = sorted(pool, key=lambda cid: (latest_scores.get(cid, 4), CRITERION_IDS.index(cid)))
    return ranked[:2]


# ---------------------------------------------------------------------------
# 1. Program plan
# ---------------------------------------------------------------------------


def generate_plan(
    *,
    teacher_name: str,
    language: str,
    subject: str,
    grade: str,
    weeks: int,
    focus_criteria: list[str],
    goal: str,
    latest_analysis: dict[str, Any] | None,
) -> ProgramPlan:
    if coach.is_demo_mode():
        focus = focus_criteria or suggest_focus((latest_analysis or {}).get("scores")) or [
            "differentiation",
            "engagement",
        ]
        return _mock_plan(language, subject, grade, weeks, focus, goal)

    focus_instruction = (
        f"The teacher chose these focus criteria: {', '.join(focus_criteria)}. "
        "Return exactly these ids in focus_criteria."
        if focus_criteria
        else (
            "The teacher asked YOU to choose 1-2 focus criteria. Base the choice on the "
            "latest analysis below (lowest scores and highest-priority improvements) and "
            "on the personal goal; explain the choice briefly in overview."
        )
    )
    latest = "No previous single-lesson analysis is available."
    if latest_analysis:
        fb = latest_analysis.get("feedback") or {}
        latest = (
            f"Latest analysis ({latest_analysis.get('created_at')}, {latest_analysis.get('subject')}, "
            f"grade {latest_analysis.get('grade')}): scores {json.dumps(latest_analysis.get('scores'))}; "
            f"summary: {str(fb.get('summary', ''))[:600]}; improvements: "
            + "; ".join(str(i.get("text", "")) for i in (fb.get("improvements") or [])[:3])
        )
    schema = (
        "{\n"
        '  "title": "short motivating program title",\n'
        '  "overview": "3-5 sentences: why these focus areas, what the teacher will practice, how success will look",\n'
        '  "focus_criteria": ["1-2 rubric ids"],\n'
        '  "weeks": [\n'
        '    {"week": 1, "focus": "short weekly focus", "task": "one concrete, observable classroom practice task for this week (2-4 sentences)", '
        '"evidence": "exactly what to submit at the end of the week (e.g. lesson plan + 3 exit tickets + reflection)"}\n'
        f"    ... exactly {weeks} items, week 1..{weeks}\n"
        "  ]\n"
        "}"
    )
    user = (
        f"Teacher: {teacher_name}\nSubject: {subject}\nGrade: {grade}\n"
        f"Program length: {weeks} weeks\n"
        f"Personal goal (may be empty): {goal or '-'}\n\n"
        f"Rubric criteria ids:\n{_rubric_lines()}\n\n"
        f"{focus_instruction}\n\n{latest}\n\n"
        "Design a progressive plan: week 1 builds a baseline and a first small habit, the "
        "middle weeks deepen and vary the technique, the last week consolidates both focus "
        "areas in one complete lesson. Tasks must fit this subject and grade.\n\n"
        f"Required JSON schema:\n{schema}"
    )
    messages = [{"role": "system", "content": _system(language)}, {"role": "user", "content": user}]

    def parse(raw: str) -> ProgramPlan:
        data = json.loads(coach.extract_json_object(raw))
        plan = ProgramPlan.model_validate(data)
        if len(plan.weeks) < weeks:
            raise ValueError(f"weeks must contain exactly {weeks} items, got {len(plan.weeks)}")
        plan.weeks = plan.weeks[:weeks]
        if focus_criteria:
            plan.focus_criteria = list(focus_criteria)
        return plan

    return coach.complete_validated(messages, parse)


# ---------------------------------------------------------------------------
# 2. Weekly review
# ---------------------------------------------------------------------------


def current_task(program: dict[str, Any], week_number: int) -> dict[str, Any]:
    """The task for a week: the coach's adjusted task from last week, else the plan."""
    plan_weeks = program["plan"].get("weeks") or []
    base = plan_weeks[week_number - 1] if 0 < week_number <= len(plan_weeks) else {}
    task = {
        "focus": base.get("focus", ""),
        "task": base.get("task", ""),
        "evidence": base.get("evidence", ""),
        "adjusted": False,
    }
    for sub in program.get("submissions") or []:
        if sub["week_number"] == week_number - 1:
            nxt = (sub.get("feedback") or {}).get("next_task")
            if nxt and nxt.get("task"):
                task = {
                    "focus": nxt.get("focus") or task["focus"],
                    "task": nxt["task"],
                    "evidence": nxt.get("evidence") or task["evidence"],
                    "adjusted": True,
                }
    return task


def _format_previous_weeks(program: dict[str, Any]) -> str:
    subs = program.get("submissions") or []
    if not subs:
        return "No previous weeks yet: this is the first weekly submission."
    focus = program["focus_criteria"]
    blocks = []
    for sub in subs:
        fb = sub.get("feedback") or {}
        check = fb.get("task_check") or {}
        focus_scores = ", ".join(f"{cid} {sub['scores'].get(cid, '?')}/4" for cid in focus)
        nxt = fb.get("next_task") or {}
        blocks.append(
            f"Week {sub['week_number']}: task was \"{sub['task'].get('task', '')}\". "
            f"Task check: {check.get('status', '?')} ({str(check.get('comment', ''))[:200]}). "
            f"Focus scores: {focus_scores}. Average {sub['average_score']}/4. "
            f"Teacher reflection: \"{sub.get('reflection', '')[:400]}\". "
            f"Coach summary: {str(fb.get('summary', ''))[:400]} "
            f"Micro-actions given: {'; '.join(fb.get('micro_actions') or [])}. "
            f"Next task assigned: \"{nxt.get('task', '')}\""
        )
    return "\n".join(blocks)


def review_week(
    *,
    program: dict[str, Any],
    week_number: int,
    task: dict[str, Any],
    material: str,
    reflection: str,
) -> WeekFeedback:
    language = program["language"]
    is_last = week_number >= program["weeks"]
    if coach.is_demo_mode():
        fb = _mock_week(program, week_number, task, material, reflection)
        return coach.localize_labels(fb, language)

    text = material.strip()
    if len(text) > MAX_WEEK_MATERIAL_CHARS:
        text = text[:MAX_WEEK_MATERIAL_CHARS] + "\n[...truncated...]"
    plan_weeks = program["plan"].get("weeks") or []
    upcoming = plan_weeks[week_number] if week_number < len(plan_weeks) else None
    baseline = program.get("baseline") or {}
    schema = (
        "{\n"
        '  "summary": "3-5 sentences about this week\'s evidence, centred on the focus criteria",\n'
        '  "task_check": {"status": "done|partial|not_done", "comment": "was THIS week\'s assigned task carried out and how well, with evidence"},\n'
        '  "rubric": [6 items, one per id: {"id": "objectives", "label": "string", "score": 1-4, "evidence": "short quote or observation"}],\n'
        '  "strengths": [{"text": "string", "evidence": "optional quote"}]  (1-3 items),\n'
        '  "improvements": [{"text": "string", "priority": "high|medium|low", "evidence": "optional quote"}]  (1-2 items),\n'
        '  "micro_actions": ["1-2 small observable actions for next week\'s lessons"],\n'
        + (
            '  "next_task": null  (this is the final week),\n'
            if is_last
            else '  "next_task": {"focus": "string", "task": "next week\'s task, ADJUSTED to this week\'s result (easier if not done, harder if done well)", "evidence": "what to submit next week"},\n'
        )
        + '  "progress_note": "2-4 sentences comparing with previous weeks and the baseline; name concrete changes"\n'
        "}"
    )
    user = (
        f"Program: \"{program['plan'].get('title', '')}\" - week {week_number} of {program['weeks']}.\n"
        f"Teacher: {program.get('teacher_name')}; subject {program['subject']}; grade {program['grade']}.\n"
        f"Focus criteria: {', '.join(program['focus_criteria'])}.\n"
        f"Personal goal: {program.get('goal') or '-'}\n"
        f"Program overview: {program['plan'].get('overview', '')}\n"
        f"Baseline scores before the program: {json.dumps(baseline.get('scores')) if baseline else 'none (week 1 is the baseline)'}\n\n"
        f"THIS WEEK'S ASSIGNED TASK (week {week_number}): focus \"{task.get('focus')}\"; task \"{task.get('task')}\"; "
        f"evidence requested: \"{task.get('evidence')}\"\n"
        + (
            f"Originally planned task for next week (week {week_number + 1}): \"{upcoming.get('task')}\" - adjust it as needed.\n"
            if upcoming
            else ""
        )
        + f"\nPrevious weeks (chronological):\n{_format_previous_weeks(program)}\n\n"
        f"Rubric criteria (score each 1-4: 1 not visible, 2 emerging, 3 solid, 4 strong exemplar):\n{_rubric_lines()}\n\n"
        f"Teacher's reflection for this week:\n---\n{reflection.strip() or '(no reflection provided)'}\n---\n\n"
        f"Submitted materials for this week:\n---\n{text}\n---\n\n"
        "Follow up explicitly on last week's micro-actions in progress_note when there are previous weeks.\n\n"
        f"Required JSON schema:\n{schema}"
    )
    messages = [{"role": "system", "content": _system(language)}, {"role": "user", "content": user}]

    def parse(raw: str) -> WeekFeedback:
        data = json.loads(coach.extract_json_object(raw))
        if isinstance(data, dict) and "feedback" in data and isinstance(data["feedback"], dict):
            data = data["feedback"]
        fb = WeekFeedback.model_validate(data)
        if is_last:
            fb.next_task = None
        return fb

    fb = coach.complete_validated(messages, parse)
    return coach.localize_labels(fb, language)


# ---------------------------------------------------------------------------
# 3. Final report
# ---------------------------------------------------------------------------


def before_after(program: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    """Deterministic before/after per focus criterion (baseline or week 1 -> last week)."""
    subs = program.get("submissions") or []
    baseline = (program.get("baseline") or {}).get("scores") or (subs[0]["scores"] if subs else {})
    last = subs[-1]["scores"] if subs else {}
    out = {}
    for cid in program["focus_criteria"]:
        before = baseline.get(cid)
        after = last.get(cid)
        out[cid] = {
            "before": float(before) if before is not None else None,
            "after": float(after) if after is not None else None,
        }
    return out


def final_report(program: dict[str, Any]) -> FinalReport:
    language = program["language"]
    numbers = before_after(program)
    if coach.is_demo_mode():
        report = _mock_report(program, numbers)
    else:
        schema = (
            "{\n"
            '  "growth_summary": "4-6 sentences: the teacher\'s growth story across the program, with evidence",\n'
            '  "focus_comparison": [{"id": "focus criterion id", "comment": "what changed from before to after, concretely"}],\n'
            '  "achievements": ["3-5 concrete achievements, each tied to a week"],\n'
            '  "recommendations": ["3-4 recommendations for the next program"],\n'
            '  "next_focus": ["1-2 rubric ids recommended for the next program"]\n'
            "}"
        )
        user = (
            f"Program \"{program['plan'].get('title', '')}\" has been completed ({program['weeks']} weeks).\n"
            f"Teacher: {program.get('teacher_name')}; subject {program['subject']}; grade {program['grade']}.\n"
            f"Focus criteria: {', '.join(program['focus_criteria'])}. Personal goal: {program.get('goal') or '-'}\n"
            f"Before/after scores on focus criteria (computed): {json.dumps(numbers)}\n\n"
            f"Week-by-week record:\n{_format_previous_weeks(program)}\n\n"
            f"Rubric criteria ids:\n{_rubric_lines()}\n\n"
            "Write an encouraging but honest final growth report.\n\n"
            f"Required JSON schema:\n{schema}"
        )
        messages = [{"role": "system", "content": _system(language)}, {"role": "user", "content": user}]

        def parse(raw: str) -> FinalReport:
            data = json.loads(coach.extract_json_object(raw))
            return FinalReport.model_validate(data)

        report = coach.complete_validated(messages, parse)

    # Numbers always come from stored scores, never from the model.
    comments = {item.id: item.comment for item in report.focus_comparison}
    report.focus_comparison = [
        FocusComparison(
            id=cid,
            label=_label(cid, language),
            before=numbers[cid]["before"],
            after=numbers[cid]["after"],
            comment=comments.get(cid, ""),
        )
        for cid in program["focus_criteria"]
    ]
    if not report.next_focus:
        last = (program.get("submissions") or [{}])[-1].get("scores") or {}
        report.next_focus = suggest_focus(last, exclude=program["focus_criteria"])
    return report


# ---------------------------------------------------------------------------
# Mock mode (no API key): plausible, language-aware, deterministic output
# ---------------------------------------------------------------------------

TECHNIQUES = {
    "objectives": {
        "en": "write the objective and two success criteria in student-friendly words, and revisit them in the last 5 minutes",
        "ru": "запишите цель и два критерия успеха понятным ученикам языком и вернитесь к ним в последние 5 минут",
        "kk": "мақсат пен екі табыс критерийін оқушыға түсінікті тілмен жазып, соңғы 5 минутта оларға қайта оралыңыз",
    },
    "structure_pacing": {
        "en": "plan timed lesson stages with a visible timer and one attention reset every 10-12 minutes",
        "ru": "распланируйте этапы урока по минутам с видимым таймером и делайте «перезагрузку внимания» каждые 10–12 минут",
        "kk": "сабақ кезеңдерін көрінетін таймермен минутқа дейін жоспарлап, әр 10–12 минут сайын назарды қайта жинаңыз",
    },
    "explanation_practice": {
        "en": "keep teacher explanation under 10 minutes and give at least 15 minutes of pair or individual practice",
        "ru": "ограничьте объяснение 10 минутами и дайте не менее 15 минут парной или самостоятельной практики",
        "kk": "түсіндіруді 10 минутпен шектеп, кемінде 15 минут жұптық не өздік практика беріңіз",
    },
    "differentiation": {
        "en": "prepare three levels of the main task (support, core, stretch) and let students choose their entry point",
        "ru": "подготовьте основное задание в трёх уровнях (поддержка, базовый, вызов) и дайте ученикам выбрать уровень",
        "kk": "негізгі тапсырманы үш деңгейде (қолдау, базалық, күрделі) дайындап, оқушыларға деңгейді таңдатыңыз",
    },
    "engagement": {
        "en": "use think-pair-share and no-hands-up questioning with name sticks at least twice per lesson",
        "ru": "используйте «подумай — обсуди в паре — поделись» и опрос без поднятых рук (палочки с именами) минимум дважды за урок",
        "kk": "«ойлан — жұпта талқыла — бөліс» әдісін және қол көтерусіз сұрауды (есімі жазылған таяқшалар) сабақта кемінде екі рет қолданыңыз",
    },
    "language_clarity": {
        "en": "prepare a bilingual (Kazakh/Russian) glossary of 6-8 key terms and model sentence frames for answers",
        "ru": "подготовьте двуязычный (казахский/русский) словарик из 6–8 ключевых терминов и речевые образцы для ответов",
        "kk": "6–8 негізгі терминнен тұратын қазақша/орысша сөздік пен жауапқа арналған сөйлем үлгілерін дайындаңыз",
    },
}

MOCK = {
    "en": {
        "ev_other": "Consistent with previous weeks; not a focus area this week.",
        "title": "{weeks}-week growth program",
        "overview": (
            "Over {weeks} weeks we will work on {focus} in your {subject} lessons for grade {grade}. "
            "Each week you try one concrete technique, submit short evidence, and get adjusted feedback. "
            "{goal_line}This plan was generated in demo mode to show how CoTeach programs work."
        ),
        "goal_line": "Your personal goal: \u201c{goal}\u201d. ",
        "w_first_focus": "Baseline and first habit: {crit}",
        "w_first_task": "Teach a normal lesson and {tech}. Note what students did differently.",
        "w_first_ev": "Lesson plan or slides + 3-5 sentences of reflection",
        "w_mid_focus": "Deepen: {crit}",
        "w_mid_task": "Repeat and vary the technique: {tech}. Collect quick student feedback with a 2-question exit ticket.",
        "w_mid_ev": "Lesson materials, 3 sample exit tickets, and your reflection",
        "w_last_focus": "Consolidate: {crits}",
        "w_last_task": "Teach one complete lesson that combines the techniques for all focus areas, ideally observed by a colleague.",
        "w_last_ev": "Full lesson plan or a transcript of a 10-minute fragment + reflection",
        "summary": "Week {n} materials show the focus technique in use: \u201c{quote}\u201d. {focus} is becoming more visible, though it is not yet consistent across all stages of the lesson. (Demo mode feedback.)",
        "check_done": "Yes, the task was carried out: the materials and your reflection describe it clearly.",
        "check_partial": "Partly done: the plan mentions the technique, but there is little evidence of how students responded. Add a reflection next time.",
        "strength1": "You tried this week's technique in a real lesson.",
        "strength2": "The lesson keeps a clear structure that students can follow.",
        "impr1": "Make {crit} visible in more than one stage of the lesson, not only at the start.",
        "impr2": "Collect one piece of student evidence (exit ticket, short answer) to check the effect.",
        "act1": "In the first 5 minutes, say out loud what students will be able to do by the end.",
        "act2": "Keep two student answers from this week to compare next week.",
        "adjusted": "Adjusted after week {n}: ",
        "progress_first": "This is the first week, so these scores are your program baseline. Next week we will compare against them.",
        "progress_next": "Last week you planned: \u201c{prev}\u201d. Your focus score for {crit} moved from {before} to {after}. Keep building on that.",
        "report_summary": "Across {weeks} weeks you practiced {focus} in real {subject} lessons. Your focus scores moved from {before} to {after} on average, and your reflections show growing confidence in planning for different students. (Demo mode report.)",
        "report_comment": "From {before} to {after}: the technique is now planned deliberately rather than occasionally.",
        "ach": [
            "Completed all weekly tasks ({weeks} of {weeks}) and submitted evidence every week.",
            "Week 1: established a clear baseline and a first small habit.",
            "Final week: combined the focus techniques in one complete lesson.",
        ],
        "rec": [
            "Keep one technique from this program as a weekly routine.",
            "Ask a colleague to observe one lesson per month with the same rubric.",
            "Start the next program with the criteria recommended below.",
        ],
    },
    "ru": {
        "ev_other": "На уровне прошлых недель; не в фокусе этой недели.",
        "title": "Программа роста · {weeks} нед.",
        "overview": (
            "За {weeks} нед. мы будем работать над направлениями «{focus}» на ваших уроках по предмету «{subject}» в {grade} классе. "
            "Каждую неделю вы пробуете один конкретный приём, присылаете короткие материалы и получаете скорректированную обратную связь. "
            "{goal_line}План сформирован в демо-режиме, чтобы показать работу программы."
        ),
        "goal_line": "Ваша личная цель: «{goal}». ",
        "w_first_focus": "Старт и первая привычка: {crit}",
        "w_first_task": "Проведите обычный урок и {tech}. Отметьте, что ученики делали по-другому.",
        "w_first_ev": "План урока или слайды + 3–5 предложений рефлексии",
        "w_mid_focus": "Углубление: {crit}",
        "w_mid_task": "Повторите и разнообразьте приём: {tech}. Соберите обратную связь учеников через мини-билет из 2 вопросов.",
        "w_mid_ev": "Материалы урока, 3 примера мини-билетов и ваша рефлексия",
        "w_last_focus": "Закрепление: {crits}",
        "w_last_task": "Проведите один целостный урок, объединив приёмы по всем направлениям; по возможности пригласите коллегу.",
        "w_last_ev": "Полный план урока или расшифровка 10-минутного фрагмента + рефлексия",
        "summary": "Материалы {n}-й недели показывают, что приём применяется: «{quote}». Направление «{focus}» становится заметнее, но пока не на всех этапах урока. (Демо-режим.)",
        "check_done": "Да, задание выполнено: материалы и рефлексия хорошо его описывают.",
        "check_partial": "Выполнено частично: приём упомянут в плане, но мало данных о том, как отреагировали ученики. В следующий раз добавьте рефлексию.",
        "strength1": "Вы применили приём недели на реальном уроке.",
        "strength2": "У урока понятная структура, по которой легко двигаться классу.",
        "impr1": "Сделайте направление «{crit}» видимым не только в начале, но и на других этапах урока.",
        "impr2": "Соберите хотя бы одно свидетельство от учеников (мини-билет, короткий ответ), чтобы проверить эффект.",
        "act1": "В первые 5 минут проговорите вслух, что ученики смогут сделать к концу урока.",
        "act2": "Сохраните два ответа учеников этой недели, чтобы сравнить их на следующей.",
        "adjusted": "Скорректировано после {n}-й недели: ",
        "progress_first": "Это первая неделя, поэтому эти баллы — отправная точка программы. На следующей неделе сравним результат с ними.",
        "progress_next": "На прошлой неделе вы планировали: «{prev}». Балл по направлению «{crit}» изменился с {before} до {after}. Продолжайте в том же духе.",
        "report_summary": "За {weeks} нед. вы отработали направления «{focus}» на реальных уроках по предмету «{subject}». Баллы по фокусным критериям выросли в среднем с {before} до {after}, а рефлексии показывают растущую уверенность. (Демо-режим.)",
        "report_comment": "С {before} до {after}: приём теперь планируется осознанно, а не от случая к случаю.",
        "ach": [
            "Выполнены все еженедельные задания ({weeks} из {weeks}), материалы сданы каждую неделю.",
            "Неделя 1: зафиксирована отправная точка и первая привычка.",
            "Финальная неделя: приёмы по всем направлениям объединены в одном уроке.",
        ],
        "rec": [
            "Оставьте один приём из программы как еженедельную привычку.",
            "Раз в месяц приглашайте коллегу на урок с той же рубрикой.",
            "Начните следующую программу с рекомендованных ниже критериев.",
        ],
    },
    "kk": {
        "ev_other": "Өткен апталар деңгейінде; бұл аптаның фокусы емес.",
        "title": "Даму бағдарламасы · {weeks} апта",
        "overview": (
            "{weeks} апта бойы «{subject}» пәні бойынша {grade}-сыныптағы сабақтарыңызда «{focus}» бағыттары бойынша жұмыс істейміз. "
            "Әр апта бір нақты тәсілді сынап, қысқа материал жібересіз және түзетілген кері байланыс аласыз. "
            "{goal_line}Бұл жоспар бағдарламаның жұмысын көрсету үшін демо-режимде жасалды."
        ),
        "goal_line": "Жеке мақсатыңыз: «{goal}». ",
        "w_first_focus": "Бастау және алғашқы әдет: {crit}",
        "w_first_task": "Әдеттегі сабақ өткізіп, {tech}. Оқушылар нені басқаша істегенін белгілеңіз.",
        "w_first_ev": "Сабақ жоспары немесе слайдтар + 3–5 сөйлем рефлексия",
        "w_mid_focus": "Тереңдету: {crit}",
        "w_mid_task": "Тәсілді қайталап, түрлендіріңіз: {tech}. 2 сұрақтық шығу билетімен оқушылардан кері байланыс жинаңыз.",
        "w_mid_ev": "Сабақ материалдары, 3 шығу билетінің үлгісі және рефлексияңыз",
        "w_last_focus": "Бекіту: {crits}",
        "w_last_task": "Барлық бағыттағы тәсілдерді біріктіріп, бір толық сабақ өткізіңіз; мүмкін болса, әріптесіңізді шақырыңыз.",
        "w_last_ev": "Толық сабақ жоспары немесе 10 минуттық үзіндінің транскрипті + рефлексия",
        "summary": "{n}-апта материалдары тәсілдің қолданылғанын көрсетеді: «{quote}». «{focus}» бағыты айқындала түсуде, бірақ сабақтың барлық кезеңінде емес. (Демо-режим.)",
        "check_done": "Иә, тапсырма орындалды: материалдар мен рефлексия оны анық сипаттайды.",
        "check_partial": "Ішінара орындалды: тәсіл жоспарда аталған, бірақ оқушылардың қалай қабылдағаны туралы дерек аз. Келесі жолы рефлексия қосыңыз.",
        "strength1": "Аптаның тәсілін нақты сабақта қолдандыңыз.",
        "strength2": "Сабақтың сыныпқа түсінікті құрылымы бар.",
        "impr1": "«{crit}» бағытын сабақтың басында ғана емес, басқа кезеңдерінде де көрінетін етіңіз.",
        "impr2": "Әсерін тексеру үшін оқушылардан кемінде бір дәлел жинаңыз (шығу билеті, қысқа жауап).",
        "act1": "Алғашқы 5 минутта оқушылар сабақ соңында не істей алатынын дауыстап айтыңыз.",
        "act2": "Келесі аптада салыстыру үшін осы аптадағы екі оқушы жауабын сақтаңыз.",
        "adjusted": "{n}-аптадан кейін түзетілді: ",
        "progress_first": "Бұл бірінші апта, сондықтан бұл ұпайлар — бағдарламаның бастапқы нүктесі. Келесі аптада солармен салыстырамыз.",
        "progress_next": "Өткен аптада сіз жоспарладыңыз: «{prev}». «{crit}» бағыты бойынша ұпай {before}-ден {after}-ге өзгерді. Осылай жалғастырыңыз.",
        "report_summary": "{weeks} апта бойы «{subject}» сабақтарында «{focus}» бағыттарын жаттықтырдыңыз. Фокус критерийлері бойынша ұпайлар орта есеппен {before}-ден {after}-ге өсті, рефлексиялар сенімділіктің артқанын көрсетеді. (Демо-режим.)",
        "report_comment": "{before}-ден {after}-ге: тәсіл енді кездейсоқ емес, саналы түрде жоспарланады.",
        "ach": [
            "Барлық {weeks} апталық тапсырма орындалып, материалдар әр апта жіберілді.",
            "1-апта: бастапқы нүкте мен алғашқы әдет қалыптасты.",
            "Соңғы апта: барлық бағыттағы тәсілдер бір сабақта біріктірілді.",
        ],
        "rec": [
            "Бағдарламадағы бір тәсілді апталық әдетке айналдырыңыз.",
            "Айына бір рет әріптесіңізді сол рубрикамен сабаққа шақырыңыз.",
            "Келесі бағдарламаны төменде ұсынылған критерийлерден бастаңыз.",
        ],
    },
}


def _focus_names(focus: list[str], language: str) -> str:
    return ", ".join(_label(cid, language).lower() if language != "en" else _label(cid, language) for cid in focus)


def _mock_plan(language, subject, grade, weeks, focus, goal) -> ProgramPlan:
    lang = _lang(language)
    pack = MOCK[lang]
    names = _focus_names(focus, lang)
    items = []
    for n in range(1, weeks + 1):
        cid = focus[(n - 1) % len(focus)]
        crit = _label(cid, lang)
        tech = TECHNIQUES[cid][lang]
        if n == 1:
            items.append({"week": n, "focus": pack["w_first_focus"].format(crit=crit), "task": pack["w_first_task"].format(tech=tech), "evidence": pack["w_first_ev"]})
        elif n == weeks:
            items.append({"week": n, "focus": pack["w_last_focus"].format(crits=names), "task": pack["w_last_task"], "evidence": pack["w_last_ev"]})
        else:
            items.append({"week": n, "focus": pack["w_mid_focus"].format(crit=crit), "task": pack["w_mid_task"].format(tech=tech), "evidence": pack["w_mid_ev"]})
    goal_line = pack["goal_line"].format(goal=goal.strip()[:200]) if goal.strip() else ""
    return ProgramPlan.model_validate(
        {
            "title": pack["title"].format(weeks=weeks),
            "overview": pack["overview"].format(weeks=weeks, focus=names, subject=subject, grade=grade, goal_line=goal_line),
            "focus_criteria": focus,
            "weeks": items,
        }
    )


def _mock_scores(program: dict[str, Any], week_number: int) -> dict[str, int]:
    weeks = max(2, program["weeks"])
    focus = program["focus_criteria"]
    base = (program.get("baseline") or {}).get("scores") or {}
    scores = {}
    for cid in CRITERION_IDS:
        start = int(base.get(cid, 2 if cid in focus or cid == "differentiation" else 3))
        if cid in focus:
            start = min(start, 2)
            gain = round((4 - start) * (week_number - 1) / (weeks - 1))
            scores[cid] = max(1, min(4, start + gain))
        else:
            scores[cid] = max(1, min(4, start))
    return scores


def _mock_week(program, week_number, task, material, reflection) -> WeekFeedback:
    lang = _lang(program["language"])
    pack = MOCK[lang]
    focus = program["focus_criteria"]
    cid = focus[(week_number - 1) % len(focus)]
    crit = _label(cid, lang)
    scores = _mock_scores(program, week_number)
    quote = coach._snippet(material, "—")
    rubric = [
        {"id": c, "label": _label(c, lang), "score": scores[c], "evidence": f"\u201c{quote[:140]}\u201d" if c in focus else pack["ev_other"]}
        for c in CRITERION_IDS
    ]
    subs = program.get("submissions") or []
    if subs:
        prev = subs[-1]
        prev_action = (prev.get("feedback") or {}).get("micro_actions") or ["—"]
        progress = pack["progress_next"].format(
            prev=prev_action[0].rstrip(". "), crit=crit, before=prev["scores"].get(cid, "?"), after=scores[cid]
        )
    else:
        progress = pack["progress_first"]
    next_task = None
    if week_number < program["weeks"]:
        planned = (program["plan"].get("weeks") or [])[week_number]
        next_task = {
            "focus": planned["focus"],
            "task": pack["adjusted"].format(n=week_number) + planned["task"],
            "evidence": planned["evidence"],
        }
    status = "done" if len(reflection.strip()) >= 20 else "partial"
    return WeekFeedback.model_validate(
        {
            "summary": pack["summary"].format(n=week_number, quote=quote, focus=crit),
            "task_check": {"status": status, "comment": pack["check_done" if status == "done" else "check_partial"]},
            "rubric": rubric,
            "strengths": [{"text": pack["strength1"], "evidence": quote}, {"text": pack["strength2"]}],
            "improvements": [
                {"text": pack["impr1"].format(crit=crit), "priority": "high"},
                {"text": pack["impr2"], "priority": "medium"},
            ],
            "micro_actions": [pack["act1"], pack["act2"]],
            "next_task": next_task,
            "progress_note": progress,
        }
    )


def _mock_report(program, numbers) -> FinalReport:
    lang = _lang(program["language"])
    pack = MOCK[lang]
    befores = [v["before"] for v in numbers.values() if v["before"] is not None]
    afters = [v["after"] for v in numbers.values() if v["after"] is not None]
    avg = lambda xs: f"{sum(xs) / len(xs):.1f}" if xs else "—"  # noqa: E731
    return FinalReport.model_validate(
        {
            "growth_summary": pack["report_summary"].format(
                weeks=program["weeks"], focus=_focus_names(program["focus_criteria"], lang),
                subject=program["subject"], before=avg(befores), after=avg(afters),
            ),
            "focus_comparison": [
                {"id": cid, "comment": pack["report_comment"].format(before=v["before"], after=v["after"])}
                for cid, v in numbers.items()
            ],
            "achievements": [a.format(weeks=program["weeks"]) for a in pack["ach"]],
            "recommendations": pack["rec"],
            "next_focus": [],
        }
    )
