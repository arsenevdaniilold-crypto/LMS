import { describe, it, expect } from 'vitest'
import {
  REDISTRIBUTION_TOLERANCE,
  allFilled,
  canRedistribute,
  computeMean,
  gradeMaxFor,
  isInRange,
  isWithinTolerance,
  meanDiff,
} from './redistribution'

describe('gradeMaxFor', () => {
  it('maps each grade scale to its maximum', () => {
    expect(gradeMaxFor('0-5')).toBe(5)
    expect(gradeMaxFor('0-1')).toBe(1)
    expect(gradeMaxFor('0-100')).toBe(100)
  })
  it('defaults to 100 for unknown/undefined', () => {
    expect(gradeMaxFor(undefined)).toBe(100)
  })
})

describe('computeMean', () => {
  it('averages numeric values', () => {
    expect(computeMean([3, 5])).toBe(4)
    expect(computeMean([1, 2, 3])).toBe(2)
  })
  it('ignores missing/NaN entries', () => {
    expect(computeMean([4, undefined, NaN, null])).toBe(4)
  })
  it('returns 0 when nothing is filled', () => {
    expect(computeMean([])).toBe(0)
    expect(computeMean([undefined, null])).toBe(0)
  })
})

describe('isWithinTolerance (±0.005)', () => {
  it('accepts an exact mean', () => {
    expect(isWithinTolerance(4, 4)).toBe(true)
  })
  it('accepts a mean comfortably inside the tolerance', () => {
    expect(isWithinTolerance(50.004, 50)).toBe(true)
    expect(isWithinTolerance(49.996, 50)).toBe(true)
  })
  it('rejects just outside the tolerance', () => {
    expect(isWithinTolerance(50.02, 50)).toBe(false)
    expect(isWithinTolerance(3.5, 4)).toBe(false)
  })
  // NOTE: the exact 0.005 boundary is floating-point sensitive in JS:
  // 50.005 - 50 === 0.005000000000000782 > 0.005, so the frontend treats the
  // exact boundary as *outside* tolerance. The backend uses Decimal, where the
  // same boundary is exact and therefore accepted. Distributions are normally
  // well inside the band, so this asymmetry is harmless in practice.
  it('treats the exact 0.005 boundary as outside (JS float artifact)', () => {
    expect(meanDiff(50.005, 50)).toBeGreaterThan(0.005)
    expect(isWithinTolerance(50.005, 50)).toBe(false)
  })
  it('uses the same tolerance constant as the backend', () => {
    expect(REDISTRIBUTION_TOLERANCE).toBe(0.005)
  })
})

describe('isInRange', () => {
  it('accepts values within [0, max]', () => {
    expect(isInRange(0, 5)).toBe(true)
    expect(isInRange(5, 5)).toBe(true)
    expect(isInRange(2.5, 5)).toBe(true)
  })
  it('rejects negatives and over-max', () => {
    expect(isInRange(-1, 5)).toBe(false)
    expect(isInRange(6, 5)).toBe(false)
  })
})

describe('allFilled', () => {
  it('is true only when every entry is a number', () => {
    expect(allFilled([3, 5])).toBe(true)
    expect(allFilled([3, undefined])).toBe(false)
    expect(allFilled([])).toBe(false)
  })
})

describe('canRedistribute', () => {
  it('passes for a valid distribution (mean == target, all in range)', () => {
    // team grade 4 on 0-5 scale, [3, 5] -> mean 4
    expect(canRedistribute([3, 5], 4, 5)).toBe(true)
  })
  it('fails when the mean does not match the team grade', () => {
    expect(canRedistribute([2, 5], 4, 5)).toBe(false)
  })
  it('fails when a grade is out of range even if the mean matches', () => {
    // mean of [2, 6] is 4, but 6 > max 5
    expect(canRedistribute([2, 6], 4, 5)).toBe(false)
  })
  it('fails when not all members are graded', () => {
    expect(canRedistribute([4, undefined], 4, 5)).toBe(false)
  })
  it('passes within the tolerance band', () => {
    // 0-100 scale, grade 50, [49.99, 50.01] -> mean 50.00
    expect(canRedistribute([49.99, 50.01], 50, 100)).toBe(true)
  })
})
