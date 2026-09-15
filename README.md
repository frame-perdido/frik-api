# Frikiserie API

API REST con 1500 títulos (322 series + 1178 películas) y +17000 capítulos con videos embebidos.

## Endpoints

- `GET /series` — Listado de series (filtros: anio, decada, q, con_caps, page, limit)
- `GET /peliculas` — Listado de películas
- `GET /buscar?q=...` — Búsqueda global
- `GET /serie/{slug}` — Ficha de una serie
- `GET /serie/{slug}/capitulos` — Capítulos (filtro temporada)
- `GET /capitulo?serie={slug}&temporada=1&capitulo=1` — Capítulo específico
- `GET /stats` — Estadísticas

## Deploy en Render

1. Sube este repo a GitHub
2. En Render → New → Web Service → conecta el repo
3. Render detecta `render.yaml` automáticamente
4. Listo 🚀
