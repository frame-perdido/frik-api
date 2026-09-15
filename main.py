
import json, gzip, unicodedata, re
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Frikiserie API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# Cargar datos (soporta .json y .json.gz)
DATA_FILE = Path(__file__).parent / "frikiserie_full.json"
DATA_GZ = Path(__file__).parent / "frikiserie_full.json.gz"

if DATA_GZ.exists():
    with gzip.open(DATA_GZ, "rt", encoding="utf-8") as f:
        records = json.load(f)
else:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

print(f"[startup] Cargados {len(records)} registros")

def filtrar(tipo=None, anio=None, q=None, decada=None, con_caps=None):
    res = records
    if tipo:   res = [r for r in res if r["tipo"] == tipo]
    if anio:   res = [r for r in res if r["fecha"] == anio]
    if decada: res = [r for r in res if decada <= r["fecha"] < decada + 10]
    if con_caps is True:
        res = [r for r in res if r.get("numCapitulosDisponibles", 0) > 0]
    if q:
        ql = q.lower()
        res = [r for r in res if ql in r["titulo"].lower()
               or ql in (r.get("descripcion") or "").lower()]
    return res

def resumen(r):
    return {k: v for k, v in r.items() if k != "capitulos"}

@app.get("/")
def root():
    return {"api": "Frikiserie", "version": "2.0",
            "endpoints": ["/series", "/peliculas", "/buscar",
                          "/serie/{slug}", "/serie/{slug}/capitulos",
                          "/capitulo?serie=<slug>&temporada=1&capitulo=1",
                          "/stats"]}

@app.get("/series")
def get_series(anio: int | None = None, decada: int | None = None,
               q: str | None = None, con_caps: bool | None = None,
               page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    res = filtrar(tipo="serie", anio=anio, decada=decada, q=q, con_caps=con_caps)
    total = len(res); start = (page - 1) * limit
    return {"total": total, "page": page, "limit": limit,
            "items": [resumen(r) for r in res[start:start + limit]]}

@app.get("/peliculas")
def get_peliculas(anio: int | None = None, decada: int | None = None,
                  q: str | None = None,
                  page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    res = filtrar(tipo="pelicula", anio=anio, decada=decada, q=q)
    total = len(res); start = (page - 1) * limit
    return {"total": total, "page": page, "limit": limit,
            "items": res[start:start + limit]}

@app.get("/buscar")
def buscar(q: str, tipo: str | None = None, limit: int = 30):
    if not q or len(q) < 2:
        raise HTTPException(400, "q debe tener al menos 2 caracteres")
    res = filtrar(tipo=tipo, q=q)[:limit]
    return {"query": q, "total": len(res), "items": [resumen(r) for r in res]}

@app.get("/serie/{slug}")
def get_serie(slug: str, with_caps: bool = False):
    for r in records:
        if r["slug"] == slug:
            if with_caps:
                return r
            out = resumen(r)
            out["numCapitulosDisponibles"] = r.get("numCapitulosDisponibles", 0)
            return out
    raise HTTPException(404, "No encontrada")

@app.get("/serie/{slug}/capitulos")
def get_capitulos(slug: str, temporada: int | None = None,
                  page: int = Query(1, ge=1), limit: int = Query(100, ge=1, le=500)):
    for r in records:
        if r["slug"] == slug:
            caps = r.get("capitulos", [])
            if temporada is not None:
                caps = [c for c in caps if c["temporada"] == temporada]
            total = len(caps); start = (page - 1) * limit
            return {"slug": slug, "titulo": r["titulo"],
                    "total": total, "page": page, "limit": limit,
                    "items": caps[start:start + limit]}
    raise HTTPException(404, "Serie no encontrada")

@app.get("/capitulo")
def get_capitulo(serie: str, temporada: int, capitulo: int):
    for r in records:
        if r["slug"] == serie:
            for c in r.get("capitulos", []):
                if c["temporada"] == temporada and c["capitulo"] == capitulo:
                    return {"serie": r["titulo"], "slug": r["slug"], **c}
            raise HTTPException(404, "Capítulo no encontrado")
    raise HTTPException(404, "Serie no encontrada")

@app.get("/stats")
def stats():
    s = [r for r in records if r["tipo"] == "serie"]
    p = [r for r in records if r["tipo"] == "pelicula"]
    return {"total": len(records), "series": len(s), "peliculas": len(p),
            "series_con_capitulos": sum(1 for r in s if r.get("numCapitulosDisponibles", 0) > 0),
            "total_capitulos": sum(r.get("numCapitulosDisponibles", 0) for r in records)}
