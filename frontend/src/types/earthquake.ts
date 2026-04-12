export interface EarthquakeEvent {
  id: string
  title: string
  main_time: string
  magnitude: number
  magnitude_type: string
  depth_km: number
  latitude: number
  longitude: number
  place: string
  country: string
  alert_level: 'Green' | 'Yellow' | 'Orange' | 'Red' | 'Unknown'
  tsunami: 0 | 1
  felt: number | null
  status: string
  source: string
  link: string
  severity_text: string
  population_text: string
}

export interface AlertBreakdown {
  green: number
  yellow: number
  orange: number
  red: number
  unknown: number
}

export interface TopRegion {
  region: string
  count: number
}

export interface EarthquakeSummary {
  total_count: number
  average_magnitude: number
  max_magnitude: number
  tsunami_count: number
  alert_breakdown: AlertBreakdown
  top_regions: TopRegion[]
}
