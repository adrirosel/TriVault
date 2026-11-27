DOCUMENTO DE ARQUITECTURA Y ESPECIFICACIÓN FUNCIONAL 

# Gestor de Finanzas Personales, Liquidez e Inversión 

Plan maestro de ingeniería de software, modelo de datos, stack tecnológico y protocolo de desarrollo asistido con Cursor. 

## 1. Visión del Producto y Alcance Consolidado 

El objetivo de este proyecto es construir una aplicación web Full-Stack orientada al control granular del flujo de caja personal, la segmentación patrimonial por niveles de liquidez y el seguimiento realista del rendimiento de inversiones frente a la inflación. El sistema está diseñado tanto para resolver una necesidad real de gestión financiera diaria como para servir de proyecto técnico de referencia en un portafolio profesional de desarrollo de software. 

Para garantizar que la aplicación sea técnicamente viable, segura y financieramente rigurosa, se ha realizado una auditoría funcional que integra las propuestas originales validadas junto con alternativas de ingeniería para los requisitos que presentan bloqueos normativos o de experiencia de usuario. 

|Módulo Funcional|Propuesta Original|Solución Técnica Aprobada|
|---|---|---|
|Segmentación de<br>Capital|Separar el dinero en tres bloques: uso<br>diario, colchón de emergencia e<br>inversión en fondos.|Aprobada sin cambios.Modelado<br>mediante entidades de cuentas tipadas<br>(<br>checking ,<br>emergency ,<br>investment ) con balances<br>independientes y cálculo agregado de<br>patrimonio neto.|
|Control de Flujo y<br>Categorías|Registro diario de ingresos y gastos<br>clasificados para identificar fugas de<br>capital y capacidad de ahorro.|Aprobada sin cambios.CRUD<br>completo de transacciones vinculadas a<br>categorías personalizables (fijas y<br>variables) con filtros temporales y<br>analítica por partidas.|
|Captura de Pagos con<br>Tarjeta|Interceptar en tiempo real cada pago<br>realizado con tarjeta bancaria<br>directamente en la aplicación.|Sustituida por limitaciones PSD2.<br>Implementación en dos fases: (1)<br>Importador de extractos CSV/Excel<br>bancarios con detección de duplicados<br>mediante hash; (2) Endpoint Webhook<br>para recibir notificaciones desde Atajos<br>(iOS) o MacroDroid (Android).|
|Recordatorios Diarios|Enviar 1 o 2 notificaciones diarias al<br>usuario autenticado para recordar el<br>registro de gastos.|Sustituida por fiabilidad móvil.<br>Integración con un Bot privado de<br>Telegram disparado por un Cron Job<br>diario, permitiendo además registrar<br>gastos respondiendo directamente al<br>mensaje sin abrir el navegador.|



Especificación Técnica — Gestor de Finanzas Personales 

Page 1 of 6 

|Módulo Funcional|Propuesta Original|Solución Técnica Aprobada|
|---|---|---|
|Inflación e Inversiones|Cruzar diariamente el valor de los<br>fondos indexados con el IPC actualizado<br>en tiempo real en España.|Rediseñada por rigor financiero.<br>Cálculo de rentabilidad real de fondos<br>(capital aportado vs. valor actual por<br>ISIN) por un lado, y parámetro manual<br>de IPC anual aplicado específicamente<br>al cálculo de pérdida de poder<br>adquisitivo del dinero parado en colchón<br>y cuenta corriente.|
|Dashboard Analítico|Panel visual centralizado con métricas<br>de evolución, distribución y balances.|Aprobada con arquitectura limpia.<br>Vista principal con resumen de los tres<br>cubos de liquidez, flujo de caja mensual<br>(ingresos vs. gastos), distribución por<br>categorías y erosión por inflación del<br>efectivo.|



## 2. Stack Tecnológico y Estrategia de Evolución 

La selección tecnológica equilibra un entorno de desarrollo robusto y tipado con una ruta clara de migración hacia servicios gestionados en la nube sin reescribir la lógica de negocio. 

- Frontend <mark>( /frontend )</mark> : Desarrollado con React, Vite y TypeScript en modo estricto. Se utilizará una arquitectura modular basada en componentes funcionales, gestión de estado del servidor mediante peticiones tipadas con interfaces compartidas, y una librería de gráficos ligera para las visualizaciones del dashboard. 

- Backend <mark>( /backend )</mark> : Desarrollado en Python 3.11+ utilizando FastAPI como framework principal por su alto rendimiento, validación automática de esquemas mediante Pydantic y generación nativa de documentación interactiva OpenAPI/Swagger. 

- Capa de Acceso a Datos y Migración (MySQL a Supabase): En la fase inicial de desarrollo local y pruebas de integración se utilizará MySQL como motor relacional, interactuando a través de SQLAlchemy (ORM) y Alembic para el control de versiones de migraciones. Gracias al uso de SQLAlchemy como capa de abstracción y evitando funciones propietarias exclusivas de MySQL en las consultas, el proyecto podrá migrar posteriormente a Supabase (PostgreSQL) cambiando únicamente el controlador de conexión ( <mark>psycopg )</mark> y la cadena <mark>DATABASE_URL</mark> en las variables de entorno, manteniendo intactos los modelos y repositorios. 

## 3. Arquitectura del Repositorio y Organización de Carpetas 

El proyecto se estructurará como un monorepo limpio con separación estricta de responsabilidades entre cliente y servidor. Las dos carpetas principales en la raíz del repositorio serán <mark>frontend/</mark> y <mark>backend/ ,</mark> acompañadas únicamente por los archivos globales de configuración y documentación. 

Especificación Técnica — Gestor de Finanzas Personales 

Page 2 of 6 

```text
gestor-finanzas-personales/
├── README.md                      # Documentación técnica, arquitectura y guía de despliegue
├── .gitignore                     # Exclusión de entornos virtuales, node_modules y .env
├── backend/                       # Aplicación servidor en Python + FastAPI
│   ├── app/
│   │   ├── main.py                # Punto de entrada FastAPI, configuración CORS y middlewares
│   │   ├── core/
│   │   │   ├── config.py          # Gestión de variables de entorno (Pydantic BaseSettings)
│   │   │   ├── database.py        # Motor SQLAlchemy, sesión y abstracción MySQL -> Supabase
│   │   │   └── security.py        # Hashing de contraseñas (bcrypt) y generación/validación JWT
│   │   ├── models/                # Modelos ORM (User, Account, Category, Transaction, FundPosition)
│   │   ├── schemas/               # Esquemas Pydantic para validación de Request y Response
│   │   ├── api/
│   │   │   ├── deps.py            # Dependencias inyectables (get_db, get_current_user)
│   │   │   └── routes/            # Endpoints organizados por dominio (auth, accounts, transactions, analytics, imports)
│   │   └── services/              # Lógica de negocio pura (cálculo inflación, parser CSV, agregaciones)
│   ├── alembic/                   # Historial de migraciones de esquema de base de datos
│   ├── tests/                     # Pruebas unitarias y de integración con Pytest
│   ├── requirements.txt           # Dependencias fijadas de Python
│   └── vercel.json                # Configuración de enrutamiento para despliegue serverless en Vercel
└── frontend/                      # Aplicación cliente en React + Vite + TypeScript
    ├── public/                    # Activos estáticos
    ├── src/
    │   ├── api/                   # Cliente HTTP centralizado (Axios/Fetch) con interceptores JWT
    │   ├── types/                 # Definiciones TypeScript estrictas alineadas con los esquemas FastAPI
    │   ├── context/               # Contexto global de autenticación y estado de sesión
    │   ├── components/            # Componentes reutilizables de interfaz (tablas, formularios, tarjetas KPI)
    │   ├── pages/                 # Vistas principales (Login, Register, Dashboard, Cuentas, Inversiones, ImportarCSV)
    │   ├── utils/                 # Formateadores de moneda (EUR), fechas y validaciones locales
    │   ├── App.tsx                # Enrutamiento protegido y estructura de navegación
    │   └── main.tsx               # Punto de montaje de React
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

Especificación Técnica — Gestor de Finanzas Personales 

Page 3 of 6 

## 4. Diseño de la Base de Datos Relacional 

Toda consulta de lectura, escritura o borrado en la base de datos estará obligatoriamente filtrada por <mark>user_id</mark> extraído del token JWT autenticado, garantizando aislamiento total entre usuarios. El modelo relacional consta de seis entidades fundamentales: 

|Tabla|Columnas Clave y Tipos|Propósito y Reglas de Integridad|
|---|---|---|
|users|id(PK),<br>email(Unique),<br>password_hash ,<br>telegram_chat_id(Nullable),<br>annual_inflation_rate<br>(Decimal, default 2.50),<br>created_at|Almacena credenciales, el identificador opcional<br>para notificaciones en Telegram y la tasa de<br>inflación anual configurable por el usuario para<br>los cálculos de erosión monetaria.|
|accounts|id(PK),<br>user_id(FK),<br>name ,<br>bucket_type(ENUM:<br>daily ,<br>emergency ,<br>investment ),<br>current_balance(Decimal<br>12,2),<br>currency(EUR)|Implementa la separación en los tres cubos<br>financieros. El saldo se actualiza de forma<br>transaccional ante cada ingreso, gasto o<br>transferencia interna.|
|categories|id(PK),<br>user_id(FK),<br>name ,<br>type(ENUM:<br>income ,<br>expense ),<br>is_fixed<br>(Boolean)|Permite clasificar movimientos y distinguir gastos<br>estructurales fijos (alquiler, suministros) de gastos<br>variables discrecionales (ocio, restauración).|
|transactions|id(PK),<br>user_id(FK),<br>account_id(FK),<br>category_id(FK),<br>amount<br>(Decimal 12,2),<br>type(ENUM:<br>income ,<br>expense ,<br>transfer ),<br>description ,<br>transaction_date ,<br>import_hash(Unique Nullable)|Registro central de movimientos. El campo<br>import_hash(generado mediante SHA-256<br>de fecha + importe + concepto) impide duplicados<br>al subir extractos CSV bancarios repetidos.|
|fund_positions|id(PK),<br>user_id(FK),<br>account_id(FK),<br>isin ,<br>fund_name ,<br>shares(Decimal<br>12,4),<br>total_invested<br>(Decimal 12,2),<br>current_nav<br>(Decimal 12,4),<br>last_updated|Registra las posiciones en fondos indexados<br>vinculadas a una cuenta de tipo<br>investment .<br>Calculaplusvalía latente comparando<br>shares *<br>current_navfrente a<br>total_invested .|



## 5. Lógica Financiera y Cálculos del Sistema 

Para evitar distorsiones analíticas en el dashboard, el backend expondrá un servicio específico ( <mark>services/analytics_service.py</mark> ) encargado de ejecutar tres bloques de cálculo bien diferenciados: 

Especificación Técnica — Gestor de Finanzas Personales 

Page 4 of 6 

1. Balance de Flujo de Caja y Tasa de Ahorro: Para un rango de fechas seleccionado (por defecto, el mes natural en curso), suma todos los registros con <mark>type = 'income'</mark> y resta los registros con <mark>type = 'expense' ,</mark> excluyendo explícitamente los movimientos internos entre cuentas propias <mark>( type = 'transfer' )</mark> para no inflar artificialmente ingresos ni gastos. La tasa de ahorro se calcula como <mark>((Ingresos - Gastos) / Ingresos) × 100 .</mark> 

2. Erosión por Inflación del Dinero Líquido: Se toma la suma de saldos de las cuentas marcadas como <mark>daily</mark> y <mark>emergency .</mark> Aplicando la tasa de inflación anual configurada por el usuario ( r ), se calcula la pérdida estimada de poder adquisitivo anual <mark>( Saldo_Liquido × (r / 100)</mark> ) y mensual, mostrando de forma transparente el coste de oportunidad de mantener exceso de liquidez fuera de activos remunerados. 

3. Rendimiento Real de Fondos Indexados: Cada posición en <mark>fund_positions</mark> compara el valor de mercado actual ( <mark>participaciones × valor_liquidativo</mark> ) contra el capital neto aportado. La rentabilidad porcentual nominal se compara frente a la inflación acumulada del periodo de tenencia para determinar si la cartera bate o no al IPC en términos reales. 

## 6. Plan de Implementación por Fases 

El desarrollo se ejecutará de forma incremental, validando cada fase antes de iniciar la siguiente: 

|Fase|Entregables Técnicos|Criterio de Aceptación|
|---|---|---|
|Fase 1: Núcleo<br>y Auth|Estructura de carpetas<br>frontend/y<br>backend/ , conexión a MySQL con<br>SQLAlchemy, registro/login con JWT, CRUD<br>de cuentas (3 cubos), categorías y<br>transacciones manuales.|Un usuario puede registrarse, iniciar<br>sesión, crear sus tres cuentas, registrar<br>ingresos/gastos y verificar que los saldos<br>se actualizan correctamente sin acceso<br>cruzado entre usuarios.|
|Fase 2:<br>Dashboard e<br>Inversión|Endpoints de agregación analítica, módulo de<br>posiciones en fondos indexados (ISIN,<br>participaciones, aportaciones), cálculo de<br>erosión por inflación en liquidez y gráficos en<br>React.|El dashboard muestra el patrimonio<br>dividido por cubos, la comparativa<br>ingresos/gastos por categoría, la<br>rentabilidad de fondos y el impacto anual<br>de la inflación sobre el colchón.|
|Fase 3:<br>Automatización|Parser de extractos CSV bancarios con<br>deduplicación por hash, endpoint Webhook<br>para registro rápido desde el móvil y cron job<br>conectado a Bot de Telegram para<br>recordatorios diarios.|Subir dos veces el mismo CSV del banco<br>no duplica movimientos, y el bot envía el<br>recordatorio diario permitiendo registrar un<br>gasto desde el chat.|
|Fase 4:<br>Migración y<br>Cloud|Migración de base de datos de MySQL local a<br>Supabase (PostgreSQL), configuración de<br>variables de entorno de producción y<br>despliegue continuo en Vercel.|La aplicación funciona en producción con<br>HTTPS, base de datos persistente en<br>Supabase y flujos completos operativos.|



## 7. Estrategia de Despliegue en Vercel 

El repositorio se conectará directamente a Vercel configurando dos proyectos independientes apuntando al mismo repositorio de GitHub mediante la opción Root Directory, lo que permite despliegues atómicos e independientes para cliente y servidor: 

Especificación Técnica — Gestor de Finanzas Personales 

Page 5 of 6 

- Despliegue del Frontend ( <mark>Root Directory: frontend</mark> ): Vercel detectará automáticamente el preset de Vite. Ejecutará <mark>npm run build</mark> y servirá los archivos estáticos compilados desde su red CDN global. Se configurará la variable de entorno <mark>VITE_API_URL</mark> apuntando a la URL pública del backend y un archivo <mark>vercel.json</mark> con reglas de reescritura hacia <mark>/index.html</mark> para soportar el enrutamiento SPA de React Router sin errores 404 al recargar rutas. 

- Despliegue del Backend ( <mark>Root Directory: backend</mark> ): FastAPI se desplegará utilizando el runtime oficial de Python de Vercel mediante funciones serverless. Se incluirá un archivo <mark>backend/vercel.json</mark> que redirija todas las peticiones entrantes hacia <mark>app/main.py .</mark> Las 

- credenciales críticas ( <mark>DATABASE_URL</mark> de Supabase, <mark>SECRET_KEY</mark> para JWT, 

- <mark>TELEGRAM_BOT_TOKEN</mark> y <mark>ALLOWED_ORIGINS</mark> para CORS) se almacenarán cifradas en el panel de 

- Environment Variables de Vercel. Para los recordatorios diarios, se utilizará Vercel Cron Jobs invocando un endpoint protegido ( <mark>/api/cron/daily-reminder )</mark> validado mediante cabecera <mark>Authorization: Bearer CRON_SECRET .</mark> 

## 8. Gobernanza y Metodología de Trabajo con Cursor 

Regla de Oro de Colaboración (Archivo <mark>.cursorrules )</mark> : Antes de escribir, modificar o eliminar cualquier archivo de código, la IA debe presentar su propuesta de diseño, explicar qué archivos va a tocar y qué decisiones técnicas implica, y esperar confirmación explícita del desarrollador antes de implementar nada. El control arquitectónico pertenece siempre al autor del proyecto. 

- Diseña tú la base de datos y la arquitectura primero: Define tú las tablas, las relaciones y los endpoints antes de pedirle código a Cursor. No delegues el modelado inicial de entidades ni la estructura de carpetas a la generación automática. 

- Pide módulos pequeños y revísalos: No le pidas "hazme el dashboard". Pídele primero la consulta SQL o el endpoint que agrupa los gastos por categoría, léelo línea a línea, asegúrate de que no hay fallos de seguridad (como que un usuario pueda ver los gastos de otro si cambia el ID en la petición) y refactóralo a tu estilo antes de pasar al componente visual. 

- Haz commits atómicos y con sentido: Mantén un historial de Git granular y profesional con mensajes descriptivos siguiendo convenciones estándar (por ejemplo, feat: add CSV bank statement parser <u><mark>,</mark></u> <mark>fix: prevent duplicate transactions on import</mark> , sec: enforce user_id filter on account queries ). Evita los commits masivos que agrupan múltiples funcionalidades sin revisar, asegurando que cada punto del historial sea auditable, reversible y comprensible en una revisión técnica o entrevista. 

Especificación Técnica — Gestor de Finanzas Personales 

Page 6 of 6 

