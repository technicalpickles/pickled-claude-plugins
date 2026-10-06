import { describe, expect, test } from 'claude-code/testing'

describe('/session-id', () => {
  test('prints the session ID', async ($, on) => {
    on('session.id', () => ({ value: 'abc-123' }))

    const result = await $.command.run({
      command: 'session-id',
      args: '',
      origin: { kind: 'composer' },
      presentation: { isFullscreen: false, columns: 80 },
    })

    expect(result.text).toBe('abc-123')
  })
})
