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

function world(on: On, env: Record<string, string> = {}, config: string | null = CONFIG, vaultExists = true) {
  const vars: Record<string, string> = { HOME: '/home/t', ...env }
  on('env.get', (_$, e) => ({ value: vars[e.name] }))
  on('fs.read', () => (config === null ? { deny: 'ENOENT' } : { value: config }))
  on('fs.exists', () => ({ value: vaultExists }))
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

test('park_vault overrides the default and expands ~', { options: { park_vault: '~/elsewhere' } }, async ($, on) => {
  world(on)
  expect(await ask($, 'agent-meta:park')).toBe('BODY\n\nPark vault: /home/t/elsewhere')
})

test('no config file, or a missing vault dir, adds nothing', async ($, on) => {
  world(on, {}, null)
  expect(await ask($, 'agent-meta:park')).toBe('BODY')
})

test('park_in_vault off adds nothing', { options: { park_in_vault: false } }, async ($, on) => {
  world(on)
  expect(await ask($, 'agent-meta:park')).toBe('BODY')
})

test('a default vault that is not a directory adds nothing', async ($, on) => {
  world(on, {}, CONFIG, false)
  expect(await ask($, 'agent-meta:park')).toBe('BODY')
})
