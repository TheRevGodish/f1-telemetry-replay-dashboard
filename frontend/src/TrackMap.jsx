import { useMemo } from 'react'
import { teamOf } from './teams'

const PAD = 40 // padding around the track bbox in image units

/**
 * trackPath = [[x, y], ...]            the traced loop
 * positions = { [driver]: { x, y } }   cars, already on the line
 */
export default function TrackMap({ trackPath, positions }) {
  const { pathD, viewBox } = useMemo(() => {
    let minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity
    for (const [x, y] of trackPath) {
      if (x < minx) minx = x
      if (x > maxx) maxx = x
      if (y < miny) miny = y
      if (y > maxy) maxy = y
    }
    const d = 'M' + trackPath.map((p) => `${p[0]},${p[1]}`).join('L') + 'Z'
    const vb = `${minx - PAD} ${miny - PAD} ${maxx - minx + 2 * PAD} ${maxy - miny + 2 * PAD}`
    return { pathD: d, viewBox: vb }
  }, [trackPath])

  return (
    <svg className="track-svg" viewBox={viewBox} preserveAspectRatio="xMidYMid meet">
      {/* track outline traced from ./frontend/public/china_trackmap.jpg */}
      <path
        d={pathD}
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.9"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* One group per car */}
      {Object.entries(positions).map(([num, p]) => {
        const team = teamOf(Number(num))
        return (
          <g key={num}>
            <circle cx={p.x} cy={p.y} r="10" fill={team.color} stroke="#ffffff" strokeWidth="2.5" />
            <text
              x={p.x + 14}
              y={p.y + 6}
              fontSize="20"
              fontWeight="700"
              fill="#ffffff"
              style={{ paintOrder: 'stroke', stroke: '#0b0f17', strokeWidth: 4 }}
            >
              {team.code}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
