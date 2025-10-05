import { useState } from 'react'
import { API_URL } from '../config'

export default function Advisor() {
  const [query, setQuery] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingStatus, setLoadingStatus] = useState('')

  const handleAsk = async () => {
    if (!query.trim()) return

    setLoading(true)
    setRecommendations([])

    // Loading stages
    const stages = [
      'Analyzing your requirements...',
      'Searching course catalog...',
      'Fetching course data...',
      'Matching courses to your needs...',
      'Generating recommendations...'
    ]

    let stageIndex = 0
    const statusInterval = setInterval(() => {
      if (stageIndex < stages.length) {
        setLoadingStatus(stages[stageIndex])
        stageIndex++
      }
    }, 700)

    try {
      const response = await fetch(`${API_URL}/api/advisor/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await response.json()

      clearInterval(statusInterval)
      setLoadingStatus('')
      setRecommendations(data.recommendations || [])
    } catch (error) {
      clearInterval(statusInterval)
      setLoadingStatus('')
      console.error('Error:', error)
      alert('Failed to get recommendations. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl">
            <span className="text-3xl">🎓</span>
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Course Advisor</h2>
            <p className="text-gray-600">AI-powered academic planning assistant</p>
          </div>
        </div>

        {/* Example Queries */}
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-semibold text-purple-900 mb-2">💡 Example requests:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-purple-800">
            <div>• "I need 400-level CS core courses"</div>
            <div>• "Show me interesting AI classes"</div>
            <div>• "PHIL courses for my humanities requirement"</div>
            <div>• "Easy gen-eds for natural sciences"</div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="What courses do you need advice on?"
            className="flex-1 px-6 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-lg transition-all"
          />
          <button
            onClick={handleAsk}
            disabled={loading}
            className="px-8 py-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-semibold rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Analyzing...
              </span>
            ) : (
              'Get Advice'
            )}
          </button>
        </div>
      </div>

      {/* Loading Status */}
      {loading && loadingStatus && (
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 border-l-4 border-purple-700 p-4 mb-6 rounded-lg animate-pulse">
          <div className="flex items-center gap-3">
            <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <p className="text-white font-semibold">
              {loadingStatus}
            </p>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-4">
            <h3 className="font-bold text-xl text-white flex items-center gap-2">
              <span className="text-2xl">📚</span>
              Recommended Courses
            </h3>
          </div>
          <div className="p-6 space-y-4">
            {recommendations.map((course, idx) => (
              <div key={idx} className="group p-5 bg-gradient-to-br from-purple-50 to-white rounded-xl border-2 border-purple-100 hover:border-purple-400 hover:shadow-lg transition-all">
                <div className="flex items-start gap-3 mb-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 bg-purple-600 text-white text-sm font-bold rounded-lg">
                        {course.code}
                      </span>
                      <h4 className="font-bold text-xl text-gray-800 group-hover:text-purple-600 transition-colors">
                        {course.title}
                      </h4>
                    </div>

                    {course.description && (
                      <p className="text-sm text-gray-700 leading-relaxed mb-3">
                        {course.description}
                      </p>
                    )}

                    {course.reason && (
                      <div className="flex items-start gap-2 bg-green-50 border border-green-200 rounded-lg p-3">
                        <span className="text-green-600 text-xl flex-shrink-0">✓</span>
                        <span className="text-sm text-green-800 font-medium">{course.reason}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
