import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useSummary } from '../hooks/useSummary'
import { useEarthquakes } from '../hooks/useEarthquakes'
import type { EarthquakeEvent } from '../types/earthquake'

const ALERT_COLORS: Record<string, string> = {
  green: '#22c55e',
  yellow: '#eab308',
  orange: '#f97316',
  red: '#ef4444',
  unknown: '#94a3b8',
}

function KPICard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 flex flex-col gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-white">{value}</span>
    </div>
  )
}

function buildMagnitudeHistogram(events: EarthquakeEvent[]) {
  const bins: Record<string, number> = {}
  for (let i = 0; i <= 8; i++) {
    bins[`${i}-${i + 1}`] = 0
  }
  for (const e of events) {
    const bin = Math.floor(e.magnitude)
    const key = `${bin}-${bin + 1}`
    if (key in bins) bins[key]++
  }
  return Object.entries(bins).map(([bin, count]) => ({ bin, count }))
}

function Spinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

const PAGE_SIZE = 20

export default function AnalyticsPage() {
  const { data: summary, isLoading: summaryLoading, isError: summaryError } = useSummary()
  const { data: events, isLoading: eventsLoading, isError: eventsError } = useEarthquakes(1000)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(0)

  const isLoading = summaryLoading || eventsLoading
  const isError = summaryError || eventsError

  if (isLoading) return <Spinner />
  if (isError || !summary || !events) {
    return (
      <div className="flex items-center justify-center h-48 text-red-400">
        Failed to load data. Please check the API and try again.
      </div>
    )
  }

  const top10 = [...events].sort((a, b) => b.magnitude - a.magnitude).slice(0, 10)
  const magHistogram = buildMagnitudeHistogram(events)

  // Search/grid
  const filteredEvents = events.filter((ev) =>
    ev.place.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const totalPages = Math.ceil(filteredEvents.length / PAGE_SIZE)
  const pageEvents = filteredEvents.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE)
  const alertPieData = [
    { name: 'Green', value: summary.alert_breakdown.green, color: ALERT_COLORS.green },
    { name: 'Yellow', value: summary.alert_breakdown.yellow, color: ALERT_COLORS.yellow },
    { name: 'Orange', value: summary.alert_breakdown.orange, color: ALERT_COLORS.orange },
    { name: 'Red', value: summary.alert_breakdown.red, color: ALERT_COLORS.red },
    { name: 'Unknown', value: summary.alert_breakdown.unknown, color: ALERT_COLORS.unknown },
  ].filter((d) => d.value > 0)

  const topRegionsData = summary.top_regions.map((r) => ({
    region: r.region.length > 15 ? r.region.slice(0, 15) + '…' : r.region,
    count: r.count,
  }))

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard label="Total Events" value={summary.total_count.toLocaleString()} />
        <KPICard label="Avg Magnitude" value={summary.average_magnitude.toFixed(2)} />
        <KPICard label="Max Magnitude" value={summary.max_magnitude.toFixed(1)} />
        <KPICard label="Tsunami Alerts" value={summary.tsunami_count} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Magnitude Distribution */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Magnitude Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={magHistogram} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="bin" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Alert Level Pie */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Alert Level Breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={alertPieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {alertPieData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Regions */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Top Regions</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={topRegionsData} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <YAxis type="category" dataKey="region" tick={{ fill: '#9ca3af', fontSize: 11 }} width={120} />
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
            <Bar dataKey="count" fill="#8b5cf6" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top 10 Significant Events */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Top 10 Significant Events</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-2 pr-4">Place</th>
                <th className="text-right py-2 pr-4">Magnitude</th>
                <th className="text-right py-2 pr-4">Depth (km)</th>
                <th className="text-right py-2">Time (UTC)</th>
              </tr>
            </thead>
            <tbody>
              {top10.map((ev) => (
                <tr key={ev.id} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                  <td className="py-2 pr-4 text-gray-200 max-w-xs truncate">{ev.place}</td>
                  <td className="py-2 pr-4 text-right font-semibold text-orange-400">{ev.magnitude.toFixed(1)}</td>
                  <td className="py-2 pr-4 text-right text-gray-300">{ev.depth_km.toFixed(1)}</td>
                  <td className="py-2 text-right text-gray-400 text-xs whitespace-nowrap">
                    {new Date(ev.main_time).toUTCString().replace(' GMT', ' UTC')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Search/Grid */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300">All Events</h3>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setCurrentPage(0)
            }}
            placeholder="Search by place..."
            className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 border border-gray-600 focus:outline-none focus:border-blue-500 placeholder-gray-400 w-56"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-2 pr-4">Place</th>
                <th className="text-right py-2 pr-4">Magnitude</th>
                <th className="text-right py-2 pr-4">Depth (km)</th>
                <th className="text-right py-2 pr-4">Time (UTC)</th>
                <th className="text-right py-2 pr-4">Alert</th>
                <th className="text-right py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {pageEvents.map((ev) => (
                <tr key={ev.id} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                  <td className="py-1.5 pr-4 text-gray-200 max-w-xs truncate">{ev.place}</td>
                  <td className="py-1.5 pr-4 text-right font-semibold text-orange-400">{ev.magnitude.toFixed(1)}</td>
                  <td className="py-1.5 pr-4 text-right text-gray-300">{ev.depth_km.toFixed(1)}</td>
                  <td className="py-1.5 pr-4 text-right text-gray-400 text-xs whitespace-nowrap">
                    {new Date(ev.main_time).toUTCString().replace(' GMT', ' UTC')}
                  </td>
                  <td className="py-1.5 pr-4 text-right">
                    <span
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{ backgroundColor: ALERT_COLORS[ev.alert_level.toLowerCase()] + '33', color: ALERT_COLORS[ev.alert_level.toLowerCase()] }}
                    >
                      {ev.alert_level}
                    </span>
                  </td>
                  <td className="py-1.5 text-right text-gray-400 text-xs">{ev.source}</td>
                </tr>
              ))}
              {pageEvents.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No events match your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between mt-3 text-sm text-gray-400">
          <span>
            Showing {filteredEvents.length === 0 ? 0 : currentPage * PAGE_SIZE + 1}–
            {Math.min((currentPage + 1) * PAGE_SIZE, filteredEvents.length)} of {filteredEvents.length}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded transition-colors text-xs"
            >
              Prev
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 rounded transition-colors text-xs"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
