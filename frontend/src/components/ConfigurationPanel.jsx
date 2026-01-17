function ConfigurationPanel({
  temperature,
  setTemperature,
  maxTokens,
  setMaxTokens,
}) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Configuration
      </h2>

      <div className="space-y-4">
        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Temperature: {temperature}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.0 (Deterministic)</span>
            <span>2.0 (Creative)</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Tokens: {maxTokens}
          </label>
          <input
            type="number"
            min="1"
            max="4096"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1000)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <p className="text-xs text-gray-500 mt-1">
            Maximum tokens in the response (1-4096)
          </p>
        </div>
      </div>
    </div>
  );
}

export default ConfigurationPanel;
