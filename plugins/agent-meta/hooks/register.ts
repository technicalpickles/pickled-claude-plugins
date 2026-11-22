import type { Register } from 'claude-code'
import {
  buildMessage,
  handoffPathFrom,
  isUnparkSkill,
  modelNoteFor,
  noticeFor,
  parseHandoff,
  parseMessage,
} from './unpark-notify'

export const register: Register = on => {
  const told = new Set<string>()

  on('skill.prompt', async ($, e, next) => {
    if (!isUnparkSkill(e.skill)) return next(e)

    try {
      const path = handoffPathFrom(e.text)
      if (!path) return next(e)

      const handoff = parseHandoff(await $.fs.read(path))
      if (!handoff || handoff.sessionId === (await $.session.id())) return next(e)

      const key = `${handoff.sessionId} ${path}`
      if (told.has(key)) return next(e)
      told.add(key)

      await $.session.send({ to: { sessionId: handoff.sessionId }, text: buildMessage(path) })
    } catch {
      // a missing handoff or a refused send must never stop the resume
    }
    return next(e)
  })

  // The origin side: note the FYI without starting a model turn.
  on('session.receive', async ($, e, next) => {
    if (e.agentId !== undefined || e.origin.kind !== 'peer') return next(e)
    const fyi = parseMessage(e.text)
    if (!fyi) return next(e)

    // The model note is the one that matters, so append it first: if it lands
    // and the notice is refused, the FYI still did its job.
    const note = (type: 'system' | 'user', text: string) =>
      $.session.append({ message: { type, content: [{ type: 'text', text }] } }).then(
        r => !('deny' in r && r.deny),
        () => false,
      )
    if (!(await note('user', modelNoteFor(fyi)))) return next(e) // a costly FYI beats a lost one
    await note('system', noticeFor(fyi))
    return { consumed: 'unpark handoff FYI, noted without a turn' }
  })

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'session-id',
      description: 'Show the current session ID',
      immediate: true,
    })
    return next(e)
  })

  on('command.run', { command: 'session-id' }, async $ => ({
    text: await $.session.id(),
  }))
}
