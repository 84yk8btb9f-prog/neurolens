# Security Policy

## Reporting a Vulnerability

Please **do not open a public GitHub issue** for security vulnerabilities.

Instead, email **niksapa150@gmail.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal repro is ideal)
- Affected component (backend, frontend, or deployment config)

You should receive an acknowledgment within a few days. This is a small
open-source project maintained on a best-effort basis, so response and fix
timelines aren't guaranteed, but reports will be taken seriously and credited
in the fix (unless you'd prefer otherwise).

## Supported Versions

NeuroPulse does not currently maintain multiple release branches. Only the
latest commit on `main` is supported — please update before reporting an
issue that may already be fixed.

| Version | Supported |
| ------- | --------- |
| `main` (latest) | yes |
| older commits | no |

## Scope Notes

NeuroPulse is self-hosted by design and has no built-in multi-user auth or
billing. If you self-host a public instance, you are responsible for network
exposure, rate limiting, and access control at your deployment layer (reverse
proxy, HF Space visibility settings, Vercel project settings, etc.).
