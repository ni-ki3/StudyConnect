from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Like, Match, Message

app = Flask(__name__)

app.config["SECRET_KEY"] = "studyconnect_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studyconnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

import models  # важно для создания таблиц

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Паролі не співпадають."

        if User.query.filter_by(email=email).first():
            return "Користувач з таким email вже існує."

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("profile"))

        return "Невірний email або пароль."

    return render_template("login.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        current_user.faculty = request.form["faculty"]
        current_user.course = request.form["course"]
        current_user.about = request.form["about"]
        current_user.interests = request.form["interests"]

        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("edit_profile.html")


@app.route("/discover")
@login_required
def discover():

    users = User.query.filter(User.id != current_user.id).all()

    return render_template("discover.html", users=users)


@app.route("/like/<int:user_id>")
@login_required
def like(user_id):

    # создаём лайк 
    existing_like = Like.query.filter_by(
        from_user_id=current_user.id,
        to_user_id=user_id
    ).first()

    if not existing_like:
        db.session.add(Like(
            from_user_id=current_user.id,
            to_user_id=user_id
        ))

    # проверяем взаимный лайк
    reverse_like = Like.query.filter_by(
        from_user_id=user_id,
        to_user_id=current_user.id
    ).first()

    if reverse_like:

        # проверяем, существует ли match
        match = Match.query.filter_by(
            user1_id=min(current_user.id, user_id),
            user2_id=max(current_user.id, user_id)
        ).first()

        if not match:
            db.session.add(Match(
                user1_id=min(current_user.id, user_id),
                user2_id=max(current_user.id, user_id)
            ))

    db.session.commit()

    return redirect(url_for("discover"))


@app.route("/matches")
@login_required
def matches():

    all_matches = Match.query.filter(
        (Match.user1_id == current_user.id) |
        (Match.user2_id == current_user.id)
    ).all()

    users = []

    for m in all_matches:
        if m.user1_id == current_user.id:
            users.append(User.query.get(m.user2_id))
        else:
            users.append(User.query.get(m.user1_id))

    return render_template("matches.html", users=users)


@app.route("/chat")
@login_required
def chat():

    all_matches = Match.query.filter(
        (Match.user1_id == current_user.id) |
        (Match.user2_id == current_user.id)
    ).all()

    users = []

    for m in all_matches:
        if m.user1_id == current_user.id:
            users.append(User.query.get(m.user2_id))
        else:
            users.append(User.query.get(m.user1_id))

    return render_template("chat.html", users=users)

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat_with(user_id):

    if request.method == "POST":

        text = request.form["text"]

        new_message = Message(
            sender_id=current_user.id,
            receiver_id=user_id,
            text=text
        )

        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for("chat_with", user_id=user_id))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).all()

    other_user = User.query.get(user_id)

    return render_template(
        "chat_room.html",
        messages=messages,
        user=other_user
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)