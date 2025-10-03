import { useState } from 'react'

export default function EventScanner() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setPreview(URL.createObjectURL(selectedFile))
    }
  }

  const handleScan = async () => {
    if (!file) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/api/events/scan', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setEvent(data.event)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to scan event. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const downloadICS = () => {
    if (!event) return

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Testudo++//EN
BEGIN:VEVENT
SUMMARY:${event.title}
DTSTART:${event.datetime}
LOCATION:${event.location}
DESCRIPTION:${event.description || ''}
END:VEVENT
END:VCALENDAR`

    const blob = new Blob([icsContent], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'event.ics'
    a.click()
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4">Event-to-Calendar Scanner</h2>
        <p className="text-gray-600 mb-4">
          Upload a photo of an event flyer and we'll extract the details automatically.
        </p>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer inline-block px-6 py-2 bg-umd-red text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Choose Image
          </label>
          {preview && (
            <div className="mt-4">
              <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded" />
            </div>
          )}
        </div>

        {file && (
          <button
            onClick={handleScan}
            disabled={loading}
            className="mt-4 w-full px-6 py-3 bg-umd-gold text-gray-900 font-semibold rounded-lg hover:bg-yellow-400 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Scanning...' : 'Extract Event Details'}
          </button>
        )}
      </div>

      {event && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Event Detected</h3>
          <div className="space-y-2 mb-4">
            <p><span className="font-semibold">Title:</span> {event.title}</p>
            <p><span className="font-semibold">Date/Time:</span> {event.datetime}</p>
            <p><span className="font-semibold">Location:</span> {event.location}</p>
            {event.description && (
              <p><span className="font-semibold">Details:</span> {event.description}</p>
            )}
          </div>
          <button
            onClick={downloadICS}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            📅 Download .ics File
          </button>
        </div>
      )}
    </div>
  )
}
