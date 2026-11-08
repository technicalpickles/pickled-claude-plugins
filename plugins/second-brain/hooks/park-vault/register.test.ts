import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import { defaultVault } from './register'

const CONFIG = `# Second Brain Configuration

## Vaults

- primary: /v/personal
- work: /v/work

Default: work
`

test('defaultVault honours the Default line, else the first vault', () => {
  expect(defaultVault(CONFIG)).toBe('/v/work')
  expect(defaultVault(CONFIG.replace('Default: work', ''))).toBe('/v/personal')
  expect(defaultVault('nothing here')).toBe(undefined)
})

function world(
  on: On,
  env: Record<string, string> = {},
  configs: Record<string, string> = { '/home/t/.claude/second-brain.md': CONFIG },
  existing: string[] | null = null,
  reads: string[] = [],
) {
  const vars: Record<string, string> = { HOME: '/home/t', ...env }
  on('env.get', (_$, e) => ({ value: vars[e.name] }))
  on('fs.read', (_$, e) => {
    reads.push(e.path)
    return e.path in configs ? { value: configs[e.path] } : { deny: 'ENOENT' }
  })
  on('fs.exists', (_$, e) => ({ value: existing === null || existing.includes(e.path) }))
  on('skill.prompt', (_$, e) => ({ text: e.text }))
}

const ask = ($: any, skill: string) => $.skill.prompt({ skill, text: 'BODY' }).then((r: any) => r.text)

test('park gets the default vault line', async ($, on) => {
  world(on)
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /v/work')
})

test('unpark gets it too', async ($, on) => {
  world(on)
  expect(await ask($, 'agent-meta:unpark')).toContain('Park vault: /v/work')
})

test('other skills are untouched', async ($, on) => {
  world(on)
  expect(await ask($, 'git:commit')).toBe('BODY')
})

test('SB_NOTE_VAULT wins over second-brain.md', async ($, on) => {
  world(on, { SB_NOTE_VAULT: ' /v/scratch ' })
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /v/scratch')
})

test('an SB_NOTE_VAULT that is not a directory falls back to the config', async ($, on) => {
  world(on, { SB_NOTE_VAULT: '/v/gone' }, undefined, ['/v/work'])
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /v/work')
})

test('CLAUDE_CONFIG_DIR replaces ~/.claude as the dir second-brain.md is read from', async ($, on) => {
  const reads: string[] = []
  world(
    on,
    { CLAUDE_CONFIG_DIR: '/cfg' },
    { '/cfg/second-brain.md': CONFIG, '/home/t/.claude/second-brain.md': '- home: /v/home' },
    null,
    reads,
  )
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /v/work')
  expect(reads).toEqual(['/cfg/second-brain.md'])
})

test('a CLAUDE_CONFIG_DIR list falls through to the next dir', async ($, on) => {
  world(on, { CLAUDE_CONFIG_DIR: '/a,/b' }, { '/b/second-brain.md': '- b: /v/b' })
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /v/b')
})

test('no config file adds nothing', async ($, on) => {
  world(on, {}, {})
  expect(await ask($, 'agent-meta:park')).toBe('BODY')
})

test('a default vault that is not a directory adds nothing', async ($, on) => {
  world(on, {}, undefined, [])
  expect(await ask($, 'agent-meta:park')).toBe('BODY')
})
