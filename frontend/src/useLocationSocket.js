import { useEffect, useRef, useState } from 'react'

// Garbage values from OpenF1 we must never render (car in garage, etc)
const isSentinel = (x, y) => (x === -8325 && y === -7058) || (x === 0 && y === 0)

// Smoothing time constant (s), bigger = smoother
const TAU = 0.5

// Temporal continuity, only look for the car's spot within +/- this many indices
const WINDOW = 25

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v))

function loopExtent(loop) {
  let minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity
  for (const [x, y] of loop) {
    if (x < minx) minx = x
    if (x > maxx) maxx = x
    if (y < miny) miny = y
    if (y > maxy) maxy = y
  }
  return Math.max(maxx - minx, maxy - miny)
}

function projectFrac(pt, loop, prev) {
  const N = loop.length
  let bestD = Infinity
  let bestFrac = prev ?? 0
  const lo = prev == null ? 0 : Math.floor(prev) - WINDOW
  const hi = prev == null ? N : Math.floor(prev) + WINDOW
  for (let k = lo; k < hi; k++) {
    const i = ((k % N) + N) % N
    const a = loop[i]
    const b = loop[(i + 1) % N]
    const abx = b[0] - a[0]
    const aby = b[1] - a[1]
    const apx = pt[0] - a[0]
    const apy = pt[1] - a[1]
    const len2 = abx * abx + aby * aby || 1
    const t = clamp((apx * abx + apy * aby) / len2, 0, 1)
    const dx = apx - t * abx
    const dy = apy - t * aby
    const d = dx * dx + dy * dy
    if (d < bestD) {
      bestD = d
      bestFrac = i + t
    }
  }
  return { frac: bestFrac, dist2: bestD }
}

/**
 * Subscribes to the location WebSocket and returns each car's position ON the
 * traced track path.
 *
 * Pipeline per driver, per animation frame:
 *   1. ease the raw telemetry XY toward its latest value (exponential smoothing)
 *   2. project that smoothed XY onto the telemetry reference loop -> fractional
 *   3. read the traced path at the SAME index -> a point exactly on the drawn line
 */
export function useLocationSocket(url, dataLoop, trackPath) {
  const driversRef = useRef(new Map())
  const [positions, setPositions] = useState({})
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!dataLoop || !trackPath) return

    let ws
    let raf
    let closed = false
    let lastFrame = performance.now()

    const globalThresh = (loopExtent(dataLoop) * 0.08) ** 2
    const N = trackPath.length

    const connect = () => {
      ws = new WebSocket(url)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (!closed) setTimeout(connect, 1000)
      }
      ws.onmessage = (e) => {
        const p = JSON.parse(e.data)
        if (isSentinel(p.x, p.y)) return
        const d = driversRef.current.get(p.driver_number)
        if (!d) {
          driversRef.current.set(p.driver_number, {
            targetX: p.x, targetY: p.y, renderX: p.x, renderY: p.y, frac: null,
          })
        } else {
          d.targetX = p.x
          d.targetY = p.y
        }
      }
    }

    const tick = () => {
      const now = performance.now()
      const dt = (now - lastFrame) / 1000
      lastFrame = now
      const alpha = 1 - Math.exp(-dt / TAU)

      const snapshot = {}
      for (const [num, d] of driversRef.current) {
        d.renderX += (d.targetX - d.renderX) * alpha
        d.renderY += (d.targetY - d.renderY) * alpha

        let { frac, dist2 } = projectFrac([d.renderX, d.renderY], dataLoop, d.frac)
        if (d.frac != null && dist2 > globalThresh) {
          frac = projectFrac([d.renderX, d.renderY], dataLoop, null).frac
        }
        d.frac = frac

        const i0 = Math.floor(frac) % N
        const i1 = (i0 + 1) % N
        const f = frac - Math.floor(frac)
        snapshot[num] = {
          x: trackPath[i0][0] * (1 - f) + trackPath[i1][0] * f,
          y: trackPath[i0][1] * (1 - f) + trackPath[i1][1] * f,
        }
      }
      setPositions(snapshot)
      raf = requestAnimationFrame(tick)
    }

    connect()
    raf = requestAnimationFrame(tick)

    return () => {
      closed = true
      cancelAnimationFrame(raf)
      if (ws) ws.close()
    }
  }, [url, dataLoop, trackPath])

  return { positions, connected }
}
