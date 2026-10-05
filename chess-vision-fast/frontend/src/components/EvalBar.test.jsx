import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import EvalBar from './EvalBar'

describe('EvalBar', () => {
  it('shows an even bar when there is no score', () => {
    render(<EvalBar score={null} />)
    expect(screen.getByTestId('eval-white')).toHaveStyle({ height: '50%' })
    expect(screen.getByTestId('eval-text')).toHaveTextContent('0.00')
  })

  it('shows the formatted centipawn score', () => {
    render(<EvalBar score={{ cp: 142, mate: null }} />)
    expect(screen.getByTestId('eval-text')).toHaveTextContent('+1.42')
  })

  it('fills the bar completely for a White mate', () => {
    render(<EvalBar score={{ cp: null, mate: 3 }} />)
    expect(screen.getByTestId('eval-white')).toHaveStyle({ height: '100%' })
    expect(screen.getByTestId('eval-text')).toHaveTextContent('M3')
  })

  it('empties the bar for a Black mate', () => {
    render(<EvalBar score={{ cp: null, mate: -2 }} />)
    expect(screen.getByTestId('eval-white')).toHaveStyle({ height: '0%' })
    expect(screen.getByTestId('eval-text')).toHaveTextContent('-M2')
  })
})
