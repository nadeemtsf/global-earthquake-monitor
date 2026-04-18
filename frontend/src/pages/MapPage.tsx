import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEarthquakes } from '../hooks/useEarthquakes'

// Fix leaflet default icon issue
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const ALERT_COLORS: Record<string, string> = {
  Red: '#ef4444',
  Orange: '#f97316',
  Yellow: '#eab308',
  Green: '#22c55e',
  Unknown: '#94a3b8',
}

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
      <MapContainer
        center={[20, 0]}
        zoom={2}
        className="h-full w-full"
        style={{ background: '#1a2234' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {events?.map((ev) => (
          <CircleMarker
            key={ev.id}
            center={[ev.latitude, ev.longitude]}
            radius={Math.max(4, ev.magnitude * 3)}
            pathOptions={{
              color: ALERT_COLORS[ev.alert_level] ?? ALERT_COLORS.Unknown,
              fillColor: ALERT_COLORS[ev.alert_level] ?? ALERT_COLORS.Unknown,
              fillOpacity: 0.6,
              weight: 1,
            }}
          >
            <Popup>
              <div className="text-sm space-y-1">
                <p className="font-semibold">{ev.place}</p>
                <p>Magnitude: <strong>{ev.magnitude.toFixed(1)}</strong></p>
                <p>Time: {new Date(ev.main_time).toUTCString()}</p>
                <p>Alert: <strong>{ev.alert_level}</strong></p>
                <p>Depth: {ev.depth_km.toFixed(1)} km</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}
