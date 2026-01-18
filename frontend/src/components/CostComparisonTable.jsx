import React from 'react'
import { Settings } from 'lucide-react'

const ConfigurationPanel = ({ temperature, setTemperature, maxTokens, setMaxTokens }) => {
  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        Configuration
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Temperature: {temperature.toFixed(1)}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>Deterministic (0.0)</span>
            <span>Creative (2.0)</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Max Tokens: {maxTokens}
          </label>
          <input
            type="range"
            min="50"
            max="2000"
            step="50"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>Short (50)</span>
            <span>Long (2000)</span>
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          <strong>Note:</strong> Temperature controls randomness (0=deterministic, 2=creative). Max tokens limits response length.
        </p>
      </div>
    </div>
  )
}

export default ConfigurationPanel