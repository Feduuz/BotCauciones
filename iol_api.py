import requests
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Cargamos variables del archivo .env
load_dotenv()

# ======================
# CONFIGURACIÓN
# ======================
IOL_USER = "IOL_USER"
IOL_PASS = "IOL_PASS"
BASE_URL = "https://api.invertironline.com"

# Variables de control del token
_tokens = {}
_token_expira: float = 0


# ======================
# LOGIN Y REFRESH TOKEN
# ======================
def _login() -> str:
    """Hace login en IOL y devuelve un access_token válido"""
    global _tokens, _token_expira
    url = f"{BASE_URL}/token"
    payload = {
        "username": IOL_USER,
        "password": IOL_PASS,
        "grant_type": "password"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    r = requests.post(url, data=payload, headers=headers, timeout=15)
    r.raise_for_status()  # lanza excepción si falla
    _tokens = r.json()

    # Guardamos el tiempo en que expira el token (restamos unos segundos de margen)
    _token_expira = time.time() + int(_tokens.get("expires_in", 600)) - 10
    return _tokens["access_token"]


def _get_token():
    """Devuelve un token válido (login si no existe o está vencido)"""
    global _tokens, _token_expira
    if not _tokens or time.time() > _token_expira:
        return _login()
    return _tokens["access_token"]

def _auth_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {_get_token()}"}

# ======================
# HELPERS
# ======================
def _normalize_list(payload: Any) -> List[Dict[str, Any]]:
    """
    Normaliza la respuesta de IOL a lista de dicts.
    Si viene un dict con clave 'cauciones' / 'titulos' / 'data', la usa.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("cauciones", "titulos", "Titulos", "items", "data"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
        # Si es un solo objeto, lo envolvemos en lista
        return [payload]
    return []

# ======================
# FUNCIONES DE LA API
# ======================
def cotizacion_cauciones() -> List[Dict[str, Any]]:
    """
    Consulta las cauciones en el mercado BCBA.
    Intenta variantes de endpoint y reintenta si el token venció.
    """
    urls = [
        f"{BASE_URL}/api/v2/Cotizaciones/cauciones/BCBA",
        f"{BASE_URL}/api/v2/cotizaciones/cauciones/BCBA",  # fallback por si el server es case-sensitive
    ]

    headers = _auth_headers()

    last_err = None
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 401:
                # Token vencido o inválido → relogin y 2º intento inmediato
                _login()
                headers = _auth_headers()
                r = requests.get(url, headers=headers, timeout=15)

            if r.status_code == 404:
                # probamos con la próxima variante de URL
                last_err = requests.HTTPError("404 Not Found")
                continue

            r.raise_for_status()
            return _normalize_list(r.json())

        except requests.RequestException as e:
            last_err = e
            continue

    # Si ninguna URL funcionó:
    raise RuntimeError(f"No se pudo obtener cauciones: {last_err}")
