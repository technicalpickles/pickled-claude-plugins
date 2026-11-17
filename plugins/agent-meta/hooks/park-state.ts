const MAX_LINES = 40

export const isParkSkill = (skill: string): boolean => skill === 'park' || skill.endsWith(':park')

export const gitStateBlock = (statusOutput: string): string | undefined => {
  const lines = statusOutput.split('\n').filter(Boolean)
  if (lines.length === 0) return undefined
  const shown = lines.slice(0, MAX_LINES)
  if (lines.length > MAX_LINES) shown.push(`... ${lines.length - MAX_LINES} more`)
  return ['Git state (`git status --short --branch` at park time):', '```', ...shown, '```'].join('\n')
}
