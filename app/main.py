import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

from .db import init_db, insert_inbound  # <-- NUEVO

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    logger.info("💚 [HEALTH] Health check solicitado")
    return {"ok": True}

@app.get("/ping")
def ping():
    logger.info("🏓 [PING] Ping recibido")
    return {"message": "pong", "timestamp": datetime.now().isoformat()}

@app.post("/webhook/sheets")
async def webhook_sheets(payload: SheetPayload, request: Request, x_webhook_token: str | None = Header(default=None)):
    # Obtener información del cliente
    client_ip = request.client.host if request.client else "unknown"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"🔄 [WEBHOOK] Nueva llamada recibida desde {client_ip} a las {timestamp}")
    
    # Validar token
    if EXPECTED_TOKEN and (x_webhook_token != EXPECTED_TOKEN):
        logger.error("❌ [WEBHOOK] Token inválido - Acceso denegado")
        raise HTTPException(status_code=401, detail="invalid token")
    
    logger.info("✅ [WEBHOOK] Token válido")

    try:
        body_dict = payload.model_dump()

        # LOG detallado del contenido
        logger.info("📊 [WEBHOOK] Datos recibidos:")
        logger.info(f"  📋 Sheet: {body_dict.get('sheet')}")
        logger.info(f"  🔢 Row Number: {body_dict.get('rowNumber')}")
        logger.info(f"  📄 Row Data: {json.dumps(body_dict.get('row', {}), ensure_ascii=False)}")

        # LOG en consola (formato legacy)
        print("==== NUEVA LLAMADA DESDE SHEETS ====")
        print(f"sheet: {body_dict.get('sheet')}   rowNumber: {body_dict.get('rowNumber')}")
        print("row:")
        print(json.dumps(body_dict.get("row", {}), ensure_ascii=False, indent=2))
        print("====================================")

        # INSERT en SQLite
        logger.info("💾 [WEBHOOK] Guardando en base de datos...")
        insert_inbound(
            sheet=body_dict.get("sheet"),
            row_number=body_dict.get("rowNumber"),
            row=body_dict.get("row") or {},
        )
        logger.info("✅ [WEBHOOK] Datos guardados exitosamente en la base de datos")

        logger.info("🎉 [WEBHOOK] Procesamiento completado con éxito")
        return {"ok": True, "received": True}

    except Exception as e:
        logger.error(f"❌ [WEBHOOK] Error durante el procesamiento: {str(e)}")
        logger.error(f"❌ [WEBHOOK] Tipo de error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Error procesando webhook: {str(e)}")
