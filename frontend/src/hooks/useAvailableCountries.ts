import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchEarthquakes } from '../api/client'
import { useFilterStore } from '../store/filterStore'

export function useAvailableCountries() {
  const { source, startDate, endDate, minMagnitude, alertLevels } = useFilterStore()

  const { data: events, isLoading } = useQuery({
    queryKey: ['available-countries', source, startDate, endDate, minMagnitude, alertLevels],
    queryFn: () =>
      fetchEarthquakes({
        source,
        start_date: startDate,
        end_date: endDate,
        min_magnitude: minMagnitude,
        alert_levels: alertLevels,
        limit: 500,
        offset: 0,
      }),
  })

  const countries = useMemo(() => {
    if (!events) return []
    const unique = new Set(events.map((e) => e.country))
    unique.delete('Unknown')
    unique.delete('')
    return [...unique].sort((a, b) => a.localeCompare(b))
  }, [events])

  return { countries, isLoading }
}
