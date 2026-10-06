import type { Register } from 'claude-code'

export const register: Register = on => {
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
