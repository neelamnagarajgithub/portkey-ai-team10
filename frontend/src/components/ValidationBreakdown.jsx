import React from 'react'
import { CheckCircle, AlertTriangle } from 'lucide-react'

const ValidationBreakdown = ({ results }) => {
  // Safely handle empty or undefined results
  if (!results || results.length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <CheckCircle className="w-6 h-6 text-success" />
          Validation Breakdown
        </h2>
        <p className="text-gray-500 dark:text-gray-400">No validation data available</p>
      </div>
    )
  }

  // Count validation methods used
  const validationStats = results.reduce((acc, result) => {
    if (result.validation_method) {
      acc[result.validation_method] = (acc[result.validation_method] || 0) + 1
    }
    return acc
  }, {})

  // Count confidence levels
  const confidenceStats = results.reduce((acc, result) => {
    if (result.validation_confidence) {
      acc[result.validation_confidence] = (acc[result.validation_confidence] || 0) + 1
    }
    return acc
  }, {})

  const validatedCount = results.filter(r => r.validation_score !== null && r.validation_score !== undefined).length
  const validationRate = results.length > 0 ? (validatedCount / results.length) * 100 : 0

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <CheckCircle className="w-6 h-6 text-success" />
        Validation Breakdown
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Validation Rate */}
        <div>
          <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Validation Rate</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${validationRate === 100 ? 'bg-green-500' : 'bg-yellow-500'}`}
                  style={{ width: `${validationRate}%` }}
                />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {validationRate.toFixed(0)}%
            </div>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            {validatedCount} of {results.length} results validated
          </p>
        </div>

        {/* Validation Methods */}
        <div>
          <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Methods Used</h3>
          {Object.keys(validationStats).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(validationStats).map(([method, count]) => (
                <div key={method} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {method.replace(/_/g, ' ')}
                  </span>
                  <span className="badge-info">
                    {count} ({validatedCount > 0 ? ((count / validatedCount) * 100).toFixed(0) : 0}%)
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">No validation methods recorded</p>
          )}
        </div>
      </div>

      {/* Confidence Levels */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Confidence Levels</h3>
        <div className="grid grid-cols-3 gap-4">
          {['HIGH', 'MEDIUM', 'LOW'].map(level => {
            const count = confidenceStats[level] || 0
            const percent = validatedCount > 0 ? (count / validatedCount) * 100 : 0
            return (
              <div key={level} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{level}</span>
                  {level === 'HIGH' && <CheckCircle className="w-5 h-5 text-green-500" />}
                  {level === 'MEDIUM' && <AlertTriangle className="w-5 h-5 text-yellow-500" />}
                  {level === 'LOW' && <AlertTriangle className="w-5 h-5 text-orange-500" />}
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{percent.toFixed(0)}% of validated</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ValidationBreakdown