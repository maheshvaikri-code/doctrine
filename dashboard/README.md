# Doctrine Control Room

Local dashboard prototype for Doctrine’s enterprise evidence and execution
control plane.

## What it demonstrates

- Portfolio-wide gate posture and evidence coverage
- Evidence velocity and chain-integrity signals
- Doctrine → MAPLE Runtime → Policy Shield → Trust Engine execution flow
- Policy activity, release candidates, and keyboard command palette
- Live, loading, partial, unavailable, and empty interface states
- Responsive navigation and reduced-motion behavior

All displayed organizations, events, metrics, and repository names are
**prototype data**. The interface does not call production systems.

## Run locally

Requires Node.js 22.13 or newer.

```bash
npm install
npm run dev
```

Then open the local address printed by the development server.

Verification:

```bash
npm run lint
npm test
npm audit --omit=dev --audit-level=high
```

## Design sources

- [Motion](https://motion.dev/) supplies the React animation runtime.
- [Kokonut UI](https://kokonutui.com/) informed component tactility and spacing.
- [Bklit UI](https://bklit.com/) informed analytical density and chart treatment.
- [Anime.js](https://animejs.com/) informed motion research, but is not installed;
  a second animation runtime would duplicate Motion without earning its weight.

The implementation owns its dashboard components and does not copy premium
registry source.
