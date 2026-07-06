"""
🏥 Athlete Injury Risk Predictor — Advanced Edition (Single-File Build)
========================================================================
A professional PyQt5 desktop application that estimates an athlete's
short-term injury risk using a transparent, multi-factor sports-medicine
inspired scoring engine.

Everything — risk engine, database, themes, widgets, and all pages —
lives in this one file for easy distribution and running.

Run with:
    pip install PyQt5 matplotlib
    python3 injury_risk_app.py

KEY FEATURES
------------
 1. Multi-factor injury risk score (0-100) with full transparent breakdown
 2. Injury-specific prevention exercise plan, tailored to the athlete's sport
 3. Recommended reassessment / follow-up timeline based on risk severity
 4. Individual Athlete Trends page — track one athlete's risk over time
 5. Follow-Up Alerts page — surfaces overdue / high-priority athletes
 6. One-click PDF report export for any single assessment
 7. Searchable, filterable History with JSON export
 8. Dashboard + Statistics pages with live charts (pie / bar / trend)
 9. Four polished visual themes, medium/normal-density layout for standard displays

The window opens at a normal, medium-sized default geometry with
comfortably (but not oversized) legible text and widgets.
"""

import sys
import os
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QComboBox, QSizePolicy, QLineEdit,
    QSpinBox, QDoubleSpinBox, QScrollArea, QGridLayout, QCheckBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QTextDocument, QFontMetrics
from PyQt5.QtPrintSupport import QPrinter

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ============================================================================
# 1. RISK ENGINE  (pure logic, no GUI dependencies)
# ============================================================================

SPORT_PROFILES: Dict[str, Dict] = {
    "🏃 Running / Track & Field": {
        "load_multiplier": 1.10, "impact_multiplier": 1.25,
        "common_injuries": ["Stress Fractures", "IT Band Syndrome", "Shin Splints",
                             "Plantar Fasciitis", "Achilles Tendinopathy"],
        "regions": ["Shins", "Knees", "Achilles", "Feet"],
        "prevention": [
            "Increase weekly mileage by no more than 10%; ensure adequate calcium/vitamin D intake",
            "Strengthen hip abductors with side-lying leg raises and clamshells",
            "Calf-raise strengthening; avoid sudden increases in running surface hardness",
            "Daily foot-arch strengthening and calf stretching before runs",
            "Eccentric calf raises 3x/week; rotate footwear every 300-500 km",
        ],
    },
    "⚽ Football / Soccer": {
        "load_multiplier": 1.20, "impact_multiplier": 1.35,
        "common_injuries": ["ACL Tears", "Hamstring Strains", "Ankle Sprains",
                             "Groin Strains", "Concussion"],
        "regions": ["Knees", "Hamstrings", "Ankles", "Groin"],
        "prevention": [
            "Neuromuscular landing-mechanics training (soft-knee, hip-dominant landings)",
            "Nordic hamstring curls 2-3x/week during in-season training",
            "Balance/proprioception drills; consider bracing after any prior sprain",
            "Copenhagen adductor exercises 2x/week",
            "Neck strengthening plus strict return-to-play protocol after any head impact",
        ],
    },
    "🏀 Basketball": {
        "load_multiplier": 1.15, "impact_multiplier": 1.30,
        "common_injuries": ["Ankle Sprains", "ACL/Meniscus Tears", "Patellar Tendinopathy (Jumper's Knee)",
                             "Finger/Hand Fractures", "Achilles Rupture"],
        "regions": ["Ankles", "Knees", "Fingers", "Achilles"],
        "prevention": [
            "Balance-board training plus supportive, well-fitted footwear",
            "Jump-landing technique coaching (soft knees, avoid valgus collapse)",
            "Eccentric squats and patellar-tendon load management on hard courts",
            "Ball-handling drills; tape or brace fingers with prior injury",
            "Calf strengthening; monitor cumulative jump-load on hard surfaces",
        ],
    },
    "🏋️ Weightlifting / Powerlifting": {
        "load_multiplier": 1.30, "impact_multiplier": 0.85,
        "common_injuries": ["Lower Back Strain", "Rotator Cuff Injury", "Bicep/Pec Tears",
                             "Wrist Strain", "Herniated Disc"],
        "regions": ["Lower Back", "Shoulders", "Wrists", "Elbows"],
        "prevention": [
            "Core-bracing drills; keep strict form on deadlifts and squats",
            "Scapular stability work — face pulls and band rows",
            "Progress load gradually; avoid maximal ego-lifting on bench press",
            "Wrist mobility/strength work; use wrist wraps on heavy pressing days",
            "Core stabilization training; avoid excessive spinal loading with poor form",
        ],
    },
    "🏊 Swimming": {
        "load_multiplier": 1.05, "impact_multiplier": 0.60,
        "common_injuries": ["Swimmer's Shoulder (Impingement)", "Rotator Cuff Strain",
                             "Knee Pain (Breaststroke)", "Lower Back Strain"],
        "regions": ["Shoulders", "Neck", "Knees"],
        "prevention": [
            "Scapular stabilization plus rotator-cuff strengthening 2-3x/week",
            "Balance pulling and pushing strength ratios in dryland training",
            "Hip mobility work and technique review of the breaststroke whip kick",
            "Core strengthening plus streamline posture drills",
        ],
    },
    "🎾 Tennis / Racquet Sports": {
        "load_multiplier": 1.10, "impact_multiplier": 1.05,
        "common_injuries": ["Tennis Elbow (Lateral Epicondylitis)", "Rotator Cuff Injury",
                             "Ankle Sprains", "Lower Back Strain"],
        "regions": ["Elbow", "Shoulder", "Ankles", "Lower Back"],
        "prevention": [
            "Eccentric wrist-extensor exercises 2-3x/week",
            "Shoulder external-rotation strengthening with resistance bands",
            "Lateral agility and proprioception training",
            "Core rotational strength work plus serve-mechanics review",
        ],
    },
    "🚴 Cycling": {
        "load_multiplier": 1.05, "impact_multiplier": 0.75,
        "common_injuries": ["Patellofemoral Pain", "Lower Back Pain", "Neck Strain",
                             "Achilles Tendinopathy", "IT Band Syndrome"],
        "regions": ["Knees", "Lower Back", "Neck"],
        "prevention": [
            "Professional bike-fit review plus quad/hip strengthening",
            "Core endurance training and saddle-position check",
            "Neck mobility drills; re-check handlebar height",
            "Review cleat position; add eccentric calf loading",
            "Hip strengthening plus a saddle-height review",
        ],
    },
    "🤸 Gymnastics": {
        "load_multiplier": 1.25, "impact_multiplier": 1.30,
        "common_injuries": ["Wrist Stress Injury", "Ankle Sprains", "Lower Back Spondylolysis",
                             "Shoulder Instability", "ACL Tears"],
        "regions": ["Wrists", "Lower Back", "Ankles", "Shoulders"],
        "prevention": [
            "Gradual wrist-loading progression plus targeted strength conditioning",
            "Landing technique and proprioceptive training after every dismount",
            "Core stabilization work; limit repetitive spinal hyperextension",
            "Rotator-cuff and scapular-stabilizer strengthening",
            "Dedicated landing-mechanics coaching on dismounts",
        ],
    },
    "🥊 Combat Sports (MMA/Boxing)": {
        "load_multiplier": 1.30, "impact_multiplier": 1.40,
        "common_injuries": ["Concussion", "Hand/Wrist Fractures", "Facial Trauma",
                             "Rib Fractures", "Knee Ligament Injury"],
        "regions": ["Head", "Hands", "Ribs", "Knees"],
        "prevention": [
            "Neck strengthening plus mandatory headgear use in sparring",
            "Correct hand-wrapping technique and gradual heavy-bag volume progression",
            "Consistent mouthguard/headgear use plus defensive-technique drilling",
            "Core conditioning plus controlled, capped sparring intensity",
            "Lower-body stability and footwork drilling",
        ],
    },
    "🔥 CrossFit / Functional Fitness": {
        "load_multiplier": 1.25, "impact_multiplier": 1.00,
        "common_injuries": ["Shoulder Impingement", "Lower Back Strain", "Knee Tendinopathy",
                             "Wrist Strain", "Rhabdomyolysis (Overtraining)"],
        "regions": ["Shoulders", "Lower Back", "Knees", "Wrists"],
        "prevention": [
            "Scapular control drills plus overhead mobility work",
            "Technique coaching on Olympic lifts; brace the core on every rep",
            "Eccentric loading and gradual box-jump volume progression",
            "Wrist mobility prep before high-rep gymnastics movements",
            "Scale WOD intensity to fitness level; prioritize hydration and rest days",
        ],
    },
    "⚾ Baseball / Softball": {
        "load_multiplier": 1.10, "impact_multiplier": 0.95,
        "common_injuries": ["UCL Tear (Tommy John)", "Rotator Cuff Injury", "Labrum Tear",
                             "Elbow Tendinopathy"],
        "regions": ["Elbow", "Shoulder"],
        "prevention": [
            "Strict pitch-count monitoring plus a structured long-toss progression",
            "Scapular stability work and season-long throwing periodization",
            "Shoulder external-rotation strengthening plus mechanics review",
            "Gradual throwing-volume increases with a daily arm-care routine",
        ],
    },
    "🏐 Volleyball": {
        "load_multiplier": 1.10, "impact_multiplier": 1.10,
        "common_injuries": ["Patellar Tendinopathy (Jumper's Knee)", "Ankle Sprains",
                             "Shoulder Impingement", "Finger Sprains"],
        "regions": ["Knees", "Ankles", "Shoulders", "Fingers"],
        "prevention": [
            "Eccentric quad loading plus jump-landing mechanics training",
            "Balance training and ankle bracing on repeated jump landings",
            "Scapular strengthening plus spike-mechanics review",
            "Buddy taping plus blocking-technique drills",
        ],
    },
}

AGE_GROUPS = ["Under 18", "18-25", "26-35", "36-45", "46-55", "56+"]
INTENSITY_LEVELS = ["Low", "Moderate", "High", "Very High / Elite"]
COMPETITION_PHASES = ["Off-Season", "Pre-Season", "In-Season", "Playoffs / Peak Competition"]

RISK_BANDS = [
    (0, 25, "Low", "🟢"),
    (25, 50, "Moderate", "🟡"),
    (50, 75, "High", "🟠"),
    (75, 101, "Critical", "🔴"),
]

REASSESS_DAYS_MAP = {"Low": 30, "Moderate": 14, "High": 7, "Critical": 3}


@dataclass
class AthleteInput:
    name: str
    sport: str
    age_group: str
    height_cm: float
    weight_kg: float
    training_hours_week: float
    intensity: str
    rest_days_week: int
    sleep_hours: float
    prior_injuries_12mo: int
    days_since_last_injury: int
    flexibility_score: int
    stress_level: int
    hydration_level: int
    warms_up: bool
    proper_equipment: bool
    competition_phase: str


@dataclass
class RiskResult:
    score: float
    category: str
    emoji: str
    urgency: float
    needs_professional: bool
    bmi: float
    bmi_category: str
    factor_breakdown: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    common_injuries: List[str] = field(default_factory=list)
    focus_regions: List[str] = field(default_factory=list)
    prevention_plan: List[Dict] = field(default_factory=list)
    reassess_days: int = 14
    reassess_note: str = ""
    timestamp: str = ""


def _bmi(height_cm: float, weight_kg: float):
    h = max(height_cm, 1) / 100.0
    bmi = weight_kg / (h * h)
    if bmi < 18.5:
        cat = "Underweight"
    elif bmi < 25:
        cat = "Normal"
    elif bmi < 30:
        cat = "Overweight"
    else:
        cat = "Obese"
    return round(bmi, 1), cat


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def calculate_risk(inp: AthleteInput) -> RiskResult:
    profile = SPORT_PROFILES.get(inp.sport, list(SPORT_PROFILES.values())[0])
    breakdown = []

    def add(label, points, note):
        breakdown.append({"factor": label, "points": round(points, 1), "note": note})
        return points

    score = 0.0

    if inp.training_hours_week <= 5:
        pts = 3
    elif inp.training_hours_week <= 10:
        pts = 8
    elif inp.training_hours_week <= 16:
        pts = 13
    elif inp.training_hours_week <= 22:
        pts = 17
    else:
        pts = 20
    pts *= profile["load_multiplier"]
    score += add("Training Volume", pts, f"{inp.training_hours_week} hrs/week in a "
                 f"{'high-impact' if profile['impact_multiplier'] > 1 else 'moderate-impact'} sport")

    intensity_map = {"Low": 2, "Moderate": 7, "High": 12, "Very High / Elite": 15}
    pts = intensity_map.get(inp.intensity, 7)
    score += add("Training Intensity", pts, f"Reported intensity: {inp.intensity}")

    if inp.rest_days_week >= 3:
        pts = 1
    elif inp.rest_days_week == 2:
        pts = 5
    elif inp.rest_days_week == 1:
        pts = 10
    else:
        pts = 15
    score += add("Recovery Days", pts, f"Only {inp.rest_days_week} rest day(s)/week" if inp.rest_days_week < 2
                 else f"{inp.rest_days_week} rest days/week — adequate")

    if inp.sleep_hours >= 8:
        pts = 1
    elif inp.sleep_hours >= 7:
        pts = 4
    elif inp.sleep_hours >= 6:
        pts = 9
    elif inp.sleep_hours >= 5:
        pts = 13
    else:
        pts = 15
    score += add("Sleep Quality", pts, f"{inp.sleep_hours} hrs/night average")

    pts = min(inp.prior_injuries_12mo * 6, 18)
    if inp.days_since_last_injury <= 30:
        pts += 8
        note = f"{inp.prior_injuries_12mo} injuries in 12mo, last one only {inp.days_since_last_injury} days ago"
    elif inp.days_since_last_injury <= 90:
        pts += 4
        note = f"{inp.prior_injuries_12mo} injuries in 12mo, recovering within last 3 months"
    else:
        note = f"{inp.prior_injuries_12mo} injuries reported in the past 12 months"
    score += add("Injury History", pts, note)

    pts = (10 - inp.flexibility_score) * 1.0
    score += add("Flexibility / Mobility", pts, f"Self-rated mobility: {inp.flexibility_score}/10")

    pts = inp.stress_level * 0.8
    score += add("Stress / Mental Fatigue", pts, f"Self-rated stress: {inp.stress_level}/10")

    pts = (10 - inp.hydration_level) * 0.7
    score += add("Hydration", pts, f"Self-rated hydration: {inp.hydration_level}/10")

    pts = 0 if inp.warms_up else 6
    score += add("Warm-up Routine", pts, "Warms up consistently" if inp.warms_up else "Skips/irregular warm-ups")

    pts = 0 if inp.proper_equipment else 5
    score += add("Equipment / Footwear", pts, "Uses proper gear" if inp.proper_equipment
                 else "Reports inadequate/worn gear")

    bmi, bmi_cat = _bmi(inp.height_cm, inp.weight_kg)
    bmi_pts = {"Underweight": 4, "Normal": 0, "Overweight": 4, "Obese": 8}[bmi_cat]
    score += add("Body Composition (BMI)", bmi_pts, f"BMI {bmi} ({bmi_cat})")

    age_pts = {"Under 18": 3, "18-25": 1, "26-35": 2, "36-45": 5, "46-55": 7, "56+": 8}
    pts = age_pts.get(inp.age_group, 3)
    score += add("Age Group", pts, f"Age group: {inp.age_group}")

    phase_pts = {"Off-Season": 0, "Pre-Season": 3, "In-Season": 4, "Playoffs / Peak Competition": 6}
    pts = phase_pts.get(inp.competition_phase, 2)
    score += add("Competition Phase", pts, f"Currently: {inp.competition_phase}")

    impact_pts = 8 * (profile["impact_multiplier"] - 0.6) / (1.4 - 0.6)
    impact_pts = _clamp(impact_pts, 0, 10)
    score += add("Sport Impact Profile", impact_pts, f"{inp.sport} carries "
                 f"{'high' if profile['impact_multiplier'] > 1.15 else 'moderate' if profile['impact_multiplier'] > 0.9 else 'lower'} "
                 f"structural impact demand")

    score = _clamp(score, 0, 100)

    category, emoji = "Low", "🟢"
    for lo, hi, cat, em in RISK_BANDS:
        if lo <= score < hi:
            category, emoji = cat, em
            break

    urgency = score
    if inp.days_since_last_injury <= 14:
        urgency += 8
    if inp.stress_level >= 9 and inp.sleep_hours < 6:
        urgency += 5
    urgency = round(_clamp(urgency, 0, 100) / 10, 1)

    needs_professional = score >= 50 or inp.days_since_last_injury <= 14 or inp.prior_injuries_12mo >= 3

    recs = []
    if inp.rest_days_week < 2:
        recs.append("🛌 Increase recovery to at least 2 full rest days per week to reduce cumulative fatigue.")
    if inp.sleep_hours < 7:
        recs.append("😴 Prioritize 7-9 hours of sleep nightly — sleep debt is strongly linked to injury risk.")
    if inp.flexibility_score <= 5:
        recs.append("🧘 Add a daily mobility/stretching routine (10-15 min) to improve tissue tolerance.")
    if inp.hydration_level <= 5:
        recs.append("💧 Improve hydration strategy, especially around training sessions.")
    if not inp.warms_up:
        recs.append("🔥 Implement a structured dynamic warm-up before every session.")
    if not inp.proper_equipment:
        recs.append("👟 Replace worn or inappropriate equipment/footwear for your sport.")
    if inp.stress_level >= 7:
        recs.append("🧠 Consider stress-management techniques (breathing, journaling, sports psych) — mental fatigue raises injury risk.")
    if inp.prior_injuries_12mo >= 2:
        recs.append("📋 Discuss a structured return-to-play / prevention plan with a sports medicine professional.")
    if bmi_cat in ("Underweight", "Obese"):
        recs.append(f"🍎 Consult a sports nutritionist — current BMI category ({bmi_cat}) may increase load-related risk.")
    if inp.training_hours_week > 16 and inp.intensity in ("High", "Very High / Elite"):
        recs.append("📉 Consider periodizing training (deload weeks) to manage very high combined volume + intensity.")
    if not recs:
        recs.append("✅ Great habits overall! Maintain current recovery and training balance.")

    prevention_texts = profile.get("prevention", [])
    prevention_plan = [
        {"injury": injury, "exercise": prevention_texts[i] if i < len(prevention_texts) else "Follow general strength & mobility best practices."}
        for i, injury in enumerate(profile["common_injuries"])
    ]

    reassess_days = REASSESS_DAYS_MAP.get(category, 14)
    if needs_professional:
        reassess_note = "See a sports medicine professional before returning to full training load."
    elif category in ("High", "Critical"):
        reassess_note = "Reduce load and monitor symptoms closely until the next check-in."
    else:
        reassess_note = "Re-run this assessment on schedule to track how your habits are trending."

    return RiskResult(
        score=round(score, 1), category=category, emoji=emoji, urgency=urgency,
        needs_professional=needs_professional, bmi=bmi, bmi_category=bmi_cat,
        factor_breakdown=breakdown, recommendations=recs,
        common_injuries=profile["common_injuries"], focus_regions=profile["regions"],
        prevention_plan=prevention_plan, reassess_days=reassess_days, reassess_note=reassess_note,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ============================================================================
# 2. DATABASE  (SQLite persistence)
# ============================================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "injury_risk_history.db")


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                athlete_name TEXT,
                sport TEXT,
                age_group TEXT,
                score REAL,
                category TEXT,
                urgency REAL,
                needs_professional INTEGER,
                bmi REAL,
                bmi_category TEXT,
                reassess_days INTEGER DEFAULT 14,
                details_json TEXT
            )
        """)
        # Migration guard: older DB files created before reassess_days existed.
        try:
            conn.execute("ALTER TABLE assessments ADD COLUMN reassess_days INTEGER DEFAULT 14")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def insert_assessment(self, record: Dict) -> int:
        conn = self._connect()
        cur = conn.execute("""
            INSERT INTO assessments
                (timestamp, athlete_name, sport, age_group, score, category,
                 urgency, needs_professional, bmi, bmi_category, reassess_days, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["timestamp"], record["athlete_name"], record["sport"], record["age_group"],
            record["score"], record["category"], record["urgency"],
            1 if record["needs_professional"] else 0,
            record["bmi"], record["bmi_category"], record.get("reassess_days", 14),
            json.dumps(record.get("details", {})),
        ))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    def fetch_all(self) -> List[Dict]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM assessments ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def clear_all(self):
        conn = self._connect()
        conn.execute("DELETE FROM assessments")
        conn.commit()
        conn.close()

    def delete_by_id(self, record_id: int):
        conn = self._connect()
        conn.execute("DELETE FROM assessments WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()

    def delete_many(self, record_ids: List[int]):
        if not record_ids:
            return
        conn = self._connect()
        conn.executemany("DELETE FROM assessments WHERE id = ?", [(i,) for i in record_ids])
        conn.commit()
        conn.close()

    def stats_summary(self) -> Dict:
        rows = self.fetch_all()
        if not rows:
            return {"total": 0, "avg_score": 0, "high_risk_count": 0,
                    "professional_needed": 0, "by_sport": {}, "by_category": {}}
        total = len(rows)
        avg_score = round(sum(r["score"] for r in rows) / total, 1)
        high_risk = sum(1 for r in rows if r["category"] in ("High", "Critical"))
        prof_needed = sum(1 for r in rows if r["needs_professional"])
        by_sport, by_category = {}, {}
        for r in rows:
            by_sport[r["sport"]] = by_sport.get(r["sport"], 0) + 1
            by_category[r["category"]] = by_category.get(r["category"], 0) + 1
        return {"total": total, "avg_score": avg_score, "high_risk_count": high_risk,
                "professional_needed": prof_needed, "by_sport": by_sport, "by_category": by_category}


# ============================================================================
# 3. THEMES  (medium-density QSS — tuned for normal, non-maximized windows)
# ============================================================================
#
# Palette design notes (v5.1 — "Spectrum, medium density"):
#   * Each theme carries FOUR genuinely distinct severity hues
#     (low -> moderate -> high -> critical) that move around the color
#     wheel (green -> amber -> orange -> red) instead of four shades of
#     the same brown/red. "Critical" is a true red, clearly different
#     from "High"'s orange — not just a darker version of it.
#   * "accent" (primary chrome / buttons) and "accent2" (secondary chrome)
#     are picked from a *different* part of the wheel than the severity
#     colors (blue + violet) so the UI doesn't read as monochrome.
#   * Only body text and borders use near-black/near-white — no other
#     element is allowed to go "muddy dark".
#   * Font sizes / paddings here were scaled down from the original
#     "giant, made-for-4K-and-maximized" build to a normal desktop-app
#     density that reads comfortably in a regular, non-maximized window.

THEMES = {
    "🌤️ Light Neutral": {
        "bg": "#F5F3EE", "sidebar": "#EEE9DE", "sidebar_active": "#DCEAE6",
        "card": "#FFFFFF", "text": "#20242B", "muted": "#68707C",
        "accent": "#2563EB", "accent2": "#7C3AED",
        "low": "#15A05A", "moderate": "#D89A1E", "high": "#E8672B", "critical": "#DC2A2A",
        "border": "#E3DDCF",
    },
    "🌙 Midnight Dark": {
        "bg": "#171A21", "sidebar": "#11141A", "sidebar_active": "#232B38",
        "card": "#1E222C", "text": "#EDEEF2", "muted": "#9AA0AC",
        "accent": "#5B9CF6", "accent2": "#A78BFA",
        "low": "#34C77E", "moderate": "#E7B84D", "high": "#F0813F", "critical": "#F1554F",
        "border": "#2B303B",
    },
    "🌊 Ocean Blue": {
        "bg": "#EAF3F8", "sidebar": "#D9EBF4", "sidebar_active": "#BFE0EE",
        "card": "#FFFFFF", "text": "#0F2F44", "muted": "#4C6C7D",
        "accent": "#0E7490", "accent2": "#6D28D9",
        "low": "#1E9A57", "moderate": "#CE8F16", "high": "#DD6A28", "critical": "#D33A3A",
        "border": "#C7E0EA",
    },
    "🌲 Forest Pro": {
        "bg": "#F1F5EE", "sidebar": "#E3ECDB", "sidebar_active": "#CDE2C1",
        "card": "#FFFFFF", "text": "#1E2B1A", "muted": "#5A6B52",
        "accent": "#2E7D32", "accent2": "#8E44AD",
        "low": "#2FA34D", "moderate": "#D7A116", "high": "#DD7A22", "critical": "#D13B2E",
        "border": "#D6E2CC",
    },
}


def build_qss(p: dict) -> str:
    return f"""
    QWidget {{
        background-color: {p['bg']};
        color: {p['text']};
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}
    QFrame#sidebar {{
        background-color: {p['sidebar']};
        border-right: 1px solid {p['border']};
    }}
    QLabel#brandTitle {{
        font-size: 21px;
        font-weight: 800;
        color: {p['text']};
    }}
    QLabel#brandSubtitle {{
        font-size: 11px;
        color: {p['accent']};
        font-weight: 700;
        letter-spacing: 1.5px;
    }}
    QPushButton#navBtn {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
        color: {p['text']};
        background-color: transparent;
    }}
    QPushButton#navBtn:hover {{
        background-color: {p['sidebar_active']};
    }}
    QPushButton#navBtnActive {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 800;
        color: {p['text']};
        background-color: {p['sidebar_active']};
        border-left: 4px solid {p['accent']};
    }}
    QLabel#pageTitle {{
        font-size: 26px;
        font-weight: 800;
        color: {p['text']};
        padding: 4px 0px 2px 0px;
    }}
    QLabel#pageSubtitle {{
        font-size: 13px;
        color: {p['muted']};
        padding-bottom: 8px;
    }}
    QLabel#sectionHeading {{
        font-size: 16px;
        font-weight: 800;
        color: {p['accent']};
        padding-top: 10px;
        padding-bottom: 2px;
        background-color: transparent;
    }}
    QFrame#card {{
        background-color: {p['card']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}
    QLabel#kpiValue {{
        font-size: 26px;
        font-weight: 800;
        color: {p['accent']};
        background-color: transparent;
    }}
    QLabel#kpiLabel {{
        font-size: 12px;
        color: {p['muted']};
        font-weight: 700;
        background-color: transparent;
    }}
    QPushButton#primaryBtn {{
        background-color: {p['accent']};
        color: white;
        font-weight: 700;
        font-size: 13.5px;
        padding: 10px 18px;
        border-radius: 10px;
        border: none;
    }}
    QPushButton#primaryBtn:hover {{ background-color: {p['accent2']}; }}
    QPushButton#dangerBtn {{
        background-color: {p['critical']};
        color: white;
        font-weight: 700;
        font-size: 12.5px;
        padding: 8px 14px;
        border-radius: 8px;
        border: none;
    }}
    QPushButton#dangerBtn:hover {{ background-color: {p['high']}; }}
    QPushButton#secondaryBtn {{
        background-color: {p['accent2']};
        color: white;
        font-weight: 700;
        font-size: 12.5px;
        padding: 8px 14px;
        border-radius: 8px;
        border: none;
    }}
    QPushButton#secondaryBtn:hover {{ opacity: 0.9; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {p['card']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 7px 10px;
        font-size: 13px;
        min-height: 18px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p['card']};
        selection-background-color: {p['sidebar_active']};
        font-size: 13px;
    }}
    QSlider::groove:horizontal {{
        height: 5px;
        background: {p['border']};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {p['accent']};
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QTableWidget {{
        background-color: {p['card']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        gridline-color: {p['border']};
        font-size: 12.5px;
    }}
    QHeaderView::section {{
        background-color: {p['sidebar']};
        color: {p['accent']};
        font-weight: 800;
        font-size: 12px;
        padding: 9px 8px;
        border: none;
        border-bottom: 2px solid {p['border']};
    }}
    QTableWidget::item {{ padding: 7px; }}
    QScrollBar:vertical {{
        background: {p['bg']};
        width: 11px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['sidebar_active']};
        border-radius: 5px;
        min-height: 24px;
    }}
    QProgressBar {{
        border: 1px solid {p['border']};
        border-radius: 9px;
        text-align: center;
        font-weight: 700;
        font-size: 11px;
        background-color: {p['bg']};
        height: 20px;
    }}
    QProgressBar::chunk {{
        border-radius: 8px;
    }}
    QGroupBox {{
        font-weight: 700;
        font-size: 13.5px;
        border: 1px solid {p['border']};
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {p['accent']};
    }}
    QLabel {{
        background-color: transparent;
    }}
    """


# ============================================================================
# 4. REUSABLE WIDGETS  (medium KPI cards + hand-painted gauge)
# ============================================================================

class KpiCard(QFrame):
    def __init__(self, emoji: str, value: str, label: str, accent: str = "#2E6E9E", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 22px; background-color: transparent;")
        top.addWidget(emoji_label)
        top.addStretch()
        layout.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("kpiValue")
        self.value_label.setStyleSheet(f"color: {accent}; font-size: 24px; font-weight: 800; background-color: transparent;")
        layout.addWidget(self.value_label)

        text_label = QLabel(label)
        text_label.setObjectName("kpiLabel")
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 12px; font-weight: 700; background-color: transparent;")
        layout.addWidget(text_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class RiskGauge(QWidget):
    """
    A hand-painted circular gauge showing 0-100 risk score.

    The widget size is capped so the arc and its text can never balloon
    to an oversized, dominating block on a large monitor — and the score
    number / category word sit on a fixed vertical rhythm (two dedicated
    text bands) so they stay comfortably proportioned and never collide.
    """

    MAX_DIAMETER = 190

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0.0
        self._color = QColor("#3E7D4C")
        self._label = "LOW"
        self.setMinimumSize(150, 150)
        self.setMaximumSize(self.MAX_DIAMETER, self.MAX_DIAMETER)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def set_score(self, score: float, color: str, label: str):
        self._score = max(0.0, min(100.0, score))
        self._color = QColor(color)
        self._label = label
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height(), self.MAX_DIAMETER) - 14
        cx = self.width() / 2
        cy = self.height() / 2
        rect = QRectF(cx - side / 2, cy - side / 2, side, side)
        pen_width = max(10, side * 0.09)

        track_pen = QPen(QColor("#DCD5C8"), pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 90 * 16, -270 * 16)

        value_pen = QPen(self._color, pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(value_pen)
        span = -270 * (self._score / 100.0)
        painter.drawArc(rect, 90 * 16, int(span * 16))

        # Two fixed text bands (score number, then category word) so the
        # two lines keep a consistent, proportioned relationship to the
        # ring instead of one overwhelming the other.
        score_font_size = max(14, min(24, int(side * 0.17)))
        label_font_size = max(8, min(12, int(side * 0.075)))

        score_rect = QRectF(rect.x(), cy - side * 0.22, side, side * 0.30)
        label_rect = QRectF(rect.x(), cy + side * 0.10, side, side * 0.16)

        painter.setPen(QColor(self._color))
        font = QFont("Segoe UI", score_font_size, QFont.Bold)
        painter.setFont(font)
        painter.drawText(score_rect, Qt.AlignCenter, f"{self._score:.0f}")

        font2 = QFont("Segoe UI", label_font_size, QFont.Bold)
        font2.setLetterSpacing(QFont.PercentageSpacing, 105)
        painter.setFont(font2)
        painter.drawText(label_rect, Qt.AlignCenter, self._label)


class SectionHeading(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("sectionHeading")


def themed_axes_style(ax, fig, p):
    """Shared matplotlib theming helper used by every chart in the app."""
    fig.patch.set_facecolor(p["card"])
    ax.set_facecolor(p["card"])
    ax.tick_params(colors=p["text"])
    for spine in ax.spines.values():
        spine.set_color(p["border"])
    ax.title.set_color(p["text"])
    ax.xaxis.label.set_color(p["text"])
    ax.yaxis.label.set_color(p["text"])


def category_color(p: dict, category: str) -> str:
    """Single source of truth mapping a risk category to its themed color."""
    return {"Low": p["low"], "Moderate": p["moderate"], "High": p["high"], "Critical": p["critical"]}.get(
        category, p["accent"]
    )


def shade_by_magnitude(hex_color: str, fraction: float, min_fraction: float = 0.18) -> str:
    """
    Blend `hex_color` toward white based on `fraction` (0.0-1.0).

    fraction close to 1.0 -> full, saturated color (this factor dominates).
    fraction close to 0.0 -> pale, washed-out tint of the same color
    (this factor barely contributes), instead of every bar rendering as
    one flat, undifferentiated color regardless of magnitude.

    `min_fraction` puts a floor under how pale a bar can get, so even a
    near-zero contribution stays a faint but visible tint of the color
    rather than turning invisible white.
    """
    fraction = max(min_fraction, min(1.0, fraction))
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = round(r + (255 - r) * (1 - fraction))
    g = round(g + (255 - g) * (1 - fraction))
    b = round(b + (255 - b) * (1 - fraction))
    return f"#{r:02X}{g:02X}{b:02X}"


# ============================================================================
# 5. PAGES
# ============================================================================

class DashboardPage(QWidget):
    def __init__(self, db, on_new_analysis, theme_palette, on_change=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.on_new_analysis = on_new_analysis
        self.palette = theme_palette
        self.on_change = on_change

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel("🏆 Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Overview of athlete injury risk assessments")
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        new_btn = QPushButton("➕  New Analysis")
        new_btn.setObjectName("primaryBtn")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self.on_new_analysis)
        header_row.addWidget(new_btn, alignment=Qt.AlignVCenter)
        outer.addLayout(header_row)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(16)
        outer.addLayout(self.kpi_row)

        outer.addWidget(SectionHeading("🕒 Recent Assessments"))

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Athlete", "Sport", "Risk Score", "Category", "Pro Care?", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 44)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table, stretch=1)

        self.refresh()

    def refresh(self):
        stats = self.db.stats_summary()
        while self.kpi_row.count():
            item = self.kpi_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        p = self.palette
        cards = [
            ("📊", str(stats["total"]), "Total Assessments", p["accent"]),
            ("⚖️", f"{stats['avg_score']}/100", "Average Risk Score", p["accent2"]),
            ("🚨", str(stats["high_risk_count"]), "High / Critical Cases", p["critical"]),
            ("🩺", str(stats["professional_needed"]), "Need Professional Care", p["moderate"]),
        ]
        for emoji, value, label, color in cards:
            self.kpi_row.addWidget(KpiCard(emoji, value, label, color))

        rows = self.db.fetch_all()[:12]
        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            values = [rec["timestamp"], rec["athlete_name"] or "—", rec["sport"],
                      f"{rec['score']}/100", rec["category"], "Yes" if rec["needs_professional"] else "No"]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter if c not in (1, 2) else Qt.AlignLeft | Qt.AlignVCenter)
                if c == 4:
                    item.setForeground(QColor(category_color(p, val)))
                self.table.setItem(r, c, item)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("dangerBtn")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip("Delete")
            del_btn.setFixedWidth(36)
            del_btn.setStyleSheet(
                f"QPushButton {{ background-color: {p['critical']}; color: white; font-weight: 700; "
                f"font-size: 13px; padding: 4px 0px; border-radius: 6px; border: none; }}"
            )
            del_btn.clicked.connect(lambda _, rid=rec["id"], name=rec["athlete_name"]: self.delete_single(rid, name))
            self.table.setCellWidget(r, 6, del_btn)

        if not rows:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("No assessments yet — click 'New Analysis' to get started 🚀")
            empty.setTextAlignment(Qt.AlignCenter)
            self.table.setSpan(0, 0, 1, 7)
            self.table.setItem(0, 0, empty)

    def delete_single(self, record_id: int, athlete_name: str):
        confirm = QMessageBox.question(
            self, "Delete Assessment",
            f"Delete this assessment for {athlete_name or 'this athlete'} permanently?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_by_id(record_id)
            self.refresh()
            if self.on_change:
                self.on_change()


class NewAnalysisPage(QWidget):
    def __init__(self, db, theme_palette, on_saved, parent=None):
        super().__init__(parent)
        self.db = db
        self.palette = theme_palette
        self.on_saved = on_saved
        self.last_result = None
        self.last_input = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(12)

        title = QLabel("🧪 New Injury Risk Analysis")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Fill in the athlete's profile to generate a personalized risk report")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(20)
        outer.addLayout(body, stretch=1)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.NoFrame)
        form_container = QFrame()
        form_container.setObjectName("card")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(10)
        form_scroll.setWidget(form_container)
        body.addWidget(form_scroll, stretch=5)

        form_layout.addWidget(SectionHeading("👤 Athlete Profile"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        row = 0

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Alex Morgan")
        grid.addWidget(QLabel("Athlete Name:"), row, 0)
        grid.addWidget(self.name_edit, row, 1); row += 1

        self.sport_combo = QComboBox()
        self.sport_combo.addItems(list(SPORT_PROFILES.keys()))
        grid.addWidget(QLabel("Sport / Discipline:"), row, 0)
        grid.addWidget(self.sport_combo, row, 1); row += 1

        self.age_combo = QComboBox()
        self.age_combo.addItems(AGE_GROUPS)
        self.age_combo.setCurrentIndex(1)
        grid.addWidget(QLabel("Age Group:"), row, 0)
        grid.addWidget(self.age_combo, row, 1); row += 1

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(100, 230)
        self.height_spin.setValue(175)
        self.height_spin.setSuffix(" cm")
        grid.addWidget(QLabel("Height:"), row, 0)
        grid.addWidget(self.height_spin, row, 1); row += 1

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(30, 200)
        self.weight_spin.setValue(72)
        self.weight_spin.setSuffix(" kg")
        grid.addWidget(QLabel("Weight:"), row, 0)
        grid.addWidget(self.weight_spin, row, 1); row += 1

        form_layout.addLayout(grid)
        form_layout.addWidget(SectionHeading("🏋️ Training Load"))
        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(16)
        grid2.setVerticalSpacing(10)
        row = 0

        self.training_hours = QDoubleSpinBox()
        self.training_hours.setRange(0, 40)
        self.training_hours.setValue(10)
        self.training_hours.setSuffix(" hrs/week")
        grid2.addWidget(QLabel("Training Volume:"), row, 0)
        grid2.addWidget(self.training_hours, row, 1); row += 1

        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(INTENSITY_LEVELS)
        self.intensity_combo.setCurrentIndex(1)
        grid2.addWidget(QLabel("Training Intensity:"), row, 0)
        grid2.addWidget(self.intensity_combo, row, 1); row += 1

        self.rest_days = QSpinBox()
        self.rest_days.setRange(0, 7)
        self.rest_days.setValue(2)
        grid2.addWidget(QLabel("Rest Days / Week:"), row, 0)
        grid2.addWidget(self.rest_days, row, 1); row += 1

        self.phase_combo = QComboBox()
        self.phase_combo.addItems(COMPETITION_PHASES)
        grid2.addWidget(QLabel("Competition Phase:"), row, 0)
        grid2.addWidget(self.phase_combo, row, 1); row += 1

        form_layout.addLayout(grid2)
        form_layout.addWidget(SectionHeading("💤 Recovery & Wellness"))
        grid3 = QGridLayout()
        grid3.setHorizontalSpacing(16)
        grid3.setVerticalSpacing(10)
        row = 0

        self.sleep_hours = QDoubleSpinBox()
        self.sleep_hours.setRange(3, 12)
        self.sleep_hours.setValue(7.5)
        self.sleep_hours.setSuffix(" hrs/night")
        grid3.addWidget(QLabel("Average Sleep:"), row, 0)
        grid3.addWidget(self.sleep_hours, row, 1); row += 1

        self.flexibility = QSpinBox()
        self.flexibility.setRange(1, 10)
        self.flexibility.setValue(6)
        grid3.addWidget(QLabel("Flexibility / Mobility (1-10):"), row, 0)
        grid3.addWidget(self.flexibility, row, 1); row += 1

        self.stress = QSpinBox()
        self.stress.setRange(1, 10)
        self.stress.setValue(4)
        grid3.addWidget(QLabel("Stress / Mental Fatigue (1-10):"), row, 0)
        grid3.addWidget(self.stress, row, 1); row += 1

        self.hydration = QSpinBox()
        self.hydration.setRange(1, 10)
        self.hydration.setValue(7)
        grid3.addWidget(QLabel("Hydration Level (1-10):"), row, 0)
        grid3.addWidget(self.hydration, row, 1); row += 1

        form_layout.addLayout(grid3)
        form_layout.addWidget(SectionHeading("🩹 Injury History & Habits"))
        grid4 = QGridLayout()
        grid4.setHorizontalSpacing(16)
        grid4.setVerticalSpacing(10)
        row = 0

        self.prior_injuries = QSpinBox()
        self.prior_injuries.setRange(0, 10)
        grid4.addWidget(QLabel("Injuries in Last 12 Months:"), row, 0)
        grid4.addWidget(self.prior_injuries, row, 1); row += 1

        self.days_since_injury = QSpinBox()
        self.days_since_injury.setRange(0, 999)
        self.days_since_injury.setValue(999)
        self.days_since_injury.setSpecialValueText("N/A (no recent injury)")
        grid4.addWidget(QLabel("Days Since Last Injury:"), row, 0)
        grid4.addWidget(self.days_since_injury, row, 1); row += 1

        self.warmup_check = QCheckBox("Consistently performs a proper warm-up")
        self.warmup_check.setChecked(True)
        grid4.addWidget(self.warmup_check, row, 0, 1, 2); row += 1

        self.equipment_check = QCheckBox("Uses proper / well-maintained equipment")
        self.equipment_check.setChecked(True)
        grid4.addWidget(self.equipment_check, row, 0, 1, 2); row += 1

        form_layout.addLayout(grid4)

        analyze_btn = QPushButton("🔍  Analyze Injury Risk")
        analyze_btn.setObjectName("primaryBtn")
        analyze_btn.setCursor(Qt.PointingHandCursor)
        analyze_btn.clicked.connect(self.run_analysis)
        form_layout.addWidget(analyze_btn)
        form_layout.addStretch()

        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setFrameShape(QFrame.NoFrame)
        self.result_container = QFrame()
        self.result_container.setObjectName("card")
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(20, 18, 20, 18)
        self.result_layout.setSpacing(10)
        result_scroll.setWidget(self.result_container)
        body.addWidget(result_scroll, stretch=6)

        self._build_placeholder()

    def _clear_results(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _build_placeholder(self):
        self._clear_results()
        self.result_layout.addWidget(SectionHeading("📋 Risk Report"))
        placeholder = QLabel("👇 Complete the form and click 'Analyze Injury Risk' to generate\n"
                              "a full personalized report with gauge, factor breakdown,\n"
                              "prevention plan, and a reassessment timeline. 💡")
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet("padding: 50px 18px; font-size: 14px; font-weight: 500; background-color: transparent;")
        placeholder.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(placeholder)
        self.result_layout.addStretch()

    def run_analysis(self):
        sport = self.sport_combo.currentText()
        inp = AthleteInput(
            name=self.name_edit.text().strip() or "Unnamed Athlete",
            sport=sport, age_group=self.age_combo.currentText(),
            height_cm=self.height_spin.value(), weight_kg=self.weight_spin.value(),
            training_hours_week=self.training_hours.value(), intensity=self.intensity_combo.currentText(),
            rest_days_week=self.rest_days.value(), sleep_hours=self.sleep_hours.value(),
            prior_injuries_12mo=self.prior_injuries.value(),
            days_since_last_injury=self.days_since_injury.value(),
            flexibility_score=self.flexibility.value(), stress_level=self.stress.value(),
            hydration_level=self.hydration.value(), warms_up=self.warmup_check.isChecked(),
            proper_equipment=self.equipment_check.isChecked(),
            competition_phase=self.phase_combo.currentText(),
        )
        result = calculate_risk(inp)
        self.last_result = result
        self.last_input = inp
        self._render_result(inp, result)

        record = {
            "timestamp": result.timestamp, "athlete_name": inp.name, "sport": inp.sport,
            "age_group": inp.age_group, "score": result.score, "category": result.category,
            "urgency": result.urgency, "needs_professional": result.needs_professional,
            "bmi": result.bmi, "bmi_category": result.bmi_category,
            "reassess_days": result.reassess_days,
            "details": {"recommendations": result.recommendations, "breakdown": result.factor_breakdown,
                        "prevention_plan": result.prevention_plan},
        }
        self.db.insert_assessment(record)
        if self.on_saved:
            self.on_saved()

    def _render_result(self, inp, result):
        self._clear_results()
        p = self.palette
        color = category_color(p, result.category)

        top_row = QHBoxLayout()
        top_row.addWidget(SectionHeading("📋 Risk Report"))
        top_row.addStretch()
        pdf_btn = QPushButton("🖨️  Export PDF Report")
        pdf_btn.setObjectName("secondaryBtn")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.clicked.connect(self.export_pdf)
        top_row.addWidget(pdf_btn)
        self.result_layout.addLayout(top_row)

        header = QHBoxLayout()
        header.setSpacing(18)
        gauge = RiskGauge()
        gauge.set_score(result.score, color, result.category.upper())
        header.addWidget(gauge, 0, Qt.AlignTop)

        info_col = QVBoxLayout()
        info_col.setSpacing(8)
        name_label = QLabel(f"{result.emoji} {inp.name} — {inp.sport}")
        name_label.setStyleSheet("font-size: 17px; font-weight: 800; background-color: transparent;")
        name_label.setWordWrap(True)
        info_col.addWidget(name_label)

        cat_label = QLabel(f"Risk Category: <b style='color:{color}'>{result.category}</b>  |  "
                            f"Urgency: <b>{result.urgency}/10</b>")
        cat_label.setStyleSheet("font-size: 13.5px; background-color: transparent;")
        info_col.addWidget(cat_label)

        bmi_label = QLabel(f"BMI: {result.bmi} ({result.bmi_category})")
        bmi_label.setStyleSheet("font-size: 12.5px; background-color: transparent;")
        info_col.addWidget(bmi_label)

        if result.needs_professional:
            pro_label = QLabel("🩺 Professional sports-medicine consultation recommended")
            pro_label.setStyleSheet(f"color: {p['critical']}; font-weight: 700; font-size: 12.5px; background-color: transparent;")
        else:
            pro_label = QLabel("✅ No immediate professional consultation flagged")
            pro_label.setStyleSheet(f"color: {p['low']}; font-weight: 700; font-size: 12.5px; background-color: transparent;")
        pro_label.setWordWrap(True)
        info_col.addWidget(pro_label)
        info_col.addStretch()
        header.addLayout(info_col, stretch=1)
        self.result_layout.addLayout(header)

        # --- Reassessment timeline (feature) ---
        self.result_layout.addWidget(SectionHeading("⏱️ Recommended Reassessment"))
        reassess_date = (datetime.now() + timedelta(days=result.reassess_days)).strftime("%b %d, %Y")
        reassess_label = QLabel(
            f"Reassess in <b>{result.reassess_days} day(s)</b> — around <b>{reassess_date}</b>.<br>{result.reassess_note}"
        )
        reassess_label.setWordWrap(True)
        reassess_label.setStyleSheet("font-size: 12.5px; background-color: transparent;")
        self.result_layout.addWidget(reassess_label)

        self.result_layout.addWidget(SectionHeading("📊 Contributing Factors"))
        max_pts = max((f["points"] for f in result.factor_breakdown), default=1) or 1
        for f in sorted(result.factor_breakdown, key=lambda x: -x["points"]):
            row = QVBoxLayout()
            row.setSpacing(4)
            lbl = QLabel(f"{f['factor']}  —  {f['note']}")
            lbl.setStyleSheet("font-size: 11.5px; background-color: transparent;")
            row.addWidget(lbl)
            bar = QProgressBar()
            bar.setRange(0, 100)
            pct = int((f["points"] / max_pts) * 100)
            bar.setValue(pct)
            bar.setFormat(f"{f['points']:.1f} pts")
            bar.setTextVisible(True)
            bar_color = shade_by_magnitude(color, pct / 100.0)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {bar_color}; }}")
            row.addWidget(bar)
            self.result_layout.addLayout(row)

        self.result_layout.addWidget(SectionHeading("⚠️ Common Injury Risks for This Sport"))
        injuries_text = "  •  ".join(result.common_injuries)
        inj_label = QLabel(injuries_text)
        inj_label.setWordWrap(True)
        inj_label.setStyleSheet("font-size: 12.5px; background-color: transparent;")
        self.result_layout.addWidget(inj_label)

        regions_text = "🎯 Focus Regions: " + ", ".join(result.focus_regions)
        regions_label = QLabel(regions_text)
        regions_label.setStyleSheet("font-style: italic; font-size: 12px; padding-top: 4px; background-color: transparent;")
        self.result_layout.addWidget(regions_label)

        # --- Injury-specific prevention plan (feature) ---
        self.result_layout.addWidget(SectionHeading("🛡️ Injury-Specific Prevention Plan"))
        for item in result.prevention_plan:
            line = QLabel(f"• <b>{item['injury']}</b> — {item['exercise']}")
            line.setWordWrap(True)
            line.setStyleSheet("padding: 3px 0; font-size: 12px; background-color: transparent;")
            self.result_layout.addWidget(line)

        self.result_layout.addWidget(SectionHeading("💡 Personalized Recommendations"))
        for rec in result.recommendations:
            rec_label = QLabel(f"• {rec}")
            rec_label.setWordWrap(True)
            rec_label.setStyleSheet("padding: 3px 0; font-size: 12.5px; background-color: transparent;")
            self.result_layout.addWidget(rec_label)

        self.result_layout.addStretch()

    def export_pdf(self):
        if not self.last_result or not self.last_input:
            QMessageBox.information(self, "Export PDF", "Run an analysis first.")
            return
        result, inp = self.last_result, self.last_input
        default_name = f"{inp.name.replace(' ', '_')}_risk_report.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", default_name, "PDF Files (*.pdf)")
        if not path:
            return

        factors_html = "".join(
            f"<li><b>{f['factor']}</b> ({f['points']} pts) — {f['note']}</li>"
            for f in sorted(result.factor_breakdown, key=lambda x: -x['points'])
        )
        prevention_html = "".join(
            f"<li><b>{item['injury']}</b> — {item['exercise']}</li>" for item in result.prevention_plan
        )
        recs_html = "".join(f"<li>{r}</li>" for r in result.recommendations)
        reassess_date = (datetime.now() + timedelta(days=result.reassess_days)).strftime("%b %d, %Y")

        html = f"""
        <h1 style="color:#2563EB;">🏥 Athlete Injury Risk Report</h1>
        <p><b>Athlete:</b> {inp.name} &nbsp;&nbsp; <b>Sport:</b> {inp.sport}</p>
        <p><b>Assessment Date:</b> {result.timestamp}</p>
        <h2>Risk Score: {result.score}/100 — {result.category}</h2>
        <p><b>Urgency:</b> {result.urgency}/10 &nbsp;&nbsp; <b>BMI:</b> {result.bmi} ({result.bmi_category})</p>
        <p><b>Professional care needed:</b> {"Yes" if result.needs_professional else "No"}</p>
        <h3>⏱️ Recommended Reassessment</h3>
        <p>Reassess in {result.reassess_days} day(s), around {reassess_date}. {result.reassess_note}</p>
        <h3>📊 Contributing Factors</h3>
        <ul>{factors_html}</ul>
        <h3>🛡️ Injury-Specific Prevention Plan</h3>
        <ul>{prevention_html}</ul>
        <h3>💡 Personalized Recommendations</h3>
        <ul>{recs_html}</ul>
        <p style="font-size:11px;color:#888;">This report is an educational decision-support tool and is not a
        medical diagnosis. Always consult a licensed medical professional for treatment decisions.</p>
        """

        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        doc.print_(printer)
        QMessageBox.information(self, "Export Complete", f"✅ PDF report saved to:\n{path}")


class HistoryPage(QWidget):
    def __init__(self, db, theme_palette, on_change, parent=None):
        super().__init__(parent)
        self.db = db
        self.palette = theme_palette
        self.on_change = on_change

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        title = QLabel("📚 History")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Every past injury risk assessment, searchable and exportable")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(QLabel("Filter by Sport:"))
        self.sport_filter = QComboBox()
        self.sport_filter.addItem("All")
        self.sport_filter.addItems(list(SPORT_PROFILES.keys()))
        self.sport_filter.currentIndexChanged.connect(self.refresh)
        controls.addWidget(self.sport_filter)

        controls.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by athlete name…")
        self.search_edit.textChanged.connect(self.refresh)
        controls.addWidget(self.search_edit, stretch=1)

        clear_btn = QPushButton("🗑️  Clear History")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_history)
        controls.addWidget(clear_btn)

        export_btn = QPushButton("📤  Export All (JSON)")
        export_btn.setObjectName("secondaryBtn")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self.export_json)
        controls.addWidget(export_btn)

        outer.addLayout(controls)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Athlete", "Sport", "Risk Score", "Urgency", "Category", "Pro Care?", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 44)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table, stretch=1)

        self._current_rows = []
        self.refresh()

    def refresh(self):
        sport = self.sport_filter.currentText()
        search = self.search_edit.text().strip().lower()

        rows = self.db.fetch_all()
        if sport != "All":
            rows = [r for r in rows if r["sport"] == sport]
        if search:
            rows = [r for r in rows if search in (r["athlete_name"] or "").lower()]

        self._current_rows = rows
        p = self.palette

        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            values = [rec["timestamp"], rec["athlete_name"] or "—", rec["sport"],
                      f"{rec['score']}/100", f"{rec['urgency']}/10", rec["category"],
                      "Yes" if rec["needs_professional"] else "No"]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter if c not in (1, 2) else Qt.AlignLeft | Qt.AlignVCenter)
                if c == 5:
                    item.setForeground(QColor(category_color(p, val)))
                self.table.setItem(r, c, item)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("dangerBtn")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip("Delete")
            del_btn.setFixedWidth(36)
            del_btn.setStyleSheet(
                f"QPushButton {{ background-color: {p['critical']}; color: white; font-weight: 700; "
                f"font-size: 13px; padding: 4px 0px; border-radius: 6px; border: none; }}"
            )
            del_btn.clicked.connect(lambda _, rid=rec["id"], name=rec["athlete_name"]: self.delete_single(rid, name))
            self.table.setCellWidget(r, 7, del_btn)

        if not rows:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("No matching assessments found.")
            empty.setTextAlignment(Qt.AlignCenter)
            self.table.setSpan(0, 0, 1, 8)
            self.table.setItem(0, 0, empty)

    def delete_single(self, record_id: int, athlete_name: str):
        confirm = QMessageBox.question(
            self, "Delete Assessment",
            f"Delete this assessment for {athlete_name or 'this athlete'} permanently?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_by_id(record_id)
            self.refresh()
            if self.on_change:
                self.on_change()

    def clear_history(self):
        confirm = QMessageBox.question(
            self, "Clear History", "⚠️ This will permanently delete all saved assessments. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.clear_all()
            self.refresh()
            if self.on_change:
                self.on_change()

    def export_json(self):
        rows = self.db.fetch_all()
        if not rows:
            QMessageBox.information(self, "Export", "There is no history to export yet.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export History as JSON", "injury_risk_history.json",
                                               "JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=str)
            QMessageBox.information(self, "Export Complete", f"✅ Exported {len(rows)} record(s) to:\n{path}")


class StatisticsPage(QWidget):
    def __init__(self, db, theme_palette, parent=None):
        super().__init__(parent)
        self.db = db
        self.palette = theme_palette

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        title = QLabel("📈 Statistics")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Trends and distributions across all recorded assessments")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(16)
        outer.addLayout(self.kpi_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)
        outer.addLayout(charts_row, stretch=1)

        pie_card = QFrame()
        pie_card.setObjectName("card")
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setContentsMargins(16, 14, 16, 14)
        pie_layout.addWidget(SectionHeading("🥧 Risk Category Distribution"))
        self.pie_fig = Figure(figsize=(4.4, 3.4), dpi=100)
        self.pie_canvas = FigureCanvas(self.pie_fig)
        self.pie_canvas.setMinimumHeight(220)
        pie_layout.addWidget(self.pie_canvas)
        charts_row.addWidget(pie_card, stretch=1)

        bar_card = QFrame()
        bar_card.setObjectName("card")
        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(16, 14, 16, 14)
        bar_layout.addWidget(SectionHeading("🏅 Assessments by Sport"))
        self.bar_fig = Figure(figsize=(4.4, 3.4), dpi=100)
        self.bar_canvas = FigureCanvas(self.bar_fig)
        self.bar_canvas.setMinimumHeight(220)
        bar_layout.addWidget(self.bar_canvas)
        charts_row.addWidget(bar_card, stretch=1)

        trend_card = QFrame()
        trend_card.setObjectName("card")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(16, 14, 16, 14)
        trend_layout.addWidget(SectionHeading("📉 Risk Score Trend (Most Recent Assessments)"))
        self.trend_fig = Figure(figsize=(9, 2.8), dpi=100)
        self.trend_canvas = FigureCanvas(self.trend_fig)
        self.trend_canvas.setMinimumHeight(190)
        trend_layout.addWidget(self.trend_canvas)
        outer.addWidget(trend_card)

        self.refresh()

    def refresh(self):
        stats = self.db.stats_summary()
        rows = self.db.fetch_all()
        p = self.palette

        while self.kpi_row.count():
            item = self.kpi_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cards = [
            ("📊", str(stats["total"]), "Total Assessments", p["accent"]),
            ("⚖️", f"{stats['avg_score']}/100", "Average Risk Score", p["accent2"]),
            ("🚨", str(stats["high_risk_count"]), "High / Critical Cases", p["critical"]),
            ("🩺", str(stats["professional_needed"]), "Professional Care Flags", p["moderate"]),
        ]
        for emoji, value, label, color in cards:
            self.kpi_row.addWidget(KpiCard(emoji, value, label, color))

        # --- Pie chart: percentages sit inside the wedges, category names & counts
        #     move to a side legend so nothing overlaps the chart. ---
        self.pie_fig.clear()
        ax1 = self.pie_fig.add_subplot(111)
        by_cat = stats["by_category"]
        if by_cat:
            labels = list(by_cat.keys())
            sizes = list(by_cat.values())
            colors = [category_color(p, l) for l in labels]
            wedges, _, autotexts = ax1.pie(
                sizes, colors=colors, autopct="%1.0f%%", pctdistance=0.75, startangle=90,
                wedgeprops={"linewidth": 1.5, "edgecolor": p["card"]},
                textprops={"color": "white", "fontsize": 8, "fontweight": "bold"},
            )
            ax1.legend(wedges, [f"{l} ({c})" for l, c in zip(labels, sizes)],
                       loc="center left", bbox_to_anchor=(1.0, 0.5),
                       fontsize=8, frameon=False, labelcolor=p["text"])
        else:
            ax1.text(0.5, 0.5, "No data yet", ha="center", va="center", color=p["muted"])
            ax1.axis("off")
        themed_axes_style(ax1, self.pie_fig, p)
        self.pie_fig.subplots_adjust(left=0.02, right=0.62, top=0.94, bottom=0.06)
        self.pie_canvas.draw()

        # --- Bar chart: smaller rotated labels + value totals above each bar,
        #     with extra headroom so nothing collides. ---
        self.bar_fig.clear()
        ax2 = self.bar_fig.add_subplot(111)
        by_sport = stats["by_sport"]
        if by_sport:
            labels = [s.split(" ", 1)[-1] if " " in s else s for s in by_sport.keys()]
            values = list(by_sport.values())
            bars = ax2.bar(labels, values, color=p["accent"])
            ax2.bar_label(bars, fontsize=7.5, color=p["text"], padding=2)
            ax2.set_ylim(0, max(values) * 1.3)
            ax2.tick_params(axis="x", labelsize=7.5)
            for lbl in ax2.get_xticklabels():
                lbl.set_rotation(40)
                lbl.set_ha("right")
                lbl.set_rotation_mode("anchor")
            ax2.tick_params(axis="y", labelsize=8)
        else:
            ax2.text(0.5, 0.5, "No data yet", ha="center", va="center", color=p["muted"])
            ax2.axis("off")
        themed_axes_style(ax2, self.bar_fig, p)
        self.bar_fig.subplots_adjust(left=0.14, right=0.96, top=0.90, bottom=0.36)
        self.bar_canvas.draw()

        # --- Trend chart: smaller tick/legend text and extra vertical
        #     headroom so the threshold legend never sits on top of the line. ---
        self.trend_fig.clear()
        ax3 = self.trend_fig.add_subplot(111)
        recent = list(reversed(rows[:25]))
        if recent:
            x = list(range(1, len(recent) + 1))
            y = [r["score"] for r in recent]
            ax3.plot(x, y, marker="o", color=p["accent"], linewidth=1.8, markersize=4)
            ax3.axhline(50, color=p["moderate"], linestyle="--", linewidth=1.0, label="High-risk threshold (50)")
            ax3.set_ylim(0, 112)
            ax3.set_xlabel("Assessment #", fontsize=9)
            ax3.set_ylabel("Risk Score", fontsize=9)
            ax3.tick_params(labelsize=8)
            ax3.legend(fontsize=8, facecolor=p["card"], labelcolor=p["text"], loc="upper right", frameon=False)
        else:
            ax3.text(0.5, 0.5, "No data yet — run some analyses first", ha="center", va="center", color=p["muted"])
            ax3.axis("off")
        themed_axes_style(ax3, self.trend_fig, p)
        self.trend_fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.22)
        self.trend_canvas.draw()


class AthleteTrendsPage(QWidget):
    """Feature: track one athlete's risk score across multiple assessments."""

    def __init__(self, db, theme_palette, parent=None):
        super().__init__(parent)
        self.db = db
        self.palette = theme_palette

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        title = QLabel("🧍 Athlete Trends")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Track how a specific athlete's risk profile changes over time")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(QLabel("Select Athlete:"))
        self.athlete_combo = QComboBox()
        self.athlete_combo.currentIndexChanged.connect(self.refresh_selected)
        controls.addWidget(self.athlete_combo, stretch=1)
        outer.addLayout(controls)

        body = QHBoxLayout()
        body.setSpacing(18)
        outer.addLayout(body, stretch=1)

        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 14, 16, 14)
        chart_layout.addWidget(SectionHeading("📈 Risk Score Over Time"))
        self.fig = Figure(figsize=(5.6, 3.6), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumHeight(220)
        chart_layout.addWidget(self.canvas)
        body.addWidget(chart_card, stretch=3)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(18, 16, 18, 16)
        info_layout.setSpacing(10)
        info_layout.addWidget(SectionHeading("📌 Latest Snapshot"))
        self.snapshot_label = QLabel("Select an athlete with recorded assessments to see their trend.")
        self.snapshot_label.setWordWrap(True)
        self.snapshot_label.setStyleSheet("font-size: 13px; background-color: transparent;")
        info_layout.addWidget(self.snapshot_label)
        info_layout.addStretch()
        body.addWidget(info_card, stretch=2)

        self.refresh()

    def refresh(self):
        rows = self.db.fetch_all()
        names = sorted({r["athlete_name"] for r in rows if r["athlete_name"]})
        current = self.athlete_combo.currentText()
        self.athlete_combo.blockSignals(True)
        self.athlete_combo.clear()
        self.athlete_combo.addItems(names if names else ["No athletes yet"])
        idx = self.athlete_combo.findText(current)
        if idx >= 0:
            self.athlete_combo.setCurrentIndex(idx)
        self.athlete_combo.blockSignals(False)
        self.refresh_selected()

    def refresh_selected(self):
        p = self.palette
        name = self.athlete_combo.currentText()
        rows = [r for r in self.db.fetch_all() if r["athlete_name"] == name]
        rows = list(reversed(rows))  # chronological order

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        if rows and name and name != "No athletes yet":
            x = list(range(1, len(rows) + 1))
            y = [r["score"] for r in rows]
            ax.plot(x, y, marker="o", color=p["accent"], linewidth=1.8, markersize=5)
            ax.axhline(50, color=p["moderate"], linestyle="--", linewidth=1.0, label="High-risk threshold (50)")
            ax.set_ylim(0, 112)
            ax.set_xlabel("Assessment #", fontsize=9)
            ax.set_ylabel("Risk Score", fontsize=9)
            ax.tick_params(labelsize=8)
            ax.legend(fontsize=8, facecolor=p["card"], labelcolor=p["text"], loc="upper right", frameon=False)

            latest = rows[-1]
            trend = "— (first assessment on record)"
            if len(rows) >= 2:
                delta = rows[-1]["score"] - rows[-2]["score"]
                if delta > 0:
                    trend = f"⬆️ Up {delta:.1f} pts since previous check-in"
                elif delta < 0:
                    trend = f"⬇️ Down {abs(delta):.1f} pts since previous check-in"
                else:
                    trend = "➡️ No change since previous check-in"
            snapshot = (
                f"<b style='font-size:14.5px;'>{name}</b><br>{latest['sport']}<br><br>"
                f"Latest Score: <b>{latest['score']}/100</b> ({latest['category']})<br><br>"
                f"Assessments on record: <b>{len(rows)}</b><br><br>"
                f"Trend: {trend}<br><br>"
                f"Professional care flagged: <b>{'Yes' if latest['needs_professional'] else 'No'}</b>"
            )
            self.snapshot_label.setText(snapshot)
        else:
            ax.text(0.5, 0.5, "No data for this athlete yet", ha="center", va="center", color=p["muted"])
            ax.axis("off")
            self.snapshot_label.setText("Select an athlete with recorded assessments to see their trend.")
        themed_axes_style(ax, self.fig, p)
        self.fig.subplots_adjust(left=0.11, right=0.97, top=0.90, bottom=0.16)
        self.canvas.draw()


class AlertsPage(QWidget):
    """Feature: surfaces athletes who are overdue for reassessment or need follow-up care."""

    def __init__(self, db, theme_palette, parent=None):
        super().__init__(parent)
        self.db = db
        self.palette = theme_palette

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        title = QLabel("🚨 Follow-Up Alerts")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Athletes who need reassessment or professional care, sorted by urgency")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(16)
        outer.addLayout(self.kpi_row)

        outer.addWidget(SectionHeading("📋 Action Needed"))

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Athlete", "Sport", "Risk Score", "Category", "Reassess By", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table, stretch=1)

        self.refresh()

    def refresh(self):
        p = self.palette
        rows = self.db.fetch_all()
        now = datetime.now()
        flagged = []
        for r in rows:
            try:
                ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                continue
            reassess_days = r.get("reassess_days") or REASSESS_DAYS_MAP.get(r["category"], 14)
            due_date = ts + timedelta(days=reassess_days)
            overdue_days = (now - due_date).days
            is_flagged = bool(r["needs_professional"]) or r["category"] in ("High", "Critical") or overdue_days > 0
            if is_flagged:
                flagged.append((r, due_date, overdue_days))

        flagged.sort(key=lambda t: (-t[0]["score"], -t[2]))

        while self.kpi_row.count():
            item = self.kpi_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        overdue_now = sum(1 for _, _, od in flagged if od > 0)
        due_soon = sum(1 for _, due, od in flagged if od <= 0 and (due - now).days <= 7)
        cards = [
            ("🚨", str(len(flagged)), "Total Flagged Athletes", p["critical"]),
            ("⏰", str(overdue_now), "Reassessment Overdue", p["moderate"]),
            ("📅", str(due_soon), "Due Within 7 Days", p["accent"]),
        ]
        for emoji, value, label, color in cards:
            self.kpi_row.addWidget(KpiCard(emoji, value, label, color))

        self.table.setRowCount(len(flagged))
        for i, (r, due, overdue_days) in enumerate(flagged):
            status = f"Overdue {overdue_days}d" if overdue_days > 0 else f"Due in {abs(overdue_days)}d"
            if r["needs_professional"]:
                status += "  •  See Professional"
            values = [r["athlete_name"] or "—", r["sport"], f"{r['score']}/100",
                      r["category"], due.strftime("%Y-%m-%d"), status]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter if c not in (0, 1) else Qt.AlignLeft | Qt.AlignVCenter)
                if c == 3:
                    item.setForeground(QColor(category_color(p, val)))
                if c == 5 and overdue_days > 0:
                    item.setForeground(QColor(p["critical"]))
                self.table.setItem(i, c, item)

        if not flagged:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("✅ No athletes are currently flagged for follow-up.")
            empty.setTextAlignment(Qt.AlignCenter)
            self.table.setSpan(0, 0, 1, 6)
            self.table.setItem(0, 0, empty)


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 26, 32, 26)
        outer.setSpacing(16)

        title = QLabel("ℹ️ About")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Athlete Injury Risk Predictor — Advanced Edition")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll, stretch=1)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        card_layout.setSpacing(14)
        scroll.setWidget(card)

        card_layout.addWidget(SectionHeading("🏆 What This App Does"))
        desc = QLabel(
            "This tool estimates an athlete's short-term injury risk using a transparent, "
            "multi-factor heuristic model that draws on well-established sports-medicine "
            "risk factors.\n\n"
            "Those factors include training load, recovery, sleep, prior injury history, "
            "body composition, mobility, hydration, stress, and sport-specific demand "
            "profiles.\n\n"
            "It supports 12 sport categories, each with tailored \u2018common injury\u2019, "
            "\u2018focus region\u2019, and \u2018injury-specific prevention exercise\u2019 guidance, and "
            "produces a personalized action plan alongside the numeric risk score."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; line-height: 150%; background-color: transparent;")
        card_layout.addWidget(desc)

        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet("color: rgba(0,0,0,25); margin: 4px 0;")
        card_layout.addWidget(divider1)

        card_layout.addWidget(SectionHeading("✨ Key Features"))
        features = QLabel(
            "1. Multi-factor injury risk score (0-100) with a fully transparent breakdown\n\n"
            "2. Injury-specific prevention exercise plan, tailored to the athlete's sport\n\n"
            "3. Recommended reassessment / follow-up timeline based on risk severity\n\n"
            "4. Athlete Trends page — track one athlete's risk profile over time\n\n"
            "5. Follow-Up Alerts page — surfaces overdue or high-priority athletes\n\n"
            "6. One-click PDF report export for any single assessment\n\n"
            "7. Searchable, filterable History with full JSON export\n\n"
            "8. Dashboard and Statistics pages with live pie / bar / trend charts\n\n"
            "9. Four polished visual themes across a medium-density, normal-window layout"
        )
        features.setWordWrap(True)
        features.setStyleSheet("font-size: 12.5px; line-height: 150%; background-color: transparent;")
        card_layout.addWidget(features)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet("color: rgba(0,0,0,25); margin: 4px 0;")
        card_layout.addWidget(divider2)

        card_layout.addWidget(SectionHeading("⚠️ Important Disclaimer"))
        disclaimer = QLabel(
            "This application is an educational / decision-support tool only.\n\n"
            "It is NOT a medical device and does NOT provide a clinical diagnosis.\n\n"
            "Always consult a licensed physician, physiotherapist, or athletic trainer "
            "for real injury evaluation, diagnosis, or treatment decisions."
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("font-style: italic; font-size: 12.5px; line-height: 150%; background-color: transparent;")
        card_layout.addWidget(disclaimer)

        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setStyleSheet("color: rgba(0,0,0,25); margin: 4px 0;")
        card_layout.addWidget(divider3)

        card_layout.addWidget(SectionHeading("🛠️ Built With"))
        tech = QLabel("Python 3   •   PyQt5   •   SQLite   •   Matplotlib   •   Qt Print Support")
        tech.setStyleSheet("font-size: 13px; background-color: transparent;")
        card_layout.addWidget(tech)

        card_layout.addSpacing(4)
        card_layout.addWidget(SectionHeading("📦 Version"))
        version = QLabel("v5.1 — Spectrum Redesign, Medium Density")
        version.setStyleSheet("font-size: 13px; background-color: transparent;")
        card_layout.addWidget(version)

        card_layout.addStretch()


# ============================================================================
# 6. MAIN WINDOW
# ============================================================================

NAV_ITEMS = [
    ("dashboard", "🏆  Dashboard"),
    ("new_analysis", "🧪  New Analysis"),
    ("history", "📚  History"),
    ("statistics", "📈  Statistics"),
    ("athlete_trends", "🧍  Athlete Trends"),
    ("alerts", "🚨  Follow-Up Alerts"),
    ("about", "ℹ️  About"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏥 Athlete Injury Risk Predictor — Advanced Edition")
        self.resize(1360, 860)
        self.setMinimumSize(1140, 720)

        self.db = Database()
        self.current_theme_name = "🌤️ Light Neutral"

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(18, 22, 18, 18)
        side_layout.setSpacing(4)

        brand = QLabel("🏋️ Injury Risk")
        brand.setObjectName("brandTitle")
        side_layout.addWidget(brand)
        brand_sub = QLabel("PREDICTOR — PRO")
        brand_sub.setObjectName("brandSubtitle")
        side_layout.addWidget(brand_sub)

        side_layout.addSpacing(14)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: rgba(0,0,0,40);")
        side_layout.addWidget(divider)
        side_layout.addSpacing(8)

        self.nav_buttons = {}
        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda _, k=key: self.navigate(k))
            side_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        side_layout.addStretch()

        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: 700; font-size: 12px; padding-top: 4px; background-color: transparent;")
        side_layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumHeight(32)
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        side_layout.addWidget(self.theme_combo)

        version_label = QLabel("v5.1 Spectrum Redesign")
        version_label.setStyleSheet("font-size: 10.5px; padding-top: 8px; background-color: transparent;")
        version_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(version_label)

        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        self.dashboard_page = DashboardPage(self.db, lambda: self.navigate("new_analysis"),
                                             THEMES[self.current_theme_name], on_change=self.on_data_changed)
        self.new_analysis_page = NewAnalysisPage(self.db, THEMES[self.current_theme_name],
                                                  on_saved=self.on_data_changed)
        self.history_page = HistoryPage(self.db, THEMES[self.current_theme_name],
                                         on_change=self.on_data_changed)
        self.statistics_page = StatisticsPage(self.db, THEMES[self.current_theme_name])
        self.athlete_trends_page = AthleteTrendsPage(self.db, THEMES[self.current_theme_name])
        self.alerts_page = AlertsPage(self.db, THEMES[self.current_theme_name])
        self.about_page = AboutPage()

        self.pages = {
            "dashboard": self.dashboard_page, "new_analysis": self.new_analysis_page,
            "history": self.history_page, "statistics": self.statistics_page,
            "athlete_trends": self.athlete_trends_page, "alerts": self.alerts_page,
            "about": self.about_page,
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.apply_theme(self.current_theme_name)
        self.navigate("dashboard")

    def navigate(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        for k, btn in self.nav_buttons.items():
            btn.setObjectName("navBtnActive" if k == key else "navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if key == "dashboard":
            self.dashboard_page.refresh()
        elif key == "history":
            self.history_page.refresh()
        elif key == "statistics":
            self.statistics_page.refresh()
        elif key == "athlete_trends":
            self.athlete_trends_page.refresh()
        elif key == "alerts":
            self.alerts_page.refresh()

    def on_data_changed(self):
        self.dashboard_page.refresh()
        self.history_page.refresh()
        self.statistics_page.refresh()
        self.athlete_trends_page.refresh()
        self.alerts_page.refresh()

    def apply_theme(self, theme_name):
        self.current_theme_name = theme_name
        palette = THEMES[theme_name]
        self.setStyleSheet(build_qss(palette))
        for page_attr in (self.dashboard_page, self.new_analysis_page, self.history_page,
                           self.statistics_page, self.athlete_trends_page, self.alerts_page):
            page_attr.palette = palette
        self.dashboard_page.refresh()
        self.history_page.refresh()
        self.statistics_page.refresh()
        self.athlete_trends_page.refresh()
        self.alerts_page.refresh()


def main():
    # Opt into proper High-DPI scaling *before* the QApplication is created.
    # Without this, PyQt renders in raw device pixels on high-resolution /
    # scaled displays, which is why everything can look tiny (or, combined
    # with unbounded widget sizes, wildly oversized) on a big monitor.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()