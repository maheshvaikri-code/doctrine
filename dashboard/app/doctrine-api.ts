export type GateStatus = "unknown" | "running" | "passed" | "failed";
export type VerificationStatus =
  | "never_run"
  | "running"
  | "passed"
  | "failed"
  | "timed_out";

export type Gate = {
  key: "lint" | "ruff" | "tests" | "state";
  label: string;
  status: GateStatus;
  evidence: string;
};

export type Verification = {
  id: string | null;
  status: VerificationStatus;
  commit: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  exitCode: number | null;
  testCount: number | null;
  summary: string;
  gates: Gate[];
};

export type Activity = {
  commit: string;
  occurredAt: string;
  title: string;
};

export type DoctrineSnapshot = {
  apiVersion: "1";
  generatedAt: string;
  partialReasons: string[];
  repository: {
    connected: boolean;
    name: string | null;
    version: string | null;
    branch: string | null;
    commit: string | null;
    isDirty: boolean;
    trackedFiles: number;
  };
  activation: {
    status: "healthy" | "degraded";
    passing: number;
    total: number;
    findings: Array<{
      status: "pass" | "warning" | "failed";
      message: string;
    }>;
  };
  statePlane: {
    status: "healthy" | "degraded" | "missing";
    checkpointSeq: number | null;
    checkpointCommit: string | null;
    checkpoints: number;
    unresolvedEffects: number;
    role: string | null;
    phase: string | null;
  };
  verification: Verification;
  evidence: {
    reviews: number;
    qaReports: number;
    adrs: number;
    plans: number;
    goldRecords: number;
    trend: Record<"7D" | "30D" | "90D", number[]>;
    activity: Activity[];
  };
  release: {
    currentVersion: string | null;
    latestTag: string | null;
    commitsAhead: number | null;
    status: "current" | "ahead" | "unreleased";
  };
};

type JsonRecord = Record<string, unknown>;

const API_BASE =
  process.env.NEXT_PUBLIC_DOCTRINE_API_URL?.replace(/\/+$/, "") ??
  "http://127.0.0.1:8765";

export class DoctrineApiError extends Error {
  readonly code: string;

  constructor(code: string, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "DoctrineApiError";
    this.code = code;
  }
}

function record(value: unknown, path: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value as JsonRecord;
}

function stringValue(value: unknown, path: string): string {
  if (typeof value !== "string") {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value;
}

function nullableString(value: unknown, path: string): string | null {
  return value === null ? null : stringValue(value, path);
}

function numberValue(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value;
}

function nullableNumber(value: unknown, path: string): number | null {
  return value === null ? null : numberValue(value, path);
}

function booleanValue(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value;
}

function enumValue<const T extends string>(
  value: unknown,
  choices: readonly T[],
  path: string,
): T {
  if (typeof value !== "string" || !choices.includes(value as T)) {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value as T;
}

function stringList(value: unknown, path: string): string[] {
  if (!Array.isArray(value)) {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value.map((item, index) => stringValue(item, `${path}[${index}]`));
}

function integerList(value: unknown, path: string): number[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new DoctrineApiError(
      "invalid_response",
      `The bridge returned an invalid ${path}.`,
    );
  }
  return value.map((item, index) => numberValue(item, `${path}[${index}]`));
}

function parseGate(value: unknown, index: number): Gate {
  const gate = record(value, `verification.gates[${index}]`);
  return {
    key: enumValue(
      gate.key,
      ["lint", "ruff", "tests", "state"] as const,
      `verification.gates[${index}].key`,
    ),
    label: stringValue(gate.label, `verification.gates[${index}].label`),
    status: enumValue(
      gate.status,
      ["unknown", "running", "passed", "failed"] as const,
      `verification.gates[${index}].status`,
    ),
    evidence: stringValue(
      gate.evidence,
      `verification.gates[${index}].evidence`,
    ),
  };
}

export function parseVerification(value: unknown): Verification {
  const verification = record(value, "verification");
  if (!Array.isArray(verification.gates) || verification.gates.length !== 4) {
    throw new DoctrineApiError(
      "invalid_response",
      "The bridge returned an invalid verification.gates.",
    );
  }
  return {
    id: nullableString(verification.id, "verification.id"),
    status: enumValue(
      verification.status,
      ["never_run", "running", "passed", "failed", "timed_out"] as const,
      "verification.status",
    ),
    commit: nullableString(verification.commit, "verification.commit"),
    startedAt: nullableString(
      verification.startedAt,
      "verification.startedAt",
    ),
    finishedAt: nullableString(
      verification.finishedAt,
      "verification.finishedAt",
    ),
    exitCode: nullableNumber(verification.exitCode, "verification.exitCode"),
    testCount: nullableNumber(verification.testCount, "verification.testCount"),
    summary: stringValue(verification.summary, "verification.summary"),
    gates: verification.gates.map(parseGate),
  };
}

export function parseSnapshot(value: unknown): DoctrineSnapshot {
  const snapshot = record(value, "snapshot");
  if (snapshot.apiVersion !== "1") {
    throw new DoctrineApiError(
      "unsupported_api",
      "The local bridge uses an unsupported API version.",
    );
  }
  const repository = record(snapshot.repository, "repository");
  const activation = record(snapshot.activation, "activation");
  const statePlane = record(snapshot.statePlane, "statePlane");
  const evidence = record(snapshot.evidence, "evidence");
  const trend = record(evidence.trend, "evidence.trend");
  const release = record(snapshot.release, "release");
  if (!Array.isArray(activation.findings)) {
    throw new DoctrineApiError(
      "invalid_response",
      "The bridge returned invalid activation findings.",
    );
  }
  if (!Array.isArray(evidence.activity)) {
    throw new DoctrineApiError(
      "invalid_response",
      "The bridge returned invalid repository activity.",
    );
  }

  return {
    apiVersion: "1",
    generatedAt: stringValue(snapshot.generatedAt, "generatedAt"),
    partialReasons: stringList(snapshot.partialReasons, "partialReasons"),
    repository: {
      connected: booleanValue(repository.connected, "repository.connected"),
      name: nullableString(repository.name, "repository.name"),
      version: nullableString(repository.version, "repository.version"),
      branch: nullableString(repository.branch, "repository.branch"),
      commit: nullableString(repository.commit, "repository.commit"),
      isDirty: booleanValue(repository.isDirty, "repository.isDirty"),
      trackedFiles: numberValue(
        repository.trackedFiles,
        "repository.trackedFiles",
      ),
    },
    activation: {
      status: enumValue(
        activation.status,
        ["healthy", "degraded"] as const,
        "activation.status",
      ),
      passing: numberValue(activation.passing, "activation.passing"),
      total: numberValue(activation.total, "activation.total"),
      findings: activation.findings.map((value, index) => {
        const finding = record(value, `activation.findings[${index}]`);
        return {
          status: enumValue(
            finding.status,
            ["pass", "warning", "failed"] as const,
            `activation.findings[${index}].status`,
          ),
          message: stringValue(
            finding.message,
            `activation.findings[${index}].message`,
          ),
        };
      }),
    },
    statePlane: {
      status: enumValue(
        statePlane.status,
        ["healthy", "degraded", "missing"] as const,
        "statePlane.status",
      ),
      checkpointSeq: nullableNumber(
        statePlane.checkpointSeq,
        "statePlane.checkpointSeq",
      ),
      checkpointCommit: nullableString(
        statePlane.checkpointCommit,
        "statePlane.checkpointCommit",
      ),
      checkpoints: numberValue(
        statePlane.checkpoints,
        "statePlane.checkpoints",
      ),
      unresolvedEffects: numberValue(
        statePlane.unresolvedEffects,
        "statePlane.unresolvedEffects",
      ),
      role: nullableString(statePlane.role, "statePlane.role"),
      phase: nullableString(statePlane.phase, "statePlane.phase"),
    },
    verification: parseVerification(snapshot.verification),
    evidence: {
      reviews: numberValue(evidence.reviews, "evidence.reviews"),
      qaReports: numberValue(evidence.qaReports, "evidence.qaReports"),
      adrs: numberValue(evidence.adrs, "evidence.adrs"),
      plans: numberValue(evidence.plans, "evidence.plans"),
      goldRecords: numberValue(evidence.goldRecords, "evidence.goldRecords"),
      trend: {
        "7D": integerList(trend["7D"], "evidence.trend.7D"),
        "30D": integerList(trend["30D"], "evidence.trend.30D"),
        "90D": integerList(trend["90D"], "evidence.trend.90D"),
      },
      activity: evidence.activity.map((value, index) => {
        const item = record(value, `evidence.activity[${index}]`);
        return {
          commit: stringValue(
            item.commit,
            `evidence.activity[${index}].commit`,
          ),
          occurredAt: stringValue(
            item.occurredAt,
            `evidence.activity[${index}].occurredAt`,
          ),
          title: stringValue(
            item.title,
            `evidence.activity[${index}].title`,
          ),
        };
      }),
    },
    release: {
      currentVersion: nullableString(
        release.currentVersion,
        "release.currentVersion",
      ),
      latestTag: nullableString(release.latestTag, "release.latestTag"),
      commitsAhead: nullableNumber(
        release.commitsAhead,
        "release.commitsAhead",
      ),
      status: enumValue(
        release.status,
        ["current", "ahead", "unreleased"] as const,
        "release.status",
      ),
    },
  };
}

async function responseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch (cause) {
    throw new DoctrineApiError(
      "invalid_response",
      "The local bridge returned unreadable data.",
      { cause },
    );
  }
}

function errorFromPayload(value: unknown, fallback: string): DoctrineApiError {
  try {
    const envelope = record(value, "error response");
    const error = record(envelope.error, "error");
    return new DoctrineApiError(
      stringValue(error.code, "error.code"),
      stringValue(error.message, "error.message"),
    );
  } catch {
    return new DoctrineApiError("request_failed", fallback);
  }
}

export async function fetchSnapshot(
  signal: AbortSignal,
): Promise<DoctrineSnapshot> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/v1/snapshot`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal,
    });
  } catch (cause) {
    throw new DoctrineApiError(
      "bridge_unavailable",
      "The local bridge is not reachable.",
      { cause },
    );
  }
  const value = await responseJson(response);
  if (!response.ok) {
    throw errorFromPayload(value, "The repository snapshot could not be loaded.");
  }
  return parseSnapshot(value);
}

export async function startVerification(
  signal: AbortSignal,
): Promise<Verification> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/v1/verifications`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: "{}",
      signal,
    });
  } catch (cause) {
    throw new DoctrineApiError(
      "bridge_unavailable",
      "The local bridge is not reachable.",
      { cause },
    );
  }
  const value = await responseJson(response);
  if (!response.ok) {
    throw errorFromPayload(value, "Verification could not be started.");
  }
  return parseVerification(value);
}
