import React, { useState } from 'react'
import { Upload, Plus, Trash2, FileText } from 'lucide-react'

const PromptUploader = ({ prompts, setPrompts }) => {
  const [newPrompt, setNewPrompt] = useState('')

  const addPrompt = () => {
    if (newPrompt.trim()) {
      setPrompts([...prompts, newPrompt.trim()])
      setNewPrompt('')
    }
  }

  const removePrompt = (index) => {
    setPrompts(prompts.filter((_, i) => i !== index))
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        try {
          const json = JSON.parse(event.target.result)
          let extractedPrompts = []
          
          if (Array.isArray(json)) {
            extractedPrompts = json.map(item => {
              if (typeof item === 'string') return item
              if (item.messages) {
                const userMsg = item.messages.find(m => m.role === 'user')
                return userMsg?.content || ''
              }
              return ''
            }).filter(Boolean)
          }
          
          setPrompts([...prompts, ...extractedPrompts])
        } catch (err) {
          alert('Invalid JSON file: ' + err.message)
        }
      }
      reader.readAsText(file)
    }
  }

  const samplePrompts = [
    "Explain quantum computing in simple terms",
    "Write a Python function to calculate Fibonacci numbers",
    "What are the benefits of microservices architecture?",
    "Translate 'Hello, how are you?' to Spanish",
    "Summarize the key points of climate change"
  ]

  const loadSamples = () => {
    setPrompts(samplePrompts)
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          Prompts to Test
        </h2>
        <button onClick={loadSamples} className="btn-secondary text-sm">
          Load Sample Prompts
        </button>
      </div>

      {/* Add Prompt */}
      <div className="mb-4 flex gap-2">
        <input
          type="text"
          value={newPrompt}
          onChange={(e) => setNewPrompt(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addPrompt()}
          placeholder="Enter a prompt to test..."
          className="input flex-1"
        />
        <button onClick={addPrompt} className="btn-primary">
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Upload JSON */}
      <div className="mb-4">
        <label className="flex items-center justify-center gap-2 btn-secondary cursor-pointer">
          <Upload className="w-5 h-5" />
          Upload JSON
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {/* Prompts List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {prompts.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No prompts added yet. Add prompts above or load samples.
          </p>
        ) : (
          prompts.map((prompt, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
            >
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-sm font-semibold flex items-center justify-center">
                {index + 1}
              </span>
              <p className="flex-1 text-sm text-gray-700 dark:text-gray-300">{prompt}</p>
              <button
                onClick={() => removePrompt(index)}
                className="flex-shrink-0 text-red-500 hover:text-red-700 dark:hover:text-red-400"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>

      {prompts.length > 0 && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Total: {prompts.length} prompt{prompts.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}

export default PromptUploader