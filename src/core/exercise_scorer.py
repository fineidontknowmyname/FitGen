from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schemas.content import Exercise
from schemas.user import UserProfile
from schemas.common import ExperienceLevel, FitnessGoal, Equipment


_EXP_TIER: dict[ExperienceLevel, int] = {
    ExperienceLevel.beginner:     0,
    ExperienceLevel.intermediate: 1,
    ExperienceLevel.advanced:     2,
}

_DIFFICULTY_TIER: dict[str, int] = {
    "beginner":     0,
    "intermediate": 1,
    "advanced":     2,
}

_GOAL_KEYWORDS: dict[FitnessGoal, set[str]] = {
    FitnessGoal.weight_loss: {
        "cardio", "circuit", "hiit", "jump", "burpee", "metabolic",
        "interval", "sprint", "full body", "plyometric",
    },
    FitnessGoal.muscle_gain: {
        "press", "curl", "row", "pull", "push", "squat", "deadlift",
        "bench", "hypertrophy", "compound", "chest", "back", "bicep",
        "tricep", "shoulder", "leg",
    },
    FitnessGoal.strength_gain: {
        "deadlift", "squat", "bench", "overhead", "press", "clean",
        "snatch", "powerlifting", "compound", "heavy", "barbell",
    },
    FitnessGoal.endurance_gain: {
        "run", "jog", "cycle", "swim", "row", "cardio", "aerobic",
        "stamina", "long", "distance", "zone 2",
    },
    FitnessGoal.flexibility_gain: {
        "stretch", "yoga", "mobility", "hip flexor", "hamstring",
        "pigeon", "twist", "flex", "range of motion",
    },
    FitnessGoal.general_fitness: {
        "functional", "core", "balance", "stability", "mobility",
        "full body", "compound",
    },
}

DEFAULT_WEIGHTS = {
    "difficulty_match": 0.30,
    "equipment_fit":    0.20,
    "muscle_coverage":  0.20,
    "goal_alignment":   0.20,
    "safety_headroom":  0.10,
}


@dataclass(order=True)
class ScoredExercise:
    score: float = field(compare=True)
    exercise: Exercise = field(compare=False)
    factor_scores: dict[str, float] = field(compare=False, default_factory=dict)

    def __repr__(self) -> str:
        return f"ScoredExercise(score={self.score:.3f}, name={self.exercise.name!r})"


class ExerciseScorer:

    def __init__(self, weights: Optional[dict[str, float]] = None):
        w = {**DEFAULT_WEIGHTS, **(weights or {})}
        total = sum(w.values()) or 1.0
        self.weights = {k: v / total for k, v in w.items()}

    def score_and_rank(
        self,
        exercises: List[Exercise],
        user_profile: UserProfile,
        top_n: Optional[int] = None,
    ) -> List[ScoredExercise]:

        scored = [self._score_one(ex, user_profile) for ex in exercises]
        scored.sort(reverse=True)
        return scored[:top_n] if top_n is not None else scored

    def _score_one(self, ex: Exercise, profile: UserProfile) -> ScoredExercise:
        factors = {
            "difficulty_match": self._difficulty_match(ex, profile),
            "equipment_fit":    self._equipment_fit(ex, profile),
            "muscle_coverage":  self._muscle_coverage(ex),
            "goal_alignment":   self._goal_alignment(ex, profile.fitness_goal),
            "safety_headroom":  self._safety_headroom(ex),
        }
        composite = sum(self.weights[k] * v for k, v in factors.items())
        return ScoredExercise(
            score=round(composite, 4),
            exercise=ex,
            factor_scores={k: round(v, 4) for k, v in factors.items()},
        )

    @staticmethod
    def _difficulty_match(ex: Exercise, profile: UserProfile) -> float:
        user_tier = _EXP_TIER.get(profile.experience_level, 1)
        ex_tier   = _DIFFICULTY_TIER.get(
            getattr(ex, "difficulty", "intermediate").lower(), 1
        )
        diff = abs(user_tier - ex_tier)
        return max(0.0, 1.0 - diff * 0.35)

    @staticmethod
    def _equipment_fit(ex: Exercise, profile: UserProfile) -> float:
        needed: List[Equipment] = getattr(ex, "equipment_needed", [])
        non_bw = [e for e in needed if e != Equipment.bodyweight]
        if not non_bw:
            return 1.0
        owned = set(profile.equipment)
        matched = sum(1 for e in non_bw if e in owned)
        return matched / len(non_bw)

    @staticmethod
    def _muscle_coverage(ex: Exercise) -> float:
        muscles: List[str] = getattr(ex, "muscles_worked", [])
        n = len(muscles)
        if n == 0:
            return 0.20
        elif n == 1:
            return 0.30
        elif n == 2:
            return 0.55
        elif n == 3:
            return 0.75
        else:
            return min(0.90, 0.75 + (n - 3) * 0.05)

    @staticmethod
    def _goal_alignment(ex: Exercise, goal: FitnessGoal) -> float:
        keywords = _GOAL_KEYWORDS.get(goal, set())
        if not keywords:
            return 0.5

        blob = " ".join([
            ex.name,
            getattr(ex, "description", ""),
            " ".join(getattr(ex, "muscles_worked", [])),
        ]).lower()

        hits = sum(1 for kw in keywords if kw in blob)
        return min(1.0, hits / 3.0)

    @staticmethod
    def _safety_headroom(ex: Exercise) -> float:
        warnings: List[str] = getattr(ex, "safety_warnings", [])
        return max(0.20, 1.0 - len(warnings) * 0.20)


exercise_scorer = ExerciseScorer()
