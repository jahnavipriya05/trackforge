from flask import Flask, redirect, url_for, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

# =========================
# DATABASE CONFIG 
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///trackforge.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# =========================
# DATABASE MODELS
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)


class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Float)
    dates = db.Column(db.String(50))
    notes = db.Column(db.String(500), nullable=False)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    company_name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    status = db.Column(db.String(50))


# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("home.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":

        user = request.form["username"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]

        existing_user = User.query.filter_by(username=user).first()

        if existing_user:
            return "User already exists"

        new_user = User(username=user, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        session["user"] = user
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":

        user = request.form["username"]
        password = request.form["password"]

        user_data = User.query.filter_by(username=user).first()

        if user_data and check_password_hash(user_data.password, password):
            session["user"] = user_data.username
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("index"))

    username = session["user"]

    user_data = User.query.filter_by(username=username).first()
    if not user_data:
        return redirect(url_for("login"))

    sessions = StudySession.query.filter_by(user_id=user_data.id).all()
    applications = Application.query.filter_by(user_id=user_data.id).all()

    total_sessions = len(sessions)
    total_apps = len(applications)

    return render_template(
        "dashboard.html",
        user=username,
        sessions=sessions,
        applications=applications,
        total_sessions=total_sessions,
        total_apps=total_apps
    )


# ---------- ADD SESSION ----------
@app.route("/add_session", methods=["POST", "GET"])
def add_session():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        subject_name = request.form["subject"]
        hour = request.form["hours"]
        date = request.form["date"]
        note = request.form["notes"]

        user = User.query.filter_by(username=session["user"]).first()

        add_to = StudySession(
            user_id=user.id,
            subject=subject_name,
            hours=hour,
            dates=date,
            notes=note
        )

        db.session.add(add_to)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_session.html")


# ---------- EDIT SESSION ----------
@app.route("/edit_session/<int:id>", methods=["GET", "POST"])
def edit_session(id):

    if "user" not in session:
        return redirect(url_for("login"))

    data = StudySession.query.get_or_404(id)

    current_user = User.query.filter_by(username=session["user"]).first()

    if data.user_id != current_user.id:
        return "Unauthorized"

    if request.method == "POST":
        data.subject = request.form["subject"]
        data.hours = request.form["hours"]
        data.dates = request.form["date"]
        data.notes = request.form["notes"]

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_session.html", data=data)


#------------EDIT APPLICATION-----------
@app.route("/edit_application/<int:id>", methods=["GET", "POST"])
def edit_application(id):

    if "user" not in session:
        return redirect(url_for("login"))

    data = Application.query.get_or_404(id)

    current_user = User.query.filter_by(username=session["user"]).first()

    if data.user_id != current_user.id:
        return "Unauthorized"

    if request.method == "POST":
        data.company_name = request.form["company_name"]
        data.role = request.form["role"]
        data.status = request.form["status"]

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_application.html", data=data)

# ---------- DELETE SESSION ----------
@app.route("/delete_session/<int:id>")
def delete_session(id):

    if "user" not in session:
        return redirect(url_for("login"))

    data = StudySession.query.get_or_404(id)
    current_user = User.query.filter_by(username=session["user"]).first()

    if data.user_id != current_user.id:
        return "Unauthorized"

    db.session.delete(data)
    db.session.commit()

    return redirect(url_for("dashboard"))

#------------DELETE APPLICATION------------
@app.route("/delete_application/<int:id>")
def delete_application(id):

    if "user" not in session:
        return redirect(url_for("login"))

    data = Application.query.get_or_404(id)
    current_user = User.query.filter_by(username=session["user"]).first()

    if data.user_id != current_user.id:
        return "Unauthorized"
    print(data.user_id, current_user.id)

    db.session.delete(data)
    db.session.commit()

    return redirect(url_for("dashboard"))

# ---------- APPLICATION TRACKER ----------
@app.route("/application_tracker", methods=["GET", "POST"])
def application_tracker():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        comp_name = request.form["company_name"]
        role = request.form["role"]
        status = request.form["status"]

        user_data = User.query.filter_by(username=session["user"]).first()

        add_to = Application(
            user_id=user_data.id,
            company_name=comp_name,
            role=role,
            status=status
        )

        db.session.add(add_to)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("application_tracker.html")


# ---------- ABOUT ----------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------- HELP ----------
@app.route("/help")
def help():
    return render_template("help.html")

#-------------------PROFILE----------------------
@app.route("/profile", methods=["GET","POST"])
def profile():

    if "user" not in session:
        return redirect(url_for("index"))

    user = User.query.filter_by(username=session["user"]).first()

    if request.method == "POST":
        new_password = request.form["password"]

        if new_password:
            if len(new_password) < 6:
                return render_template(
                    "profile.html",
                    user=user,
                    error="Password must be at least 6 characters"
                )

            user.password = generate_password_hash(new_password)
            db.session.commit()

            return render_template(
                "profile.html",
                user=user,
                success="Password updated successfully"
            )

    return render_template("profile.html", user=user)

# ---------- FORGOT PASSWORD ----------
@app.route("/forgot", methods=["GET", "POST"])
def forgot():

    if request.method == "POST":

        username = request.form["username"]
        newpass = generate_password_hash(request.form["password"])

        user = User.query.filter_by(username=username).first()

        if user:
            user.password = newpass
            db.session.commit()
            return redirect(url_for("login"))

        return "User not found"

    return render_template("forgot.html")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run()