# TRE-4 Bihar Mock Test – 50 Ready-Made Practice Sets

A Flask + PostgreSQL/Supabase + Render-ready online mock-test platform for TRE-4 practice.

## Built-in practice sets
- 50 ready-made Practice Sets
- 40 questions per set
- 30-minute timer
- Questions are preloaded automatically on first deployment/startup; no CSV upload is needed for these built-in sets
- Original syllabus-oriented practice questions (not official/leaked exam questions)
- Secondary + Higher Secondary practice
- 5 choices: A, B, C, All of the above, More than one of the above
- Instant result, explanations, history and leaderboard

## Other features
- Subject-wise question bank
- CSV bulk import for additional 500/1000+ questions
- Admin result export CSV
- PostgreSQL/Supabase-ready
- Render-ready

## Deploy/update
Build command: `pip install -r requirements.txt`
Start command: `gunicorn app:app`

Environment variables:
- `DATABASE_URL` = PostgreSQL/Supabase connection string
- `ADMIN_PASSWORD` = admin login password
- `SECRET_KEY` = secure secret (Render can generate this)

### Updating an existing Render deployment
1. Replace the project files in your GitHub repository with this version (keep the same repository).
2. Commit the changes.
3. Render will deploy the latest commit automatically, or use Manual Deploy → Deploy latest commit.
4. On startup, the app creates the `practice_sets` and `practice_questions` tables if they do not exist and seeds all 50 sets once.
5. Your existing Supabase/PostgreSQL database and existing question bank are kept; the new built-in tables are added alongside them.

## CSV format for extra questions
Headers:
`question,subject,option_a,option_b,option_c,correct,explanation`

`correct` must be one of: `a`, `b`, `c`, `all`, `more`.
