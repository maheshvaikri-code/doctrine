# doctrine-state-plane

Makes any stateless coding model stateful inside a `.Doctrine` repo. The model never
remembers; the repo does. Three invariants:

1. **Externalized.** All state is plain canonical files under `.doctrine-state/`,
   committed to git. No vendor memory feature is load-bearing.
2. **Deterministic rehydration.** Same HEAD + same state plane → byte-identical
   hydration bundle. Rehydration is a compile step with a hash gate, not a vibe.
3. **Transactional sessions.** A session runs between checkpoints. Writes go through
   "model proposes, validator disposes" against schemas — memory cannot free-write
   itself into rot.

## Layout

```
doctrine-state-plane/
├── README.md                        ← you are here
├── STATE.md                         ← the spec: state kinds, layout, checkpoint protocol, defenses
├── schemas/
│   ├── checkpoint.schema.json       ← control plane + merkle-style index over the state plane
│   └── distillate.schema.json       ← what a session learned; hard caps mechanize "distill, never replay"
├── hydration/
│   └── HYDRATION.md                 ← assembly order, token budgets, determinism gate, adapter emit
└── examples/
    ├── checkpoint.example.json
    └── distillate.example.json
```

## How it composes with the other packs

Checkpoints hash-link as an append-only chain. Effects follow
an append-only side-effect log discipline. Intents are structured-intent outputs. The
bundle emits as canonical JSON. FDE phase gates are natural checkpoint triggers. An
optional cross-repo tier sits above this repo-local plane — imported claims arrive
tagged with their source repo, never merged silently.

## Adoption order

Start with checkpoint + distillate only (one file each, immediate value: sessions stop
re-exploring dead ends). Add the hydration compiler second. Wire adapter hooks last —
the state plane is useful even when hydration is a manual `@include`.
