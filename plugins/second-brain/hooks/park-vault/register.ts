import type { Register } from 'claude-code'

const PARK_SKILL = /^(agent-meta:)?(un)?park$/

// ~/.claude/second-brain.md lists "- name: /path" under "## Vaults" and names
// the default with "Default: name". No default line means the first vault.
export function defaultVault(config: string): string | undefined {
  const vaults = [...config.matchAll(/^- ([^:\s]+):\s*(\S.*?)\s*$/gm)].map(m => ({ name: m[1], path: m[2] }))
  const wanted = config.match(/^Default:\s*(\S+)/m)?.[1]
  return (vaults.find(v => v.name === wanted) ?? vaults[0])?.path
}

export const register: Register = on => {
  on('skill.prompt', async ($, e, next) => {
    if (!PARK_SKILL.test(e.skill)) return next(e)

    const trimmed = (v: string | undefined) => (v ?? '').trim()
    const dirs = trimmed(await $.env.get('CLAUDE_CONFIG_DIR'))
      .split(/[:,]/)
      .map(d => d.trim())
      .filter(Boolean)
    if (dirs.length === 0) dirs.push(`${trimmed(await $.env.get('HOME'))}/.claude`)

    const sources: Array<() => Promise<string | undefined>> = [
      async () => trimmed(await $.env.get('SB_NOTE_VAULT')),
      ...dirs.map(dir => async () => defaultVault(await $.fs.read(`${dir}/second-brain.md`).catch(() => ''))),
    ]
    for (const source of sources) {
      const vault = await source()
      if (vault && (await $.fs.exists(vault))) return next({ ...e, text: `${e.text}\n\nPark vault: ${vault}` })
    }
    return next(e)
  })
}
