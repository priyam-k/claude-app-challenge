import { useState } from 'react'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const DAY_ABBREV = { 'M': 'Monday', 'Tu': 'Tuesday', 'W': 'Wednesday', 'Th': 'Thursday', 'F': 'Friday' }
const HOURS = Array.from({ length: 13 }, (_, i) => i + 8) // 8am to 8pm

function parseTime(timeStr) {
  if (!timeStr || !timeStr.includes('-')) return null
  const [start, end] = timeStr.split('-')
  return { start: start.trim(), end: end.trim() }
}

function timeToMinutes(time) {
  if (!time) return 0
  const isPM = time.toLowerCase().includes('pm')
  const isAM = time.toLowerCase().includes('am')
  const cleanTime = time.replace(/[ap]m/gi, '').trim()
  const [hours, mins] = cleanTime.split(':').map(Number)

  let finalHours = hours
  if (isPM && hours !== 12) finalHours += 12
  if (isAM && hours === 12) finalHours = 0

  return finalHours * 60 + (mins || 0)
}

function parseDays(daysStr) {
  if (!daysStr) return []
  const days = []

  // Handle patterns like "MWF", "TuTh", "MW", etc.
  let i = 0
  while (i < daysStr.length) {
    if (i + 1 < daysStr.length && daysStr.substring(i, i + 2) === 'Tu') {
      days.push('Tuesday')
      i += 2
    } else if (i + 1 < daysStr.length && daysStr.substring(i, i + 2) === 'Th') {
      days.push('Thursday')
      i += 2
    } else if (daysStr[i] === 'M') {
      days.push('Monday')
      i++
    } else if (daysStr[i] === 'W') {
      days.push('Wednesday')
      i++
    } else if (daysStr[i] === 'F') {
      days.push('Friday')
      i++
    } else {
      i++
    }
  }

  return days
}

function CourseBlock({ course, onClick, colorIndex }) {
  const colors = [
    'bg-blue-500', 'bg-purple-500', 'bg-green-600', 'bg-pink-500',
    'bg-indigo-600', 'bg-teal-600', 'bg-orange-500', 'bg-red-500',
    'bg-cyan-600', 'bg-fuchsia-600', 'bg-emerald-600', 'bg-rose-600',
    'bg-violet-600', 'bg-amber-600', 'bg-sky-600', 'bg-lime-600'
  ]
  const color = colors[colorIndex % colors.length]

  return (
    <div
      onClick={onClick}
      className={`${color} text-white p-1 rounded text-xs cursor-pointer hover:opacity-90 transition-opacity overflow-hidden`}
      style={{ height: '100%' }}
    >
      <div className="font-bold truncate">{course.code}</div>
      <div className="truncate text-[10px]">{course.instructor}</div>
      <div className="truncate text-[10px]">{course.location}</div>
    </div>
  )
}

export default function CalendarView({ schedule }) {
  const [selectedCourse, setSelectedCourse] = useState(null)

  // Create a color mapping for each unique course code
  const courseColorMap = {}
  schedule.courses.forEach((course, idx) => {
    if (!courseColorMap[course.code]) {
      courseColorMap[course.code] = idx
    }
  })

  // Map courses to calendar grid
  const courseBlocks = []
  schedule.courses.forEach((course) => {
    const times = parseTime(course.time)
    if (!times) return

    const startMins = timeToMinutes(times.start)
    const endMins = timeToMinutes(times.end)
    const days = parseDays(course.days)

    days.forEach((day) => {
      courseBlocks.push({
        ...course,
        day,
        startMins,
        endMins,
        startHour: Math.floor(startMins / 60),
        duration: (endMins - startMins) / 60
      })
    })
  })

  return (
    <div className="space-y-4">
      {/* Calendar Grid */}
      <div className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden">
        <div className="grid grid-cols-6 border-b-2 border-gray-200">
          <div className="p-2 text-xs font-semibold text-gray-500 bg-gray-50">Time</div>
          {DAYS.map((day) => (
            <div key={day} className="p-2 text-center text-sm font-bold text-gray-700 bg-gray-50">
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-6 relative">
          {/* Time column */}
          <div className="border-r border-gray-200">
            {HOURS.map((hour) => (
              <div key={hour} className="h-16 border-b border-gray-100 p-1 text-xs text-gray-500">
                {hour > 12 ? hour - 12 : hour}:00{hour >= 12 ? 'pm' : 'am'}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {DAYS.map((day) => (
            <div key={day} className="relative border-r border-gray-200">
              {HOURS.map((hour) => (
                <div key={hour} className="h-16 border-b border-gray-100" />
              ))}

              {/* Course blocks */}
              {courseBlocks
                .filter((block) => block.day === day)
                .map((block, idx) => {
                  const top = ((block.startMins - 8 * 60) / 60) * 64 // 64px per hour
                  const height = block.duration * 64

                  return (
                    <div
                      key={idx}
                      className="absolute left-0 right-0 px-1"
                      style={{ top: `${top}px`, height: `${height}px` }}
                    >
                      <CourseBlock
                        course={block}
                        colorIndex={courseColorMap[block.code]}
                        onClick={() => setSelectedCourse(block)}
                      />
                    </div>
                  )
                })}
            </div>
          ))}
        </div>
      </div>

      {/* Course Details Modal */}
      {selectedCourse && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedCourse(null)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 bg-umd-red text-white text-sm font-bold rounded-lg">
                  {selectedCourse.code}
                </span>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
                  Section {selectedCourse.section}
                </span>
              </div>
              <button
                onClick={() => setSelectedCourse(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            <h3 className="text-xl font-bold text-gray-800 mb-4">{selectedCourse.title}</h3>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-purple-50 px-4 py-3 rounded-lg">
                <div className="text-xs text-purple-600 font-semibold">Instructor</div>
                <div className="text-sm text-purple-900 font-medium">
                  {selectedCourse.instructor}
                  {selectedCourse.prof_rating && (
                    <span className="ml-2 text-xs bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded font-bold">
                      ⭐{selectedCourse.prof_rating.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-green-50 px-4 py-3 rounded-lg">
                <div className="text-xs text-green-600 font-semibold">Schedule</div>
                <div className="text-sm text-green-900 font-medium">
                  {selectedCourse.days} {selectedCourse.time}
                </div>
              </div>

              <div className="bg-orange-50 px-4 py-3 rounded-lg">
                <div className="text-xs text-orange-600 font-semibold">Location</div>
                <div className="text-sm text-orange-900 font-medium">
                  {selectedCourse.location || 'TBA'}
                </div>
              </div>

              <div className="bg-blue-50 px-4 py-3 rounded-lg">
                <div className="text-xs text-blue-600 font-semibold">Availability</div>
                <div className="text-sm text-blue-900 font-medium">
                  {selectedCourse.open_seats} seats open
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="inline-flex items-center gap-1 text-sm text-gray-600 bg-gray-100 px-3 py-2 rounded-lg">
                <span className="font-semibold">{selectedCourse.credits}</span> credits
              </div>
              {selectedCourse.course_gpa && (
                <div className="inline-flex items-center gap-1 text-sm text-green-700 bg-green-100 px-3 py-2 rounded-lg">
                  <span className="font-semibold">Avg GPA: {selectedCourse.course_gpa.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
