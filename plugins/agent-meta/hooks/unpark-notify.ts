const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export type Handoff = {
  kind: 'Parked' | 'Checkpoint'
  sessionId: string
}

export const isUnparkSkill = (skill: string): boolean => skill === 'unpark' || skill.endsWith(':unpark')

export const handoffPathFrom = (promptText: string): string | undefined => {
  const match = /^ARGUMENTS: (.+)$/m.exec(promptText)
  const arg = match?.[1]?.trim().replace(/^(["'])(.*)\1$/, '$2')
  return arg ? arg : undefined
}

export const parseHandoff = (content: string): Handoff | undefined => {
  const heading = /^# (Parked|Checkpoint):/m.exec(content)
  const heading1 = /^# \S/m.exec(content)
  if (!heading || heading.index !== heading1?.index) return undefined

  const sessionId = /^\*\*Session:\*\*\s*(\S+)\s*$/m.exec(content)?.[1]
  if (!sessionId || !SESSION_ID.test(sessionId)) return undefined

  return { kind: heading[1] as Handoff['kind'], sessionId }
}

export const buildMessage = (handoffPath: string): string =>
  [
    'FYI, no reply needed: the work you parked is being picked up in a new session.',
    `Handoff: ${handoffPath}`,
    "Treat it as handed off. Don't keep working on it here unless the user says so.",
  ].join('\n')
