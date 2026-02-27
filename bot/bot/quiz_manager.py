from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import random
from typing import Dict, List


@dataclass
class Question:
    question: str
    choices: List[str]
    answer: int

    @property
    def correct_choice(self) -> str:
        return self.choices[self.answer]


@dataclass
class PlayerSession:
    score: int = 0
    asked_indexes: set[int] = field(default_factory=set)


class QuizManager:
    def __init__(self, questions_file: str) -> None:
        self._questions_path = Path(questions_file)
        self._questions: List[Question] = self._load_questions()
        self._sessions: Dict[int, PlayerSession] = {}

    def _load_questions(self) -> List[Question]:
        if not self._questions_path.exists():
            raise FileNotFoundError(f"Soru dosyası bulunamadı: {self._questions_path}")

        raw = json.loads(self._questions_path.read_text(encoding="utf-8"))
        questions: List[Question] = []

        for idx, item in enumerate(raw):
            choices = item.get("choices", [])
            answer = item.get("answer")
            if len(choices) < 2:
                raise ValueError(f"{idx}. soru için en az 2 seçenek olmalı.")
            if answer is None or not isinstance(answer, int) or answer >= len(choices) or answer < 0:
                raise ValueError(f"{idx}. sorunun doğru cevabı geçersiz.")

            questions.append(
                Question(
                    question=item["question"],
                    choices=choices,
                    answer=answer,
                )
            )
        if not questions:
            raise ValueError("Soru listesi boş olamaz.")
        return questions

    def start_session(self, user_id: int) -> None:
        self._sessions[user_id] = PlayerSession()

    def has_session(self, user_id: int) -> bool:
        return user_id in self._sessions

    def stop_session(self, user_id: int) -> int:
        session = self._sessions.pop(user_id, None)
        return session.score if session else 0

    def current_score(self, user_id: int) -> int:
        session = self._sessions.get(user_id)
        return session.score if session else 0

    def next_question(self, user_id: int) -> tuple[int, Question] | None:
        session = self._sessions.get(user_id)
        if not session:
            return None

        available_indexes = [i for i in range(len(self._questions)) if i not in session.asked_indexes]
        if not available_indexes:
            return None

        question_index = random.choice(available_indexes)
        session.asked_indexes.add(question_index)
        return question_index, self._questions[question_index]

    def check_answer(self, user_id: int, question_index: int, selected_index: int) -> tuple[bool, str]:
        session = self._sessions.get(user_id)
        if not session:
            return False, "Önce /quiz-start komutuyla oyunu başlatmalısın."

        question = self._questions[question_index]
        is_correct = question.answer == selected_index
        if is_correct:
            session.score += 1
            return True, "Doğru cevap! 🎉"

        return False, f"Yanlış cevap. Doğru seçenek: **{question.correct_choice}**"
