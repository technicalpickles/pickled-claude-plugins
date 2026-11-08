import type { On } from 'claude-code'
import { describe, expect, test } from 'claude-code/testing'

type Helper = { exitCode: number; stdout: string }

function world(on: On, env: Record<string, string> = {}, helpers: Record<string, Helper> = {}) {
  on('env.get', (_$, e) => ({ value: env[e.name] }))
  on('process.run', (_$, e) => {
    const out = helpers[e.argv[2]] ?? { exitCode: 1, stdout: '' }
    return { value: { exitCode: out.exitCode, stdout: out.stdout, stderr: '' } }
  })
  on('skill.prompt', (_$, e) => ({ text: e.text }))
}

const ask = ($: any, skill = 'agent-meta:park') =>
  $.skill.prompt({ skill, text: 'BODY' }).then((r: any) => r.text as string)

const line = (t: string) => `BODY\n\nPark destination: ${t}`

describe('park destination', () => {
  test('literal setting', { options: { destination: 'sb {file}' } }, async ($, on) => {
    world(on)
    expect(await ask($)).toBe(line('sb {file}'))
  })

  test('also on the bare skill name', { options: { destination: 'sb {file}' } }, async ($, on) => {
    world(on)
    expect(await ask($, 'park')).toBe(line('sb {file}'))
  })

  test('helper setting wins over the literal', { options: { destination: 'lit', destination_helper: 'h' } }, async ($, on) => {
    world(on, {}, { h: { exitCode: 0, stdout: 'from-helper {file}\n' } })
    expect(await ask($)).toBe(line('from-helper {file}'))
  })

  test('a failing helper falls back to the literal', { options: { destination: 'lit {file}', destination_helper: 'h' } }, async ($, on) => {
    world(on, {}, { h: { exitCode: 1, stdout: '' } })
    expect(await ask($)).toBe(line('lit {file}'))
  })

  test('a multi-line helper answer is rejected', { options: { destination_helper: 'h' } }, async ($, on) => {
    world(on, {}, { h: { exitCode: 0, stdout: 'a\nb' } })
    expect(await ask($)).toBe('BODY')
  })

  test('legacy AGENT_PARK_DESTINATION still works', async ($, on) => {
    world(on, { AGENT_PARK_DESTINATION: 'legacy {file}' })
    expect(await ask($)).toBe(line('legacy {file}'))
  })

  test('legacy helper still works', async ($, on) => {
    world(on, { AGENT_PARK_DESTINATION_HELPER: 'lh' }, { lh: { exitCode: 0, stdout: 'legacy-helper {file}' } })
    expect(await ask($)).toBe(line('legacy-helper {file}'))
  })

  test('settings beat the legacy env vars', { options: { destination: 'opt {file}' } }, async ($, on) => {
    world(on, { AGENT_PARK_DESTINATION: 'legacy {file}' })
    expect(await ask($)).toBe(line('opt {file}'))
  })

  test('empty settings fall back to the legacy env var', { options: { destination: '' } }, async ($, on) => {
    world(on, { AGENT_PARK_DESTINATION: 'legacy {file}' })
    expect(await ask($)).toBe(line('legacy {file}'))
  })

  test('nothing configured adds nothing', async ($, on) => {
    world(on)
    expect(await ask($)).toBe('BODY')
  })

  test('unpark and other skills never get a destination', { options: { destination: 'sb {file}' } }, async ($, on) => {
    world(on)
    expect(await ask($, 'agent-meta:unpark')).toBe('BODY')
    expect(await ask($, 'git:commit')).toBe('BODY')
  })
})
