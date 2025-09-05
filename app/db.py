import sqlite3
from pathlib import Path
from datetime import datetime
import json

DB_PATH = Path("datascope_sync.db")

def get_conn():
    # check_same_thread=False para usar la conexión desde el hilo del servidor
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inbound_rows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        sheet TEXT,
        row_number INTEGER,
        marca TEXT,
        modelo TEXT,
        submodelo TEXT,
        codigo TEXT,
        nombre TEXT,
        payload_json TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def insert_inbound(sheet: str | None, row_number: int | None, row: dict):
    # extraer campos útiles si existen
    marca = str(row.get("Marca") or row.get("marca") or "").strip() or None
    modelo = str(row.get("Modelo") or row.get("modelo") or "").strip() or None
    subm  = str(row.get("SubModelo") or row.get("Submodelo") or row.get("submodelo") or "").strip() or None

    codigo = None
    nombre = None
    if modelo:
        codigo = f"{modelo}_{subm}" if subm else modelo
        nombre = f"{modelo} - {subm}" if subm else modelo

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inbound_rows
        (received_at, sheet, row_number, marca, modelo, submodelo, codigo, nombre, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
        sheet,
        row_number,
        marca,
        modelo,
        subm,
        codigo,
        nombre,
        json.dumps(row, ensure_ascii=False),
    ))
    conn.commit()
    conn.close()
