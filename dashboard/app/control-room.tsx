"use client";

import {
  ArrowUpRight,
  Boxes,
  Check,
  ChevronDown,
  CircleAlert,
  Command,
  FileCheck2,
  Fingerprint,
  Gauge,
  GitBranch,
  Layers3,
  LockKeyhole,
  Menu,
  Network,
  PanelLeftClose,
  Play,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  SquareTerminal,
  Waypoints,
  X,
  Zap,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  type ComponentType,
  type KeyboardEvent as ReactKeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

type Range = "7D" | "30D" | "90D";
type SurfaceState = "live" | "loading" | "partial" | "error" | "empty";
type Icon = ComponentType<{ size?: number; strokeWidth?: number }>;

type Gate = {
  name: string;
  owner: string;
  evidence: string;
  passing: number;
  total: number;
  state: "healthy" | "watch" | "blocked";
};

const ranges: Range[] = ["7D", "30D", "90D"];
const evidenceSeries: Record<Range, number[]> = {
  "7D": [34, 46, 42, 61, 54, 72, 84, 78, 91, 88, 96, 94],
  "30D": [48, 42, 59, 66, 62, 74, 69, 81, 86, 83, 92, 97],
  "90D": [24, 32, 39, 44, 53, 58, 64, 71, 78, 84, 90, 96],
};

const gates: Gate[] = [
  {
    name: "G3 · Build",
    owner: "Engineering",
    evidence: "1,842 checks",
    passing: 46,
    total: 48,
    state: "healthy",
  },
  {
    name: "G4 · Review",
    owner: "Code review",
    evidence: "126 findings",
    passing: 43,
    total: 48,
    state: "watch",
  },
  {
    name: "G5 · Verify",
    owner: "QA + Security",
    evidence: "892 artifacts",
    passing: 45,
    total: 48,
    state: "healthy",
  },
  {
    name: "G6 · Release",
    owner: "Release council",
    evidence: "12 gold builds",
    passing: 41,
    total: 48,
    state: "blocked",
  },
];

const navItems: Array<{ label: string; href: string; icon: Icon }> = [
  { label: "Overview", href: "#overview", icon: Gauge },
  { label: "Evidence", href: "#evidence", icon: Fingerprint },
  { label: "Agents", href: "#agents", icon: Waypoints },
  { label: "Policies", href: "#policies", icon: ShieldCheck },
  { label: "Releases", href: "#releases", icon: GitBranch },
];

const commands = [
  {
    label: "Verify portfolio",
    hint: "Run Doctrine gates across eligible repositories",
    icon: Play,
  },
  {
    label: "Inspect exceptions",
    hint: "Open seven active policy exceptions",
    icon: CircleAlert,
  },
  {
    label: "Export evidence",
    hint: "Prepare an enterprise evidence bundle",
    icon: FileCheck2,
  },
  {
    label: "Open agent runtime",
    hint: "Trace runtime and policy execution",
    icon: Network,
  },
];

const activity = [
  {
    time: "12:42:08",
    title: "G5 verification passed",
    detail: "policy-shield · 214 checks · signed by QA runtime",
    tone: "success",
  },
  {
    time: "12:39:51",
    title: "Policy exception expires in 48h",
    detail: "payments-edge · DEP-014 · owner: Platform Security",
    tone: "warning",
  },
  {
    time: "12:33:26",
    title: "Agent plan reconciled",
    detail: "maple-runtime · 8 workers · 0 scope deviations",
    tone: "neutral",
  },
  {
    time: "12:18:04",
    title: "Gold candidate promoted",
    detail: "doctrineos v0.6.46 · evidence chain intact",
    tone: "success",
  },
];

function StatusDot({ state }: { state: Gate["state"] }) {
  return (
    <span className={`status-dot status-dot-${state}`} aria-hidden="true">
      <span />
    </span>
  );
}

function MetricCard({
  label,
  value,
  delta,
  icon: IconComponent,
  delay,
}: {
  label: string;
  value: string;
  delta: string;
  icon: Icon;
  delay: number;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.article
      className="metric-card"
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, delay }}
      whileHover={reduceMotion ? undefined : { y: -3 }}
    >
      <div className="metric-card-top">
        <span>{label}</span>
        <IconComponent size={17} strokeWidth={1.8} />
      </div>
      <strong>{value}</strong>
      <p>
        <span>{delta}</span> from previous window
      </p>
    </motion.article>
  );
}

function LoadingState() {
  return (
    <section className="state-stage" aria-live="polite" aria-busy="true">
      <div className="state-spinner" aria-hidden="true" />
      <p className="eyebrow">Synchronizing evidence</p>
      <h2>Building the current control picture.</h2>
      <p>Doctrine is reconciling gate results, agent events, and policy state.</p>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="state-stage">
      <div className="state-icon">
        <Boxes size={24} />
      </div>
      <p className="eyebrow">No repositories connected</p>
      <h2>Your control room is ready for its first system.</h2>
      <p>Connect a Doctrine-enabled repository to begin collecting evidence.</p>
      <button className="button button-primary" type="button">
        Connect repository <ArrowUpRight size={15} />
      </button>
    </section>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <section className="state-stage state-stage-error" role="alert">
      <div className="state-icon">
        <CircleAlert size={24} />
      </div>
      <p className="eyebrow">Evidence sync interrupted</p>
      <h2>The portfolio picture could not be refreshed.</h2>
      <p>The last verified snapshot remains available. Check the runtime and retry.</p>
      <button className="button button-primary" type="button" onClick={onRetry}>
        Retry sync
      </button>
    </section>
  );
}

export function ControlRoom() {
  const [range, setRange] = useState<Range>("30D");
  const [surfaceState, setSurfaceState] = useState<SurfaceState>("live");
  const [commandOpen, setCommandOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("Overview");
  const [notice, setNotice] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();
  const commandButtonRef = useRef<HTMLButtonElement>(null);
  const firstCommandRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isTyping =
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.isContentEditable;

      if (event.key === "/" && !isTyping) {
        event.preventDefault();
        setCommandOpen(true);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setMobileNavOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (commandOpen) firstCommandRef.current?.focus();
  }, [commandOpen]);

  const closeCommands = () => {
    setCommandOpen(false);
    commandButtonRef.current?.focus();
  };

  const chooseCommand = (label: string) => {
    setCommandOpen(false);
    setNotice(`${label} queued in prototype mode.`);
    commandButtonRef.current?.focus();
  };

  const chooseNav = (label: string) => {
    setActiveSection(label);
    setMobileNavOpen(false);
  };

  const handleCommandKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Tab") return;
    const buttons = Array.from(
      event.currentTarget.querySelectorAll<HTMLButtonElement>("button"),
    );
    if (buttons.length === 0) return;
    const first = buttons[0];
    const last = buttons[buttons.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="control-room">
      <a className="skip-link" href="#main-content">
        Skip to dashboard
      </a>

      <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <span className="brand-mark">D</span>
          <span className="brand-copy">
            <strong>DOCTRINE</strong>
            <small>Control room</small>
          </span>
          <button
            className="icon-button mobile-close"
            type="button"
            aria-label="Close navigation"
            onClick={() => setMobileNavOpen(false)}
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        <nav className="primary-nav" aria-label="Primary navigation">
          <span className="nav-label">Operate</span>
          {navItems.map((item) => (
            <a
              className={activeSection === item.label ? "active" : ""}
              href={item.href}
              key={item.label}
              onClick={() => chooseNav(item.label)}
            >
              <item.icon size={17} strokeWidth={1.8} />
              <span>{item.label}</span>
              {item.label === "Policies" && <em>7</em>}
            </a>
          ))}
        </nav>

        <div className="sidebar-workspace">
          <span className="nav-label">Workspace</span>
          <button type="button">
            <span className="workspace-avatar">ET</span>
            <span>
              <strong>Enterprise trust</strong>
              <small>48 repositories</small>
            </span>
            <ChevronDown size={14} />
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="runtime-status">
            <span className="live-beacon" />
            <span>
              <strong>Runtime healthy</strong>
              <small>All regions · 42ms</small>
            </span>
          </div>
          <button className="icon-button" type="button" aria-label="Open settings">
            <Settings2 size={17} />
          </button>
        </div>
      </aside>

      <div className="workspace-shell">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            type="button"
            aria-label="Open navigation"
            aria-expanded={mobileNavOpen}
            onClick={() => setMobileNavOpen(true)}
          >
            <Menu size={19} />
          </button>
          <div className="breadcrumb">
            <span>Enterprise trust</span>
            <span>/</span>
            <strong>{activeSection}</strong>
          </div>
          <div className="topbar-actions">
            <span className="prototype-badge">
              <Sparkles size={13} /> Prototype data
            </span>
            <button
              className="command-trigger"
              type="button"
              ref={commandButtonRef}
              onClick={() => setCommandOpen(true)}
            >
              <Search size={15} />
              <span>Search or run</span>
              <kbd>/</kbd>
            </button>
            <button className="user-avatar" type="button" aria-label="Open user menu">
              MS
            </button>
          </div>
        </header>

        <main id="main-content" tabIndex={-1}>
          <div className="dashboard-toolbar">
            <div className="surface-state-picker">
              <label htmlFor="surface-state">View state</label>
              <select
                id="surface-state"
                value={surfaceState}
                onChange={(event) =>
                  setSurfaceState(event.target.value as SurfaceState)
                }
              >
                <option value="live">Live</option>
                <option value="loading">Loading</option>
                <option value="partial">Partial</option>
                <option value="error">Unavailable</option>
                <option value="empty">Empty</option>
              </select>
            </div>
            <div className="range-switcher" aria-label="Evidence time range">
              {ranges.map((item) => (
                <button
                  type="button"
                  key={item}
                  className={range === item ? "active" : ""}
                  aria-pressed={range === item}
                  onClick={() => setRange(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {surfaceState === "loading" && <LoadingState />}
          {surfaceState === "empty" && <EmptyState />}
          {surfaceState === "error" && (
            <ErrorState onRetry={() => setSurfaceState("loading")} />
          )}

          {(surfaceState === "live" || surfaceState === "partial") && (
            <motion.div
              className="dashboard-content"
              initial={reduceMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: reduceMotion ? 0 : 0.35 }}
            >
              {surfaceState === "partial" && (
                <div className="partial-banner" role="status">
                  <CircleAlert size={17} />
                  <span>
                    <strong>Partial portfolio view.</strong> Three EU repositories
                    have not reported in the last 20 minutes.
                  </span>
                  <button type="button" onClick={() => setSurfaceState("live")}>
                    Dismiss
                  </button>
                </div>
              )}

              <section className="hero" id="overview" aria-labelledby="page-title">
                <div>
                  <p className="eyebrow">
                    <span className="live-beacon" /> Enterprise integrity · Live
                  </p>
                  <h1 id="page-title">
                    Confidence has
                    <br />a control plane.
                  </h1>
                  <p className="hero-copy">
                    Every gate, decision, exception, and agent action—connected to
                    evidence your enterprise can defend.
                  </p>
                </div>
                <div className="hero-actions">
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() =>
                      setNotice("Portfolio verification queued in prototype mode.")
                    }
                  >
                    <Play size={15} fill="currentColor" />
                    Verify portfolio
                  </button>
                  <a className="button button-secondary" href="#evidence">
                    Open evidence <ArrowUpRight size={15} />
                  </a>
                </div>
              </section>

              <section className="metric-grid" aria-label="Portfolio metrics">
                <MetricCard
                  label="Governed systems"
                  value="48"
                  delta="+4"
                  icon={Layers3}
                  delay={0.04}
                />
                <MetricCard
                  label="Verified evidence"
                  value="96.8%"
                  delta="+2.4%"
                  icon={Fingerprint}
                  delay={0.08}
                />
                <MetricCard
                  label="Open exceptions"
                  value="07"
                  delta="-3"
                  icon={CircleAlert}
                  delay={0.12}
                />
                <MetricCard
                  label="Gold candidates"
                  value="03"
                  delta="+1"
                  icon={Sparkles}
                  delay={0.16}
                />
              </section>

              <section className="dashboard-grid" id="evidence">
                <motion.article
                  className="panel gate-panel"
                  initial={reduceMotion ? false : { opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: reduceMotion ? 0 : 0.48, delay: 0.12 }}
                >
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Gate posture</p>
                      <h2>Portfolio verification</h2>
                    </div>
                    <button className="quiet-button" type="button">
                      All repositories <ChevronDown size={14} />
                    </button>
                  </header>

                  <div className="gate-summary">
                    <div>
                      <strong>91.2</strong>
                      <span>Integrity score</span>
                    </div>
                    <p>
                      <span>↑ 4.6</span> since the last release window. Three systems
                      require owner action.
                    </p>
                  </div>

                  <div className="gate-table" role="table" aria-label="Gate status">
                    <div className="gate-table-head" role="row">
                      <span role="columnheader">Gate</span>
                      <span role="columnheader">Evidence</span>
                      <span role="columnheader">Coverage</span>
                    </div>
                    {gates.map((gate) => {
                      const percentage = Math.round(
                        (gate.passing / gate.total) * 100,
                      );
                      return (
                        <div className="gate-row" role="row" key={gate.name}>
                          <div role="cell">
                            <StatusDot state={gate.state} />
                            <span>
                              <strong>{gate.name}</strong>
                              <small>{gate.owner}</small>
                            </span>
                          </div>
                          <span role="cell">{gate.evidence}</span>
                          <div role="cell" className="coverage-cell">
                            <span>
                              {gate.passing}/{gate.total}
                            </span>
                            <progress
                              value={gate.passing}
                              max={gate.total}
                              aria-label={`${gate.name}: ${percentage}% covered`}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </motion.article>

                <motion.article
                  className="panel evidence-panel"
                  initial={reduceMotion ? false : { opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: reduceMotion ? 0 : 0.48, delay: 0.18 }}
                >
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Evidence velocity</p>
                      <h2>Proof, not promises</h2>
                    </div>
                    <span className="panel-number">18.4k</span>
                  </header>
                  <p className="panel-subcopy">
                    Signed checks collected across the portfolio.
                  </p>
                  <div className="evidence-chart" aria-label={`${range} evidence trend`}>
                    <div className="chart-grid" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                      <span />
                    </div>
                    <div className="chart-bars" aria-hidden="true">
                      {evidenceSeries[range].map((height, index) => (
                        <motion.span
                          key={`${range}-${index}`}
                          initial={reduceMotion ? false : { height: 0 }}
                          animate={{ height: `${height}%` }}
                          transition={{
                            duration: reduceMotion ? 0 : 0.38,
                            delay: reduceMotion ? 0 : index * 0.018,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="chart-footer">
                    <span>Jul 01</span>
                    <span>Jul 25</span>
                  </div>
                  <div className="evidence-callout">
                    <ShieldCheck size={19} />
                    <span>
                      <strong>99.4% chain integrity</strong>
                      <small>All evidence roots reconciled 2m ago</small>
                    </span>
                  </div>
                </motion.article>
              </section>

              <section className="runtime-grid" id="agents">
                <article className="panel runtime-panel">
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Execution fabric</p>
                      <h2>From intent to enforced action</h2>
                    </div>
                    <span className="live-status">
                      <span className="live-beacon" /> Live
                    </span>
                  </header>
                  <div className="runtime-flow" aria-label="Execution system flow">
                    <div className="runtime-node featured">
                      <span className="node-icon">
                        <Command size={18} />
                      </span>
                      <span>
                        <small>Govern</small>
                        <strong>Doctrine</strong>
                      </span>
                    </div>
                    <span className="flow-connector" aria-hidden="true">
                      <i />
                    </span>
                    <div className="runtime-node">
                      <span className="node-icon">
                        <Waypoints size={18} />
                      </span>
                      <span>
                        <small>Coordinate</small>
                        <strong>Maple Runtime</strong>
                      </span>
                    </div>
                    <span className="flow-connector" aria-hidden="true">
                      <i />
                    </span>
                    <div className="runtime-node">
                      <span className="node-icon">
                        <LockKeyhole size={18} />
                      </span>
                      <span>
                        <small>Enforce</small>
                        <strong>Policy Shield</strong>
                      </span>
                    </div>
                    <span className="flow-connector" aria-hidden="true">
                      <i />
                    </span>
                    <div className="runtime-node">
                      <span className="node-icon">
                        <Zap size={18} />
                      </span>
                      <span>
                        <small>Evaluate</small>
                        <strong>Trust Engine</strong>
                      </span>
                    </div>
                  </div>
                  <div className="runtime-stats">
                    <div>
                      <span>Active agents</span>
                      <strong>24</strong>
                    </div>
                    <div>
                      <span>Policy decisions</span>
                      <strong>1,284</strong>
                    </div>
                    <div>
                      <span>Median decision</span>
                      <strong>42ms</strong>
                    </div>
                    <div>
                      <span>Denied actions</span>
                      <strong>18</strong>
                    </div>
                  </div>
                </article>

                <article className="panel activity-panel" id="policies">
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Operational stream</p>
                      <h2>What changed</h2>
                    </div>
                    <button
                      className="icon-button"
                      type="button"
                      aria-label="Filter activity"
                    >
                      <Settings2 size={16} />
                    </button>
                  </header>
                  <ol className="activity-list">
                    {activity.map((item) => (
                      <li key={`${item.time}-${item.title}`}>
                        <time>{item.time}</time>
                        <span className={`activity-marker ${item.tone}`} />
                        <div>
                          <strong>{item.title}</strong>
                          <p>{item.detail}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                  <button className="text-button" type="button">
                    View complete ledger <ArrowUpRight size={14} />
                  </button>
                </article>
              </section>

              <section className="release-panel panel" id="releases">
                <div>
                  <p className="eyebrow">Release lane</p>
                  <h2>Three systems are approaching gold.</h2>
                  <p>
                    Promotion requires an intact evidence chain, zero critical
                    findings, and signed release authority.
                  </p>
                </div>
                <div className="release-candidates">
                  {[
                    ["doctrineos", "v0.6.46", "Ready", "100%"],
                    ["policy-shield", "v0.9.2-rc1", "Review", "94%"],
                    ["maple-runtime", "v1.4.0", "Verify", "88%"],
                  ].map(([name, version, stage, score]) => (
                    <button
                      type="button"
                      key={name}
                      onClick={() =>
                        setNotice(`${name} evidence opened in prototype mode.`)
                      }
                    >
                      <span className="release-icon">
                        <SquareTerminal size={17} />
                      </span>
                      <span>
                        <strong>{name}</strong>
                        <small>{version}</small>
                      </span>
                      <span className="release-stage">
                        <small>{stage}</small>
                        <strong>{score}</strong>
                      </span>
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              </section>

              <footer className="dashboard-footer">
                <span>Doctrine Control Room · prototype surface</span>
                <span>Snapshot 25 Jul 2026 · 12:42 UTC</span>
              </footer>
            </motion.div>
          )}
        </main>
      </div>

      <AnimatePresence>
        {mobileNavOpen && (
          <motion.button
            className="mobile-scrim"
            type="button"
            aria-label="Close navigation"
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileNavOpen(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {commandOpen && (
          <motion.div
            className="command-backdrop"
            role="presentation"
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) closeCommands();
            }}
          >
            <motion.div
              className="command-palette"
              role="dialog"
              aria-modal="true"
              aria-labelledby="command-title"
              onKeyDown={handleCommandKeyDown}
              initial={reduceMotion ? false : { opacity: 0, y: -14, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.99 }}
              transition={{ duration: reduceMotion ? 0 : 0.18 }}
            >
              <div className="command-search">
                <Search size={18} />
                <span id="command-title">Run a Doctrine action</span>
                <button
                  className="icon-button"
                  type="button"
                  aria-label="Close command palette"
                  onClick={closeCommands}
                >
                  <X size={17} />
                </button>
              </div>
              <p className="command-group-label">Suggested actions</p>
              <div className="command-list">
                {commands.map((item, index) => (
                  <button
                    type="button"
                    key={item.label}
                    ref={index === 0 ? firstCommandRef : undefined}
                    onClick={() => chooseCommand(item.label)}
                  >
                    <span>
                      <item.icon size={17} />
                    </span>
                    <span>
                      <strong>{item.label}</strong>
                      <small>{item.hint}</small>
                    </span>
                    <ArrowUpRight size={15} />
                  </button>
                ))}
              </div>
              <div className="command-footer">
                <span>
                  <kbd>↑</kbd>
                  <kbd>↓</kbd> Navigate
                </span>
                <span>
                  <kbd>esc</kbd> Close
                </span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {notice && (
          <motion.div
            className="toast"
            role="status"
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
          >
            <span>
              <Check size={15} />
            </span>
            <p>{notice}</p>
            <button
              type="button"
              aria-label="Dismiss notification"
              onClick={() => setNotice(null)}
            >
              <X size={15} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
