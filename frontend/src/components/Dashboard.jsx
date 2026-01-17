import React, { useState } from 'react'
import { Activity, Zap, TrendingDown, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import PromptUploader from './PromptUploader'
import ModelSelector from './ModelSelector'
import ConfigurationPanel from './ConfigurationPanel'
import AnalysisResults from './AnalysisResults'
import axios from 'axios'

const Dashboard = () => {
  const [prompts, setPrompts] = useState([])
  const [selectedModels, setSelectedModels] = useState(['gpt-4o', 'gpt-4o-mini'])
  const [temperature, setTemperature] = useState(0.0)
  const [maxTokens, setMaxTokens] = useState(300)
  const [analysisData, setAnalysisData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)

  const handleAnalyze = async () => {
    if (prompts.length === 0) {
      setError('Please add at least one prompt')
      return
    }

    if (selectedModels.length < 2) {
      setError('Please select at least 2 models to compare')
      return
    }

    setLoading(true)
    setError(null)
    setProgress(0)
    setAnalysisData(null)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 5, 90))
      }, 500)

      const payload = {
        prompts: prompts.map(p => ({
          messages: [{ role: 'user', content: p }],
          metadata: {}
        })),
        models: selectedModels,
        temperature: temperature,
        max_tokens: maxTokens
      }

      console.log('Sending request:', payload)

      const response = await axios.post('/api/replay', payload)

      clearInterval(progressInterval)
      setProgress(100)
      
      console.log('Received response:', response.data)
      console.log('Type of response.data:', typeof response.data)
      
      // CRITICAL FIX: Parse JSON string if backend returns string
      let parsedData = response.data
      if (typeof response.data === 'string') {
        console.log('⚠️ Response is a string, parsing JSON...')
        parsedData = JSON.parse(response.data)
        console.log('✅ Parsed data:', parsedData)
      }
      
      setAnalysisData(parsedData)
      
    } catch (err) {
      console.error('Analysis error:', err)
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to analyze. Check backend logs.'
      )
    } finally {
      setLoading(false)
    }
  }

  const resetAnalysis = () => {
    setAnalysisData(null)
    setProgress(0)
    setError(null)
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-3">
          <Activity className="w-10 h-10 text-primary" />
          Cost-Quality Optimizer
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          Replay historical prompts across models to find the optimal cost-quality trade-off
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Prompts</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{prompts.length}</p>
            </div>
            <Zap className="w-8 h-8 text-primary" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Models</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{selectedModels.length}</p>
            </div>
            <Activity className="w-8 h-8 text-secondary" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Calls</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {prompts.length * selectedModels.length}
              </p>
            </div>
            <TrendingDown className="w-8 h-8 text-success" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                {analysisData ? 'Complete' : loading ? 'Running...' : 'Ready'}
              </p>
            </div>
            {analysisData ? (
              <CheckCircle className="w-8 h-8 text-success" />
            ) : error ? (
              <AlertCircle className="w-8 h-8 text-danger" />
            ) : loading ? (
              <Loader className="w-8 h-8 text-primary animate-spin" />
            ) : (
              <Activity className="w-8 h-8 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-800 dark:text-red-300">Error</h3>
              <p className="text-sm text-red-700 dark:text-red-400 whitespace-pre-wrap">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {!analysisData ? (
        <div className="space-y-6">
          <PromptUploader prompts={prompts} setPrompts={setPrompts} />
          <ModelSelector selectedModels={selectedModels} setSelectedModels={setSelectedModels} />
          <ConfigurationPanel
            temperature={temperature}
            setTemperature={setTemperature}
            maxTokens={maxTokens}
            setMaxTokens={setMaxTokens}
          />
          
          <div className="flex justify-center gap-4">
            <button
              onClick={handleAnalyze}
              disabled={loading || prompts.length === 0 || selectedModels.length < 2}
              className="btn-primary px-8 py-3 text-lg flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  🚀 Analyze Models
                </>
              )}
            </button>
          </div>

          {/* Progress Bar */}
          {loading && (
            <div className="card">
              <div className="mb-2 flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Processing...</span>
                <span className="font-semibold">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-primary h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
                Replaying {prompts.length} prompts across {selectedModels.length} models...
              </p>
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="mb-6 flex justify-end">
            <button onClick={resetAnalysis} className="btn-secondary">
              ← New Analysis
            </button>
          </div>
          <AnalysisResults data={analysisData} />
        </div>
      )}
    </div>
  )
}

export default Dashboard