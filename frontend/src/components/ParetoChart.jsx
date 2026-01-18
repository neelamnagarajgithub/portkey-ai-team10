import React from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
  Label
} from 'recharts'

const ParetoChart = ({ data, summary }) => {
  // Prepare data for chart
  const chartData = data.map(point => ({
    ...point,
    // Convert cost for better visualization (cost per call)
    costDisplay: point.cost * 1000, // per 1K tokens
    qualityPct: point.quality * 100,
    // Size for bubble (based on success rate)
    size: summary[point.model] ? (summary[point.model].successful_calls / summary[point.model].total_calls) * 100 : 50
  }))

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const modelSummary = summary[data.model]
      
      return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-bold text-gray-900 dark:text-white mb-2">{data.model}</p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-600 dark:text-gray-400">
              Cost: <span className="font-semibold">${(data.cost * 1000).toFixed(4)}</span> / 1K tokens
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Quality: <span className="font-semibold">{data.qualityPct.toFixed(1)}%</span>
            </p>
            {modelSummary && (
              <>
                <p className="text-gray-600 dark:text-gray-400">
                  Success Rate: <span className="font-semibold">
                    {((modelSummary.successful_calls / modelSummary.total_calls) * 100).toFixed(1)}%
                  </span>
                </p>
                <p className="text-gray-600 dark:text-gray-400">
                  Latency: <span className="font-semibold">{modelSummary.avg_latency_ms.toFixed(0)}ms</span>
                </p>
                <p className="text-gray-600 dark:text-gray-400">
                  Validation: <span className="font-semibold">{modelSummary.avg_validation_score.toFixed(1)}/100</span>
                </p>
              </>
            )}
            {data.is_optimal && (
              <p className="text-green-600 dark:text-green-400 font-semibold mt-2">
                ⭐ Pareto Optimal
              </p>
            )}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full">
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 60, left: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              type="number"
              dataKey="costDisplay"
              name="Cost"
              stroke="#9ca3af"
              domain={['dataMin - 0.01', 'dataMax + 0.01']}
            >
              <Label value="Cost per 1K tokens ($)" position="bottom" offset={40} style={{ fill: '#9ca3af' }} />
            </XAxis>
            <YAxis
              type="number"
              dataKey="qualityPct"
              name="Quality"
              stroke="#9ca3af"
              domain={['dataMin - 5', 'dataMax + 5']}
            >
              <Label value="Quality Score (%)" angle={-90} position="left" offset={40} style={{ fill: '#9ca3af' }} />
            </YAxis>
            <ZAxis type="number" dataKey="size" range={[100, 400]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Non-optimal points */}
            <Scatter
              name="Models"
              data={chartData.filter(d => !d.is_optimal)}
              fill="#8b5cf6"
            />
            
            {/* Optimal points (Pareto frontier) */}
            <Scatter
              name="Pareto Optimal"
              data={chartData.filter(d => d.is_optimal)}
              fill="#10b981"
              shape="star"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-sm text-gray-600 dark:text-gray-400 space-y-1">
        <p className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-green-500"></span>
          <strong>Green stars</strong> are Pareto optimal (best cost-quality trade-offs)
        </p>
        <p className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-purple-500"></span>
          <strong>Purple circles</strong> are dominated by better alternatives
        </p>
        <p className="mt-2">
          💡 <strong>Tip:</strong> Move towards top-left for better quality and lower cost
        </p>
      </div>
    </div>
  )
}

export default ParetoChart