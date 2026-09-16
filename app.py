import os, csv, io, random
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
db_url = os.getenv("DATABASE_URL", "sqlite:///tre4.db")
if db_url.startswith("postgres://"): db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

SUBJECTS = ["Hindi", "English", "Mathematics", "Science", "Social Science", "General Studies", "Other"]

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(100), nullable=False, default="General Studies")
    option_a = db.Column(db.String(1000), nullable=False)
    option_b = db.Column(db.String(1000), nullable=False)
    option_c = db.Column(db.String(1000), nullable=False)
    correct = db.Column(db.String(10), nullable=False)
    explanation = db.Column(db.Text, default="")

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    roll = db.Column(db.String(100), nullable=False, index=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    correct_count = db.Column(db.Integer, nullable=False)
    wrong_count = db.Column(db.Integer, nullable=False)
    unattempted = db.Column(db.Integer, nullable=False)
    student = db.relationship("Student")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

with app.app_context():
    db.create_all()

def admin_required():
    return session.get("admin") is True

def option_text(q, key):
    return {
        "a": q.option_a, "b": q.option_b, "c": q.option_c,
        "all": "All of the above", "more": "More than one of the above"
    }.get(key, "")

@app.route("/")
def index():
    counts = {s: Question.query.filter_by(subject=s).count() for s in SUBJECTS}
    total = Question.query.count()
    return render_template("index.html", counts=counts, total=total)

@app.route("/start", methods=["POST"])
def start():
    name, roll = request.form.get("name","").strip(), request.form.get("roll","").strip()
    subjects = request.form.getlist("subjects")
    if not name or not roll:
        flash("Name और Roll/Mobile भरना जरूरी है।", "error")
        return redirect(url_for("index"))
    query = Question.query
    if subjects and "All" not in subjects:
        query = query.filter(Question.subject.in_(subjects))
    questions = query.all()
    if len(questions) < 40:
        flash(f"Selected subjects में कम से कम 40 questions चाहिए। अभी {len(questions)} हैं।", "error")
        return redirect(url_for("index"))
    student = Student(name=name, roll=roll)
    db.session.add(student); db.session.commit()
    selected = random.sample(questions, 40)
    random.shuffle(selected)
    session["student_id"] = student.id
    session["questions"] = [q.id for q in selected]
    session["answers"] = {}
    return redirect(url_for("test"))

@app.route("/test")
def test():
    ids = session.get("questions")
    if not ids or not session.get("student_id"): return redirect(url_for("index"))
    rows = Question.query.filter(Question.id.in_(ids)).all()
    by_id = {q.id:q for q in rows}
    questions = [by_id[i] for i in ids if i in by_id]
    return render_template("test.html", questions=questions, duration=40)

@app.route("/submit", methods=["POST"])
def submit():
    ids = session.get("questions", [])
    if not ids: return redirect(url_for("index"))
    rows = Question.query.filter(Question.id.in_(ids)).all()
    by_id = {q.id:q for q in rows}
    correct = wrong = unattempted = 0
    details = []
    for qid in ids:
        q = by_id.get(qid)
        ans = request.form.get(f"q_{qid}")
        if not ans: unattempted += 1; status = "unattempted"
        elif ans == q.correct: correct += 1; status = "correct"
        else: wrong += 1; status = "wrong"
        details.append({"q":q, "answer":ans, "status":status})
    result = Result(student_id=session["student_id"], score=correct, total=len(ids),
                    correct_count=correct, wrong_count=wrong, unattempted=unattempted)
    db.session.add(result); db.session.commit()
    session.pop("questions", None); session.pop("student_id", None)
    return render_template("result.html", result=result, details=details)

@app.route("/history/<int:student_id>")
def history(student_id):
    student = Student.query.get_or_404(student_id)
    results = Result.query.filter_by(student_id=student_id).order_by(Result.id.desc()).all()
    return render_template("history.html", student=student, results=results)

@app.route("/leaderboard")
def leaderboard():
    # Best score per student, then recent attempt as tie-breaker.
    results = Result.query.order_by(Result.score.desc(), Result.id.asc()).all()
    best = {}
    for r in results:
        if r.student_id not in best: best[r.student_id] = r
    rows = sorted(best.values(), key=lambda r: (-r.score, r.id))
    return render_template("leaderboard.html", rows=rows[:100])

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == os.getenv("ADMIN_PASSWORD","admin123"):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Invalid password", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None); return redirect(url_for("index"))

@app.route("/admin")
def admin():
    if not admin_required(): return redirect(url_for("admin_login"))
    subject = request.args.get("subject","All")
    query = Question.query.order_by(Question.id.desc())
    if subject != "All": query = query.filter_by(subject=subject)
    questions = query.all()
    results = Result.query.order_by(Result.id.desc()).all()
    counts = {s: Question.query.filter_by(subject=s).count() for s in SUBJECTS}
    return render_template("admin.html", questions=questions, results=results, subjects=SUBJECTS, counts=counts, active_subject=subject)

@app.route("/admin/question/add", methods=["POST"])
def add_question():
    if not admin_required(): return redirect(url_for("admin_login"))
    q = Question(text=request.form["text"].strip(), subject=request.form["subject"],
                 option_a=request.form["a"].strip(), option_b=request.form["b"].strip(),
                 option_c=request.form["c"].strip(), correct=request.form["correct"],
                 explanation=request.form.get("explanation","").strip())
    db.session.add(q); db.session.commit()
    flash("Question added.", "success"); return redirect(url_for("admin"))

@app.route("/admin/question/delete/<int:q_id>", methods=["POST"])
def delete_question(q_id):
    if not admin_required(): return redirect(url_for("admin_login"))
    q = Question.query.get_or_404(q_id); db.session.delete(q); db.session.commit()
    flash("Question deleted.", "success"); return redirect(url_for("admin"))

@app.route("/admin/import", methods=["POST"])
def import_questions():
    if not admin_required(): return redirect(url_for("admin_login"))
    f = request.files.get("file")
    if not f or not f.filename:
        flash("CSV file select करें।", "error"); return redirect(url_for("admin"))
    if not f.filename.lower().endswith(".csv"):
        flash("इस version में CSV import supported है। Excel को CSV UTF-8 में save करके upload करें।", "error")
        return redirect(url_for("admin"))
    raw = f.read()
    try: text = raw.decode("utf-8-sig")
    except UnicodeDecodeError: text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    required = {"question","subject","option_a","option_b","option_c","correct"}
    headers = {h.strip() for h in (reader.fieldnames or [])}
    if not required.issubset(headers):
        flash("CSV columns: question, subject, option_a, option_b, option_c, correct, explanation", "error")
        return redirect(url_for("admin"))
    added, skipped = 0, 0
    for row in reader:
        try:
            correct = row.get("correct","").strip().lower()
            if correct not in {"a","b","c","all","more"}: skipped += 1; continue
            subject = row.get("subject","General Studies").strip() or "General Studies"
            if subject not in SUBJECTS: subject = "Other"
            q = Question(text=row["question"].strip(), subject=subject,
                         option_a=row["option_a"].strip(), option_b=row["option_b"].strip(),
                         option_c=row["option_c"].strip(), correct=correct,
                         explanation=row.get("explanation","").strip())
            if not q.text or not q.option_a or not q.option_b or not q.option_c: skipped += 1; continue
            db.session.add(q); added += 1
        except Exception:
            skipped += 1
    db.session.commit()
    flash(f"Imported {added} questions; skipped {skipped}.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/export")
def export_results():
    if not admin_required(): return redirect(url_for("admin_login"))
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["Student","Roll/Mobile","Score","Total","Correct","Wrong","Unattempted","Date"])
    for r in Result.query.order_by(Result.id.desc()).all():
        w.writerow([r.student.name, r.student.roll, r.score, r.total, r.correct_count, r.wrong_count, r.unattempted, r.created_at])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=tre4_results.csv"})

@app.route("/admin/template")
def csv_template():
    if not admin_required(): return redirect(url_for("admin_login"))
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["question","subject","option_a","option_b","option_c","correct","explanation"])
    w.writerow(["भारत का संविधान कब लागू हुआ?","General Studies","26 Jan 1950","15 Aug 1947","26 Nov 1949","a","संविधान 26 जनवरी 1950 को लागू हुआ।"])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=tre4_question_template.csv"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
