import requests
import time

def get_convex_url():
    env_path = ".env.local"
    with open(env_path) as f:
        for line in f:
            if line.startswith("CONVEX_URL="):
                return line.strip().split("=", 1)[1]
    raise Exception("CONVEX_URL no encontrada en .env.local")

CONVEX_URL = get_convex_url()

def _post(endpoint: str, body: dict, reintentos: int = 3):
    for intento in range(reintentos):
        try:
            res = requests.post(
                f"{CONVEX_URL}/api/{endpoint}",
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=15,
            )
            data = res.json()
            if data.get("status") != "success":
                raise Exception(data.get("errorMessage", f"Error en {endpoint}"))
            return data["value"]
        except Exception as e:
            if intento < reintentos - 1:
                time.sleep(1)
                continue
            raise e

def convex_query(path: str, args: dict = {}):
    return _post("query", {"path": path, "args": args, "format": "json"})

def convex_mutation(path: str, args: dict = {}):
    return _post("mutation", {"path": path, "args": args, "format": "json"})