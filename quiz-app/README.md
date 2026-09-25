# QuizArc — Full-Stack Quiz & Daily Challenge App

A gamified trivia web app built with **Flask** (backend) and **vanilla HTML/CSS/JS** (frontend). Features daily quests, XP leveling, streak tracking, question-by-question review, tamper-proof sessions, and dual leaderboards.

---

## 🔄 Complete User Workflow

```
Login → Dashboard → Daily Challenge / Practice → Quiz → Streak + XP → Result → Review → Leaderboard
```

1. **Login / Register (`Login`)**
   - User signs in with username & 4–10 digit PIN (hashed with `werkzeug.security`).
   - Includes rate-limiting protection against brute-force PIN attempts.
2. **User Dashboard (`Dashboard`)**
   - Profile card displaying User Avatar, Level Badge (`Lv. 4`), XP Progress bar (`75/100 XP`), Total XP, Active Streak, and Best Streak.
3. **Mode Selection (`Daily Challenge / Practice`)**
   - **Daily Challenge**: 10 mixed questions across all categories with **+50% Bonus XP** (1 completion per day).
   - **Practice Mode**: Custom selection across 6 categories & 3 difficulty tiers (Easy 25s, Medium 20s, Hard 12s).
4. **Active Quiz (`Quiz`)**
   - Interactive timed quiz interface with live countdown bar, question cards, live streak counter, and live XP earned pill.
5. **Streak + XP Calculation (`Streak + XP`)**
   - Server-side calculation of base XP & daily bonus XP. Persists active streak days and player level in SQLite DB.
6. **Results Summary (`Result`)**
   - Score ring animation, accuracy percentage, XP breakdown, level progress, and **Level-Up** celebration banner.
7. **Question Review (`Review`)**
   - Question-by-question review listing every question, user's choice (green/red), correct answer, and status.
8. **Dual Leaderboards (`Leaderboard`)**
   - **Global XP Leaderboard** (Top players by Level & XP) & **Category Leaderboard** (High scores per category).

---

## ⚡ Quick Start

```bash
# 1. Install Python dependencies
cd backend
pip3 install -r requirements.txt

# 2. Seed the database (populates 180 questions)
python3 seed.py

# 3. Start the server
python3 app.py

# 4. Open in your browser
open http://127.0.0.1:5000
```

---

## 📂 Project Structure

```
quiz-app/
├── backend/
│   ├── app.py                # Flask server entry point (serves API + frontend)
│   ├── database.py           # SQLite schema & migration helper (7 tables)
│   ├── seed.py               # Database seeder (180 questions across 6 categories)
│   ├── quiz.db               # SQLite database file
│   ├── requirements.txt      # Dependencies (Flask, Flask-CORS, werkzeug)
│   └── routes/
│       ├── questions.py      # GET /api/categories, GET /api/questions, GET /api/questions/daily
│       ├── scores.py         # POST /api/scores, GET /api/leaderboard
│       └── auth.py           # Authentication, rate limiting, GET /api/user/profile
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## 📊 Database Schema

| Table | Description |
|-------|-------------|
| `categories` | 6 Categories (General, Movies, Science, History, Geography, Sports) |
| `questions` | 180 Questions with difficulty, 4 options, and correct_index |
| `players` | Users with hashed PINs, XP, level, current_streak, best_streak, last_active_date |
| `auth_tokens` | 7-day session tokens for persistent login |
| `quiz_sessions` | Single-use anti-tamper quiz session tokens (30-min TTL) |
| `scores` | Detailed submission logs with verified badges & XP earned |
| `daily_challenges` | Log of completed daily challenge quizzes per player per date |

---

## 🔐 Security Features

1. **Server-Side Scoring**: Correct answers are never sent to the frontend during quiz play.
2. **Werkzeug Password Hashing**: PINs are securely hashed using Scrypt/Pbkdf2 via `werkzeug.security`.
3. **Login Rate Limiting**: Max 5 failed login attempts per 5-minute window returns `429 Too Many Requests`.
4. **Backend Authentication Enforcement**: All quiz questions & score submissions require a valid `X-Auth-Token`.
5. **Anti-Tamper Session Tokens**: Quiz submissions check question ID membership, difficulty match, and prevent session reuse.
