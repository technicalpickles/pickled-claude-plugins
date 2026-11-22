import { describe, expect, test } from 'claude-code/testing'

const ORIGIN = '11111111-2222-3333-4444-555555555555'
const ME = '99999999-8888-7777-6666-555555555555'
const PATH = '/vault/202611151200 some topic.md'

const handoff = (heading: string, session = ORIGIN) =>
  [
    `# ${heading}: Some topic`,
    '',
    '**Parked:** 2026-11-15 12:00',
    `**Session:** ${session}`,
    '**Branch:** main',
    '',
    '## Next Steps',
    '1. Run the dashboard check',
    '2. Open the PR',
  ].join('\n')

const unparkPrompt = (args: string) => `# Unpark\n\nbody\n\nARGUMENTS: ${args}`

describe('unpark tells the session a handoff came from', () => {
  const run = async (
    $: any,
    on: any,
    opts: { file?: string | Error; skill?: string; text?: string; isDelivered?: boolean },
  ) => {
    const sent: { to: unknown; text: string }[] = []
    on('session.id', () => ({ value: ME }))
    on('skill.prompt', (_$: any, e: any) => ({ text: e.text }))
    on('fs.read', () => {
      if (opts.file instanceof Error) throw opts.file
      return { value: opts.file ?? '' }
    })
    on('session.send', (_$: any, e: any) => {
      sent.push({ to: e.to, text: e.text })
      return opts.isDelivered === false ? { isDelivered: false, reason: 'no live session' } : { isDelivered: true }
    })
    const result = await $.skill.prompt({
      skill: opts.skill ?? 'agent-meta:unpark',
      text: opts.text ?? unparkPrompt(PATH),
    })
    return { sent, result }
  }

  test('a Parked handoff sends one FYI naming the file, never its next steps', async ($, on) => {
    const { sent, result } = await run($, on, { file: handoff('Parked') })

    expect(sent).toHaveLength(1)
    expect(String(sent[0].to)).toContain(ORIGIN)
    expect(sent[0].text).toContain('no reply needed')
    expect(sent[0].text).toContain(PATH)
    expect(sent[0].text).not.toContain('Run the dashboard check')
    expect(result.text).toContain('ARGUMENTS:')
  })

  test('a Checkpoint handoff sends too', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Checkpoint') })
    expect(sent).toHaveLength(1)
  })

  test('a Wrapped record sends nothing', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Wrapped') })
    expect(sent).toHaveLength(0)
  })

  test('no path argument sends nothing', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked'), text: '# Unpark\n\nbody' })
    expect(sent).toHaveLength(0)
  })

  test('a missing file sends nothing and the skill still loads', async ($, on) => {
    const { sent, result } = await run($, on, { file: new Error('ENOENT') })
    expect(sent).toHaveLength(0)
    expect(result.text).toContain('ARGUMENTS:')
  })

  test('a non-UUID Session id sends nothing', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked', 'unknown') })
    expect(sent).toHaveLength(0)
  })

  test('a handoff with no Session line sends nothing', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked').replace(/^\*\*Session:.*\n/m, '') })
    expect(sent).toHaveLength(0)
  })

  test('resuming inside the origin session sends nothing', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked', ME) })
    expect(sent).toHaveLength(0)
  })

  test('other skills are left alone', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked'), skill: 'agent-meta:park' })
    expect(sent).toHaveLength(0)
  })

  test('a refused send does not break the skill', async ($, on) => {
    const { result } = await run($, on, { file: handoff('Parked'), isDelivered: false })
    expect(result.text).toContain('ARGUMENTS:')
  })

  test('a path with spaces and quotes is read whole', async ($, on) => {
    const { sent } = await run($, on, { file: handoff('Parked'), text: unparkPrompt(`"${PATH}"`) })
    expect(sent[0].text).toContain(`Handoff: ${PATH}`)
  })

  test('the same handoff is announced once', async ($, on) => {
    const sent: unknown[] = []
    on('session.id', () => ({ value: ME }))
    on('skill.prompt', (_$: any, e: any) => ({ text: e.text }))
    on('fs.read', () => ({ value: handoff('Parked') }))
    on('session.send', (_$: any, e: any) => {
      sent.push(e.text)
      return { isDelivered: true }
    })
    await $.skill.prompt({ skill: 'agent-meta:unpark', text: unparkPrompt(PATH) })
    await $.skill.prompt({ skill: 'agent-meta:unpark', text: unparkPrompt(PATH) })
    expect(sent).toHaveLength(1)
  })
})

describe('the origin notes the FYI without a model turn', () => {
  // Registers every engine stub before the test first calls $.
  const stubs = (on: any, opts: { appendFails?: boolean } = {}) => {
    const seen = { appended: [] as { type: string; text: string }[], passedOn: false, sent: '' }
    on('session.id', () => ({ value: ME }))
    on('skill.prompt', (_$: any, e: any) => ({ text: e.text }))
    on('fs.read', () => ({ value: handoff('Parked') }))
    on('session.send', (_$: any, e: any) => {
      seen.sent = e.text
      return { isDelivered: true }
    })
    on('session.append', (_$: any, e: any, next: any) => {
      if (opts.appendFails) return { deny: 'refused by policy' }
      seen.appended.push({ type: e.message.type, text: e.message.content[0].text })
      return next(e)
    })
    on('session.receive', (_$: any, e: any) => {
      seen.passedOn = true
      return { text: e.text }
    })
    return seen
  }

  // What the sender really writes, wrapped the way a cross-session delivery can arrive.
  const sentFyi = async ($: any, seen: { sent: string }) => {
    await $.skill.prompt({ skill: 'agent-meta:unpark', text: unparkPrompt(PATH) })
    return `<cross-session-message from="uds:/tmp/x.sock" from-plugin="agent-meta">\n${seen.sent}\n</cross-session-message>`
  }

  const receive = ($: any, text: string, extra: Record<string, unknown> = {}) =>
    $.session.receive({ origin: { kind: 'peer', plugin: 'agent-meta' }, text, ...extra })

  test('an FYI is consumed and leaves a notice and a note for the next turn', async ($, on) => {
    const seen = stubs(on)
    const result = await receive($, await sentFyi($, seen))

    expect(seen.passedOn).toBe(false)
    expect(result.consumed).toBeTruthy()
    const byType = Object.fromEntries(seen.appended.map(a => [a.type, a.text]))
    expect(Object.keys(byType).sort()).toEqual(['system', 'user'])
    expect(byType.system).toContain(PATH)
    expect(byType.user).toContain(PATH)
    expect(byType.user).toContain('handed off')
  })

  test('an ordinary peer message passes through', async ($, on) => {
    const seen = stubs(on)
    const result = await receive($, 'can you rerun the tests?')
    expect(seen.passedOn).toBe(true)
    expect(result.text).toBe('can you rerun the tests?')
    expect(seen.appended).toHaveLength(0)
  })

  test('an FYI to a subagent passes through', async ($, on) => {
    const seen = stubs(on)
    await receive($, await sentFyi($, seen), { agentId: 'agent-1' })
    expect(seen.passedOn).toBe(true)
    expect(seen.appended).toHaveLength(0)
  })

  test('an FYI-shaped prompt that is not from a peer passes through', async ($, on) => {
    const seen = stubs(on)
    await receive($, await sentFyi($, seen), { origin: { kind: 'bridge' } })
    expect(seen.passedOn).toBe(true)
    expect(seen.appended).toHaveLength(0)
  })

  test('a failed append falls back to delivering the FYI', async ($, on) => {
    const seen = stubs(on, { appendFails: true })
    const result = await receive($, await sentFyi($, seen))
    expect(seen.passedOn).toBe(true)
    expect(result.text).toContain(`Handoff: ${PATH}`)
  })
})
