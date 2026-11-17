import type { Register } from 'claude-code'
import { gitStateBlock, isParkSkill } from './park-state'
import { buildMessage, handoffPathFrom, isUnparkSkill, parseHandoff } from './unpark-notify'

export const register: Register = on => {
  const told = new Set<string>()

  on('skill.prompt', async ($, e, next) => {
    if (isParkSkill(e.skill)) {
      try {
        const { exitCode, stdout } = await $.process.run(['git', 'status', '--short', '--branch'], { timeoutMs: 5000 })
        const block = exitCode === 0 ? gitStateBlock(stdout) : undefined
        if (block) return next({ ...e, text: `${e.text}\n\n${block}` })
      } catch {
        // no git, or not a repo: park works without the block
      }
      return next(e)
    }
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
