import { useEffect, useState } from 'react'
import { WS_URL } from './config'
import { useLocationSocket } from './useLocationSocket'
import TrackMap from './TrackMap'

export default function App() {
  const [trackPath, setTrackPath] = useState(null)
  const [dataLoop, setDataLoop] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch('/track_path.json').then((r) => r.json()),
      fetch('/data_loop.json').then((r) => r.json()),
    ])
      .then(([tp, dl]) => {
        setTrackPath(tp.points)
        setDataLoop(dl.points)
      })
      .catch((e) => setError(e.message))
  }, [])

  const { positions, connected } = useLocationSocket(WS_URL, dataLoop, trackPath)

  const carCount = Object.keys(positions).length
  const ready = trackPath && dataLoop

  return (
    <div className="app">
      <header>
        <h1>F1 Live China 2026</h1>
        <span className={`badge ${connected ? 'on' : 'off'}`}>
          {connected ? `${carCount} car${carCount === 1 ? '' : 's'}` : 'disconnected'}
        </span>
      </header>
      <div className="map-wrap">
        {error && <div className="status">Failed to load track: {error}</div>}
        {!error && !ready && <div className="status">Loading track…</div>}
        {ready && <TrackMap trackPath={trackPath} positions={positions} />}
      </div>
    </div>
  )
}
