import { useState, useEffect, useRef, useCallback } from 'react'
import { useEarthquakes } from '../hooks/useEarthquakes'
import EarthquakeMap from '../components/map/EarthquakeMap'

const SPEEDS = [1, 5, 10] as const
type Speed = (typeof SPEEDS)[number]

export default function TimelinePage() {
  const { data: events, isLoading, isError } = useEarthquakes(500)

  const [currentTime, setCurrentTime] = useState<Date>(new Date())
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState<Speed>(1)
  const [scrubberValue, setScrubberValue] = useState(0)

  const rafRef = useRef<number | null>(null)
  const lastFrameRef = useRef<number | null>(null)

  const { minTime, maxTime } = (() => {
    if (!events || events.length === 0) {
      const now = new Date()
      return { minTime: now, maxTime: now }
    }
    const times = events.map((e) => new Date(e.main_time).getTime())
    return {
      minTime: new Date(Math.min(...times)),
      maxTime: new Date(Math.max(...times)),
    }
  })()

  const timeRange = maxTime.getTime() - minTime.getTime()

  useEffect(() => {
    if (events && events.length > 0) {
      setCurrentTime(minTime)
      setScrubberValue(0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events])

  const stopPlayback = useCallback(() => {
    setIsPlaying(false)
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    lastFrameRef.current = null
  }, [])

  const tick = useCallback(
    (timestamp: number) => {
      if (lastFrameRef.current === null) {
        lastFrameRef.current = timestamp
      }
      const elapsed = timestamp - lastFrameRef.current
      lastFrameRef.current = timestamp

      const advanceMs = (speed * 86400000 * elapsed) / 1000

      setCurrentTime((prev) => {
        const next = new Date(prev.getTime() + advanceMs)
        if (next >= maxTime) {
          stopPlayback()
          setScrubberValue(100)
          return maxTime
        }
        const ratio = timeRange > 0 ? ((next.getTime() - minTime.getTime()) / timeRange) * 100 : 0
        setScrubberValue(ratio)
        return next
      })

      rafRef.current = requestAnimationFrame(tick)
    },
    [speed, maxTime, minTime, timeRange, stopPlayback],
  )

  useEffect(() => {
    if (isPlaying) {
      rafRef.current = requestAnimationFrame(tick)
    } else {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      lastFrameRef.current = null
    }
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    }
  }, [isPlaying, tick])

  function handleScrubber(value: number) {
    stopPlayback()
    setScrubberValue(value)
    if (timeRange > 0) {
      setCurrentTime(new Date(minTime.getTime() + (value / 100) * timeRange))
    }
  }

  function togglePlay() {
    if (isPlaying) {
      stopPlayback()
    } else {
      if (currentTime >= maxTime) {
        setCurrentTime(minTime)
        setScrubberValue(0)
      }
      setIsPlaying(true)
    }
  }

  const visibleEvents = events?.filter((ev) => new Date(ev.main_time) <= currentTime)

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Controls */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex flex-col gap-2 shrink-0">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={togglePlay}
            disabled={isLoading || !events}
            className="px-5 py-1.5 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-medium transition-colors"
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Speed:</span>
            {SPEEDS.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  speed === s
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          <span className="ml-auto text-sm text-blue-300 font-mono">
            {currentTime.toUTCString().replace(' GMT', ' UTC')}
          </span>

          {visibleEvents && (
            <span className="text-xs text-gray-400">
              {visibleEvents.length} / {events?.length ?? 0} events
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-24 truncate">
            {minTime.toLocaleDateString()}
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={0.1}
            value={scrubberValue}
            onChange={(e) => handleScrubber(Number(e.target.value))}
            className="flex-1 accent-blue-500"
          />
          <span className="text-xs text-gray-500 w-24 text-right truncate">
            {maxTime.toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
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
        {visibleEvents && <EarthquakeMap events={visibleEvents} />}
      </div>
    </div>
  )
}
