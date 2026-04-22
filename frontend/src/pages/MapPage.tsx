import { useEarthquakes } from '../hooks/useEarthquakes'
import EarthquakeMap from '../components/map/EarthquakeMap'

export default function MapPage() {
  const { data: events, isLoading, isError } = useEarthquakes(500)

  return (
    <div className="relative h-[calc(100vh-120px)]">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/70 z-10">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      {isError && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-red-800 text-white px-4 py-2 rounded z-10">
          Failed to load earthquake data
        </div>
      )}
      {events && <EarthquakeMap events={events} />}
    </div>
  )
}
