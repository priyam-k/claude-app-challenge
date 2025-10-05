import { useState, useEffect } from 'react'
import CalendarView from './CalendarView'
import { API_URL } from '../config'

export default function ScheduleBuilder() {
  const [query, setQuery] = useState('')
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(false)
  const [terms, setTerms] = useState([])
  const [selectedTerm, setSelectedTerm] = useState('')
  const [viewMode, setViewMode] = useState('calendar') // 'calendar' or 'list'
  const [explanation, setExplanation] = useState('')
  const [loadingStatus, setLoadingStatus] = useState('')

  useEffect(() => {
    // Fetch available terms
    fetch(`${API_URL}/api/terms`)
      .then(res => res.json())
      .then(data => {
        setTerms(data.terms || [])
        setSelectedTerm(data.current || '')
      })
      .catch(err => console.error('Error fetching terms:', err))
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setSchedules([])
    setExplanation('')

    // Simulate loading stages
    const stages = [
      'Analyzing your request...',
      'Searching Schedule of Classes...',
      'Finding relevant courses...',
      'Fetching course sections...',
      'Building schedules...',
      'Checking for conflicts...',
      'Finalizing results...'
    ]

    let stageIndex = 0
    const statusInterval = setInterval(() => {
      if (stageIndex < stages.length) {
        setLoadingStatus(stages[stageIndex])
        stageIndex++
      }
    }, 800)

    try {
      const response = await fetch(`${API_URL}/api/schedule/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, term_id: selectedTerm })
      })
      const data = await response.json()
      console.log('Received data:', data)

      clearInterval(statusInterval)
      setLoadingStatus('')

      if (data.schedules && Array.isArray(data.schedules)) {
        setSchedules(data.schedules)
        setExplanation(data.explanation || '')
      } else {
        console.error('Invalid response format:', data)
        setSchedules([])
        setExplanation(data.explanation || 'Invalid response format')
      }
    } catch (error) {
      clearInterval(statusInterval)
      setLoadingStatus('')
      console.error('Error:', error)
      setSchedules([])
      setExplanation('Failed to build schedule. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-umd-red rounded-xl">
            <span className="text-3xl">📅</span>
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Smart Schedule Builder</h2>
            <p className="text-gray-600">AI-powered schedule generation with conflict detection</p>
          </div>
        </div>

        {/* Example Queries */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-semibold text-blue-900 mb-2">💡 Try asking:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-blue-800">
            <div>• "Build me a CS schedule with morning classes"</div>
            <div>• "I need 15 credits, prefer best professors"</div>
            <div>• "Schedule with CMSC and MATH courses"</div>
            <div>• "Gen-eds with minimal gaps between classes"</div>
          </div>
        </div>

        {/* Search Bar + Term Selector */}
        <div className="space-y-3">
          <div className="flex gap-3">
            <select
              value={selectedTerm}
              onChange={(e) => setSelectedTerm(e.target.value)}
              className="px-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-umd-red focus:border-transparent text-lg transition-all bg-white"
            >
              {terms.map(term => (
                <option key={term.id} value={term.id}>{term.label}</option>
              ))}
            </select>

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Describe your ideal schedule..."
              className="flex-1 px-6 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-umd-red focus:border-transparent text-lg transition-all"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-8 py-4 bg-gradient-to-r from-umd-red to-red-600 text-white font-semibold rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Building...
                </span>
              ) : (
                'Build Schedule'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Loading Status */}
      {loading && loadingStatus && (
        <div className="bg-gradient-to-r from-umd-red to-red-600 border-l-4 border-umd-gold p-4 mb-6 rounded-lg animate-pulse">
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

      {/* Results Summary */}
      {!loading && explanation && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-lg">
          <p className="text-blue-900 font-semibold">
            {explanation}
          </p>
        </div>
      )}

      {/* Results */}
      {schedules.length > 0 && (
        <div className="space-y-6">
          {schedules.map((schedule, idx) => (
            <div key={idx} className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="bg-gradient-to-r from-umd-red to-red-600 px-6 py-4 flex items-center justify-between">
                <h3 className="font-bold text-xl text-white flex items-center gap-2">
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm">Schedule #{idx + 1}</span>
                </h3>
                <div className="flex items-center gap-3">
                  <span className="bg-umd-gold text-gray-900 px-4 py-1 rounded-full font-bold">
                    {schedule.total_credits} Credits
                  </span>
                  <div className="flex bg-white/20 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setViewMode('calendar')}
                      className={`px-3 py-1 text-sm font-semibold transition-colors ${
                        viewMode === 'calendar' ? 'bg-white text-umd-red' : 'text-white hover:bg-white/10'
                      }`}
                    >
                      📅 Calendar
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={`px-3 py-1 text-sm font-semibold transition-colors ${
                        viewMode === 'list' ? 'bg-white text-umd-red' : 'text-white hover:bg-white/10'
                      }`}
                    >
                      📋 List
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-6">
                {viewMode === 'calendar' ? (
                  <CalendarView schedule={schedule} />
                ) : (
                  <div className="space-y-3">
                {schedule.courses && schedule.courses.length > 0 ? (
                  schedule.courses.map((course, i) => (
                    <div key={i} className="group p-5 bg-gradient-to-br from-gray-50 to-white rounded-xl border-2 border-gray-100 hover:border-umd-red hover:shadow-md transition-all">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="px-3 py-1 bg-umd-red text-white text-sm font-bold rounded-lg">
                              {course.code}
                            </span>
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
                              Section {course.section}
                            </span>
                            <h4 className="font-bold text-lg text-gray-800 group-hover:text-umd-red transition-colors">
                              {course.title}
                            </h4>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                            <div className="bg-purple-50 px-3 py-2 rounded-lg">
                              <div className="text-xs text-purple-600 font-semibold">Instructor</div>
                              <div className="text-sm text-purple-900 font-medium">
                                {course.instructor}
                                {course.prof_rating && (
                                  <span className="ml-1 text-xs bg-yellow-400 text-yellow-900 px-1.5 py-0.5 rounded font-bold">
                                    ⭐{course.prof_rating.toFixed(1)}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="bg-green-50 px-3 py-2 rounded-lg">
                              <div className="text-xs text-green-600 font-semibold">Schedule</div>
                              <div className="text-sm text-green-900 font-medium">{course.days} {course.time}</div>
                            </div>

                            <div className="bg-orange-50 px-3 py-2 rounded-lg">
                              <div className="text-xs text-orange-600 font-semibold">Location</div>
                              <div className="text-sm text-orange-900 font-medium">{course.location || 'TBA'}</div>
                            </div>

                            <div className="bg-blue-50 px-3 py-2 rounded-lg">
                              <div className="text-xs text-blue-600 font-semibold">Availability</div>
                              <div className="text-sm text-blue-900 font-medium">
                                {course.open_seats} seats open
                              </div>
                            </div>
                          </div>

                          <div className="mt-3 flex items-center gap-2">
                            <div className="inline-flex items-center gap-1 text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-lg">
                              <span className="font-semibold">{course.credits}</span> credits
                            </div>
                            {course.course_gpa && (
                              <div className="inline-flex items-center gap-1 text-sm text-green-700 bg-green-100 px-3 py-1 rounded-lg">
                                <span className="font-semibold">Avg GPA: {course.course_gpa.toFixed(2)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-4xl mb-2">📭</div>
                    <div>No schedule could be built with these constraints</div>
                  </div>
                )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
