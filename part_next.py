import os
from flask import Flask, request, render_template, url_for
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

SKILLS = [
    "python", "java", "c", "c++", "sql",
    "html", "css", "javascript", "react",
    "nodejs", "aws", "docker", "git",
    "flask", "mongodb", "mysql"
]


def extract_skills(text):
    text = (text or "").lower()
    return {
        skill for skill in SKILLS
        if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text)
    }
def generate_ai_feedback(score, matched, missing):
    feedback = []

    if score >= 80:
        feedback.append(
            "Your profile strongly matches the job requirements."
        )
    elif score >= 50:
        feedback.append(
            "Your profile is partially aligned with the role."
        )
    else:
        feedback.append(
            "There is a significant skill gap for this position."
        )

    if matched:
        feedback.append(
            f"Your strongest matching skills are: {', '.join(matched[:5])}."
        )

    if missing:
        feedback.append(
            f"Consider learning: {', '.join(missing[:5])}."
        )

    return " ".join(feedback)


def analyze_resume(resume_text, job_text):
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    score = round((len(matched) / len(job_skills) * 100) if job_skills else 0, 2)
    recommendation = (
        "Excellent match! Your resume aligns very well with the job requirements."
        if score >= 80 else
        "Good match. Add the missing skills to improve your chances."
        if score >= 50 else
        "Your profile needs improvement. Focus on the missing skills listed below."
    )

    if score >= 90:
        rank = "Top 10%"
    elif score >= 75:
        rank = "Top 25%"
    elif score >= 50:
        rank = "Top 50%"
    else:
        rank = "Below Average"

    feedback = generate_ai_feedback(score, matched, missing)
    def learning_roadmap(missing):
        roadmap = []

        for skill in missing:
            roadmap.append(f"Learn {skill}")

        return roadmap

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": recommendation,
        "rank": rank,
        "feedback": feedback,
        "ai_feedback": generate_ai_feedback(score, matched, missing),
        "learning_roadmap": learning_roadmap(missing),
        "roadmap": learning_roadmap(missing),
    }


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_blank(value):
    return not value or not value.strip()

photo_url = "default_link"  # Yeh function ke bahar hai


@app.route("/", methods=["GET", "POST"])
def home():
    global photo_url  # Python ko batao ki hum bahar wala variable use kar rahe hain
    resume = ""
    job = ""
    analysis = None
    error = None

    if request.method == "POST":
        resume = request.form.get("resume", "").strip()
        job = request.form.get("job", "").strip()
        photo = request.files.get("photo")
        photo_url = photo_url  # Ab yeh error nahi dega

        if is_blank(resume) or is_blank(job):
            error = "Please paste both your resume and the job description."
        else:
            if photo and photo.filename:
                if allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                    photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    photo.save(photo_path)
                    photo_url = url_for("static", filename=f"uploads/{filename}")
                else:
                    error = "Only PNG, JPG, JPEG, and GIF files are allowed for the resume photo."

            if not error:
                analysis = analyze_resume(resume, job)

    return render_template(
        "index.html",
        resume=resume,
        job=job,
        analysis=analysis,
        error=error,
        skills=SKILLS,
        photo_url=photo_url,
    )


if __name__ == "__main__":
    app.run(debug=True)