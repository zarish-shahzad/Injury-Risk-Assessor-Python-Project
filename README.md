# Injury-Risk-Assessor-Python-Project
A PyQt5 desktop app that scores athletes' injury risk from training, recovery, and health factors, then generates sport-specific prevention plans, trend tracking, and exportable PDF/JSON reports.


> A professional, single-file **PyQt5 desktop application** that estimates an athlete's short-term injury risk using a transparent, multi-factor, sports-medicine-inspired scoring engine — complete with prevention plans, trend tracking, follow-up alerts, and one-click PDF reports.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Charts-Matplotlib-11557C?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [How the Risk Engine Works](#-how-the-risk-engine-works)
- [Supported Sports](#-supported-sports)
- [Application Pages](#-application-pages)
- [Visual Themes](#-visual-themes)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Database Schema](#-database-schema)
- [Screenshots / UI Walkthrough](#-ui-walkthrough)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## 🌟 Overview

The **Athlete Injury Risk Predictor** is a decision-support tool designed for coaches, athletic trainers, physiotherapists, and athletes themselves. It combines well-established sports-medicine risk factors — training load, recovery, sleep, prior injury history, body composition, mobility, hydration, stress, and sport-specific demand profiles — into a single, transparent **0–100 risk score**.

Unlike a "black box" prediction, every point in the score is broken down and explained, so the user understands **exactly why** an athlete is flagged as high risk, and receives a **personalized, sport-specific prevention plan** in response.

The entire application — risk engine, database layer, UI themes, custom widgets, and all pages — is built as a **single, portable Python file** for easy distribution and execution.

---

## ✨ Key Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | 🧮 **Multi-Factor Risk Score** | A 0–100 injury risk score built from 13+ weighted factors, with a fully transparent, itemized breakdown |
| 2 | 🛡️ **Prevention Plans** | Injury-specific prevention exercises automatically tailored to the athlete's sport |
| 3 | ⏱️ **Reassessment Timeline** | Automatically recommends a follow-up date based on risk severity (3–30 days) |
| 4 | 🧍 **Athlete Trends** | Track a single athlete's risk score across multiple assessments over time |
| 5 | 🚨 **Follow-Up Alerts** | Surfaces overdue or high-priority athletes who need attention |
| 6 | 🖨️ **PDF Report Export** | One-click, professional PDF report generation for any assessment |
| 7 | 📚 **Searchable History** | Filter, search, and export all past assessments as JSON |
| 8 | 📊 **Dashboard & Statistics** | Live pie, bar, and trend charts summarizing all recorded data |
| 9 | 🎨 **Four Visual Themes** | Light, Dark, Ocean, and Forest themes — all with a comfortable, medium-density layout |

---

## 🧠 How the Risk Engine Works

The engine computes a composite score (clamped between **0–100**) from the following weighted factors:

| Factor | Considers | Max Impact |
|--------|-----------|-----------|
| 🏋️ Training Volume | Weekly training hours × sport load multiplier | ~26 pts |
| 🔥 Training Intensity | Self-reported intensity level | 15 pts |
| 😴 Recovery Days | Rest days per week | 15 pts |
| 💤 Sleep Quality | Average nightly sleep | 15 pts |
| 🩹 Injury History | Prior injuries in 12 months + recency | ~26 pts |
| 🧘 Flexibility / Mobility | Self-rated mobility score (1–10) | 9 pts |
| 🧠 Stress / Mental Fatigue | Self-rated stress score (1–10) | 8 pts |
| 💧 Hydration | Self-rated hydration score (1–10) | 6.3 pts |
| 🔥 Warm-up Routine | Whether the athlete warms up consistently | 6 pts |
| 👟 Equipment | Whether proper gear/footwear is used | 5 pts |
| ⚖️ Body Composition (BMI) | Height/weight-derived BMI category | 8 pts |
| 🎂 Age Group | Six age brackets, from Under-18 to 56+ | 8 pts |
| 📅 Competition Phase | Off-season → Playoffs / Peak Competition | 6 pts |
| 🏃 Sport Impact Profile | Structural/impact demand of the chosen sport | 10 pts |

### Risk Bands

| Score Range | Category | Indicator | Reassessment Window |
|:-----------:|:--------:|:---------:|:--------------------:|
| 0 – 24 | Low | 🟢 | Every 30 days |
| 25 – 49 | Moderate | 🟡 | Every 14 days |
| 50 – 74 | High | 🟠 | Every 7 days |
| 75 – 100 | Critical | 🔴 | Every 3 days |

Athletes are also flagged for **professional consultation** if their score is ≥ 50, they were injured within the last 14 days, or they've had 3+ injuries in the past year.

---

## 🏅 Supported Sports

The app includes tailored profiles — including load/impact multipliers, common injuries, focus regions, and prevention exercises — for **12 sports**:

| Sport | Common Injury Focus |
|-------|---------------------|
| 🏃 Running / Track & Field | Stress fractures, IT band syndrome, shin splints |
| ⚽ Football / Soccer | ACL tears, hamstring strains, ankle sprains |
| 🏀 Basketball | Ankle sprains, ACL/meniscus tears, jumper's knee |
| 🏋️ Weightlifting / Powerlifting | Lower back strain, rotator cuff injury, disc herniation |
| 🏊 Swimming | Swimmer's shoulder, rotator cuff strain |
| 🎾 Tennis / Racquet Sports | Tennis elbow, rotator cuff injury, ankle sprains |
| 🚴 Cycling | Patellofemoral pain, lower back pain, neck strain |
| 🤸 Gymnastics | Wrist stress injury, spondylolysis, shoulder instability |
| 🥊 Combat Sports (MMA/Boxing) | Concussion, hand/wrist fractures, rib fractures |
| 🔥 CrossFit / Functional Fitness | Shoulder impingement, knee tendinopathy, overtraining |
| ⚾ Baseball / Softball | UCL tear (Tommy John), rotator cuff injury, labrum tear |
| 🏐 Volleyball | Jumper's knee, ankle sprains, shoulder impingement |

---

## 🗂️ Application Pages

| Page | Purpose |
|------|---------|
| 🏆 **Dashboard** | KPI overview + recent assessments table with quick-delete |
| 🧪 **New Analysis** | Full athlete intake form → generates risk report, gauge, and PDF export |
| 📚 **History** | Searchable/filterable log of every assessment, with JSON export |
| 📈 **Statistics** | Pie chart (risk categories), bar chart (by sport), trend chart (recent scores) |
| 🧍 **Athlete Trends** | Per-athlete risk score history and change-over-time snapshot |
| 🚨 **Follow-Up Alerts** | Surfaces overdue reassessments and high-priority / professional-care cases |
| ℹ️ **About** | App description, feature list, disclaimer, and version info |

---

## 🎨 Visual Themes

| Theme | Vibe |
|-------|------|
| 🌤️ Light Neutral | Clean, bright, professional |
| 🌙 Midnight Dark | Low-light, modern dark mode |
| 🌊 Ocean Blue | Cool, calming blue palette |
| 🌲 Forest Pro | Earthy green, natural tone |

All four themes share consistent, color-blind-friendly severity colors (🟢 Low → 🟡 Moderate → 🟠 High → 🔴 Critical) so risk levels are always visually distinguishable.

---

## ⚙️ Installation

### Prerequisites

- Python **3.8+**
- pip

### 1. Clone or download the repository

```bash
git clone https://github.com/your-username/athlete-injury-risk-predictor.git
cd athlete-injury-risk-predictor
```

### 2. Install dependencies

```bash
pip install PyQt5 matplotlib
```

### 3. Run the application

```bash
python3 injury_risk_app.py
```

That's it — no additional configuration, external services, or API keys are required. The app creates its own local SQLite database (`injury_risk_history.db`) on first run.

---

## 🚀 Usage

1. Launch the app — you'll land on the **Dashboard**.
2. Click **➕ New Analysis** to open the intake form.
3. Fill in the athlete's profile: sport, training load, recovery habits, injury history, etc.
4. Click **🔍 Analyze Injury Risk** to generate:
   - A circular risk gauge (0–100)
   - A full contributing-factors breakdown
   - Sport-specific common injuries & focus regions
   - A tailored prevention plan
   - Personalized recommendations
   - A recommended reassessment date
5. Optionally click **🖨️ Export PDF Report** to save a shareable report.
6. Browse **History** to search past assessments or export everything as JSON.
7. Check **Statistics** and **Athlete Trends** for aggregate and individual insights.
8. Visit **Follow-Up Alerts** regularly to catch overdue or high-priority athletes.

---

## 📁 Project Structure

```
injury_risk_app.py          # Single-file application (entire app lives here)
├── 1. RISK ENGINE           # Pure logic — sport profiles, scoring, dataclasses
├── 2. DATABASE               # SQLite persistence layer
├── 3. THEMES                 # QSS stylesheets for 4 visual themes
├── 4. REUSABLE WIDGETS       # KpiCard, RiskGauge, SectionHeading, chart helpers
├── 5. PAGES                  # Dashboard, New Analysis, History, Statistics,
│                              Athlete Trends, Alerts, About
└── 6. MAIN WINDOW            # Navigation shell + app entry point

injury_risk_history.db      # Auto-generated local SQLite database (created on first run)
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3 |
| GUI Framework | PyQt5 |
| Charts | Matplotlib (Qt5Agg backend) |
| Persistence | SQLite3 |
| PDF Export | Qt Print Support (`QTextDocument` → `QPrinter`) |

---

## 🗄️ Database Schema

The app stores every assessment in a local SQLite table called `assessments`:

| Column | Type | Description |
|--------|------|--------------|
| `id` | INTEGER (PK) | Auto-incrementing record ID |
| `timestamp` | TEXT | Date/time the assessment was run |
| `athlete_name` | TEXT | Athlete's name |
| `sport` | TEXT | Selected sport/discipline |
| `age_group` | TEXT | Selected age bracket |
| `score` | REAL | Computed risk score (0–100) |
| `category` | TEXT | Low / Moderate / High / Critical |
| `urgency` | REAL | Urgency rating (0–10) |
| `needs_professional` | INTEGER | Flag (0/1) for professional care |
| `bmi` | REAL | Computed BMI |
| `bmi_category` | TEXT | Underweight / Normal / Overweight / Obese |
| `reassess_days` | INTEGER | Recommended days until next check-in |
| `details_json` | TEXT | Full JSON blob of factor breakdown, recommendations, and prevention plan |

---

## 🖼️ UI Walkthrough

- **Dashboard** → at-a-glance KPIs + recent activity table
- **New Analysis** → two-pane layout: intake form (left) + live risk report with gauge (right)
- **History** → full searchable/filterable table with per-row delete and JSON export
- **Statistics** → pie chart, bar chart, and trend line, all theme-aware
- **Athlete Trends** → single-athlete line chart + latest snapshot card
- **Follow-Up Alerts** → prioritized table of athletes needing attention
- **About** → in-app documentation and disclaimer

*(Add your own screenshots here once available — e.g. `docs/screenshots/dashboard.png`.)*

---

## 🧭 Roadmap

- [ ] Multi-user / multi-team support
- [ ] Cloud sync / shared team database
- [ ] Configurable risk-factor weights per organization
- [ ] CSV import for bulk athlete onboarding
- [ ] Mobile companion app

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

This application is an **educational / decision-support tool only**.

It is **not a medical device** and does **not** provide a clinical diagnosis. Always consult a licensed physician, physiotherapist, or athletic trainer for real injury evaluation, diagnosis, or treatment decisions.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ using Python & PyQt5 — v5.1 "Spectrum Redesign"</p>
