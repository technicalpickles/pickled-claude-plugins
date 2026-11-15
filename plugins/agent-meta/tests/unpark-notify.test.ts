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

  test('a Parked handoff sends one FYI naming the file and first step', async ($, on) => {
    const { sent, result } = await run($, on, { file: handoff('Parked') })

    expect(sent).toHaveLength(1)
    expect(String(sent[0].to)).toContain(ORIGIN)
    expect(sent[0].text).toContain('no reply needed')
    expect(sent[0].text).toContain(PATH)
    expect(sent[0].text).toContain('Starting with: Run the dashboard check')
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
