# core/ords_client.py
import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("ords-client")

ORDS_BASE_URL = (
    "https://gabdddcba32cc06-agenteaidb.adb.us-ashburn-1.oraclecloudapps.com/ords/admin"
)

TIMEOUT = 20.0


async def ords_request(method: str, path: str, payload: Optional[dict] = None) -> Dict[str, Any]:
    """
    Llama ORDS (AutoREST) y retorna JSON (dict).
    - Si ORDS responde vacío (común en DELETE), retorna {}.
    Lanza:
      - httpx.RequestError (conectividad)
      - httpx.HTTPStatusError (4xx/5xx)
    """
    # Normaliza path
    if not path.startswith("/"):
        path = "/" + path

    url = f"{ORDS_BASE_URL}{path}"

    headers = {
        "Accept": "application/json",
    }
    # Solo envía Content-Type cuando hay JSON
    if payload is not None:
        headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.request(
                method=method.upper(),
                url=url,
                json=payload if payload is not None else None,
                headers=headers,
            )
        except httpx.RequestError:
            logger.exception("ORDS connection error: %s %s", method, url)
            raise

    # Errores ORDS
    if resp.status_code >= 400:
        logger.error("ORDS error %s %s -> %s | %s", method, url, resp.status_code, resp.text)
        raise httpx.HTTPStatusError(
            message=f"ORDS error {resp.status_code}",
            request=resp.request,
            response=resp,
        )

    # ✅ Manejo de respuesta vacía (muy común en DELETE)
    if resp.content is None or len(resp.content) == 0:
        return {}

    text = resp.text.strip() if resp.text else ""
    if text == "":
        return {}

    # Si hay body, intentamos JSON; si no, devolvemos {} pero lo dejamos logueado
    try:
        return resp.json()
    except Exception:
        logger.warning("ORDS returned non-JSON body for %s %s -> %s", method, url, text[:300])
        return {}
