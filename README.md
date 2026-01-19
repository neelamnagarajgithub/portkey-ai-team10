# Cost-Quality Optimization via Historical Replay

## Problem Statement
Model choices are often made blindly. Companies spend thousands on premium LLMs without knowing if cheaper alternatives could work just as well for their specific use case.

## Solution
A system that:
- ✅ Replays historical prompt-completion data across multiple models
- ✅ Evaluates cost, quality, and refusal rates
- ✅ Measures trade-offs with visual Pareto frontier
- ✅ Recommends optimal model configurations with confidence scores

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Demo Flow
1. Upload historical prompts (JSON)
2. Select models to compare (GPT-4o, GPT-4o-mini, Claude, etc.)
3. Click "Analyze" → System replays across all models
4. View results:
   - Cost comparison table
   - Pareto frontier chart (cost vs quality)
   - Smart recommendation: "Use Model X for Y% savings with Z% quality retention"

## Architecture

### Backend (FastAPI)
- `main.py` - API endpoints
- `replay_engine.py` - Core replay logic using LiteLLM
- `portkey_client.py` - Pricing data from Portkey API
- `quality_scorer.py` - Consistency & quality metrics
- `recommender.py` - Intelligent recommendation engine

### Frontend (React + Vite)
- Interactive dashboard
- Pareto frontier visualization (Recharts)
- Real-time progress updates
- Dark mode UI

## Data Flow
```
Historical Prompts (JSON/DB)
    ↓
Replay Engine (LiteLLM)
    ↓
Multiple Model APIs (OpenAI, Anthropic, Google)
    ↓
Quality Scorer + Cost Calculator (Portkey)
    ↓
Recommendation Engine
    ↓
Interactive Dashboard
```

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, LiteLLM, Pydantic, Pandas
- **Frontend**: React, Vite, Recharts, TailwindCSS
- **Pricing**: Portkey Models API (free, no auth)
- **LLM Gateway**: LiteLLM (multi-provider)

## Features

### ✅ Implemented
- Historical replay across 3+ models
- Portkey pricing integration
- Quality consistency scoring
- Pareto frontier analysis
- Smart recommendations

### 🚧 Roadmap
- Guardrail impact measurement
- Integration with s_enricher LLMCallDB
- Custom quality metrics
- Cost projections
- A/B testing automation

## License
JMV
