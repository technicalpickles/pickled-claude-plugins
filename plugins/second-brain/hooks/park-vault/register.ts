import type { Register } from 'claude-code'

const PARK_SKILL = /^(agent-meta:)?(un)?park$/

// ~/.claude/second-brain.md lists "- name: /path" under "## Vaults" and names
// the default with "Default: name". No default line means the first vault.
export function defaultVault(config: string): string | undefined {
  const vaults = [...config.matchAll(/^- ([^:\s]+):\s*(\S.*?)\s*$/gm)].map(m => ({ name: m[1], path: m[2] }))
  const wanted = config.match(/^Default:\s*(\S+)/m)?.[1]
  return (vaults.find(v => v.name === wanted) ?? vaults[0])?.path
}

export const register: Register = (on, options) => {
  on('skill.prompt', async ($, e, next) => {
    if (options.park_in_vault === false || !PARK_SKILL.test(e.skill)) return next(e)
    if (((await $.env.get('AGENT_PARK_VAULT')) ?? '').trim() !== '') return next(e)

    const home = (await $.env.get('HOME')) ?? ''
    const config = await $.fs.read(`${home}/.claude/second-brain.md`).catch(() => '')
    const vault = defaultVault(config)
    if (!vault || !(await $.fs.exists(vault))) return next(e)

    return next({ ...e, text: `${e.text}\n\nPark vault: ${vault}` })
  })
}
