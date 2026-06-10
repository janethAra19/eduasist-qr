import requests
import os

# Leer URL de Convex desde .env.local
def get_convex_url():
    env_path = ".env.local"
    with open(env_path) as f:
        for line in f:
            if line.startswith("CONVEX_URL="):
                return line.strip().split("=", 1)[1]
    raise Exception("CONVEX_URL no encontrada en .env.local")

CONVEX_URL = get_convex_url()

def convex_query(path: str, args: dict = {}):
    res = requests.post(
        f"{CONVEX_URL}/api/query",
        headers={"Content-Type": "application/json"},
        json={"path": path, "args": args, "format": "json"},
        timeout=10,
    )
    data = res.json()
    if data.get("status") != "success":
        raise Exception(data.get("errorMessage", "Error en query"))
    return data["value"]

def convex_mutation(path: str, args: dict = {}):
    res = requests.post(
        f"{CONVEX_URL}/api/mutation",
        headers={"Content-Type": "application/json"},
        json={"path": path, "args": args, "format": "json"},
        timeout=10,
    )
    data = res.json()
    if data.get("status") != "success":
        raise Exception(data.get("errorMessage", "Error en mutation"))
    return data["value"]