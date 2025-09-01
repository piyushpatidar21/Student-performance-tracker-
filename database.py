#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#..venv\Scripts\Activate.ps1
import sqlite3
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os

DB_PATH = os.environ.get("STUDENT_TRACKER_DB_PATH", "student_tracker.db")


@contextmanager
def get_conn():
    # check_same_thread=False allows use across Streamlit threads safely when each function opens/closes
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def create_tables() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        # Users table: unique username, role is Student or Teacher
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Student','Teacher'))
            );
            """
        )
        # Students table for performance records
        # name is a free text field; for student self-entries we use their username as "name"
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                attendance REAL NOT NULL,
                marks REAL NOT NULL,
                assignments REAL NOT NULL,
                study_hours REAL NOT NULL,
                extracurriculars REAL NOT NULL,
                predicted_grade TEXT NOT NULL CHECK (predicted_grade IN ('A','B','C','D'))
            );
            """
        )
        conn.commit()


# User operations
def add_user(username: str, password_hash: str, role: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_user(username: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None


# Student operations
def add_student(
    name: str,
    attendance: float,
    marks: float,
    assignments: float,
    study_hours: float,
    extracurriculars: float,
    predicted_grade: str,
) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO students
            (name, attendance, marks, assignments, study_hours, extracurriculars, predicted_grade)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                attendance,
                marks,
                assignments,
                study_hours,
                extracurriculars,
                predicted_grade,
            ),
        )
        conn.commit()
        return cur.lastrowid


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
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE students
            SET name = ?, attendance = ?, marks = ?, assignments = ?, study_hours = ?, extracurriculars = ?, predicted_grade = ?
            WHERE id = ?
            """,
            (
                name,
                attendance,
                marks,
                assignments,
                study_hours,
                extracurriculars,
                predicted_grade,
                student_id,
            ),
        )
        conn.commit()
        return cur.rowcount > 0


def remove_student(student_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cur.rowcount > 0


def get_all_students() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def get_students_by_name(name: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE name = ? ORDER BY id DESC", (name,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


# Initialize tables on import
create_tables()
