import React from 'react'
import { BarChart3, Clock, DollarSign, CheckCircle, XCircle, Activity } from 'lucide-react'

const MetricsTable = ({ summary }) => {
  if (!summary || Object.keys(summary).length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-primary" />
          Detailed Metrics
        </h2>
        <p className="text-gray-500 dark:text-gray-400">No metrics available</p>
      </div>
    )
  }

  const models = Object.keys(summary)

  const formatCost = (cost) => `$${(cost || 0).toFixed(8)}`
  const formatPercent = (value) => `${((value || 0) * 100).toFixed(1)}%`
  const formatMs = (ms) => `${(ms || 0).toFixed(0)}ms`

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <BarChart3 className="w-6 h-6 text-primary" />
        Detailed Metrics
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-300 dark:border-gray-600">
              <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-white">Model</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">
                <div className="flex items-center justify-end gap-1">
                  <DollarSign className="w-4 h-4" />
                  Cost/Call
                </div>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">
                <div className="flex items-center justify-end gap-1">
                  <Clock className="w-4 h-4" />
                  Latency
                </div>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">
                <div className="flex items-center justify-end gap-1">
                  <Activity className="w-4 h-4" />
                  Consistency
                </div>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">Success</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">Validation</th>
            </tr>
          </thead>
          <tbody>
            {models.map((modelName) => {
              const metrics = summary[modelName]
              if (!metrics) return null
              
              const successRate = metrics.total_calls > 0 ? (metrics.successful_calls / metrics.total_calls) * 100 : 0

              return (
                <tr
                  key={modelName}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                    {modelName}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-gray-700 dark:text-gray-300">
                    {formatCost(metrics.avg_cost_per_call)}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                    <div>
                      {formatMs(metrics.avg_latency_ms)}
                      <div className="text-xs text-gray-500">
                        p95: {formatMs(metrics.p95_latency_ms)}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {formatPercent(metrics.consistency_score)}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className={`flex items-center justify-end gap-1 ${successRate === 100 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                      {successRate === 100 ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      {successRate.toFixed(0)}%
                      <span className="text-xs text-gray-500">
                        ({metrics.successful_calls}/{metrics.total_calls})
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    {metrics.avg_validation_score > 0 ? (
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {metrics.avg_validation_score.toFixed(1)}/100
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Calls</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {Object.values(summary).reduce((sum, m) => sum + (m?.total_calls || 0), 0)}
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Cost</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            ${Object.values(summary).reduce((sum, m) => sum + (m?.total_cost || 0), 0).toFixed(6)}
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Models Tested</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {models.length}
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Success</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {models.length > 0 ? (Object.values(summary).reduce((sum, m) => {
              const rate = m && m.total_calls > 0 ? (m.successful_calls / m.total_calls) : 0
              return sum + rate
            }, 0) / models.length * 100).toFixed(0) : 0}%
          </p>
        </div>
      </div>
    </div>
  )
}

export default MetricsTable