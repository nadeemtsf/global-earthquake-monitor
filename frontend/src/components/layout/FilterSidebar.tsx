import { useState } from 'react'
import { useFilterStore, type FilterState } from '../../store/filterStore'

const ALERT_LEVELS = ['Green', 'Yellow', 'Orange', 'Red']

const COMMON_COUNTRIES = [
  'United States', 'Japan', 'Indonesia', 'China', 'Turkey',
  'Mexico', 'Italy', 'Greece', 'Chile', 'Peru',
  'Iran', 'New Zealand', 'Philippines', 'India', 'Pakistan',
  'Afghanistan', 'Nepal', 'Papua New Guinea', 'Tonga', 'Vanuatu',
]

export default function FilterSidebar() {
  const store = useFilterStore()

  const [localSource, setLocalSource] = useState<FilterState['source']>(store.source)
  const [localStart, setLocalStart] = useState(store.startDate ?? '')
  const [localEnd, setLocalEnd] = useState(store.endDate ?? '')
  const [localMag, setLocalMag] = useState(store.minMagnitude)
  const [localAlerts, setLocalAlerts] = useState<string[]>(store.alertLevels)
  const [localCountries, setLocalCountries] = useState<string[]>(store.countries)
  const [countrySearch, setCountrySearch] = useState('')

  function toggleAlert(level: string) {
    setLocalAlerts((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]
    )
  }

  function toggleCountry(country: string) {
    setLocalCountries((prev) =>
      prev.includes(country) ? prev.filter((c) => c !== country) : [...prev, country]
    )
  }

  const filteredCountries = COMMON_COUNTRIES.filter((c) =>
    c.toLowerCase().includes(countrySearch.toLowerCase())
  )

  function applyFilters() {
    store.applyFilters({
      source: localSource,
      startDate: localStart || null,
      endDate: localEnd || null,
      minMagnitude: localMag,
      alertLevels: localAlerts,
      countries: localCountries,
    })
  }

  return (
    <aside className="w-64 bg-gray-800 text-white flex flex-col p-4 shrink-0 overflow-y-auto">
      <h2 className="text-lg font-semibold mb-4 text-blue-400">Filters</h2>

      {/* Source */}
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">Source</label>
        <select
          value={localSource}
          onChange={(e) => setLocalSource(e.target.value as FilterState['source'])}
          className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        >
          <option value="USGS">USGS</option>
          <option value="GDACS">GDACS</option>
          <option value="BOTH">BOTH</option>
        </select>
      </div>

      {/* Date range */}
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">Start Date</label>
        <input
          type="date"
          value={localStart}
          onChange={(e) => setLocalStart(e.target.value)}
          className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        />
      </div>
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">End Date</label>
        <input
          type="date"
          value={localEnd}
          onChange={(e) => setLocalEnd(e.target.value)}
          className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Magnitude */}
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">
          Min Magnitude: <span className="text-white font-semibold">{localMag}</span>
        </label>
        <input
          type="range"
          min={0}
          max={9}
          step={0.5}
          value={localMag}
          onChange={(e) => setLocalMag(Number(e.target.value))}
          className="w-full accent-blue-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0</span>
          <span>9</span>
        </div>
      </div>

      {/* Alert levels */}
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wide">Alert Levels</label>
        {ALERT_LEVELS.map((level) => (
          <label key={level} className="flex items-center gap-2 mb-1 cursor-pointer">
            <input
              type="checkbox"
              checked={localAlerts.includes(level)}
              onChange={() => toggleAlert(level)}
              className="accent-blue-500"
            />
            <span className="text-sm">{level}</span>
          </label>
        ))}
      </div>

      {/* Country filter */}
      <div className="mb-6">
        <label className="block text-xs text-gray-400 mb-2 uppercase tracking-wide">
          Countries {localCountries.length > 0 && <span className="text-blue-400">({localCountries.length})</span>}
        </label>
        <input
          type="text"
          value={countrySearch}
          onChange={(e) => setCountrySearch(e.target.value)}
          placeholder="Search countries..."
          className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-xs border border-gray-600 focus:outline-none focus:border-blue-500 placeholder-gray-500 mb-2"
        />
        <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
          {filteredCountries.map((country) => (
            <label key={country} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={localCountries.includes(country)}
                onChange={() => toggleCountry(country)}
                className="accent-blue-500 shrink-0"
              />
              <span className="text-xs text-gray-300">{country}</span>
            </label>
          ))}
        </div>
        {localCountries.length > 0 && (
          <button
            onClick={() => setLocalCountries([])}
            className="mt-2 text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Clear countries
          </button>
        )}
      </div>

      <button
        onClick={applyFilters}
        className="mt-auto w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded transition-colors text-sm"
      >
        Apply Filters
      </button>
    </aside>
  )
}
