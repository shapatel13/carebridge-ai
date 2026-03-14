/**
 * Count syllables in a word using a simple heuristic.
 */
function countSyllables(word: string): number {
  word = word.toLowerCase().replace(/[^a-z]/g, '')
  if (word.length <= 3) return 1
  word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '')
  word = word.replace(/^y/, '')
  const matches = word.match(/[aeiouy]{1,2}/g)
  return matches ? matches.length : 1
}

/**
 * Calculate Flesch-Kincaid Grade Level.
 * Returns a grade number (e.g., 5.2 means ~5th grade reading level).
 */
export function fleschKincaidGrade(text: string): number {
  if (!text.trim()) return 0

  const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 0)
  const words = text.split(/\s+/).filter((w) => w.replace(/[^a-zA-Z]/g, '').length > 0)

  if (sentences.length === 0 || words.length === 0) return 0

  const totalSyllables = words.reduce((sum, w) => sum + countSyllables(w), 0)

  const grade =
    0.39 * (words.length / sentences.length) +
    11.8 * (totalSyllables / words.length) -
    15.59

  return Math.max(0, Math.round(grade * 10) / 10)
}

/**
 * Get a severity label for the readability grade.
 */
export function gradeSeverity(grade: number): 'green' | 'yellow' | 'red' {
  if (grade <= 6) return 'green'
  if (grade <= 8) return 'yellow'
  return 'red'
}
