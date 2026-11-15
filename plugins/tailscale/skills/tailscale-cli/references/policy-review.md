# Reviewing and validating a tailnet policy

Tools and gotchas for auditing a policy file, or checking an edit before it goes live. Reading the policy itself is covered in [acls.md](acls.md).

## The validate endpoint

`POST /api/v2/tailnet/-/acl/validate` takes a candidate policy as the body, checks syntax, and runs its `tests` block without applying anything. A read-only OAuth client (`policy_file:read`) can call it.

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/hujson" \
  --data-binary @candidate.hujson \
  "https://api.tailscale.com/api/v2/tailnet/-/acl/validate"
```

**It returns HTTP 200 whether the policy passes or fails.** The body is the verdict: `{}` is a pass, a body with `message` and `data` is a failure. A script that checks only the status code will report success on every broken policy.

- **Run a negative control.** Flip one test to an assertion that must fail and confirm the failure shows up before you trust a clean pass.
- **A test `src` must be a login or a tag.** An autogroup is rejected with `unknown user or host`, and that one bad entry makes every test in the file report the error.
- **Measure exposure before changing anything.** Validate the live policy with deny tests added. Each `want: Drop, got: Accept` is a path the current policy leaves open, and you changed nothing to learn it.

## Services are their own grant target

A grant to a host's tag does not open the Services that host serves, and a deny test on the host's tag says nothing about them. `*` does cover Services. Use `svc:<name>` as a grant `dst`, and `svc:<name>:<port>` as a test destination.

`autoApprovers.services` matches on the tag the *Service* carries, not on the tag of the node hosting it. The Services page documents this; the policy syntax reference has no `services` subsection.

An orphaned-looking Service (defined in `vip-services` but advertised by no host's routes) may be dead config, or a Service whose host is down. Find out who is meant to host it before deleting anything.

## Containers borrow the host's identity

Docker NATs container traffic through the host, so it arrives from the host's tailnet address and gets the host's grants. That includes containers that share the network namespace of a userspace-mode Tailscale sidecar: the sidecar's identity covers inbound traffic only. To check, send one request to a listener on another node and read the source address it sees.

Treat trust as inbound. A trusted tag should say what a node may host and who may rely on it, and its outbound grants should stay minimal, because everything on that host shares them.

## Tailscale SSH needs two rules

The `ssh` rule, plus network access to port 22. Under default-deny, a correct `ssh` rule alone still fails.

**Tagging a user-owned node is a lockout risk.** It works from the console with no re-auth, and it removes the user identity, so any `ssh` rule or grant keyed on that user stops matching. Key expiry is left as it was. Removing all tags later needs a re-auth on the node, which makes it one-way for a remote box.

## Funnel under default-deny

The docs name only the `funnel` nodeAttr. Whether ingress also needs a grant is undocumented, so verify after a policy change.

## What else a read-only client can see

With an all-read client: `devices?fields=all`, `keys?all=true`, `vip-services`, `settings`, `dns/*`, and `webhooks`. The log-stream config returns 403.

In `keys`, an auth key whose `capabilities.devices.create` has no `tags` joins nodes as the creating user. Reusable, untagged, and device approval off together make a join ticket for anyone holding the key.

## Managing the policy from git

`gitops-pusher test` and `gitops-pusher apply` run from any CI. `policy_file:read` is enough to validate; applying needs `policy_file`. Console revert is unavailable under GitOps.

## Review checklist

Run these as a repeatable audit:

1. A default-allow wildcard grant (`*` to `*`) still active, which makes every specific grant decorative.
2. Legacy `acls` rules alongside `grants`; read both.
3. A `tests` block exists, and a negative control proves it can fail.
4. Tags: each is owned by something specific, and its outbound grants are minimal.
5. Auth keys: reusable, untagged keys, and device approval settings.
6. Services: a grant target for each, `autoApprovers.services` semantics understood, no orphans.
7. Stale devices: expired keys, long-offline nodes.
8. Client version spread across nodes.
