import type { Register } from 'claude-code'
import { buildMessage, handoffPathFrom, isUnparkSkill, parseHandoff } from './unpark-notify'

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
