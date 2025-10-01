# Casa IoT — Simulador (Flask + MongoDB + Render)

Demo académica sencilla para simular un entorno IoT doméstico:
- Registro / login de usuarios
- Dispositivo **Puerta de la Sala** (switch ON/OFF)
- **Sensor de Temperatura** simulado (lectura al consultar estado)
- Persistencia de estados y eventos en **MongoDB**
- Lista para desplegar en **Render**

## Estructura
```
.
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
└── static/
    ├── css/styles.css
    └── js/app.js
```

## Variables de entorno
Crea `.env` a partir de `.env.example` y define:
- `MONGO_URI` → cadena de conexión de MongoDB Atlas.
- `SECRET_KEY` → texto aleatorio para sesiones Flask.

## Desarrollo local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Luego edita .env
python app.py
```
Abre http://localhost:5000

> **Nota:** Render también usará `MONGO_URI` que definas como variable de entorno en el panel o vinculada al `render.yaml`.

## Despliegue en Render
1. Sube este repo a GitHub/GitLab.
2. En Render, crea un **Web Service** desde el repo.
3. Usa este `render.yaml` o configura manualmente:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
   - Health Check Path: `/healthz`
4. Añade la variable de entorno `MONGO_URI` con tu cadena de **MongoDB Atlas**.
5. Render generará automáticamente `SECRET_KEY` si usas `render.yaml` (o ponlo tú).

## Colecciones MongoDB
- `users`: { name, email, password_hash, created_at }
- `devices`: { user_id, name, slug, type, state, created_at }
- `events`: registros de toggles y lecturas de temperatura

Durante el registro se crean dispositivos por defecto para el usuario.

## API rápida
- `GET /api/state` → estado actual + lectura de temperatura
- `POST /api/toggle/door_sala` → alterna puerta ON/OFF

## Créditos
Proyecto educativo. Usa Bootstrap para un estilo cálido (beige/café) inspirado en tonos colombianos.
