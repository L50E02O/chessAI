import React from 'react'

const detectors = [
  { label: 'Lichess (default)', value: 'lichess' },
  { label: 'YOLOv8 (local)', value: 'yolo' },
]

export default function Controls({ depth, setDepth, timeMs, setTimeMs, detector, setDetector }) {
  return (
    <div className= space-y-3>
      <div className=grid grid-cols-2 gap-2>
        <label className=text-sm text-slate-400>
          Profundidad
          <input
            type=number
            min={1}
            max={30}
            value={depth}
            onChange={(event) => setDepth(Number(event.target.value))}
            className=mt-1 w-full rounded bg-slate-900 px-2 py-1 text-white
          />
        </label>
        <label className=text-sm text-slate-400>
          Tiempo (ms)
          <input
            type=number
            min={100}
            max={5000}
            step={100}
            value={timeMs}
            onChange={(event) => setTimeMs(Number(event.target.value))}
            className=mt-1 w-full rounded bg-slate-900 px-2 py-1 text-white
          />
        </label>
      </div>
      <label className=text-sm text-slate-400>
        Detector
        <select
          value={detector}
          onChange={(event) => setDetector(event.target.value)}
          className=mt-1 w-full rounded bg-slate-900 px-2 py-1 text-white
        >
          {detectors.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
