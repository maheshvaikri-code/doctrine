"use client";

import {
  Activity,
  ArrowUpRight,
  Boxes,
  Check,
  CircleAlert,
  Command,
  FileCheck2,
  Fingerprint,
  Gauge,
  GitBranch,
  Layers3,
  LockKeyhole,
  Menu,
  PanelLeftClose,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  SquareTerminal,
  Waypoints,
  X,
  Zap,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  type ComponentType,
  type KeyboardEvent as ReactKeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  DoctrineApiError,
  type DoctrineSnapshot,
  type Gate,
  fetchSnapshot,
  startVerification,
} from "./doctrine-api";

type Range = "7D" | "30D" | "90D";
type SurfaceState = "live" | "loading" | "partial" | "error" | "empty";
type Icon = ComponentType<{ size?: number; strokeWidth?: number }>;
type Notice = { message: string; tone: "success" | "error" };
type CommandId = "verify" | "refresh" | "evidence" | "release";

const ranges: Range[] = ["7D", "30D", "90D"];
const navItems: Array<{ label: string; href: string; icon: Icon }> = [
  { label: "Overview", href: "#overview", icon: Gauge },
  { label: "Verification", href: "#verification", icon: Fingerprint },
  { label: "Runtime", href: "#runtime", icon: Waypoints },
  { label: "Activity", href: "#activity", icon: Activity },
  { label: "Release", href: "#release", icon: GitBranch },
];
const commands: Array<{
  id: CommandId;
  label: string;
  hint: string;
  icon: Icon;
}> = [
  {
    id: "verify",
    label: "Run verification",
    hint: "Execute the four Doctrine source-repository gates",
    icon: Play,
  },
  {
    id: "refresh",
    label: "Refresh snapshot",
    hint: "Re-read repository, activation, state, and release evidence",
    icon: RefreshCw,
  },
  {
    id: "evidence",
    label: "Open verification",
    hint: "Jump to the current gate evidence",
    icon: FileCheck2,
  },
  {
    id: "release",
    label: "Inspect release identity",
    hint: "Jump to version, tag, and commit distance",
    icon: GitBranch,
  },
];

function formatSnapshotTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "time unavailable";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

function formatActivityTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--:--";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function chartHeights(values: number[]): number[] {
  const highest = Math.max(...values, 0);
  if (highest === 0) return values.map(() => 0);
  return values.map((value) =>
    value === 0 ? 0 : Math.max(12, Math.round((value / highest) * 100)),
  );
}

function gateTone(status: Gate["status"]): "healthy" | "watch" | "blocked" {
  if (status === "passed") return "healthy";
  if (status === "failed") return "blocked";
  return "watch";
}

function StatusDot({ status }: { status: Gate["status"] }) {
  const state = gateTone(status);
  return (
    <span className={`status-dot status-dot-${state}`} aria-hidden="true">
      <span />
    </span>
  );
}

function MetricCard({
  label,
  value,
  detail,
  icon: IconComponent,
  delay,
}: {
  label: string;
  value: string;
  detail: string;
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
      <p>{detail}</p>
    </motion.article>
  );
}

function LoadingState() {
  return (
    <section className="state-stage" aria-live="polite" aria-busy="true">
      <div className="state-spinner" aria-hidden="true" />
      <p className="eyebrow">Connecting to Doctrine</p>
      <h1>Reading the repository control state.</h1>
      <p>The local bridge is collecting activation, gate, state, and release evidence.</p>
    </section>
  );
}

function EmptyState({ onRetry }: { onRetry: () => void }) {
  return (
    <section className="state-stage">
      <div className="state-icon">
        <Boxes size={24} />
      </div>
      <p className="eyebrow">No Doctrine repository connected</p>
      <h1>The bridge is running, but this folder is not Doctrine-enabled.</h1>
      <p>Restart the bridge from a Doctrine repository, then retry this snapshot.</p>
      <button className="button button-primary" type="button" onClick={onRetry}>
        Retry connection <RefreshCw size={15} />
      </button>
    </section>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <section className="state-stage state-stage-error" role="alert">
      <div className="state-icon">
        <CircleAlert size={24} />
      </div>
      <p className="eyebrow">Local bridge unavailable</p>
      <h1>The repository control state could not be loaded.</h1>
      <p>{message} Start `doctrine-dashboard` in the repository and retry.</p>
      <button className="button button-primary" type="button" onClick={onRetry}>
        Retry connection <RefreshCw size={15} />
      </button>
    </section>
  );
}

function RuntimeNode({
  icon: IconComponent,
  verb,
  name,
  status,
  connected,
  featured = false,
}: {
  icon: Icon;
  verb: string;
  name: string;
  status: string;
  connected: boolean;
  featured?: boolean;
}) {
  return (
    <div
      className={`runtime-node ${featured ? "featured" : ""} ${
        connected ? "" : "runtime-node-offline"
      }`}
    >
      <span className="node-icon">
        <IconComponent size={18} />
      </span>
      <span>
        <small>{verb}</small>
        <strong>{name}</strong>
        <em>{status}</em>
      </span>
    </div>
  );
}

export function LiveControlRoom() {
  const [range, setRange] = useState<Range>("30D");
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [snapshot, setSnapshot] = useState<DoctrineSnapshot | null>(null);
  const [errorMessage, setErrorMessage] = useState(
    "The local bridge is not reachable.",
  );
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("Overview");
  const [notice, setNotice] = useState<Notice | null>(null);
  const reduceMotion = useReducedMotion();
  const requestRef = useRef<AbortController | null>(null);
  const commandButtonRef = useRef<HTMLButtonElement>(null);
  const firstCommandRef = useRef<HTMLButtonElement>(null);
  const lastVerificationStatus = useRef<string | null>(null);

  const refreshSnapshot = useCallback(async (announce = false) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    let timedOut = false;
    const timeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 5000);
    await Promise.resolve();
    if (controller.signal.aborted) {
      window.clearTimeout(timeout);
      return;
    }
    setIsRefreshing(true);
    try {
      const current = await fetchSnapshot(controller.signal);
      setSnapshot(current);
      setLoadState("ready");
      setErrorMessage("");
      if (announce) {
        setNotice({
          message: "Repository evidence refreshed.",
          tone: "success",
        });
      }
    } catch (cause) {
      if (controller.signal.aborted && !timedOut) return;
      const message =
        cause instanceof DoctrineApiError
          ? cause.message
          : "The repository snapshot could not be loaded.";
      setErrorMessage(
        timedOut ? "The local bridge did not respond within five seconds." : message,
      );
      setLoadState("error");
    } finally {
      window.clearTimeout(timeout);
      if (requestRef.current === controller) requestRef.current = null;
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const initialRequest = window.setTimeout(() => {
      void refreshSnapshot();
    }, 0);
    return () => {
      window.clearTimeout(initialRequest);
      requestRef.current?.abort();
    };
  }, [refreshSnapshot]);

  useEffect(() => {
    if (snapshot?.verification.status !== "running") return;
    const interval = window.setInterval(() => {
      void refreshSnapshot();
    }, 1500);
    return () => window.clearInterval(interval);
  }, [refreshSnapshot, snapshot?.verification.status]);

  useEffect(() => {
    const current = snapshot?.verification.status ?? null;
    if (
      lastVerificationStatus.current === "running" &&
      current &&
      current !== "running"
    ) {
      setNotice({
        message:
          current === "passed"
            ? "Doctrine verification passed."
            : "Doctrine verification finished with findings.",
        tone: current === "passed" ? "success" : "error",
      });
    }
    lastVerificationStatus.current = current;
  }, [snapshot?.verification.status]);

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

  const runVerification = async () => {
    if (snapshot?.verification.status === "running") return;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    try {
      const verification = await startVerification(controller.signal);
      setSnapshot((current) =>
        current ? { ...current, verification } : current,
      );
      setNotice({
        message: "Doctrine verification started.",
        tone: "success",
      });
    } catch (cause) {
      setNotice({
        message:
          cause instanceof DoctrineApiError
            ? cause.message
            : "Verification could not be started.",
        tone: "error",
      });
    } finally {
      window.clearTimeout(timeout);
    }
  };

  const closeCommands = () => {
    setCommandOpen(false);
    commandButtonRef.current?.focus();
  };

  const scrollTo = (id: string) => {
    document.querySelector(id)?.scrollIntoView({ behavior: "smooth" });
  };

  const chooseCommand = (id: CommandId) => {
    closeCommands();
    if (id === "verify") {
      void runVerification();
    } else if (id === "refresh") {
      void refreshSnapshot(true);
    } else if (id === "evidence") {
      scrollTo("#verification");
    } else {
      scrollTo("#release");
    }
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

  let surfaceState: SurfaceState = "loading";
  if (loadState === "error") {
    surfaceState = "error";
  } else if (loadState === "ready" && snapshot) {
    if (!snapshot.repository.connected) {
      surfaceState = "empty";
    } else if (
      snapshot.partialReasons.length > 0 ||
      snapshot.verification.status === "running"
    ) {
      surfaceState = "partial";
    } else {
      surfaceState = "live";
    }
  }

  const repositoryName = snapshot?.repository.name ?? "Doctrine repository";
  const verification = snapshot?.verification;
  const passedGates =
    verification?.gates.filter((gate) => gate.status === "passed").length ?? 0;
  const integrityScore = Math.round((passedGates / 4) * 100);
  const evidenceCount = snapshot
    ? snapshot.evidence.reviews +
      snapshot.evidence.qaReports +
      snapshot.evidence.adrs +
      snapshot.evidence.plans +
      snapshot.evidence.goldRecords
    : 0;
  const trendValues = snapshot?.evidence.trend[range] ?? [0];
  const heights = chartHeights(trendValues);
  const verificationRunning = verification?.status === "running";

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
              {item.label === "Activity" &&
                Boolean(snapshot?.statePlane.unresolvedEffects) && (
                  <em>{snapshot?.statePlane.unresolvedEffects}</em>
                )}
            </a>
          ))}
        </nav>

        <div className="sidebar-workspace">
          <span className="nav-label">Repository</span>
          <div className="workspace-summary">
            <span className="workspace-avatar">
              {repositoryName.slice(0, 2).toUpperCase()}
            </span>
            <span>
              <strong>{repositoryName}</strong>
              <small>
                {snapshot?.repository.branch ?? "branch unavailable"} ·{" "}
                {snapshot?.repository.commit ?? "commit unavailable"}
              </small>
            </span>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="runtime-status">
            <span
              className={surfaceState === "error" ? "offline-beacon" : "live-beacon"}
            />
            <span>
              <strong>
                {surfaceState === "error" ? "Bridge offline" : "Bridge connected"}
              </strong>
              <small>Loopback · API v1</small>
            </span>
          </div>
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
            <span>{repositoryName}</span>
            <span>/</span>
            <strong>{activeSection}</strong>
          </div>
          <div className="topbar-actions">
            <span className="prototype-badge live-data-badge">
              <ShieldCheck size={13} /> Repository evidence
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
            <button
              className="icon-button refresh-button"
              type="button"
              aria-label="Refresh repository evidence"
              disabled={isRefreshing}
              onClick={() => void refreshSnapshot(true)}
            >
              <RefreshCw size={17} className={isRefreshing ? "is-spinning" : ""} />
            </button>
          </div>
        </header>

        <main id="main-content" tabIndex={-1}>
          {surfaceState === "loading" && <LoadingState />}
          {surfaceState === "error" && (
            <ErrorState
              message={errorMessage}
              onRetry={() => void refreshSnapshot()}
            />
          )}
          {surfaceState === "empty" && (
            <EmptyState onRetry={() => void refreshSnapshot()} />
          )}

          {(surfaceState === "live" || surfaceState === "partial") && snapshot && (
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
                    <strong>Partial evidence.</strong>{" "}
                    {verificationRunning
                      ? "Verification is running; gate results will update automatically."
                      : snapshot.partialReasons.join(" ")}
                  </span>
                </div>
              )}

              <section className="hero" id="overview" aria-labelledby="page-title">
                <div>
                  <p className="eyebrow">
                    <span className="live-beacon" /> {repositoryName} ·{" "}
                    {snapshot.repository.isDirty ? "Working tree dirty" : "Tree clean"}
                  </p>
                  <h1 id="page-title">
                    Confidence has
                    <br />a control plane.
                  </h1>
                  <p className="hero-copy">
                    Repository identity, activation, gate evidence, state-chain
                    integrity, and release distance—read from Doctrine itself.
                  </p>
                </div>
                <div className="hero-actions">
                  <button
                    className="button button-primary"
                    type="button"
                    disabled={verificationRunning}
                    onClick={() => void runVerification()}
                  >
                    {verificationRunning ? (
                      <RefreshCw size={15} className="is-spinning" />
                    ) : (
                      <Play size={15} fill="currentColor" />
                    )}
                    {verificationRunning ? "Verifying…" : "Run verification"}
                  </button>
                  <a className="button button-secondary" href="#verification">
                    Open evidence <ArrowUpRight size={15} />
                  </a>
                </div>
              </section>

              <section className="metric-grid" aria-label="Repository metrics">
                <MetricCard
                  label="Tracked files"
                  value={snapshot.repository.trackedFiles.toLocaleString()}
                  detail={`${snapshot.repository.branch ?? "Detached"} · ${
                    snapshot.repository.commit ?? "unknown commit"
                  }`}
                  icon={Layers3}
                  delay={0.04}
                />
                <MetricCard
                  label="Activation"
                  value={`${snapshot.activation.passing}/${snapshot.activation.total}`}
                  detail={
                    snapshot.activation.status === "healthy"
                      ? "Critical activation checks pass"
                      : "Activation needs attention"
                  }
                  icon={Command}
                  delay={0.08}
                />
                <MetricCard
                  label="State checkpoints"
                  value={snapshot.statePlane.checkpoints.toLocaleString()}
                  detail={
                    snapshot.statePlane.status === "healthy"
                      ? `Chain intact · seq ${snapshot.statePlane.checkpointSeq ?? "—"}`
                      : "State evidence unavailable"
                  }
                  icon={Fingerprint}
                  delay={0.12}
                />
                <MetricCard
                  label="Verification gates"
                  value={`${passedGates}/4`}
                  detail={verification?.summary ?? "No verification evidence"}
                  icon={ShieldCheck}
                  delay={0.16}
                />
              </section>

              <section className="dashboard-grid" id="verification">
                <motion.article
                  className="panel gate-panel"
                  initial={reduceMotion ? false : { opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: reduceMotion ? 0 : 0.48, delay: 0.12 }}
                >
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Gate posture</p>
                      <h2>Doctrine verification</h2>
                    </div>
                    <span className={`verification-chip ${verification?.status}`}>
                      {verification?.status.replace("_", " ") ?? "unknown"}
                    </span>
                  </header>

                  <div className="gate-summary">
                    <div>
                      <strong>{integrityScore}</strong>
                      <span>Gate score</span>
                    </div>
                    <p>{verification?.summary}</p>
                  </div>

                  <div className="gate-table" role="table" aria-label="Gate status">
                    <div className="gate-table-head" role="row">
                      <span role="columnheader">Gate</span>
                      <span role="columnheader">Evidence</span>
                      <span role="columnheader">Status</span>
                    </div>
                    {verification?.gates.map((gate) => (
                      <div className="gate-row" role="row" key={gate.key}>
                        <div role="cell">
                          <StatusDot status={gate.status} />
                          <span>
                            <strong>{gate.label}</strong>
                            <small>{gate.key}</small>
                          </span>
                        </div>
                        <span role="cell">{gate.evidence}</span>
                        <div role="cell" className="coverage-cell">
                          <span className={`gate-result gate-result-${gate.status}`}>
                            {gate.status}
                          </span>
                        </div>
                      </div>
                    ))}
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
                      <p className="eyebrow">Change evidence</p>
                      <h2>Repository activity</h2>
                    </div>
                    <span className="panel-number">
                      {trendValues.reduce((sum, value) => sum + value, 0)}
                    </span>
                  </header>
                  <p className="panel-subcopy">Commits observed in the selected window.</p>
                  <div className="evidence-chart" aria-label={`${range} commit trend`}>
                    <div className="chart-grid" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                      <span />
                    </div>
                    <div className="chart-bars" aria-hidden="true">
                      {heights.map((height, index) => (
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
                  <div className="range-switcher chart-range" aria-label="Commit range">
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
                  <div className="evidence-callout">
                    <FileCheck2 size={19} />
                    <span>
                      <strong>{evidenceCount} governance artifacts</strong>
                      <small>
                        {snapshot.evidence.reviews} reviews ·{" "}
                        {snapshot.evidence.qaReports} QA · {snapshot.evidence.adrs} ADRs
                      </small>
                    </span>
                  </div>
                </motion.article>
              </section>

              <section className="runtime-grid" id="runtime">
                <article className="panel runtime-panel">
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Execution fabric</p>
                      <h2>Connected systems, stated honestly</h2>
                    </div>
                    <span className="live-status">
                      <span className="live-beacon" /> Doctrine connected
                    </span>
                  </header>
                  <div className="runtime-flow" aria-label="Execution system flow">
                    <RuntimeNode
                      icon={Command}
                      verb="Govern"
                      name="Doctrine"
                      status="Connected"
                      connected
                      featured
                    />
                    <span className="flow-connector flow-connector-dormant" aria-hidden>
                      <i />
                    </span>
                    <RuntimeNode
                      icon={Waypoints}
                      verb="Coordinate"
                      name="MAPLE Runtime"
                      status="Not connected"
                      connected={false}
                    />
                    <span className="flow-connector flow-connector-dormant" aria-hidden>
                      <i />
                    </span>
                    <RuntimeNode
                      icon={LockKeyhole}
                      verb="Enforce"
                      name="Policy Shield"
                      status="Not connected"
                      connected={false}
                    />
                    <span className="flow-connector flow-connector-dormant" aria-hidden>
                      <i />
                    </span>
                    <RuntimeNode
                      icon={Zap}
                      verb="Evaluate"
                      name="Trust Engine"
                      status="Not connected"
                      connected={false}
                    />
                  </div>
                  <div className="runtime-stats">
                    <div>
                      <span>State role</span>
                      <strong>{snapshot.statePlane.role ?? "—"}</strong>
                    </div>
                    <div>
                      <span>State phase</span>
                      <strong>{snapshot.statePlane.phase ?? "—"}</strong>
                    </div>
                    <div>
                      <span>Unresolved effects</span>
                      <strong>{snapshot.statePlane.unresolvedEffects}</strong>
                    </div>
                    <div>
                      <span>API</span>
                      <strong>v{snapshot.apiVersion}</strong>
                    </div>
                  </div>
                </article>

                <article className="panel activity-panel" id="activity">
                  <header className="panel-header">
                    <div>
                      <p className="eyebrow">Git ledger</p>
                      <h2>What changed</h2>
                    </div>
                  </header>
                  {snapshot.evidence.activity.length ? (
                    <ol className="activity-list">
                      {snapshot.evidence.activity.slice(0, 5).map((item) => (
                        <li key={item.commit}>
                          <time dateTime={item.occurredAt}>
                            {formatActivityTime(item.occurredAt)}
                          </time>
                          <span className="activity-marker neutral" />
                          <div>
                            <strong>{item.title}</strong>
                            <p>{item.commit}</p>
                          </div>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="panel-empty">No commit activity was returned.</p>
                  )}
                </article>
              </section>

              <section className="release-panel panel" id="release">
                <div>
                  <p className="eyebrow">Release identity</p>
                  <h2>
                    {snapshot.release.status === "current"
                      ? "Version and tag are aligned."
                      : "The repository is ahead of its latest tag."}
                  </h2>
                  <p>
                    Publishing and Gold promotion remain outside this UI and require
                    explicit human authority.
                  </p>
                </div>
                <div className="release-candidates">
                  <div className="release-record">
                    <span className="release-icon">
                      <SquareTerminal size={17} />
                    </span>
                    <span>
                      <strong>{repositoryName}</strong>
                      <small>
                        package {snapshot.release.currentVersion ?? "unversioned"}
                      </small>
                    </span>
                    <span className="release-stage">
                      <small>{snapshot.release.latestTag ?? "No tag"}</small>
                      <strong>
                        {snapshot.release.commitsAhead ?? "—"} commits ahead
                      </strong>
                    </span>
                  </div>
                </div>
              </section>

              <footer className="dashboard-footer">
                <span>Doctrine Control Room · live repository adapter</span>
                <span>Snapshot {formatSnapshotTime(snapshot.generatedAt)}</span>
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
              <p className="command-group-label">Available actions</p>
              <div className="command-list">
                {commands.map((item, index) => (
                  <button
                    type="button"
                    key={item.id}
                    ref={index === 0 ? firstCommandRef : undefined}
                    disabled={item.id === "verify" && verificationRunning}
                    onClick={() => chooseCommand(item.id)}
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
                  <kbd>tab</kbd> Navigate
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
            className={`toast toast-${notice.tone}`}
            role={notice.tone === "error" ? "alert" : "status"}
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
          >
            <span>
              {notice.tone === "success" ? (
                <Check size={15} />
              ) : (
                <CircleAlert size={15} />
              )}
            </span>
            <p>{notice.message}</p>
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
