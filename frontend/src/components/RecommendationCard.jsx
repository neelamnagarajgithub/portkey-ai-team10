import React from 'react'
import { Lightbulb, TrendingDown, TrendingUp, AlertTriangle, CheckCircle, Award } from 'lucide-react'

const RecommendationCard = ({ recommendation }) => {
  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case 'HIGH':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border-green-300 dark:border-green-700'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700'
      case 'LOW':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 border-orange-300 dark:border-orange-700'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
    }
  }

  const getConfidenceIcon = (confidence) => {
    switch (confidence) {
      case 'HIGH':
        return <CheckCircle className="w-5 h-5" />
      case 'MEDIUM':
        return <Award className="w-5 h-5" />
      default:
        return <AlertTriangle className="w-5 h-5" />
    }
  }

  return (
    <div className={`card border-2 ${recommendation.confidence === 'HIGH' ? 'border-green-400 dark:border-green-600' : 'border-primary'} bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-850`}>
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Lightbulb className="w-7 h-7 text-yellow-500" />
          Smart Recommendation
        </h2>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border-2 flex items-center gap-1 ${getConfidenceColor(recommendation.confidence)}`}>
          {getConfidenceIcon(recommendation.confidence)}
          {recommendation.confidence} Confidence
        </span>
      </div>

      {/* Main Recommendation */}
      <div className="mb-6 p-4 bg-gradient-to-r from-primary/10 to-secondary/10 dark:from-primary/20 dark:to-secondary/20 rounded-lg border border-primary/20">
        <div className="flex items-center gap-3 mb-2">
          <CheckCircle className="w-6 h-6 text-success flex-shrink-0" />
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            Switch to {recommendation.recommended_model}
          </h3>
        </div>
        <p className="text-gray-700 dark:text-gray-300 ml-9">
          {recommendation.reasoning}
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-5 h-5 text-green-600 dark:text-green-400" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Cost Savings</h4>
          </div>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">
            {recommendation.cost_savings_pct.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            ${recommendation.cost_savings_usd_per_1k.toFixed(6)} per 1K tokens
          </p>
        </div>

        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Quality Retained</h4>
          </div>
          <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {recommendation.quality_retention_pct.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            of baseline quality
          </p>
        </div>

        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Tested On</h4>
          </div>
          <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
            {recommendation.tested_on_calls}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            real prompts
          </p>
        </div>
      </div>

      {/* Baseline Comparison */}
      <div className="mb-6 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          <strong>Baseline:</strong> {recommendation.baseline_model}
        </p>
      </div>

      {/* Risks */}
      {recommendation.risks && recommendation.risks.length > 0 && (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Potential Risks</h4>
          </div>
          <ul className="space-y-1 ml-7">
            {recommendation.risks.map((risk, idx) => (
              <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                • {risk}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default RecommendationCard