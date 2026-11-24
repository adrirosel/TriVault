# TriVault — Gestor de Finanzas Personales, Liquidez e Inversión

**TriVault** (`trivault`) es una aplicación web Full-Stack diseñada para llevar el control granular del flujo de caja personal, segmentar el patrimonio por niveles de liquidez y medir el rendimiento real de las inversiones frente a la inflación.

---

## 1. ¿En qué consiste el producto?

La aplicación resuelve la gestión financiera personal mediante seis pilares:

- **Segmentación en 3 cubos de liquidez**: separación del capital en cuentas de uso diario (`daily`), colchón de emergencia (`emergency`) e inversión (`investment`), con saldos independientes y visión agregada del patrimonio neto.
- **Control de flujo de caja y categorías**: registro de ingresos, gastos (fijos y variables) y transferencias internas entre cuentas propias sin distorsionar las métricas de ahorro.
- **Erosión por inflación en liquidez**: cálculo transparente de la pérdida de poder adquisitivo anual y mensual del dinero mantenido en efectivo (`daily` + `emergency`).
- **Seguimiento real de fondos indexados**: registro de posiciones por ISIN y detalle de cada aportación/compra (fecha, participaciones, valor liquidativo y comisión) para comparar la rentabilidad nominal frente a la inflación acumulada del periodo de tenencia.
- **Dashboard analítico**: panel visual con evolución de flujo de caja, distribución por categorías, peso de cada cubo y rendimiento de cartera.
- **Automatización progresiva**: importación de extractos bancarios CSV con detección de duplicados mediante hash SHA-256, registro rápido vía Webhook móvil y recordatorios diarios mediante Bot de Telegram.

---

## 2. Stack Tecnológico

### Frontend (`/frontend`)
- **React + Vite + TypeScript** (modo estricto)
- **Tailwind CSS** para el sistema de estilos
- **Recharts** para visualizaciones y gráficos analíticos
- **React Router** para navegación protegida

### Backend (`/backend`)
- **Python 3.11+ & FastAPI** (validación con Pydantic y documentación OpenAPI/Swagger)
- **SQLAlchemy 2.x** (ORM) + **Alembic** (migraciones de base de datos)
- **JWT + bcrypt** para autenticación y aislamiento estricto por usuario (`user_id`)
- **Pytest** para pruebas unitarias y de integración

### Base de Datos y Evolución
- **Desarrollo local**: **MySQL** (instalación local o Docker)
- **Producción**: **Supabase (PostgreSQL)** mediante capa de abstracción SQLAlchemy, evitando SQL propietario para migrar cambiando únicamente `DATABASE_URL` y el driver `psycopg`.

---

## 3. Estructura del Repositorio

```text
trivault/
├── CONTEXT.md                    # Arquitectura, modelo de datos y reglas de contexto para IA
├── README.md                     # Documentación principal del proyecto
├── .gitignore                    # Exclusión de secretos (.env), dependencias y builds
├── .github/workflows/            # CI/CD (PENDIENTE: aún no hay ci.yml)
├── docs/
│   └── especificacion-tecnica.md # Especificación funcional y técnica base
├── backend/                      # API REST en FastAPI + SQLAlchemy + Alembic
└── frontend/                     # SPA en React + Vite + TypeScript + Tailwind
```

---

## 3.1 Estado de Fase 1 y pendientes

**Gate Fase 1: BLOQUEADA** (no avanzar a Fase 2 hasta cerrar el CI como mínimo).

| Entregable | Estado |
|---|---|
| Backend (MySQL + Alembic, auth JWT, cuentas, categorías, transacciones/transferencias, `PATCH /auth/me`) | Completo |
| Frontend (Vite + React + TS + Tailwind, login/register, dashboard overview, CRUD cuentas/categorías/transacciones) | Completo en `feat/frontend-core` |
| CI GitHub Actions (Pytest + `tsc` / `vite build`) | **Pendiente** — falta `.github/workflows/ci.yml` |
| Test de rollback mid-transfer (saldos intactos ante fallo) | **Pendiente** (soft-gap) |
| Recharts / analytics / fondos (Fase 2), CSV / Telegram (Fase 3), Supabase prod (Fase 4) | Fuera de alcance actual |

### Desarrollo local (frontend)

```bash
# MySQL (Docker) + API
docker compose up -d
cd backend && .venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# SPA (proxy /api -> :8000; host IPv4)
cd frontend
copy .env.example .env   # VITE_API_URL vacío usa el proxy de Vite
npm install
npm run dev              # http://127.0.0.1:5173
```

En `backend/.env`, `ALLOWED_ORIGINS` debe incluir `http://127.0.0.1:5173` y/o `http://localhost:5173`.

---

## 4. Despliegue e Infraestructura

El despliegue está diseñado como un monorepo conectado a **Vercel**, **Supabase** y **GitHub Actions**:

1. **Frontend en Vercel** (`Root Directory: frontend`):
   - Compilación automática de Vite (`npm run build`) servida desde la CDN global de Vercel.
   - Reglas de reescritura en `frontend/vercel.json` hacia `/index.html` para soporte SPA.
   - Variable de entorno `VITE_API_URL` apuntando a la URL pública del backend.
2. **Backend en Vercel Serverless** (`Root Directory: backend`):
   - Ejecución de FastAPI con el runtime oficial de Python mediante `backend/vercel.json`.
   - Credenciales críticas (`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, y en fases avanzadas `TELEGRAM_BOT_TOKEN` y `CRON_SECRET`) configuradas únicamente en las **Environment Variables** cifradas de Vercel y en **GitHub Secrets**.
   - En Fase 3, los recordatorios diarios se disparan con **Vercel Cron Jobs** sobre `/api/cron/daily-reminder`.
3. **Base de datos en Supabase**:
   - Instancia PostgreSQL gestionada en producción, migrada desde el esquema versionado con Alembic.
4. **Automatización con GitHub Actions** (**pendiente de implementar**):
   - Objetivo: Pytest contra MySQL de test, typecheck y `vite build` en PRs / pushes a `develop` y `main`.
   - CD a Vercel solo tras checks verdes; no fusionar trabajo de feature en ramas de deploy sin revisión.

> **Seguridad**: ningún archivo `.env`, clave privada o credencial se sube al repositorio. Utiliza siempre los archivos `.env.example` como plantilla local.

---

## 5. Flujo de Trabajo (IA + Git)

### Colaboración con Inteligencia Artificial
El proyecto sigue un flujo de desarrollo asistido donde **el control arquitectónico pertenece siempre al desarrollador**:
1. **Contexto compartido**: la IA consulta [CONTEXT.md](CONTEXT.md) antes de cada tarea para respetar el stack, el esquema de 6 tablas y las reglas de seguridad.
2. **Planificación antes de codificar**: antes de crear o modificar archivos de código, la IA presenta un plan técnico detallado (archivos a tocar, diseño de endpoints/tablas e implicaciones) y espera aprobación explícita o modificaciones por parte del autor.
3. **Iteración en módulos pequeños**: se implementa pieza a pieza, revisando la lógica y verificando la seguridad (por ejemplo, aislamiento por `user_id`) antes de avanzar al siguiente módulo.

### Estrategia de Ramas y Versionado en Git
- **`main`**: rama de producción estable. Nunca se resuelven conflictos directamente sobre `main`.
- **`develop`**: rama auxiliar de integración donde se fusionan las ramas de trabajo y se validan los checks de CI antes de pasar a `main`.
- **Ramas de vida corta**: todo cambio parte de `develop` en ramas específicas (`feat/...`, `fix/...`, `docs/...`, `test/...`).
- **Commits y Tags**: commits frecuentes y atómicos con mensajes descriptivos siguiendo Conventional Commits (`feat:`, `fix:`, `sec:`, `docs:`, `test:`, `refactor:`), acompañados de tags semánticos periódicos (`v0.1.0`, `v0.2.0`, etc.).
