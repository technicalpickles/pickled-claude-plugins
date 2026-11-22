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

const FYI = 'FYI, no reply needed: the work you parked is being picked up in a new session.'

export const buildMessage = (handoffPath: string): string =>
  [
    FYI,
    `Handoff: ${handoffPath}`,
    "Treat it as handed off. Don't keep working on it here unless the user says so.",
  ].join('\n')

export type Fyi = { path: string }

// Unanchored, so a delivery wrapped in a cross-session envelope still parses.
export const parseMessage = (text: string): Fyi | undefined => {
  if (!text.includes(FYI)) return undefined
  const path = /^\s*Handoff: (.+?)\s*$/m.exec(text)?.[1]
  return path ? { path } : undefined
}

export const noticeFor = ({ path }: Fyi): string => `Handed off: ${path} is being picked up in another session.`

export const modelNoteFor = ({ path }: Fyi): string =>
  [
    // Says who it is from: some engine versions send the row bare, inside the user's turn.
    `Note from the agent-meta plugin, not from the user: the handoff at ${path} was resumed in another session while this one was parked.`,
    "Treat that work as handed off. Don't keep working on it here unless the user says so.",
  ].join('\n')
