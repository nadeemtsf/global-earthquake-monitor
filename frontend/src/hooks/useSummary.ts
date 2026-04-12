import { useQuery } from '@tanstack/react-query'
import { fetchSummary } from '../api/client'
import { useFilterStore } from '../store/filterStore'

export function useSummary() {
  const { source, startDate, endDate, minMagnitude, alertLevels, countries } = useFilterStore()

  return useQuery({
    queryKey: ['summary', source, startDate, endDate, minMagnitude, alertLevels, countries],
    queryFn: () =>
      fetchSummary({
        source,
        start_date: startDate,
        end_date: endDate,
        min_magnitude: minMagnitude,
        alert_levels: alertLevels,
        countries,
      }),
  })
}
