#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, re
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "tajna_lozinka_123"  # promijeni po želji
DB = "parking.db"

# ---------- BAZA ----------
def normalize_plate(plate: str) -> str:
    if plate is None:
        return ""
    s = plate.upper()
    s = re.sub(r'[^A-Z0-9]', '', s)
    return s

def connect():
    return sqlite3.connect(DB)

def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT UNIQUE NOT NULL,
        make TEXT,
        model TEXT,
        color TEXT,
        owner TEXT,
        notes TEXT,
        added_at TEXT
    )
    """)
    con.commit()
    con.close()

# ---------- CRUD ----------
def add_car(plate, make="", model="", color="", owner="", notes=""):
    plate_n = normalize_plate(plate)
    if not plate_n:
        return False, "Neispravne tablice."
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO cars (plate, make, model, color, owner, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (plate_n, make, model, color, owner, notes, datetime.utcnow().isoformat()))
        con.commit()
        return True, f"Auto {plate_n} uspješno dodan."
    except sqlite3.IntegrityError:
        return False, "Tablice već postoje u bazi."
    finally:
        con.close()

def get_car(plate):
    plate_n = normalize_plate(plate)
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM cars WHERE plate = ?", (plate_n,))
    row = cur.fetchone()
    con.close()
    return row

def delete_car(plate):
    plate_n = normalize_plate(plate)
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM cars WHERE plate = ?", (plate_n,))
    deleted = cur.rowcount
    con.commit()
    con.close()
    return deleted > 0

def list_all():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM cars ORDER BY plate")
    rows = cur.fetchall()
    con.close()
    return rows

# ---------- RUTE ----------
@app.route("/")
def index():
    cars = list_all()
    return render_template("index.html", cars=cars)

@app.route("/add", methods=["POST"])
def add():
    plate = request.form.get("plate")
    make = request.form.get("make")
    model = request.form.get("model")
    color = request.form.get("color")
    owner = request.form.get("owner")
    notes = request.form.get("notes")
    ok, msg = add_car(plate, make, model, color, owner, notes)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("index"))

@app.route("/check", methods=["POST"])
def check():
    plate = request.form.get("plate_check")
    car = get_car(plate)
    if car:
        flash(f"Tablice {plate.upper()} postoje u bazi.", "success")
    else:
        flash(f"Tablice {plate.upper()} nisu pronađene.", "warning")
    return redirect(url_for("index"))

@app.route("/delete/<plate>")
def delete(plate):
    if delete_car(plate):
        flash(f"Tablice {plate.upper()} obrisane.", "success")
    else:
        flash(f"Nema takvih tablica.", "danger")
    return redirect(url_for("index"))

# ---------- GLAVNI POKRETAC ----------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

