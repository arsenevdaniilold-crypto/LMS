/**
 * Pure helpers for the grade-redistribution UI.
 *
 * Mirrors the backend rule (app/services/solutions.py): the per-member grades
 * must average to the team grade within REDISTRIBUTION_TOLERANCE, and every
 * grade must sit within the assignment's scale. Kept framework-free so it can
 * be unit-tested in isolation and reused by RedistributePage.
 */
import type { GradeType } from '@/shared/api/types'

export const REDISTRIBUTION_TOLERANCE = 0.005

export function gradeMaxFor(gradeType: GradeType | undefined): number {
  if (gradeType === '0-5') return 5
  if (gradeType === '0-1') return 1
  return 100
}

/** Mean of the numeric values, ignoring missing/NaN entries. Returns 0 when empty. */
export function computeMean(values: Array<number | undefined | null>): number {
  let sum = 0
  let count = 0
  for (const v of values) {
    if (typeof v === 'number' && !Number.isNaN(v)) {
      sum += v
      count += 1
    }
  }
  return count > 0 ? sum / count : 0
}

/** Absolute distance between the current mean and the team grade. */
export function meanDiff(mean: number, target: number): number {
  return Math.abs(mean - target)
}

export function isWithinTolerance(mean: number, target: number): boolean {
  return meanDiff(mean, target) <= REDISTRIBUTION_TOLERANCE
}

export function isInRange(value: number, gradeMax: number): boolean {
  return value >= 0 && value <= gradeMax
}

/** True only when every member has a grade. */
export function allFilled(values: Array<number | undefined | null>): boolean {
  return values.length > 0 && values.every((v) => typeof v === 'number' && !Number.isNaN(v))
}

/**
 * Whether the redistribution may be submitted: all members graded, every grade
 * in range, and the mean equal to the team grade within tolerance.
 */
export function canRedistribute(
  values: Array<number | undefined | null>,
  target: number,
  gradeMax: number,
): boolean {
  if (!allFilled(values)) return false
  for (const v of values) {
    if (!isInRange(v as number, gradeMax)) return false
  }
  return isWithinTolerance(computeMean(values), target)
}
