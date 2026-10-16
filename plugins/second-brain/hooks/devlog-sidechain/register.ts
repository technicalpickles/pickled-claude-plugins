import type { EngineInterface, ModelForkResult, Register } from 'claude-code'

// Each fork re-reads the whole transcript (from cache, but still billed), so
// by default only check every Nth substantial turn and judge them together.
export const CHECK_EVERY = 4
// Turns shorter than this are chit-chat; not worth counting.
const MIN_TURN_MS = 15_000

type Config = { every: number; minMs: number; dir: string }

async function config($: EngineInterface): Promise<Config> {
  // $.env.get must take a literal, so the validator can list what's read.
  const num = (raw: string | undefined, fallback: number) => {
    const n = raw === undefined || raw === '' ? NaN : Number(raw)
    return Number.isFinite(n) && n >= 0 ? n : fallback
  }
  return {
    every: Math.max(1, num(await $.env.get('DEVLOG_SIDECHAIN_EVERY'), CHECK_EVERY)),
    minMs: num(await $.env.get('DEVLOG_SIDECHAIN_MIN_MS'), MIN_TURN_MS),
    dir: (await $.env.get('DEVLOG_SIDECHAIN_DIR')) ?? `${await $.env.get('HOME')}/.local/state/devlog-sidechain`,
  }
}

export function prompt(turns: number): string {
  return `[devlog-sidechain] Side question, not part of the conversation. Do not answer the user or continue the work.

Look only at the most recent ${turns === 1 ? 'turn' : `${turns} turns`}. Did the assistant's own work in ${turns === 1 ? 'it' : 'them'} do any of these:
- finish a feature or fix a notable bug
- discover something non-obvious (a gotcha, undocumented behavior, a workaround that took several tries, a constraint only noticed after hitting it)

Not worth logging: the user stating a fact the assistant didn't act on, acknowledgements, questions, plans not yet carried out, routine edits. If you would describe the turn as "nothing new happened", or you're unsure, the answer is NONE.

If not, reply with exactly: NONE

If so, reply with one line starting "ENTRY: " followed by one to three sentences of prose: what happened, why, anything surprising. Standalone enough to make sense without the conversation. No markdown, no title.`
}

export function parseEntry(text: string): string | undefined {
  const line = text.trim().split('\n').find(l => l.startsWith('ENTRY:'))
  const entry = line?.slice('ENTRY:'.length).trim()
  return entry ? entry : undefined
}

function hhmm(ms: number): string {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function appendTo($: EngineInterface, path: string, text: string) {
  const existing = await $.fs.read(path).catch(() => '')
  await $.fs.write(path, existing + text)
}

type Judgment = {
  outcome: string
  entry: string | undefined
  usage: Extract<ModelForkResult, { usage: unknown }>['usage'] | null
}

async function judge($: EngineInterface, sessionId: string, turns: number, via: string): Promise<Judgment> {
  const { dir } = await config($)
  const base = `${dir}/${sessionId.slice(0, 8)}`
  const startedAt = await $.clock.now()
  const r = await $.model.fork({ prompt: prompt(turns) })
  const entry = r.isAnswered ? parseEntry(r.text) : undefined
  const judgment: Judgment = {
    outcome: r.isAnswered ? (entry ? 'entry' : 'none') : r.reason,
    entry,
    usage: 'usage' in r ? r.usage : null,
  }

  const record = { at: startedAt, via, turns, ms: (await $.clock.now()) - startedAt, ...judgment }
  await appendTo($, `${base}.usage.jsonl`, `${JSON.stringify(record)}\n`)
  if (entry !== undefined) {
    const existing = await $.fs.read(`${base}.md`).catch(() => '')
    const header = existing === '' ? `# devlog-sidechain: session ${sessionId}\n\n` : ''
    await $.fs.write(`${base}.md`, `${existing}${header}- ${hhmm(await $.clock.now())} ${entry}\n`)
  }
  return judgment
}

async function judgeInBackground($: EngineInterface, sessionId: string, turns: number, inFlight: Set<string>) {
  try {
    const { entry } = await judge($, sessionId, turns, 'turn')
    if (entry !== undefined) $.ui.toast(`devlog: ${entry.slice(0, 60)}`)
  } finally {
    inFlight.delete(sessionId)
  }
}

export const register: Register = on => {
  const inFlight = new Set<string>()
  const pending = new Map<string, number>()

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'devlog-check',
      description: 'Ask the devlog side fork now whether the last N turns (default 1) are devlog-worthy',
      argumentHint: '[turns]',
    })
    return next(e)
  })

  on('command.run', { command: 'devlog-check' }, async ($, e) => {
    const turns = Math.max(1, Number.parseInt(e.args, 10) || 1)
    const j = await judge($, await $.session.id(), turns, 'command')
    const tokens = j.usage ? ` (cache read ${j.usage.cache_read_input_tokens}, in ${j.usage.input_tokens}, out ${j.usage.output_tokens})` : ''
    return { text: `devlog-check: ${j.outcome}${j.entry ? `: ${j.entry}` : ''}${tokens}` }
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined || e.isAborted) return result
    const { every, minMs } = await config($)
    if (e.durationMs < minMs) return result

    const sessionId = await $.session.id()
    const turns = (pending.get(sessionId) ?? 0) + 1
    if (turns < every || inFlight.has(sessionId)) {
      pending.set(sessionId, turns)
      return result
    }
    pending.set(sessionId, 0)
    inFlight.add(sessionId)

    // Off the dispatch: a timer outlives this hook, so the fork never holds
    // the turn open and isn't aborted when the next prompt arrives. Firing
    // right away also lands while the main thread's prompt cache is warm.
    $.clock.after(0, () => {
      void judgeInBackground($, sessionId, turns, inFlight).catch(() => {})
    })
    return result
  })
}
