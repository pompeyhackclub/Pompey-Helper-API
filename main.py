import flask
from flask import url_for
from flask_cors import CORS
import random
import argon2
import jwt
import datetime
import aiosqlite
from uuid import uuid4

app = flask.Flask(__name__)
app.secret_key = "fuhufiuafiuhefewofhefuhwef"
CORS(app)

def has_no_empty_params(rule):
    defaults = rule.defaults or {}
    arguments = rule.arguments or set()
    return len(defaults) >= len(arguments - set(defaults))

@app.route("/")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        if has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append({"url": url, "endpoint": rule.endpoint, "methods": sorted(rule.methods - {"HEAD", "OPTIONS"})})
    return flask.jsonify({"routes": links})

@app.route("/user/register", methods=["POST"])
async def register_user():
    data = flask.request.get_json()
    print(data)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return flask.jsonify({"error": "Missing required fields"}), 400

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = await cursor.fetchone()

        if existing_user:
            return flask.jsonify({"error": "Username or email already exists"}), 400

        ph = argon2.PasswordHasher()
        password_hash = ph.hash(password)

        user_uuid = str(uuid4())
        await db.execute("INSERT INTO users (uuid, username, email, passwordHash) VALUES (?, ?, ?, ?)",
                         (user_uuid, username, email, password_hash))
        await db.commit()

    return flask.jsonify({"message": "User registered successfully"})

@app.route("/user/login", methods=["POST"])
async def login_user():
    data = flask.request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return flask.jsonify({"error": "Missing required fields"}), 400

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT id, passwordHash FROM users WHERE username = ?", (username,))
        user = await cursor.fetchone()

        if not user:
            return flask.jsonify({"error": "Invalid username or password"}), 401

        user_id, password_hash = user
        ph = argon2.PasswordHasher()

        try:
            ph.verify(password_hash, password)
        except argon2.exceptions.VerifyMismatchError:
            return flask.jsonify({"error": "Invalid username or password"}), 401

        token_payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(token_payload, app.secret_key, algorithm="HS256")

    return flask.jsonify({"token": token})


@app.route("/user/logout")
def logout_user():
    pass

@app.route("/acts", methods=["GET"])
async def list_acts():
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT id, userId, location, category, item, claimedBy, completed FROM Acts")
        rows = await cursor.fetchall()

    return flask.jsonify([
        {
            "id": r[0],
            "userId": r[1],
            "location": r[2],
            "category": r[3],
            "item": r[4],
            "claimedBy": r[5],
            "completed": bool(r[6])
        }
        for r in rows
    ])


@app.route("/acts/register", methods=["POST"])
async def register_act():
    auth_header = flask.request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return flask.jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return flask.jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return flask.jsonify({"error": "Invalid token"}), 401

    user_id = payload["user_id"]

    data = flask.request.get_json()
    location = data.get("location")
    category = data.get("category")
    item = data.get("item")

    if not location or not category or not item:
        return flask.jsonify({"error": "Missing required fields: location, category, item"}), 400

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT waffle FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()

        if not row:
            return flask.jsonify({"error": "User not found"}), 404

        if row[0] < 5:
            return flask.jsonify({"error": "Insufficient waffles (need 5)"}), 402

        await db.execute("UPDATE users SET waffle = waffle - 5 WHERE id = ?", (user_id,))
        await db.execute(
            "INSERT INTO Acts (userId, location, category, item) VALUES (?, ?, ?, ?)",
            (user_id, location, category, item)
        )
        await db.commit()

    return flask.jsonify({"message": "Act registered successfully"}), 201

@app.route("/acts/claim/<int:act_id>", methods=["POST"])
async def claim_act(act_id):
    auth_header = flask.request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return flask.jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return flask.jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return flask.jsonify({"error": "Invalid token"}), 401

    user_id = payload["user_id"]

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT userId, claimedBy, completed FROM Acts WHERE id = ?", (act_id,))
        act = await cursor.fetchone()

        if not act:
            return flask.jsonify({"error": "Act not found"}), 404

        owner_id, claimed_by, completed = act

        if owner_id == user_id:
            return flask.jsonify({"error": "Cannot claim your own act"}), 400
        if claimed_by:
            return flask.jsonify({"error": "Act already claimed"}), 409
        if completed:
            return flask.jsonify({"error": "Act already completed"}), 409

        await db.execute("UPDATE Acts SET claimedBy = ? WHERE id = ?", (user_id, act_id))
        await db.commit()

    return flask.jsonify({"message": "Act claimed successfully"})

@app.route("/merch", methods=["GET"])
async def list_merch():
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT name, waffles, provider, img FROM Merch")
        rows = await cursor.fetchall()

    return flask.jsonify([
        {"name": r[0], "waffles": r[1], "provider": r[2], "img": r[3]}
        for r in rows
    ])


@app.route("/merch/register", methods=["POST"])
async def register_merch():
    auth_header = flask.request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return flask.jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return flask.jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return flask.jsonify({"error": "Invalid token"}), 401

    data = flask.request.get_json()
    name     = data.get("name")
    waffles  = data.get("waffles")
    provider = data.get("provider")
    img      = data.get("img")

    if not name or waffles is None or not provider or not img:
        return flask.jsonify({"error": "Missing required fields: name, waffles, provider, img"}), 400
    if not isinstance(waffles, int) or waffles < 0:
        return flask.jsonify({"error": "waffles must be a non-negative integer"}), 400

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT id FROM Merch WHERE name = ?", (name,))
        if await cursor.fetchone():
            return flask.jsonify({"error": "Merch item with that name already exists"}), 409

        await db.execute(
            "INSERT INTO Merch (name, waffles, provider, img) VALUES (?, ?, ?, ?)",
            (name, waffles, provider, img)
        )
        await db.commit()

    return flask.jsonify({"message": "Merch registered successfully"}), 201


@app.route("/acts/complete/<int:act_id>", methods=["POST"])
async def complete_act(act_id):
    auth_header = flask.request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return flask.jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return flask.jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return flask.jsonify({"error": "Invalid token"}), 401

    user_id = payload["user_id"]

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT claimedBy, completed FROM Acts WHERE id = ?", (act_id,))
        act = await cursor.fetchone()

        if not act:
            return flask.jsonify({"error": "Act not found"}), 404

        claimed_by, completed = act

        if claimed_by != user_id:
            return flask.jsonify({"error": "Act not claimed by you"}), 403
        if completed:
            return flask.jsonify({"error": "Act already completed"}), 409

        await db.execute("UPDATE Acts SET completed = TRUE WHERE id = ?", (act_id,))
        await db.execute("UPDATE users SET waffle = waffle + 7 WHERE id = ?", (user_id,))
        await db.commit()

    return flask.jsonify({"message": "Act marked as completed"})


