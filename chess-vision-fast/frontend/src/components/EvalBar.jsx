import React from 'react'
import { evalToWhitePercent, formatScore } from '../lib/chess'

export default function EvalBar({ score, scoreText }) {
  const whitePercent = evalToWhitePercent(score)
  let topText = score ? formatScore(score) : (scoreText ? scoreText.split(' ')[0] : '0.00')
  if (!topText.startsWith('+') && !topText.startsWith('-') && topText !== '0.00' && !topText.startsWith('M')) {
    topText = `+${topText}`
  }
  let bottomText = topText.startsWith('+') ? topText.replace('+', '-') : topText.startsWith('-') ? topText.replace('-', '+') : topText

  return (
    <div className="flex flex-col items-center justify-between h-full py-1 pr-3 select-none">
      {/* Top score pill */}
      <div data-testid="eval-text" className="text-[11px] font-bold font-mono text-emerald-400 bg-slate-900/80 px-1.5 py-0.5 rounded border border-emerald-500/30 shadow-sm">
        {topText}
      </div>

      {/* Vertical Eval Bar Gauge */}
      <div className="relative w-3.5 flex-1 my-2 rounded-full overflow-hidden bg-slate-900 border border-slate-700/80 shadow-inner flex flex-col justify-end">
        <div
          data-testid="eval-white"
          className="w-full bg-gradient-to-t from-emerald-600 to-emerald-400 rounded-full transition-all duration-500 ease-out"
          style={{ height: `${whitePercent}%` }}
        ></div>
      </div>

      {/* Bottom score pill */}
      <div className="text-[10px] font-mono text-slate-500">
        {bottomText}
      </div>
    </div>
  )
}
