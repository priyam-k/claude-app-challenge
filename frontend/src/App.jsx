import { useState } from 'react'
import ScheduleBuilder from './components/ScheduleBuilder'
import EventScanner from './components/EventScanner'
import CampusCompass from './components/CampusCompass'
import Advisor from './components/Advisor'

function App() {
  const [activeTab, setActiveTab] = useState('schedule')

  const tabs = [
    { id: 'schedule', label: 'Schedule', icon: '📅', desc: 'Build your perfect schedule', component: ScheduleBuilder },
    { id: 'advisor', label: 'Advisor', icon: '🎓', desc: 'Get course recommendations', component: Advisor },
    { id: 'events', label: 'Events', icon: '📸', desc: 'Scan event flyers', component: EventScanner },
    { id: 'compass', label: 'Compass', icon: '🧭', desc: 'Campus info & navigation', component: CampusCompass },
  ]

  const ActiveComponent = tabs.find(t => t.id === activeTab)?.component

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header with gradient */}
      <header className="bg-gradient-to-r from-umd-red to-red-700 text-white shadow-2xl">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-extrabold flex items-center gap-3">
                <span className="animate-bounce">🐢</span>
                Testudo++
                <span className="text-umd-gold text-4xl">⚡</span>
              </h1>
              <p className="text-lg mt-2 opacity-95 font-light">Your AI-powered UMD companion</p>
            </div>
            <div className="hidden md:flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm">Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation - Modern Pills */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex gap-3 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-umd-red to-red-600 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:scale-102'
                }`}
              >
                <span className="text-xl">{tab.icon}</span>
                <div className="text-left">
                  <div className="text-sm font-bold">{tab.label}</div>
                  {activeTab === tab.id && (
                    <div className="text-xs opacity-90">{tab.desc}</div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content with fade-in animation */}
      <main className="container mx-auto px-6 py-10">
        <div className="animate-fadeIn">
          {ActiveComponent ? <ActiveComponent /> : <div className="text-red-600">No component found for tab: {activeTab}</div>}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-20">
        <div className="container mx-auto px-6 py-6 text-center text-gray-600 text-sm">
          <p>Built with ❤️ for UMD students • Powered by Claude AI</p>
        </div>
      </footer>
    </div>
  )
}

export default App
