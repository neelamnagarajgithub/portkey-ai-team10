import { useState } from 'react';
import RecommendationCard from './RecommendationCard';
import CostComparisonTable from './CostComparisonTable';
import ParetoChart from './ParetoChart';
import { TrendingUp, DollarSign, Clock, CheckCircle } from 'lucide-react';

function ResultsDisplay({ results }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!results) return null;

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'comparison', label: 'Cost Comparison' },
    { id: 'pareto', label: 'Pareto Frontier' },
  ];

  return (
    <div className="space-y-6">
      {/* Recommendation Card */}
      <RecommendationCard recommendation={results.recommendation} />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Prompts</p>
              <p className="text-2xl font-bold text-gray-900">
                {results.all_results?.length || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Models Tested</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(results.summary || {}).length}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Cost</p>
              <p className="text-2xl font-bold text-gray-900">
                ${Object.values(results.summary || {})
                  .reduce((sum, m) => sum + (m.total_cost || 0), 0)
                  .toFixed(4)}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Model Performance Summary
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(results.summary || {}).map(
                  ([model, metrics]) => (
                    <div
                      key={model}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <h4 className="font-medium text-gray-900 mb-3">
                        {model}
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Success Rate:</span>
                          <span className="font-medium">
                            {metrics.successful_calls}/{metrics.total_calls} (
                            {(
                              (metrics.successful_calls /
                                metrics.total_calls) *
                              100
                            ).toFixed(1)}
                            %)
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Avg Cost:</span>
                          <span className="font-medium">
                            ${metrics.avg_cost_per_call.toFixed(6)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Avg Latency:</span>
                          <span className="font-medium">
                            {metrics.avg_latency_ms.toFixed(0)}ms
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Quality Score:</span>
                          <span className="font-medium">
                            {(metrics.consistency_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {activeTab === 'comparison' && (
            <CostComparisonTable summary={results.summary} />
          )}

          {activeTab === 'pareto' && (
            <ParetoChart paretoFrontier={results.pareto_frontier} />
          )}
        </div>
      </div>
    </div>
  );
}

export default ResultsDisplay;
