# Cost-Quality Optimization Frontend

React + Vite frontend for the Cost-Quality Optimization System.

## Features

- 📊 Interactive dashboard for analyzing LLM model performance
- 📤 Upload JSON prompts or add manually
- 🎯 Multi-model selection and comparison
- 📈 Pareto frontier visualization
- 💰 Cost comparison tables
- 🎯 Smart recommendations with confidence scores
- ⚙️ Configurable temperature and max tokens

## Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:3000` and proxy API requests to `http://localhost:8000`.

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and services
│   ├── components/    # React components
│   │   ├── Dashboard.jsx
│   │   ├── PromptInput.jsx
│   │   ├── ModelSelector.jsx
│   │   ├── ConfigurationPanel.jsx
│   │   ├── ResultsDisplay.jsx
│   │   ├── RecommendationCard.jsx
│   │   ├── CostComparisonTable.jsx
│   │   └── ParetoChart.jsx
│   ├── App.jsx        # Main app component
│   ├── main.jsx       # Entry point
│   └── index.css      # Global styles
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## Usage

1. **Add Prompts**: Upload a JSON file or add prompts manually
2. **Select Models**: Choose 2+ models to compare
3. **Configure**: Set temperature and max tokens
4. **Analyze**: Click "Analyze Models" to run the analysis
5. **Review Results**: View recommendations, cost comparisons, and Pareto frontier

## Environment Variables

Create a `.env` file to customize the API URL:

```
VITE_API_URL=http://localhost:8000
```

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Lucide React** - Icons
