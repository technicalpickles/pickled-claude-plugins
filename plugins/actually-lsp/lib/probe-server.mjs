// lib/probe-server.mjs: capability probe for actually-lsp.
//
// Spawns a language server over stdio, opens one sample source file, and asks
// for documentSymbol. The point is to ground a `ready` verdict in a real LSP
// response instead of a shell heuristic (`test -d node_modules` / `test -f
// tsconfig.json`), which mispredicts readiness differently per ecosystem
// (see gt-5ugv). Intra-project navigation works whenever the server can answer
// for the project's own symbols, regardless of whether deps are installed.
//
// Usage (invoked from hooks/session-start.sh):
//   node probe-server.mjs --server <bin> --root <dir> --sample <file> \
//     --langid <id> [--server-arg --stdio] [--wait 1200]
//
// Exit codes (consumed by compute_state):
//   0  ready          documentSymbol returned a non-empty array
//   1  not-ready      server answered but with empty/non-array/error -> a real
//                     not-runnable verdict (do NOT paper over with a heuristic)
//   2  could-not-run  spawn failed, no usable response in budget, bad args ->
//                     caller should fall back to the shell env_check
//
// stdout: one JSON line {ready, symbols, ms, langid} for logging / latency.
// All diagnostic noise goes to stderr so stdout stays parseable.
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const all = (name) => args.reduce((a, v, i) => (args[i - 1] === name ? [...a, v] : a), []);

const SERVER = opt("--server");
const ROOT = opt("--root", process.cwd());
const SAMPLE = opt("--sample");
const LANGID = opt("--langid", "plaintext");
const WAIT = parseInt(opt("--wait", "1200"), 10);
// Most servers (typescript-language-server, ruby-lsp) take `--stdio`.
// rust-analyzer is the LSP server with NO args and rejects `--stdio` (exits 2),
// so rust passes --no-stdio. Explicit --server-arg overrides both.
const serverArgs = all("--server-arg");
const noStdio = args.includes("--no-stdio");
if (serverArgs.length === 0 && !noStdio) serverArgs.push("--stdio");

// could-not-run on bad invocation
if (!SERVER || !SAMPLE) {
  console.error("probe-server: missing --server or --sample");
  process.exit(2);
}

const t0 = Date.now();
const elapsed = () => Date.now() - t0;

let proc;
try {
  proc = spawn(SERVER, serverArgs, { cwd: ROOT });
} catch (e) {
  console.error("probe-server: spawn threw:", e.message);
  process.exit(2);
}
// spawn() reports ENOENT asynchronously via 'error'
proc.on("error", (e) => {
  console.error("probe-server: spawn error:", e.message);
  process.exit(2);
});

let buf = Buffer.alloc(0);
const pending = new Map();
let nextId = 1;

function send(msg) {
  const json = JSON.stringify({ jsonrpc: "2.0", ...msg });
  proc.stdin.write(`Content-Length: ${Buffer.byteLength(json)}\r\n\r\n${json}`);
}
function request(method, params, timeoutMs) {
  const id = nextId++;
  return new Promise((resolve) => {
    const t = setTimeout(() => { pending.delete(id); resolve({ result: null, _timeout: true }); }, timeoutMs);
    pending.set(id, (m) => { clearTimeout(t); resolve(m); });
    send({ id, method, params });
  });
}
function notify(method, params) { send({ method, params }); }

proc.stdout.on("data", (chunk) => {
  buf = Buffer.concat([buf, chunk]);
  while (true) {
    const he = buf.indexOf("\r\n\r\n");
    if (he === -1) break;
    const m = buf.slice(0, he).toString().match(/Content-Length: (\d+)/i);
    if (!m) { buf = buf.slice(he + 4); continue; }
    const len = parseInt(m[1], 10), start = he + 4;
    if (buf.length < start + len) break;
    const body = buf.slice(start, start + len).toString();
    buf = buf.slice(start + len);
    let msg; try { msg = JSON.parse(body); } catch { continue; }
    if (msg.id != null && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); continue; }
    // Server-initiated request: must reply or the server can stall.
    if (msg.id != null && msg.method) {
      const result = msg.method === "workspace/configuration"
        ? (msg.params?.items || [{}]).map(() => ({}))
        : null;
      send({ id: msg.id, result });
    }
  }
});
proc.stderr.on("data", () => {});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function finish(code, symbols) {
  // stdout is the one machine-readable line; stderr already carries noise.
  process.stdout.write(JSON.stringify({ ready: code === 0, symbols, ms: elapsed(), langid: LANGID }) + "\n");
  try { send({ id: nextId++, method: "shutdown", params: {} }); notify("exit", {}); } catch {}
  try { proc.kill(); } catch {}
  process.exit(code);
}

(async () => {
  const rootUri = pathToFileURL(ROOT).href;
  const init = await request("initialize", {
    processId: process.pid, rootUri,
    capabilities: { workspace: { symbol: {}, configuration: true }, textDocument: { documentSymbol: {} } },
    workspaceFolders: [{ uri: rootUri, name: "probe" }],
  }, 3000);
  if (init._timeout) { console.error("probe-server: initialize timed out"); finish(2, 0); return; }
  notify("initialized", {});
  await sleep(300);

  let text = "";
  try { text = readFileSync(SAMPLE, "utf8"); }
  catch (e) { console.error("probe-server: cannot read sample:", e.message); finish(2, 0); return; }
  const fileUri = pathToFileURL(SAMPLE).href;
  notify("textDocument/didOpen", { textDocument: { uri: fileUri, languageId: LANGID, version: 1, text } });
  await sleep(WAIT);

  const ds = await request("textDocument/documentSymbol", { textDocument: { uri: fileUri } }, 2500);
  if (ds._timeout) { console.error("probe-server: documentSymbol timed out"); finish(2, 0); return; }
  if (ds.error) { console.error("probe-server: documentSymbol error:", JSON.stringify(ds.error)); finish(1, 0); return; }
  const n = Array.isArray(ds.result) ? ds.result.length : 0;
  finish(n > 0 ? 0 : 1, n);
})();

// Hard self-guard: if anything wedges past the caller's outer timeout budget,
// exit could-not-run rather than hang.
setTimeout(() => { console.error("probe-server: internal watchdog"); try { proc?.kill(); } catch {} process.exit(2); }, 8000);
