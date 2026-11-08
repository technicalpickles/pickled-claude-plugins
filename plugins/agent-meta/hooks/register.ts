import type { EngineInterface, Register } from 'claude-code'

const PARK = /^(agent-meta:)?park$/
const MAX_TEMPLATE_LENGTH = 2000
const HELPER_TIMEOUT_MS = 15_000

const isTemplate = (s: string) => s !== '' && s.length <= MAX_TEMPLATE_LENGTH && !/[\r\n]/.test(s)

async function runHelper($: EngineInterface, helper: string): Promise<string | undefined> {
  const ran = await $.process.run(['sh', '-c', helper], { timeoutMs: HELPER_TIMEOUT_MS }).catch(() => undefined)
  const out = ran?.exitCode === 0 ? ran.stdout.trim() : ''
  return isTemplate(out) ? out : undefined
}

// Plugin settings first, then the legacy env vars. Within each pair the helper
// wins, and one that fails or yields nothing usable falls through to the literal.
async function destination($: EngineInterface, options: Record<string, unknown>): Promise<string | undefined> {
  const text = (v: unknown) => (typeof v === 'string' ? v.trim() : '')
  const pairs = [
    { helper: text(options.destination_helper), literal: text(options.destination) },
    {
      helper: text(await $.env.get('AGENT_PARK_DESTINATION_HELPER')),
      literal: text(await $.env.get('AGENT_PARK_DESTINATION')),
    },
  ]
  for (const { helper, literal } of pairs) {
    const fromHelper = helper ? await runHelper($, helper) : undefined
    if (fromHelper) return fromHelper
    if (isTemplate(literal)) return literal
  }
  return undefined
}

export const register: Register = (on, options) => {
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

  on('skill.prompt', async ($, e, next) => {
    if (!PARK.test(e.skill)) return next(e)
    const template = await destination($, options)
    return next(template ? { ...e, text: `${e.text}\n\nPark destination: ${template}` } : e)
  })
}
