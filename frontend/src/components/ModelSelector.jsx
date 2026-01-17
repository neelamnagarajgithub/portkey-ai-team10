import React from 'react'
import { Cpu } from 'lucide-react'

const ModelSelector = ({ selectedModels, setSelectedModels }) => {
  const availableModels = [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', tier: 'Premium', cost: '$$$$' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', tier: 'Economy', cost: '$' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI', tier: 'Budget', cost: '$' },
    { id: 'claude-3-5-sonnet-20250122', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', tier: 'Premium', cost: '$$$' },
    { id: 'claude-3-5-haiku-20250122', name: 'Claude 3.5 Haiku', provider: 'Anthropic', tier: 'Economy', cost: '$' },
  ]

  const toggleModel = (modelId) => {
    if (selectedModels.includes(modelId)) {
      setSelectedModels(selectedModels.filter(m => m !== modelId))
    } else {
      setSelectedModels([...selectedModels, modelId])
    }
  }

  const getTierColor = (tier) => {
    switch (tier) {
      case 'Premium': return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
      case 'Economy': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
      case 'Budget': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <Cpu className="w-6 h-6 text-secondary" />
        Select Models to Compare
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {availableModels.map((model) => (
          <div
            key={model.id}
            onClick={() => toggleModel(model.id)}
            className={`
              p-4 rounded-lg border-2 cursor-pointer transition-all
              ${selectedModels.includes(model.id)
                ? 'border-primary bg-primary/5 dark:bg-primary/10'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-gray-900 dark:text-white">{model.name}</h3>
              <div className={`
                w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0
                ${selectedModels.includes(model.id)
                  ? 'border-primary bg-primary'
                  : 'border-gray-300 dark:border-gray-600'
                }
              `}>
                {selectedModels.includes(model.id) && (
                  <svg className="w-3 h-3 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M5 13l4 4L19 7"></path>
                  </svg>
                )}
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{model.provider}</p>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded-full ${getTierColor(model.tier)}`}>
                {model.tier}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {model.cost}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          💡 <strong>Tip:</strong> Select at least 2 models to compare. We recommend testing a premium model against economy alternatives.
        </p>
      </div>

      {selectedModels.length > 0 && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Selected: {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}

export default ModelSelector