import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useEarthquakes } from '../hooks/useEarthquakes'
import type { EarthquakeEvent } from '../types/earthquake'

interface DayData {
  date: string
  count: number
  avgMag: number
}

function groupByDay(events: EarthquakeEvent[]): DayData[] {
  const map: Record<string, { count: number; totalMag: number }> = {}

  for (const ev of events) {
    const date = ev.main_time.slice(0, 10) // YYYY-MM-DD
    if (!map[date]) map[date] = { count: 0, totalMag: 0 }
    map[date].count++
    map[date].totalMag += ev.magnitude
  }

  return Object.entries(map)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { count, totalMag }]) => ({
      date,
      count,
      avgMag: count > 0 ? parseFloat((totalMag / count).toFixed(2)) : 0,
    }))
}

function Spinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

export default function TimeSeriesPage() {
  const { data: events, isLoading, isError } = useEarthquakes(2000)

  if (isLoading) return <Spinner />
  if (isError || !events) {
    return (
      <div className="flex items-center justify-center h-48 text-red-400">
        Failed to load data. Please check the API and try again.
      </div>
    )
  }

  const dailyData = groupByDay(events)

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">
          Earthquake Count Per Day
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={dailyData} margin={{ top: 4, right: 24, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#9ca3af', fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={2}
              name="Events per day"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">
          Average Magnitude Per Day
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={dailyData} margin={{ top: 4, right: 24, bottom: 4, left: 0 }}>
            <defs>
              <linearGradient id="magGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#9ca3af', fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fill: '#9ca3af', fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey="avgMag"
              stroke="#8b5cf6"
              fill="url(#magGradient)"
              strokeWidth={2}
              dot={false}
              name="Avg magnitude"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
