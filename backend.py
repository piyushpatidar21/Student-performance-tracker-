from __future__ import annotations

import os
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import bcrypt

import database

MODEL_PATH = os.environ.get("STUDENT_TRACKER_MODEL_PATH", "model.pkl")
_MODEL: RandomForestClassifier | None = None
_CLASSES: List[str] | None = None


def _generate_synthetic_dataset(n: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    # Feature ranges
    attendance = rng.uniform(50, 100, size=n)           # %
    marks = rng.uniform(30, 100, size=n)                # %
    assignments = rng.uniform(30, 100, size=n)          # %
    study_hours = rng.uniform(0, 40, size=n)            # hours/week
    extracurriculars = rng.integers(0, 11, size=n)      # 0-10

    # Weighted composite score with some noise
    score = (
        marks * 0.5 +
        attendance * 0.2 +
        assignments * 0.15 +
        (study_hours / 40.0) * 100.0 * 0.10 +
        (extracurriculars / 10.0) * 100.0 * 0.05
    )
    noise = rng.normal(0, 5, size=n)
    score = np.clip(score + noise, 0, 100)

    # Thresholds -> Grades
    labels = np.empty(n, dtype=object)
    labels[score >= 85] = "A"
    labels[(score >= 70) & (score < 85)] = "B"
    labels[(score >= 55) & (score < 70)] = "C"
    labels[score < 55] = "D"

    X = np.column_stack([attendance, marks, assignments, study_hours, extracurriculars])
    y = labels
    return X, y


def _ensure_model():
    global _MODEL, _CLASSES
    if _MODEL is not None:
        return
    if os.path.exists(MODEL_PATH):
        _MODEL = joblib.load(MODEL_PATH)
        _CLASSES = list(_MODEL.classes_)  # type: ignore
        return
    # Train new model
    X, y = _generate_synthetic_dataset()
    model = RandomForestClassifier(n_estimators=200, random_state=0, class_weight="balanced_subsample")
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    _MODEL = model
    _CLASSES = list(model.classes_)


# Auth
def register_user(username: str, password: str, role: str) -> Tuple[bool, str]:
    if not username or not password or role not in ("Student", "Teacher"):
        return False, "Invalid inputs."
    existing = database.get_user(username)
    if existing:
        return False, "Username already exists."
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    ok = database.add_user(username, pw_hash, role)
    if not ok:
        return False, "Could not create user (username may be taken)."
    return True, "Registration successful."


def login_user(username: str, password: str) -> Tuple[bool, str, str]:
    """
    Returns (success, role, message)
    """
    user = database.get_user(username)
    if not user:
        return False, "", "User not found."
    stored_hash = user["password_hash"]
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return True, user["role"], "Login successful."
    return False, "", "Incorrect password."


# ML
def predict_grade(data: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
    """
    data must include: attendance, marks, assignments, study_hours, extracurriculars
    Returns (predicted_grade, probabilities dict by class)
    """
    _ensure_model()
    assert _MODEL is not None and _CLASSES is not None
    X = np.array(
        [
            [
                float(data["attendance"]),
                float(data["marks"]),
                float(data["assignments"]),
                float(data["study_hours"]),
                float(data["extracurriculars"]),
            ]
        ]
    )
    probs = _MODEL.predict_proba(X)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = _CLASSES[pred_idx]
    prob_map = {label: float(prob) for label, prob in zip(_CLASSES, probs)}
    return str(pred_label), prob_map


def get_recommendations(data: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    if data["attendance"] < 75:
        recs.append("Improve attendance to at least 85% for better outcomes.")
    if data["marks"] < 70:
        recs.append("Focus on core subjects to raise marks above 80%.")
    if data["assignments"] < 70:
        recs.append("Complete and revise assignments to boost assignment score.")
    if data["study_hours"] < 10:
        recs.append("Increase study hours to at least 12-15 hours/week.")
    if data["extracurriculars"] < 3:
        recs.append("Engage in extracurricular activities to build balance and soft skills.")
    if not recs:
        recs.append("Great job! Maintain consistency to keep your performance high.")
    return recs


def compute_risk(data: Dict[str, Any], prob_map: Optional[Dict[str, float]] = None) -> Tuple[float, str, List[str]]:
    """
    Computes a risk score (0-1), a categorical level, and mitigation tips.
    Heuristics combine model probabilities (if provided) and domain thresholds.
    """
    # Base from model probabilities (if provided)
    risk = 0.0
    tips: List[str] = []
    if prob_map:
        risk += prob_map.get("D", 0.0) * 1.0
        risk += prob_map.get("C", 0.0) * 0.5

    # Heuristic penalties (clamped later)
    att = float(data.get("attendance", 0))
    marks = float(data.get("marks", 0))
    asg = float(data.get("assignments", 0))
    study = float(data.get("study_hours", 0))
    extra = float(data.get("extracurriculars", 0))

    if att < 75:
        risk += 0.20
        tips.append("Raise attendance toward 85%+ with a weekly attendance plan and accountability partner.")
    if marks < 60:
        risk += 0.25
        tips.append("Schedule 2 focused study blocks/day and target weak topics to lift marks above 70%.")
    if asg < 60:
        risk += 0.20
        tips.append("Use a weekly assignment checklist and submit drafts 48h early for feedback.")
    if study < 8:
        risk += 0.10
        tips.append("Increase study time to 12–15 hrs/week using Pomodoro (25/5) and a fixed timetable.")
    if extra < 2:
        risk += 0.05
        tips.append("Join 1–2 extracurriculars to build routines and motivation.")

    # Clamp and level
    risk = min(max(risk, 0.0), 1.0)
    level = "Low"
    if risk >= 0.70:
        level = "High"
    elif risk >= 0.40:
        level = "Medium"

    # Ensure at least one positive suggestion
    if not tips:
        tips.append("Maintain current habits and review weekly to keep risk low.")
    return risk, level, tips


# Student CRUD wrappers (rely on DB)
def add_student(
    name: str,
    attendance: float,
    marks: float,
    assignments: float,
    study_hours: float,
    extracurriculars: float,
    predicted_grade: str,
) -> int:
    return database.add_student(
        name, attendance, marks, assignments, study_hours, extracurriculars, predicted_grade
    )


def update_student(
    student_id: int,
    name: str,
    attendance: float,
    marks: float,
    assignments: float,
    study_hours: float,
    extracurriculars: float,
    predicted_grade: str,
) -> bool:
    return database.update_student(
        student_id, name, attendance, marks, assignments, study_hours, extracurriculars, predicted_grade
    )


def remove_student(student_id: int) -> bool:
    return database.remove_student(student_id)


def get_all_students() -> List[Dict[str, Any]]:
    return database.get_all_students()


def get_students_by_name(name: str) -> List[Dict[str, Any]]:
    return database.get_students_by_name(name)
