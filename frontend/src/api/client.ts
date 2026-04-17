import axios from 'axios'
import type { EarthquakeEvent, EarthquakeSummary } from '../types/earthquake'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
})

export interface EarthquakeParams {
  source?: 'USGS' | 'GDACS' | 'BOTH'
  start_date?: string | null
  end_date?: string | null
  min_magnitude?: number
  alert_levels?: string[]
  countries?: string[]
  limit?: number
  offset?: number
}

interface PaginatedResponse {
  items: EarthquakeEvent[]
  total: number
  offset: number
  limit: number
}

export async function fetchEarthquakes(params: EarthquakeParams): Promise<EarthquakeEvent[]> {
  const { alert_levels, countries, start_date, end_date, ...rest } = params
  const queryParams: Record<string, unknown> = { ...rest }

  if (start_date) queryParams.start_date = start_date
  if (end_date) queryParams.end_date = end_date
  if (alert_levels && alert_levels.length > 0) queryParams['alert_levels[]'] = alert_levels
  if (countries && countries.length > 0) queryParams['countries[]'] = countries

  const response = await api.get<PaginatedResponse>('/api/v1/earthquakes', { params: queryParams })
  return response.data.items
}

export async function fetchSummary(params: Omit<EarthquakeParams, 'limit' | 'offset'>): Promise<EarthquakeSummary> {
  const { alert_levels, countries, start_date, end_date, ...rest } = params
  const queryParams: Record<string, unknown> = { ...rest }

  if (start_date) queryParams.start_date = start_date
  if (end_date) queryParams.end_date = end_date
  if (alert_levels && alert_levels.length > 0) queryParams['alert_levels[]'] = alert_levels
  if (countries && countries.length > 0) queryParams['countries[]'] = countries

  const response = await api.get<EarthquakeSummary>('/api/v1/earthquakes/summary', { params: queryParams })
  return response.data
}

export async function postChat(message: string): Promise<string> {
  const response = await api.post<{ response: string }>('/api/v1/chat', { message })
  return response.data.response
}
