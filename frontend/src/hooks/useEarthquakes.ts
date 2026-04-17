import { useQuery } from '@tanstack/react-query'
import { fetchEarthquakes } from '../api/client'
import { useFilterStore } from '../store/filterStore'

export function useEarthquakes(limit = 500, offset = 0) {
  const { source, startDate, endDate, minMagnitude, alertLevels, countries } = useFilterStore()

  return useQuery({
    queryKey: ['earthquakes', source, startDate, endDate, minMagnitude, alertLevels, countries, limit, offset],
    queryFn: () =>
      fetchEarthquakes({
        source,
        start_date: startDate,
        end_date: endDate,
        min_magnitude: minMagnitude,
        alert_levels: alertLevels,
        countries,
        limit,
        offset,
      }),
  })
}
