from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


MaterialType = Literal["lesson_plan", "presentation_text", "transcript", "student_work"]
LanguageCode = Literal["kk", "ru", "en"]
Priority = Literal["high", "medium", "low"]

RUBRIC_CRITERIA: list[dict[str, str]] = [
    {
        "id": "objectives",
        "en": "Clarity of learning objectives",
        "ru": "Ясность учебных целей",
        "kk": "Оқу мақсаттарының айқындығы",
    },
    {
        "id": "structure_pacing",
        "en": "Structure, pacing and attention management",
        "ru": "Структура, темп и управление вниманием",
        "kk": "Құрылым, қарқын және назарды басқару",
    },
    {
        "id": "explanation_practice",
        "en": "Balance of explanation vs student practice / active learning",
        "ru": "Баланс объяснения и самостоятельной практики / активного обучения",
        "kk": "Түсіндіру мен оқушы практикасы / белсенді оқыту теңгерімі",
    },
    {
        "id": "differentiation",
        "en": "Differentiation / support for different levels",
        "ru": "Дифференциация / поддержка разных уровней",
        "kk": "Деңгейлеп оқыту / әртүрлі деңгейдегі қолдау",
    },
    {
        "id": "engagement",
        "en": "Engagement techniques",
        "ru": "Приёмы вовлечения учащихся",
        "kk": "Тартқыштық тәсілдері",
    },
    {
        "id": "language_clarity",
        "en": "Language clarity (Kazakh and Russian support)",
        "ru": "Ясность языка (поддержка казахского и русского)",
        "kk": "Тілдің айқындығы (қазақ және орыс тілдерін қолдау)",
    },
]

CRITERION_IDS = [c["id"] for c in RUBRIC_CRITERIA]
CRITERION_LABELS = {c["id"]: c for c in RUBRIC_CRITERIA}


class RubricItem(BaseModel):
    id: str
    label: str = ""
    score: int = Field(ge=1, le=4)
    evidence: str

    @field_validator("id")
    @classmethod
    def known_id(cls, value: str) -> str:
        if value not in CRITERION_IDS:
            raise ValueError(f"Unknown rubric criterion: {value}")
        return value


class Strength(BaseModel):
    text: str
    evidence: str = ""


class Improvement(BaseModel):
    text: str
    priority: Priority
    evidence: str = ""


class WeekPlan(BaseModel):
    focus: str
    actions: list[str] = Field(min_length=1)


class DevelopmentPlan(BaseModel):
    week1: WeekPlan
    week2: WeekPlan


class Feedback(BaseModel):
    summary: str
    rubric: list[RubricItem] = Field(min_length=6, max_length=6)
    strengths: list[Strength] = Field(min_length=1)
    improvements: list[Improvement] = Field(min_length=1)
    micro_actions: list[str] = Field(min_length=1, max_length=2)
    development_plan: DevelopmentPlan
    progress_note: str

    @model_validator(mode="after")
    def all_criteria_present(self) -> "Feedback":
        got = [item.id for item in self.rubric]
        missing = [cid for cid in CRITERION_IDS if cid not in got]
        extra = [cid for cid in got if cid not in CRITERION_IDS]
        if missing or extra or len(set(got)) != 6:
            raise ValueError(
                f"Rubric must contain each criterion once. missing={missing} extra={extra}"
            )
        by_id = {item.id: item for item in self.rubric}
        ordered: list[RubricItem] = []
        for cid in CRITERION_IDS:
            item = by_id[cid]
            if not item.label.strip():
                item.label = CRITERION_LABELS[cid]["en"]
            ordered.append(item)
        self.rubric = ordered
        return self

    def scores_dict(self) -> dict[str, int]:
        return {item.id: item.score for item in self.rubric}

    def average_score(self) -> float:
        scores = list(self.scores_dict().values())
        return round(sum(scores) / len(scores), 2)


class AnalyzeRequest(BaseModel):
    teacher_name: str = Field(min_length=1, max_length=200)
    language: LanguageCode
    subject: str = Field(min_length=1, max_length=200)
    grade: str = Field(min_length=1, max_length=40)
    material_type: MaterialType
    text: str = ""
