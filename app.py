from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    current_user,
    logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Like, Match, Message
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["SECRET_KEY"] = "studyconnect_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studyconnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

import models  # важно для создания таблиц

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


translations = {
    "ua": {
        "home": "Головна",
        "search": "Пошук",
        "matches": "Збіги",
        "profile": "Мій профіль",
        "logout": "Вийти",
        "login": "Вхід",
        "register": "Реєстрація",

        "welcome": "Ласкаво просимо до StudyConnect",
        "subtitle": "Платформа для пошуку студентів за інтересами та командної роботи.",
        "start": "Почати",

        "edit_profile": "Редагувати профіль",
        "edit_profile_title": "Редагування профілю",
        "open_chat": "Відкрити чат",
        "save": "Зберегти",
        "name": "Ім'я",
        "photo": "Фото профілю",
        "faculty": "Факультет",
        "course": "Курс",
        "about": "Про себе",
        "interests": "Інтереси",

        "student_search": "Пошук студентів",
        "search_btn": "Шукати",
        "clear": "Очистити",
        "nothing_found": "Нічого не знайдено",
        "suitable": "Підходить",

        "your_matches": "Ваші матчі",
        "no_matches": "Поки що немає збігів",
        "no_interests": "Без інтересів",
        "no_description": "Без опису",

        "your_chats": "Ваші чати",
        "no_chats": "Поки що немає доступних чатів. Спочатку отримайте взаємний збіг.",
        "chat_with": "Чат з",
        "no_messages": "Повідомлень поки немає. Почніть спілкування",
        "write_message": "Написати повідомлення...",
        "send": "Надіслати",

        "not_specified": "Не вказано",
        "not_filled": "Не заповнено"
    },

    "en": {
        "home": "Home",
        "search": "Search",
        "matches": "Matches",
        "profile": "My profile",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",

        "welcome": "Welcome to StudyConnect",
        "subtitle": "A platform for finding students by interests and teamwork.",
        "start": "Start",

        "edit_profile": "Edit profile",
        "edit_profile_title": "Edit profile",
        "open_chat": "Open chat",
        "save": "Save",
        "name": "Name",
        "photo": "Profile photo",
        "faculty": "Faculty",
        "course": "Course",
        "about": "About",
        "interests": "Interests",

        "student_search": "Student search",
        "search_btn": "Search",
        "clear": "Clear",
        "nothing_found": "Nothing found",
        "suitable": "Suitable",

        "your_matches": "Your matches",
        "no_matches": "No matches yet",
        "no_interests": "No interests",
        "no_description": "No description",

        "your_chats": "Your chats",
        "no_chats": "No chats available yet. Get a mutual match first.",
        "chat_with": "Chat with",
        "no_messages": "No messages yet. Start the conversation",
        "write_message": "Write a message...",
        "send": "Send",

        "not_specified": "Not specified",
        "not_filled": "Not filled"
    }
}


@app.context_processor
def inject_translations():
    lang = session.get("lang", "ua")

    def t(key):
        return translations[lang].get(key, key)

    return dict(t=t, lang=lang)


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in ["ua", "en"]:
        session["lang"] = lang

    return redirect(request.referrer or url_for("index"))


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


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        current_user.username = request.form["username"]
        current_user.faculty = request.form["faculty"]
        current_user.course = request.form["course"]
        current_user.about = request.form["about"]
        current_user.interests = request.form["interests"]

        avatar = request.files.get("avatar")

        if avatar and avatar.filename:
            filename = secure_filename(avatar.filename)
            avatar_path = os.path.join("static", "avatars", filename)
            avatar.save(avatar_path)
            current_user.avatar = filename

        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("edit_profile.html")


@app.route("/discover")
@login_required
def discover():

    name = request.args.get("name", "").strip()
    faculty = request.args.get("faculty", "").strip()
    course = request.args.get("course", "").strip()
    interests = request.args.get("interests", "").strip()

    query = User.query.filter(User.id != current_user.id)

    if name:
        query = query.filter(User.username.ilike(f"%{name}%"))

    if faculty:
        query = query.filter(User.faculty.ilike(f"%{faculty}%"))

    if course:
        query = query.filter(User.course.ilike(f"%{course}%"))

    if interests:
        query = query.filter(User.interests.ilike(f"%{interests}%"))

    users = query.all()

    return render_template(
        "discover.html",
        users=users,
        name=name,
        faculty=faculty,
        course=course,
        interests=interests
    )


@app.route("/like/<int:user_id>")
@login_required
def like(user_id):

    if user_id == current_user.id:
        return redirect(url_for("discover"))

    existing_like = Like.query.filter_by(
        from_user_id=current_user.id,
        to_user_id=user_id
    ).first()

    if not existing_like:
        new_like = Like(
            from_user_id=current_user.id,
            to_user_id=user_id
        )
        db.session.add(new_like)
        db.session.commit()

    reverse_like = Like.query.filter_by(
        from_user_id=user_id,
        to_user_id=current_user.id
    ).first()

    if reverse_like:
        user1 = min(current_user.id, user_id)
        user2 = max(current_user.id, user_id)

        existing_match = Match.query.filter_by(
            user1_id=user1,
            user2_id=user2
        ).first()

        if not existing_match:
            new_match = Match(
                user1_id=user1,
                user2_id=user2
            )
            db.session.add(new_match)
            db.session.commit()

    return redirect(url_for("matches"))


@app.route("/matches")
@login_required
def matches():

    all_matches = Match.query.filter(
        (Match.user1_id == current_user.id) |
        (Match.user2_id == current_user.id)
    ).all()

    matched_users = []

    for match in all_matches:
        if match.user1_id == current_user.id:
            user = User.query.get(match.user2_id)
        else:
            user = User.query.get(match.user1_id)

        if user:
            matched_users.append(user)

    return render_template("matches.html", users=matched_users)


@app.route("/chat")
@login_required
def chat():

    all_matches = Match.query.filter(
        (Match.user1_id == current_user.id) |
        (Match.user2_id == current_user.id)
    ).all()

    users = []

    for match in all_matches:
        if match.user1_id == current_user.id:
            user = User.query.get(match.user2_id)
        else:
            user = User.query.get(match.user1_id)

        if user:
            users.append(user)

    return render_template("chat.html", users=users)


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat_with(user_id):

    user1 = min(current_user.id, user_id)
    user2 = max(current_user.id, user_id)

    match = Match.query.filter_by(
        user1_id=user1,
        user2_id=user2
    ).first()

    if not match:
        return "Чат доступний тільки після взаємного збігу."

    other_user = User.query.get(user_id)

    if request.method == "POST":

        text = request.form["text"].strip()

        if text:
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

    return render_template(
        "chat_room.html",
        messages=messages,
        user=other_user
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)