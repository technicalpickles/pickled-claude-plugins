import type { Register } from 'claude-code'
import { register as devlogSidechain } from './devlog-sidechain/register'
import { register as parkVault } from './park-vault/register'

export const register: Register = (on, options) => {
  devlogSidechain(on, options)
  parkVault(on, options)
}
