import React from 'react'
import RecommendationCard from './RecommendationCard'
import ParetoChart from './ParetoChart'
import MetricsTable from './MetricsTable'
import ValidationBreakdown from './ValidationBreakdown'
import { TrendingUp, CheckCircle } from 'lucide-react'

const AnalysisResults = ({ data }) => {
  console.log('🔍 AnalysisResults received:', data)
  
  if (!data) {
    console.log('❌ No data - returning null')
    return null
  }

  // Safely check if all_results exists and has length
  const allResults = data.all_results || []
  const hasResults = allResults.length > 0

  console.log('✅ Data exists:', {
    hasRecommendation: !!data.recommendation,
    hasParetoFrontier: !!data.pareto_frontier,
    hasSummary: !!data.summary,
    allResultsCount: allResults.length
  })

  return (
    <div className="space-y-6">
      
      {/* Recommendation Card (Hero) */}
      {data.recommendation && (
        <>
          <p style={{color: 'green'}}>Rendering RecommendationCard...</p>
          <RecommendationCard recommendation={data.recommendation} />
        </>
      )}

      {/* Pareto Frontier Chart */}
      {data.pareto_frontier && data.summary && (
        <div className="card">
          <p style={{color: 'green'}}>Rendering ParetoChart...</p>
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-success" />
            Cost vs Quality Analysis
          </h2>
          <ParetoChart data={data.pareto_frontier} summary={data.summary} />
        </div>
      )}

      {/* Detailed Metrics Table */}
      {data.summary && (
        <>
          <p style={{color: 'green'}}>Rendering MetricsTable...</p>
          <MetricsTable summary={data.summary} />
        </>
      )}

      {/* Validation Breakdown */}
      {hasResults && (
        <>
          <p style={{color: 'green'}}>Rendering ValidationBreakdown...</p>
          <ValidationBreakdown results={allResults} />
        </>
      )}

      {/* Raw Results (Collapsible) */}
      {hasResults && (
        <details className="card">
          <summary className="font-semibold cursor-pointer text-gray-700 dark:text-gray-300 hover:text-primary flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            View All {allResults.length} Individual Results
          </summary>
          <div className="mt-4 max-h-96 overflow-y-auto">
            <div className="space-y-2">
              {allResults.map((result, idx) => (
                <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded border border-gray-200 dark:border-gray-600 text-sm">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-gray-900 dark:text-white">{result.model}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${result.success ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'}`}>
                      {result.success ? '✓ Success' : '✗ Failed'}
                    </span>
                  </div>
                  {result.success && (
                    <>
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 dark:text-gray-400 mb-1">
                        <div>Cost: ${(result.cost_usd || 0).toFixed(6)}</div>
                        <div>Tokens: {result.total_tokens || 0}</div>
                        <div>Latency: {(result.latency_ms || 0).toFixed(0)}ms</div>
                      </div>
                      {result.validation_score !== null && result.validation_score !== undefined && (
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Validation: {result.validation_score.toFixed(1)}/100 ({result.validation_method || 'N/A'}) - {result.validation_confidence || 'N/A'}
                        </div>
                      )}
                      {result.output && (
                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-500 line-clamp-2">
                          {result.output}
                        </div>
                      )}
                    </>
                  )}
                  {!result.success && result.error && (
                    <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                      Error: {result.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </details>
      )}
      
    </div>
  )
}

export default AnalysisResults