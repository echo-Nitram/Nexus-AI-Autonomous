# Nexus AI Autonomous Trader v2.0

Ecosistema de Trading Agentico impulsado por LLMs. La plataforma no ejecuta reglas rigidas — entiende por que opera, gestiona el riesgo de forma autonoma y aprende de sus errores.

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│  Dashboard │ Thought Log │ Strategy Editor          │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                   Backend (FastAPI)                  │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Perception  │→ │  Reasoning   │→ │   Action   │ │
│  │   Layer     │  │    Layer     │  │   Layer    │ │
│  │             │  │              │  │            │ │
│  │ Market Data │  │  LangGraph   │  │  Executor  │ │
│  │ Sentiment   │  │  Agent Flow  │  │  (CCXT)    │ │
│  │ News/Social │  │  Strategy    │  │  Risk      │ │
│  │             │  │  Engine      │  │  Guardrail │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐                  │
│  │   Memory    │  │ Notifications│                  │
│  │  (pgvector) │  │  (Telegram)  │                  │
│  └─────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────┘
```

## Flujo del Agente (LangGraph)

```
Perceive → Recall Memory → Reason → Check Risk → Execute → Reflect
```

1. **Perceive**: Recoge datos de mercado (OHLCV, indicadores tecnicos) y sentimiento (noticias, Fear & Greed Index)
2. **Recall Memory**: Busca situaciones similares en la memoria vectorial (pgvector)
3. **Reason**: El LLM evalua la estrategia del usuario contra el estado actual del mercado
4. **Check Risk**: Guardrail deterministico (NO IA) que bloquea operaciones que excedan limites
5. **Execute**: Ejecuta la operacion via CCXT (shadow o produccion)
6. **Reflect**: Almacena el ciclo completo como memoria para aprendizaje futuro

## Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI |
| AI/LLM | LangGraph + Claude/GPT-4o |
| Exchanges | CCXT (Binance, Hyperliquid) |
| Frontend | Next.js 15 + React 19 + Tailwind + Shadcn/UI |
| Base de datos | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis + Celery |
| Infraestructura | Docker + Docker Compose |
| Notificaciones | Telegram Bot API |

## Inicio Rapido

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus API keys
```

### 2. Levantar con Docker

```bash
docker compose up -d
```

Esto inicia:
- PostgreSQL con pgvector en puerto 5432
- Redis en puerto 6379
- Backend FastAPI en http://localhost:8000
- Frontend Next.js en http://localhost:3000

### 3. Desarrollo local

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/users/` | POST | Crear usuario |
| `/api/v1/users/{id}/exchange-keys` | PUT | Configurar API keys del exchange |
| `/api/v1/strategies/` | POST | Crear estrategia en lenguaje natural |
| `/api/v1/trading/execute` | POST | Ejecutar trade manual |
| `/api/v1/trading/positions/{user_id}` | GET | Posiciones abiertas |
| `/api/v1/dashboard/portfolio/{user_id}` | GET | Resumen del portfolio |
| `/api/v1/dashboard/thoughts/{user_id}` | GET | Log de pensamientos de la IA |

## Seguridad

- API keys del exchange cifradas con Fernet (AES-128)
- Risk Guardrail deterministico que la IA NO puede sobreescribir
- Modo Shadow obligatorio las primeras 48 horas
- Limites configurables: max posicion, max perdida diaria, max trades
