import os
import random
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from flask import send_from_directory



load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_home_dev")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

client = MongoClient(MONGO_URI)
db = client["iot_home"]

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ------------- helpers --------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.users.find_one({"_id": ObjectId(uid)})

def create_default_devices(user_id):
    # Only create if none exist
    count = db.devices.count_documents({"user_id": ObjectId(user_id)})
    if count == 0:
        db.devices.insert_many([
            {
                "user_id": ObjectId(user_id),
                "name": "Puerta Sala",
                "slug": "door_sala",
                "type": "switch",
                "state": "OFF",  # OFF = cerrado (rojo), ON = abierto (verde)
                "created_at": datetime.now(timezone.utc)
            },
            {
                "user_id": ObjectId(user_id),
                "name": "Sensor Temperatura",
                "slug": "temp_sensor",
                "type": "sensor",
                "state": None,
                "created_at": datetime.now(timezone.utc)
            },
        ])

# ------------- routes --------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/sw.js")
def sw():
    return send_from_directory("static/js", "sw.js", mimetype="application/javascript")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Completa todos los campos", "danger")
            return redirect(url_for("register"))

        exists = db.users.find_one({"email": email})
        if exists:
            flash("Ese correo ya está registrado", "warning")
            return redirect(url_for("register"))

        pwd_hash = generate_password_hash(password)
        res = db.users.insert_one({
            "name": name,
            "email": email,
            "password_hash": pwd_hash,
            "created_at": datetime.now(timezone.utc)
        })
        create_default_devices(res.inserted_id)
        flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.users.find_one({"email": email})
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Credenciales inválidas", "danger")
            return redirect(url_for("login"))
        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        flash("Bienvenido/a 👋", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    devices = list(db.devices.find({"user_id": ObjectId(user["_id"])}))
    return render_template("dashboard.html", user=user, devices=devices)

# --------- APIs ---------
@app.route("/api/state", methods=["GET"])
@login_required
def api_state():
    user = current_user()

    # Fetch devices
    devices = list(db.devices.find({"user_id": ObjectId(user["_id"])}))

    # Simulate temperature and persist reading as an event
    temp_c = round(random.uniform(18.0, 29.0), 1)
    event = {
        "user_id": ObjectId(user["_id"]),
        "slug": "temp_sensor",
        "value": temp_c,
        "unit": "°C",
        "created_at": datetime.now(timezone.utc)
    }
    db.events.insert_one(event)

    # Build simple state payload
    state = {}
    for d in devices:
        state[d["slug"]] = {
            "name": d["name"],
            "type": d["type"],
            "state": d["state"]
        }
    state["temp_sensor"]["reading"] = temp_c

    return jsonify({"ok": True, "state": state})

@app.route("/api/toggle/<slug>", methods=["POST"])
@login_required
def api_toggle(slug):
    user = current_user()
    device = db.devices.find_one({"user_id": ObjectId(user["_id"]), "slug": slug})
    if not device or device["type"] != "switch":
        return jsonify({"ok": False, "error": "Dispositivo no encontrado o no conmutable"}), 404

    new_state = "OFF" if device.get("state") == "ON" else "ON"
    db.devices.update_one({"_id": device["_id"]}, {"$set": {"state": new_state}})
    db.events.insert_one({
        "user_id": ObjectId(user["_id"]),
        "slug": slug,
        "value": new_state,
        "unit": None,
        "created_at": datetime.now(timezone.utc)
    })
    return jsonify({"ok": True, "slug": slug, "state": new_state})

# Health check for Render
@app.route("/healthz")
def healthz():
    try:
        client.admin.command('ping')  # PING rápido al cluster
        return {"status": "ok", "mongo": "ok"}
    except Exception as e:
        return {"status": "ok", "mongo": "error", "detail": str(e)}

if __name__ == "__main__":
    # For local testing only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
