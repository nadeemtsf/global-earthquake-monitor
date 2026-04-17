import { create } from 'zustand'

export interface FilterState {
  source: 'USGS' | 'GDACS' | 'BOTH'
  startDate: string | null
  endDate: string | null
  minMagnitude: number
  alertLevels: string[]
  countries: string[]
}

interface FilterStore extends FilterState {
  setSource: (source: FilterState['source']) => void
  setStartDate: (date: string | null) => void
  setEndDate: (date: string | null) => void
  setMinMagnitude: (mag: number) => void
  setAlertLevels: (levels: string[]) => void
  setCountries: (countries: string[]) => void
  applyFilters: (partial: Partial<FilterState>) => void
}

export const useFilterStore = create<FilterStore>((set) => ({
  source: 'USGS',
  startDate: null,
  endDate: null,
  minMagnitude: 2.5,
  alertLevels: [],
  countries: [],

  setSource: (source) => set({ source }),
  setStartDate: (startDate) => set({ startDate }),
  setEndDate: (endDate) => set({ endDate }),
  setMinMagnitude: (minMagnitude) => set({ minMagnitude }),
  setAlertLevels: (alertLevels) => set({ alertLevels }),
  setCountries: (countries) => set({ countries }),
  applyFilters: (partial) => set(partial),
}))
