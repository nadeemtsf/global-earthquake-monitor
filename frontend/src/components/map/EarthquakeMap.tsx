import { useState, useMemo, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import useSupercluster from 'use-supercluster'
import type { EarthquakeEvent } from '../../types/earthquake'

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

function createClusterIcon(count: number) {
  const size = count < 10 ? 30 : count < 100 ? 40 : 50
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;background:rgba(59,130,246,0.7);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:${size < 40 ? 12 : 14}px;border:2px solid rgba(59,130,246,0.9)">${count}</div>`,
    className: '',
    iconSize: L.point(size, size),
    iconAnchor: [size / 2, size / 2],
  })
}

interface PointProperties {
  cluster: false
  eventId: string
  magnitude: number
  alertLevel: string
  place: string
  mainTime: string
  depthKm: number
}

type EqPoint = GeoJSON.Feature<GeoJSON.Point, PointProperties>

function BoundsTracker({
  onChange,
}: {
  onChange: (bounds: [number, number, number, number], zoom: number) => void
}) {
  const map = useMap()

  const update = useCallback(() => {
    const b = map.getBounds()
    onChange([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()], map.getZoom())
  }, [map, onChange])

  useEffect(() => {
    update()
    map.on('moveend', update)
    return () => {
      map.off('moveend', update)
    }
  }, [map, update])

  return null
}

export default function EarthquakeMap({ events }: { events: EarthquakeEvent[] }) {
  const [bounds, setBounds] = useState<[number, number, number, number]>([-180, -90, 180, 90])
  const [zoom, setZoom] = useState(2)

  const handleBoundsChange = useCallback(
    (b: [number, number, number, number], z: number) => {
      setBounds(b)
      setZoom(z)
    },
    [],
  )

  const points: EqPoint[] = useMemo(
    () =>
      events.map((ev) => ({
        type: 'Feature' as const,
        properties: {
          cluster: false as const,
          eventId: ev.id,
          magnitude: ev.magnitude,
          alertLevel: ev.alert_level,
          place: ev.place,
          mainTime: ev.main_time,
          depthKm: ev.depth_km,
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [ev.longitude, ev.latitude],
        },
      })),
    [events],
  )

  const { clusters } = useSupercluster({
    points,
    bounds,
    zoom,
    options: { radius: 75, maxZoom: 16 },
  })

  return (
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
      <BoundsTracker onChange={handleBoundsChange} />
      {clusters.map((cluster) => {
        const [lng, lat] = cluster.geometry.coordinates
        const props = cluster.properties

        if (props.cluster) {
          return (
            <Marker
              key={`cluster-${props.cluster_id}`}
              position={[lat, lng]}
              icon={createClusterIcon(props.point_count)}
            />
          )
        }

        const p = props as unknown as PointProperties
        const color = ALERT_COLORS[p.alertLevel] ?? ALERT_COLORS.Unknown
        return (
          <CircleMarker
            key={p.eventId}
            center={[lat, lng]}
            radius={Math.max(4, p.magnitude * 3)}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.6, weight: 1 }}
          >
            <Popup>
              <div className="text-sm space-y-1">
                <p className="font-semibold">{p.place}</p>
                <p>
                  Magnitude: <strong>{p.magnitude.toFixed(1)}</strong>
                </p>
                <p>Time: {new Date(p.mainTime).toUTCString()}</p>
                <p>
                  Alert: <strong>{p.alertLevel}</strong>
                </p>
                <p>Depth: {p.depthKm.toFixed(1)} km</p>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
