# CONTEXT.md — TriVault (Gestor de Finanzas Personales, Liquidez e Inversión)

> **Propósito de este archivo**: Es la fuente de verdad técnica y metodológica del proyecto **TriVault** (`trivault`). Toda sesión de trabajo asistido por IA debe leer este contexto antes de proponer o modificar código.

---

## 1. Gobernanza y Metodología de Trabajo con IA

1. **Plan previo obligatorio**: Antes de crear, modificar o eliminar cualquier archivo de código, la IA debe leer este contexto, presentar su propuesta de diseño (archivos afectados, esquema/contratos y decisiones técnicas) y **esperar aprobación explícita del autor**.
2. **Control del autor**: Todas las decisiones arquitectónicas, de producto y de prioridades las toma el desarrollador.
3. **Módulos pequeños y auditables**: Implementar de forma incremental (una entidad/endpoint/componente a la vez), revisando seguridad y lógica antes de pasar al siguiente bloque.
4. **Seguridad como prioridad**:
   - Toda consulta de lectura, escritura o borrado en BD debe filtrar obligatoriamente por `user_id` extraído del token JWT validado (nunca confiar en IDs enviados por el cliente sin verificar propiedad).
   - Nunca subir archivos `.env`, tokens, contraseñas ni claves al repositorio. Mantener `.env.example` sin valores sensibles.
5. **Retrospectiva obligatoria de fin de fase (Phase Gate)**:
   - Siempre que se considere terminada una fase (o antes de proponer/iniciar trabajo de la siguiente), la IA debe invocar la skill `.agents/skills/phase-gate-review/SKILL.md` y ejecutar una auditoría formal de entregables, seguridad, invariantes financieras, migraciones y tests para confirmar si se puede avanzar con garantías o si quedan brechas por cerrar.

---

## 2. Visión del Producto y Módulos Funcionales

**TriVault** es una aplicación web Full-Stack para el control granular del flujo de caja personal, la segmentación del patrimonio en tres niveles de liquidez y el seguimiento realista del rendimiento de fondos indexados frente a la inflación.

| Módulo | Diseño Aprobado |
|---|---|
| **Segmentación de Capital (3 Cubos)** | Cuentas tipadas en `daily` (uso diario), `emergency` (colchón de emergencia) e `investment` (inversión), con balances independientes y cálculo agregado de patrimonio neto. |
| **Control de Flujo y Categorías** | CRUD de transacciones vinculadas a categorías personalizables (`income` / `expense`, fijas o variables), con filtros temporales y analítica por partidas. |
| **Transferencias Internas** | Movimientos de tipo `transfer` entre cubos propios registrados en una única fila de `transactions` con `destination_account_id` y actualización atómica de ambos saldos. |
| **Inflación e Inversiones** | Seguimiento de posiciones en fondos indexados por ISIN y tabla dedicada de aportaciones (`fund_contributions`) para calcular rentabilidad nominal y real frente a la inflación acumulada del periodo de tenencia; cálculo independiente de erosión anual/mensual sobre liquidez (`daily` + `emergency`) mediante `annual_inflation_rate`. |
| **Captura Automatizada (Fase 3)** | Importador de extractos CSV/Excel bancarios con deduplicación por hash SHA-256 + endpoint Webhook para atajos móviles (iOS/Android). |
| **Recordatorios con Bot de Telegram (Fase 3)** | Diferido a Fase 3. Se reserva `telegram_chat_id` (nullable) en `users`; cuando se implemente en Vercel serverless usará Webhook de Telegram + Vercel Cron Job (`/api/cron/daily-reminder`). |

Documento de referencia original: [docs/especificacion-tecnica.md](docs/especificacion-tecnica.md).

---

## 3. Stack Tecnológico

- **Frontend (`/frontend`)**:
  - React + Vite + TypeScript (modo estricto).
  - **Tailwind CSS** para estilos y diseño de interfaz.
  - **Recharts** para visualizaciones analíticas declarativas en el dashboard.
  - React Router para enrutamiento SPA protegido.
- **Backend (`/backend`)**:
  - Python 3.11+ con **FastAPI** y validación mediante **Pydantic v2**.
  - **SQLAlchemy 2.x** (ORM) + **Alembic** para migraciones de esquema.
  - Autenticación JWT + hashing seguro de contraseñas (`bcrypt`).
  - **Pytest** para pruebas unitarias y de integración.
- **Base de Datos (Estrategia MySQL -> Supabase)**:
  - Desarrollo local inicial con **MySQL** (local o Docker).
  - Consultas escritas exclusivamente vía SQLAlchemy estándar evitando funciones propietarias de MySQL, permitiendo migrar en Fase 4 a **Supabase (PostgreSQL)** cambiando únicamente `DATABASE_URL` y el driver (`psycopg`).
- **Despliegue y CI/CD**:
  - **Vercel** (2 proyectos independientes desde este monorepo: `frontend` y `backend`).
  - **Supabase** (PostgreSQL gestionado en producción).
  - **GitHub Actions** para CI (tests, typecheck, build) y CD automatizado hacia Vercel.

---

## 4. Arquitectura del Repositorio

```text
trivault/
├── CONTEXT.md                        # Contexto técnico y guía de trabajo con IA
├── README.md                         # Documentación pública del proyecto
├── .gitignore                        # Exclusión de .env, entornos virtuales y builds
├── .github/
│   └── workflows/                    # Pipelines de CI/CD con GitHub Actions
├── docs/
│   └── especificacion-tecnica.md     # Especificación funcional y técnica inicial
├── backend/                          # API FastAPI (Root Directory en Vercel)
│   ├── app/
│   │   ├── main.py                   # Entrypoint FastAPI, CORS y middlewares
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic BaseSettings (.env)
│   │   │   ├── database.py           # Engine SQLAlchemy, sesiones y soporte MySQL/Postgres
│   │   │   └── security.py           # bcrypt + JWT
│   │   ├── models/                   # Modelos ORM (6 entidades)
│   │   ├── schemas/                  # Esquemas Pydantic Request/Response
│   │   ├── api/
│   │   │   ├── deps.py               # get_db, get_current_user
│   │   │   └── routes/               # auth, accounts, categories, transactions, funds, analytics, imports
│   │   └── services/                 # Lógica de negocio (analytics_service, transferencias, parser CSV)
│   ├── alembic/                      # Migraciones de BD
│   ├── tests/                        # Tests unitarios y de integración (Pytest)
│   ├── requirements.txt
│   ├── .env.example
│   └── vercel.json
└── frontend/                         # Cliente React + Vite + TS (Root Directory en Vercel)
    ├── public/
    ├── src/
    │   ├── api/                      # Cliente HTTP tipado con interceptores JWT
    │   ├── types/                    # Interfaces TypeScript alineadas con Pydantic
    │   ├── context/                  # Estado global de autenticación
    │   ├── components/               # Componentes UI reutilizables y gráficos Recharts
    │   ├── pages/                    # Login, Register, Dashboard, Cuentas, Inversiones, ImportarCSV
    │   ├── utils/                    # Formateadores EUR, fechas y validaciones
    │   ├── App.tsx
    │   └── main.tsx
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── .env.example
    └── vercel.json
```

---

## 5. Modelo de Datos Relacional (6 Entidades)

Todas las tablas de negocio incluyen `user_id` para garantizar aislamiento estricto por usuario.

1. **`users`**
   - `id` (PK), `email` (Unique), `password_hash`, `telegram_chat_id` (Nullable, reservado Fase 3), `annual_inflation_rate` (Decimal 5,2, default `2.50`), `created_at`.
2. **`accounts`**
   - `id` (PK), `user_id` (FK -> `users.id`), `name`, `bucket_type` (ENUM: `daily`, `emergency`, `investment`), `current_balance` (Decimal 12,2), `currency` (default `EUR`).
3. **`categories`**
   - `id` (PK), `user_id` (FK -> `users.id`), `name`, `type` (ENUM: `income`, `expense`), `is_fixed` (Boolean).
4. **`transactions`**
   - `id` (PK), `user_id` (FK -> `users.id`), `account_id` (FK -> `accounts.id`), `destination_account_id` (FK -> `accounts.id`, Nullable), `category_id` (FK -> `categories.id`, Nullable), `amount` (Decimal 12,2 > 0), `type` (ENUM: `income`, `expense`, `transfer`), `description`, `transaction_date`, `import_hash` (Unique Nullable, SHA-256).
   - **Reglas de integridad para transferencias**:
     - Si `type = 'transfer'`: `destination_account_id IS NOT NULL`, `destination_account_id != account_id`, y `category_id IS NULL`. Tanto `account_id` como `destination_account_id` deben pertenecer al `user_id` autenticado.
     - Si `type IN ('income', 'expense')`: `category_id IS NOT NULL` y `destination_account_id IS NULL`.
     - La actualización de saldos al crear, editar o eliminar un movimiento debe ejecutarse dentro de una única transacción atómica en base de datos, cubierta por tests de fallo/rollback.
5. **`fund_positions`**
   - `id` (PK), `user_id` (FK -> `users.id`), `account_id` (FK -> `accounts.id`, cuenta tipo `investment`), `isin`, `fund_name`, `shares` (Decimal 12,4), `total_invested` (Decimal 12,2), `current_nav` (Decimal 12,4), `last_updated`.
6. **`fund_contributions`**
   - `id` (PK), `user_id` (FK -> `users.id`), `fund_position_id` (FK -> `fund_positions.id`), `operation_date` (Date), `order_type` (ENUM: `buy`, `sell`), `shares` (Decimal 12,4), `purchase_nav` (Decimal 12,4), `gross_amount` (Decimal 12,2), `fee` (Decimal 12,2, default `0.00`), `notes` (Nullable), `created_at`.
   - Permite trazabilidad fiel de cada compra/aportación (fecha, participaciones, precio de compra, importe destinado y comisión), recalcular con exactitud la posición agregada en `fund_positions` y conocer el periodo real de tenencia para calcular la inflación acumulada.

---

## 6. Lógica Financiera (`services/analytics_service.py`)

1. **Flujo de Caja y Tasa de Ahorro**:
   - Para un rango de fechas (por defecto, mes natural en curso): suma `type = 'income'` y resta `type = 'expense'`. Excluye explícitamente `type = 'transfer'` para no distorsionar métricas.
   - `tasa_ahorro = ((ingresos - gastos) / ingresos) * 100` (controlando división por cero).
2. **Erosión por Inflación del Dinero Líquido**:
   - Suma los saldos de cuentas `daily` + `emergency`.
   - Aplica `annual_inflation_rate` (`r`) para calcular pérdida anual estimada (`saldo_liquido * (r / 100)`) y su equivalente mensual.
3. **Rendimiento Real de Fondos Indexados**:
   - Compara el valor actual (`shares * current_nav`) frente al capital neto invertido y comisiones registradas en `fund_contributions`.
   - Contrasta la rentabilidad porcentual nominal frente a la inflación acumulada estimada durante el periodo de tenencia real obtenido de `fund_contributions`.

---

## 7. Plan de Implementación por Fases

| Fase | Entregables | Criterio de Aceptación |
|---|---|---|
| **Fase 1: Núcleo, Auth y Estructura** | Scaffolding `backend/` y `frontend/`, conexión MySQL + Alembic, modelos (6 tablas), registro/login JWT, CRUD de cuentas (3 cubos), categorías y transacciones (incluyendo transferencias atómicas) + tests Pytest + CI inicial en GitHub Actions. | Un usuario puede registrarse, iniciar sesión, crear sus cuentas y categorías, registrar ingresos/gastos/transferencias y verificar saldos e integridad entre usuarios. |
| **Fase 2: Dashboard e Inversión** | `analytics_service.py`, CRUD de `fund_positions` y `fund_contributions`, cálculo de erosión por inflación, vistas en React con Tailwind CSS + gráficos en Recharts. | El dashboard muestra los 3 cubos de liquidez, flujo de caja por categorías, impacto de inflación en efectivo y rentabilidad real de fondos. |
| **Fase 3: Automatización** | Parser CSV bancario con deduplicación `import_hash` (SHA-256), endpoint Webhook móvil y módulo de Bot privado de Telegram (Webhook + Vercel Cron `/api/cron/daily-reminder`). | Subir dos veces el mismo CSV no duplica movimientos; el webhook registra gastos; el bot envía recordatorio diario y permite registrar desde chat. |
| **Fase 4: Migración y Producción** | Migración de MySQL a Supabase (PostgreSQL + `psycopg`), configuración de secretos en Vercel/GitHub Actions y despliegue continuo completo. | Aplicación operando en producción bajo HTTPS con datos persistentes en Supabase y CI/CD automático. |

**Estado Fase 1 (gate):** backend + frontend de núcleo implementados, CI creado (`.github/workflows/ci.yml`) y test de rollback mid-transfer añadido. **Pendiente para cerrar la fase:** primera ejecución del CI en verde en GitHub. Detalle operativo en [README.md](README.md) §3.1.

**Decisiones de Fase 1 (cierre):**
- Solo se admite la divisa `EUR` (multidivisa fuera de alcance); las transferencias entre divisas distintas se rechazan.
- `PATCH /transactions/{id}` permite editar todos los campos; el servicio revierte el efecto antiguo y aplica el nuevo en una única transacción, bloqueando las cuentas implicadas en orden de `id`.
- La categoría de un movimiento debe ser del mismo tipo (`income`/`expense`) que el movimiento.
- Todas las fechas se almacenan y devuelven en UTC con offset explícito (MySQL `DATETIME` no guarda zona).

---

## 8. Flujo de Trabajo Git y CI/CD

- **Ramas**:
  - `main`: rama estable/producción. No se trabaja ni se resuelven conflictos directamente aquí.
  - `develop`: rama auxiliar de integración. Todas las ramas de trabajo se fusionan primero en `develop`.
  - Ramas cortas desde `develop`: `feat/<nombre>`, `fix/<nombre>`, `docs/<nombre>`, `refactor/<nombre>`, `test/<nombre>`.
- **Commits y Versionado**:
  - Commits frecuentes, atómicos y con mensajes explícitos siguiendo Conventional Commits (`feat:`, `fix:`, `sec:`, `docs:`, `test:`, `refactor:`, `chore:`).
  - Etiquetas (tags) semánticas periódicas en `main` al cerrar hitos o fases (`v0.1.0`, `v0.2.0`, etc.).
- **GitHub Actions**:
  - CI automático en Pull Requests y pushes a `develop` / `main` (`.github/workflows/ci.yml`: ruff + round-trip Alembic + Pytest contra MySQL 8 + `tsc` / `vite build`).
  - CD automático para desplegar a Vercel tras superar los checks (no mergear features directamente en ramas de deploy sin revisión).
