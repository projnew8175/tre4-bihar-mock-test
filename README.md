# TRE-4 Bihar Mock Test v2

## Features
- Secondary + Higher Secondary common 40-mark test
- Exactly 5 choices: A, B, C, All of the above, More than one of the above
- Random 40 questions from selected subject(s)
- Subject-wise question bank
- CSV bulk import for 500/1000+ questions
- Student result + answer review
- Student result history
- Public leaderboard (best score per student)
- Admin result export CSV
- PostgreSQL/Supabase-ready
- Render-ready

## CSV format
Headers must be:
question,subject,option_a,option_b,option_c,correct,explanation

`correct` must be one of: a, b, c, all, more

Note: D and E option labels are automatically displayed as:
D. All of the above
E. More than one of the above

For Excel: open the XLSX in Excel/LibreOffice/Google Sheets and save/download as CSV UTF-8, then upload.

## Render
Build command: pip install -r requirements.txt
Start command: gunicorn app:app

Environment variables:
DATABASE_URL = PostgreSQL connection string
ADMIN_PASSWORD = your strong admin password
SECRET_KEY = generated automatically by render.yaml or set your own

Default local admin password is `admin123`; change it for production.
