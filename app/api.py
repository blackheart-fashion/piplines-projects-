"""Application factory with per-request SQLite connections and parameterized SQL."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, g, jsonify, request

from app.service import normalize_title


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("DATABASE_PATH", "data/tasks.db"),
        APP_VERSION=os.environ.get("APP_VERSION", "dev"),
        DEMO_BROKEN=os.environ.get("DEMO_BROKEN", "0") == "1",
    )
    app.config.update(config or {})
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
            "done INTEGER NOT NULL DEFAULT 0)"
        )
        connection.commit()

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=5)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    @app.get("/health")
    def health():
        if app.config["DEMO_BROKEN"]:
            return jsonify(status="unhealthy", reason="classroom failure injection"), 503
        try:
            db().execute("SELECT COUNT(*) FROM tasks").fetchone()
        except sqlite3.Error:
            return jsonify(status="unhealthy", reason="database unavailable"), 503
        return jsonify(status="ok")

    @app.get("/version")
    def version():
        return jsonify(version=app.config["APP_VERSION"])

    @app.get("/tasks")
    def list_tasks():
        rows = db().execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
        return jsonify([dict(row) | {"done": bool(row["done"])} for row in rows])

    @app.post("/tasks")
    def add_task():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="send a JSON object"), 400
        try:
            title = normalize_title(payload.get("title"))
        except ValueError as error:
            return jsonify(error=str(error)), 400
        connection = db()
        cursor = connection.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
        connection.commit()
        return jsonify(id=cursor.lastrowid, title=title, done=False), 201

    @app.patch("/tasks/<int:task_id>")
    def complete_task(task_id):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get("done")) is not bool:
            return jsonify(error="done must be a JSON boolean"), 400
        connection = db()
        cursor = connection.execute(
            "UPDATE tasks SET done = ? WHERE id = ?", (int(payload["done"]), task_id)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify(error="task not found"), 404
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return jsonify(dict(row) | {"done": bool(row["done"])})

    return app
