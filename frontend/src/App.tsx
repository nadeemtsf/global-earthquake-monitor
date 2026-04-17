import { Routes, Route, NavLink } from 'react-router-dom'
import FilterSidebar from './components/layout/FilterSidebar'

const tabs = [
  { label: 'Analytics', to: '/' },
  { label: 'Map', to: '/map' },
  { label: 'Timeline', to: '/timeline' },
  { label: 'Time Series', to: '/timeseries' },
  { label: 'Chat', to: '/chat' },
]

function Placeholder({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-full text-gray-400 text-xl">
      {name} — coming soon
    </div>
  )
}

export default function App() {
  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      <FilterSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top nav */}
        <nav className="bg-gray-800 border-b border-gray-700 flex gap-1 px-4 py-2 shrink-0">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
        {/* Main content */}
        <main className="flex-1 overflow-auto p-4">
          <Routes>
            <Route path="/" element={<Placeholder name="Analytics" />} />
            <Route path="/map" element={<Placeholder name="Map" />} />
            <Route path="/timeline" element={<Placeholder name="Timeline" />} />
            <Route path="/timeseries" element={<Placeholder name="Time Series" />} />
            <Route path="/chat" element={<Placeholder name="Chat" />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
