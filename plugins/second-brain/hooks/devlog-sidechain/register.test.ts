import type { On } from 'claude-code'
import { type Engine, expect, mock, test } from 'claude-code/testing'
import { CHECK_EVERY, parseEntry } from './register'

const sidechain = { options: { devlog_mode: 'sidechain' } }
const usage = { input_tokens: 1, output_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: 900 }

function turn(overrides: { durationMs?: number; agentId?: string } = {}) {
  return {
    answer: 'done',
    durationMs: 30_000,
    isAborted: false,
    turnId: 't1',
    reason: 'answer' as const,
    ...overrides,
  }
}

test('parseEntry reads the ENTRY line and ignores NONE', () => {
  expect(parseEntry('NONE')).toBe(undefined)
  expect(parseEntry('ENTRY: Found that X needs Y.')).toBe('Found that X needs Y.')
  expect(parseEntry('thinking...\nENTRY: Multi-line reply.\n')).toBe('Multi-line reply.')
})

function world(on: On, reply: string, env: Record<string, string> = {}) {
  const clock = mock.clock(on)
  const writes: { path: string; text: string }[] = []
  const prompts: string[] = []
  let turnDone = false
  const vars: Record<string, string> = { HOME: '/home/test', ...env }
  on('session.id', () => ({ value: 'abcdef0123456789' }))
  on('env.get', (_$, e) => ({ value: vars[e.name] }))
  on('model.fork', (_$, e) => {
    prompts.push(e.prompt)
    return { value: { isAnswered: true as const, text: reply, usage } }
  })
  on('fs.read', () => ({ deny: 'ENOENT' }))
  on('fs.write', (_$, e) => {
    writes.push(e)
    return { value: undefined }
  })
  on('ui.toast', () => ({ value: undefined }))
  on('turn.complete', () => {
    turnDone = true
    return { text: 'done' }
  })
  return { clock, writes, prompts, forks: () => prompts.length, turnDone: () => turnDone }
}

async function longTurns($: Engine, n: number) {
  for (let i = 0; i < n; i++) await $.turn.complete(turn())
}

test('forks once every CHECK_EVERY long turns, after the turn returns', sidechain, async ($, on) => {
  const w = world(on, 'ENTRY: Mods can fork the transcript off-turn.')
  await longTurns($, CHECK_EVERY - 1)
  await w.clock.settle()
  expect(w.forks()).toBe(0)

  await longTurns($, 1)
  expect(w.turnDone()).toBe(true)
  await w.clock.settle()
  expect(w.forks()).toBe(1)
  expect(w.prompts[0]).toContain(`most recent ${CHECK_EVERY} turns`)

  const entry = w.writes.find(x => x.path.endsWith('/abcdef01.md'))
  expect(entry?.text).toContain('Mods can fork the transcript off-turn.')
  const log = w.writes.find(x => x.path.endsWith('/abcdef01.usage.jsonl'))
  expect(log?.text).toContain('"outcome":"entry"')
  expect(log?.text).toContain('"cache_read_input_tokens":900')
})

test('NONE logs usage but writes no entry', sidechain, async ($, on) => {
  const w = world(on, 'NONE')
  await longTurns($, CHECK_EVERY)
  await w.clock.settle()
  expect(w.forks()).toBe(1)
  expect(w.writes.map(x => x.path)).toEqual(['/home/test/.local/state/devlog-sidechain/abcdef01.usage.jsonl'])
  expect(w.writes[0]?.text).toContain('"outcome":"none"')
})

test('env knobs: every turn, no minimum, custom dir', sidechain, async ($, on) => {
  const w = world(on, 'ENTRY: knob test', {
    DEVLOG_SIDECHAIN_EVERY: '1',
    DEVLOG_SIDECHAIN_MIN_MS: '0',
    DEVLOG_SIDECHAIN_DIR: '/scratch/out',
  })
  await $.turn.complete(turn({ durationMs: 10 }))
  await w.clock.settle()
  expect(w.forks()).toBe(1)
  expect(w.prompts[0]).toContain('most recent turn.')
  expect(w.writes.some(x => x.path === '/scratch/out/abcdef01.md')).toBe(true)
})

test('/devlog-check forks now and reports the outcome and tokens', sidechain, async ($, on) => {
  const w = world(on, 'ENTRY: checked by hand')
  const r = await $.command.run({
    command: 'devlog-check',
    args: '3',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 120 },
  })
  expect(w.forks()).toBe(1)
  expect(w.prompts[0]).toContain('most recent 3 turns')
  expect(JSON.stringify(r)).toContain('devlog-check: entry: checked by hand')
  expect(JSON.stringify(r)).toContain('cache read 900')
})

test('short turns and subagent turns never count', sidechain, async ($, on) => {
  const w = world(on, 'ENTRY: nope')
  for (let i = 0; i < CHECK_EVERY; i++) {
    await $.turn.complete(turn({ durationMs: 2_000 }))
    await $.turn.complete(turn({ agentId: 'sub-1' }))
  }
  await w.clock.settle()
  expect(w.forks()).toBe(0)
})

test('default mode (nudge) leaves the mod inert', async ($, on) => {
  const w = world(on, 'ENTRY: should never be asked')
  await longTurns($, CHECK_EVERY)
  await w.clock.settle()
  expect(w.forks()).toBe(0)
  expect(w.writes.length).toBe(0)
})

test('both mode runs the sidechain too', { options: { devlog_mode: 'both' } }, async ($, on) => {
  const w = world(on, 'ENTRY: both modes fork.')
  await longTurns($, CHECK_EVERY)
  await w.clock.settle()
  expect(w.forks()).toBe(1)
})
