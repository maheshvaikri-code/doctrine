# Doctrine Control Room

Local operational dashboard for a Doctrine-enabled repository.

## What it reads

- Repository identity from `pyproject.toml` and Git
- Doctrine activation posture and state-chain status
- Review, QA, ADR, plan, and Gold-record counts
- Recent Git activity and package/tag distance
- Current or most recent Doctrine verification, gate by gate

The only executable action is the fixed Doctrine verifier. MAPLE Runtime,
Policy Shield, and Trust Engine are shown as **not connected** until real
connectors exist.

## Run locally

Requires Python 3.11+ and Node.js 22.13+. From the repository root, start the
loopback bridge:

```bash
python tools/doctrine_dashboard.py
```

In a second terminal:

```bash
cd dashboard
npm ci
npm run dev
```

Open `http://localhost:3003/`. The client defaults to
`http://127.0.0.1:8765`; set `NEXT_PUBLIC_DOCTRINE_API_URL` before starting the
dashboard only when the bridge uses another local port.

To exercise the production build locally:

```bash
cd dashboard
npm run build
npm start -- --port 3003
```

The repository-owned production launcher includes a Windows compatibility fix
for vinext's static-asset cache. If port 3003 is occupied, choose another port
and add that exact loopback origin when starting the bridge:

```bash
python tools/doctrine_dashboard.py --origin http://localhost:3011 --origin http://127.0.0.1:3011
cd dashboard
npm start -- --port 3011
```

Verification:

```bash
python -m unittest discover -s tests -p "test_doctrine_dashboard.py"
python -m ruff check tools/doctrine_dashboard.py tests/test_doctrine_dashboard.py
cd dashboard
npm run lint
npm run typecheck
npm test
npm run audit
```

The source repository runs those dashboard gates from the lockfile on
Ubuntu and Windows with Node.js 22.13.0. Doctrine's installer does not copy
that source-only dashboard workflow into consumer repositories.

## Security boundary

The bridge binds only to `127.0.0.1`. It allows the two local dashboard origins
by default, rejects non-JSON and bodies over 1 KiB, permits one verification at
a time, rejects dirty-worktree verification, and never accepts a command or
path over HTTP. Verification is invoked with a fixed argument array, no shell,
a 180-second timeout, and a 32-KiB output tail.

This release is deliberately local-only. A hosted or multi-user Control Room
needs a separate authenticated bridge design; publishing this frontend does
not make local repository access work remotely.

## Design sources

- [Motion](https://motion.dev/) supplies the React animation runtime.
- [Kokonut UI](https://kokonutui.com/) informed component tactility and spacing.
- [Bklit UI](https://bklit.com/) informed analytical density and chart treatment.
- [Anime.js](https://animejs.com/) informed motion research, but is not installed;
  a second animation runtime would duplicate Motion without earning its weight.

The implementation owns its dashboard components and does not copy premium
registry source.
