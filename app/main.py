import os
import json
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

from .db import init_db, insert_inbound  # <-- NUEVO

load_dotenv()

EXPECTED_TOKEN = os.getenv("WEBHOOK_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="Sheets → Webhook demo")
init_db()  # <-- crea tabla si no existe

class SheetPayload(BaseModel):
    sheet: str | None = None
    rowNumber: int | None = None
    row: dict

@app.get("/health")
def health():
    print("[health] OK")
    return {"ok": True}

@app.post("/webhook/sheets")
async def webhook_sheets(payload: SheetPayload, request: Request, x_webhook_token: str | None = Header(default=None)):
    if EXPECTED_TOKEN and (x_webhook_token != EXPECTED_TOKEN):
        print("[webhook] token inválido")
        raise HTTPException(status_code=401, detail="invalid token")

    body_dict = payload.model_dump()

    # LOG en consola
    print("==== NUEVA LLAMADA DESDE SHEETS ====")
    print(f"sheet: {body_dict.get('sheet')}   rowNumber: {body_dict.get('rowNumber')}")
    print("row:")
    print(json.dumps(body_dict.get("row", {}), ensure_ascii=False, indent=2))
    print("====================================")

    # INSERT en SQLite
    insert_inbound(
        sheet=body_dict.get("sheet"),
        row_number=body_dict.get("rowNumber"),
        row=body_dict.get("row") or {},
    )

    return {"ok": True, "received": True}
