import { describe, expect, test } from 'claude-code/testing'

const STATUS = '## feat/x...origin/feat/x [ahead 1]\n M src/a.ts\n?? notes.md\n'

describe('park gets the git state appended', () => {
  const run = async ($: any, on: any, opts: { skill?: string; status?: string | Error; exitCode?: number }) => {
    const calls: string[][] = []
    on('skill.prompt', (_$: any, e: any) => ({ text: e.text }))
    on('process.run', (_$: any, e: any) => {
      calls.push(e.argv)
      if (opts.status instanceof Error) throw opts.status
      return { value: { exitCode: opts.exitCode ?? 0, stdout: opts.status ?? STATUS, stderr: '' } }
    })
    const result = await $.skill.prompt({ skill: opts.skill ?? 'agent-meta:park', text: '# Park\n\nbody' })
    return { calls, result }
  }

  test('park sees the branch line and the changed files', async ($, on) => {
    const { result } = await run($, on, {})
    expect(result.text).toContain('# Park')
    expect(result.text).toContain('Git state')
    expect(result.text).toContain('[ahead 1]')
    expect(result.text).toContain('?? notes.md')
  })

  test('outside a repo the prompt is unchanged', async ($, on) => {
    const { result } = await run($, on, { exitCode: 128, status: '' })
    expect(result.text).toBe('# Park\n\nbody')
  })

  test('a git that cannot start leaves the prompt unchanged', async ($, on) => {
    const { result } = await run($, on, { status: new Error('ENOENT') })
    expect(result.text).toBe('# Park\n\nbody')
  })

  test('a long status is capped', async ($, on) => {
    const many = ['## main', ...Array.from({ length: 60 }, (_, i) => `?? f${i}`)].join('\n')
    const { result } = await run($, on, { status: many })
    expect(result.text).toContain('... 21 more')
    expect(result.text).not.toContain('?? f59')
  })

  test('unpark and other skills are left alone', async ($, on) => {
    const { calls, result } = await run($, on, { skill: 'agent-meta:unpark' })
    expect(calls).toHaveLength(0)
    expect(result.text).not.toContain('Git state')
  })
})
