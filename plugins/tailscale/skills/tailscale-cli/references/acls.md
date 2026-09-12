# ACLs: tagOwners, grants, and the silent-drop pattern

Tailscale's tailnet-wide access policy (the ACL/policy file) is not visible to any local `tailscale` command — there is no `tailscale acl` subcommand. The only ways to see it are the admin console UI, or the API (see "Reading the live policy" below). `tailscale status`/`serve status` show *this node's* connectivity, not the policy that produced it.

## Recognize this pattern first: the silent tag drop

**Symptom:** a new node or sidecar container comes up, `tailscale status` shows it connected and healthy, but the application on top of it crash-loops on a backoff with a vague/generic error — not a clear `403` or "permission denied." The same setup steps worked for an existing, similar-looking node. The fix turns out to be an ACL change in the admin console, not a code or config bug.

**Why this happens:** `tailscale up --advertise-tags=tag:foo` (or an authkey pre-loaded with tags) doesn't hard-fail when the requesting identity isn't authorized to apply `tag:foo`. The coordination server just **strips the unauthorized tag** and lets the node join anyway, untagged. `tailscale status` reports a perfectly healthy connection because, from Tailscale's point of view, nothing went wrong — the node joined the tailnet fine. But anything downstream that gated a capability, grant, or app-level check on that tag now sees a node without it, and that failure surfaces one layer up: in the *application*, not in Tailscale.

This is why it looks like a networking bug (crash-loop, retries, backoff) when the actual cause is an authorization gap in `tagOwners` for that specific identity/authkey.

**Fix:** in the admin console (or via a policy edit), add the requesting identity to `tagOwners` for that tag — see syntax below. Then re-issue the node's auth (re-run `tailscale up` with the tag, or mint a fresh authkey with the tag baked in); a node that joined untagged doesn't retroactively pick up the tag on its own.

## Where tags and access are declared

Two different sections in the policy file, easy to conflate:

```json
{
  "tagOwners": {
    "tag:sidecar": ["autogroup:admin"]
  },
  "grants": [
    {"src": ["tag:bridge"], "dst": ["tag:sidecar:443"], "ip": ["tcp:443"]}
  ]
}
```

- **`tagOwners`** — who/what is allowed to *apply* a given tag to a device. This is the authorization the silent-drop pattern above trips over. If a key or user isn't listed here for `tag:foo`, they can request the tag but won't get it.
- **`grants`** (or the older `acls` array — see next section) — once a device *has* a tag, what it's allowed to talk to. This is ordinary network-reachability policy, and failures here look different: an actual connection refusal/timeout at the network layer, not a silent no-op.

Don't debug a connectivity symptom by only checking `grants`. If the destination side never got the tag it was supposed to have, the grant that references that tag is irrelevant — the real gap is one layer up, in `tagOwners`.

## `acls` (legacy) and `grants` (current) can coexist

Older policy files use an `acls` array (`{"action": "accept", "src": [...], "dst": [...]}`); newer ones use `grants`. **Both can be present in the same policy file at once** — Tailscale hasn't forced a migration. If you're reading a policy to understand what's allowed, check both arrays, not just whichever one you expected to find. A restriction enforced by a legacy `acls` rule is easy to miss if you only look at `grants`, and vice versa.

Also watch for a default-allow wildcard grant sitting alongside more specific rules:

```json
{"src": ["*"], "dst": ["*"], "ip": ["*"]}
```

This is Tailscale's out-of-the-box default and is easy to leave in place indefinitely — it makes every other grant in the file effectively decorative for network reachability (everything can already reach everything). If a tailnet has this wildcard, don't reason about access from the specific grants alone; check whether the wildcard is still active first, since it silently supersedes them.

## Reading the live policy

There's no local CLI equivalent; querying the policy programmatically means the Tailscale API. Once an OAuth client with the **Policy File → Read** scope exists (client ID/secret from Settings → OAuth clients in the admin console):

```bash
# Exchange client credentials for a short-lived (1hr) access token
TOKEN=$(curl -s -d "client_id=$TAILSCALE_OAUTH_CLIENT_ID" \
  -d "client_secret=$TAILSCALE_OAUTH_CLIENT_SECRET" \
  "https://api.tailscale.com/api/v2/oauth/token" | jq -r .access_token)

# Fetch the policy file (HuJSON)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.tailscale.com/api/v2/tailnet/-/acl"
```

`tailnet/-/acl` uses `-` for "the tailnet this credential belongs to" — no need to look up the tailnet name separately.

## Sidecar-container pattern

The silent-drop failure above is especially common for sidecar containers (a helper container joining the same tailnet as a main service) because sidecars are often brought up with a shared or templated authkey that wasn't updated when a new tag was introduced. Checklist when a new sidecar crash-loops after joining its tailnet fine:

1. `tailscale status --json` on the sidecar — does `.Self.Tags` actually include the tag you expect? If it's empty or missing the expected tag, that's the silent drop, not a bug in the sidecar itself.
2. If the tag is missing: check `tagOwners` in the policy for that tag — is the authkey/identity the sidecar used actually listed as an owner?
3. Fix `tagOwners`, then re-auth the sidecar (new authkey or re-run `tailscale up --advertise-tags=...`) — an already-joined, untagged node won't retroactively gain the tag.
4. Only after confirming the tag is actually present: if it's still failing, that's now a `grants`/`acls` reachability problem, not a tagging problem — check both arrays per the section above.
