package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Writing a checkpoint: the other half of external memory.
//
// Ported from doctrine_state.cmd_checkpoint. Verification (verify.go) proves a
// chain honest; this is what CREATES one, and it is the harder half - a reader
// that is wrong reports a bad verdict once, but a WRITER that is wrong corrupts
// the evidence every future reader depends on.
//
// The structural rule that makes it safe is PROPOSE/DISPOSE: every instance is
// built, schema-validated and hashed BEFORE anything touches the disk. A writer
// that validates as it goes leaves a half-written plane behind on its first
// failure - a distillate with no checkpoint, or a checkpoint whose predecessor
// hash was taken over a file that never got written - and that wreckage is
// indistinguishable from tampering to the next `verify`.

const (
	defaultKeep     = 5
	leaseTTLSeconds = 3600
	deadEndCap      = 8
	stateDirName    = ".doctrine-state"
)

var safeIDRe = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`)

// secretRes mirrors SECRET_RES. State files are committed forever, so a secret
// that reaches one cannot be redacted later - the refusal has to happen here,
// before the write, or not at all.
var secretRes = []*regexp.Regexp{
	regexp.MustCompile(`AKIA[0-9A-Z]{16}`),
	regexp.MustCompile(`-----BEGIN [A-Z ]*PRIVATE KEY-----`),
	regexp.MustCompile(`gh[pousr]_[A-Za-z0-9]{20,}`),
	regexp.MustCompile(`xox[baprs]-[A-Za-z0-9-]{10,}`),
	regexp.MustCompile(`(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*['"]?[^\s'"]{6,}`),
}

// markerRes rejects HTML-comment and sentinel tokens. Checkpoint text is
// spliced into AGENTS.md inside a managed block, so a `-->` in a distillate is
// a way OUT of that block and into instructions an agent reads every session -
// self-propagating injection through a committed file.
var markerRes = []*regexp.Regexp{
	regexp.MustCompile(`<!--`),
	regexp.MustCompile(`-->`),
	regexp.MustCompile(`doctrine:state:(begin|end)`),
}

func (pl plane) local() string   { return filepath.Join(pl.stateDir, "local") }
func (pl plane) intents() string { return filepath.Join(pl.stateDir, "intent") }
func (pl plane) effects() string { return filepath.Join(pl.stateDir, "effects") }

func gitOut(repo string, args ...string) (string, error) {
	cmd := exec.Command("git", args...)
	cmd.Dir = repo
	out, err := cmd.Output()
	return strings.TrimSpace(string(out)), err
}

func headCommit(repo string) (string, error) { return gitOut(repo, "rev-parse", "HEAD") }

func worktreeState(repo string) string {
	out, err := gitOut(repo, "status", "--porcelain")
	if err != nil || out == "" {
		return "clean"
	}
	return "dirty"
}

// nowUTC matches Python's strftime("%Y-%m-%dT%H:%M:%SZ") exactly.
//
// time.RFC3339 is NOT equivalent: it renders a numeric offset for a time whose
// location is not UTC. The schema's date-time pattern accepts both spellings,
// so the difference would validate cleanly and surface only as two tools
// writing visibly different timestamps into the same chain.
func nowUTC() string { return time.Now().UTC().Format("2006-01-02T15:04:05Z") }

// canonicalLine is the NDJSON encoding for the decisions ledger: separators
// (",", ":"), no indent - deliberately different from canonicalBytes, which
// indents. One ledger entry is exactly one line.
func canonicalLine(v any) (string, error) {
	var sb strings.Builder
	enc := json.NewEncoder(&sb)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return "", err
	}
	return strings.TrimRight(sb.String(), "\n"), nil
}

func scanSecrets(distillate map[string]any) error {
	var texts []string
	collect := func(key string, fields ...string) {
		items, _ := distillate[key].([]any)
		for _, it := range items {
			m, _ := it.(map[string]any)
			for _, f := range fields {
				if s, ok := m[f].(string); ok {
					texts = append(texts, s)
				}
			}
		}
	}
	collect("learned", "claim", "evidence")
	collect("dead_ends", "approach", "why_failed")
	for _, key := range []string{"open_threads", "next_actions"} {
		items, _ := distillate[key].([]any)
		for _, it := range items {
			if s, ok := it.(string); ok {
				texts = append(texts, s)
			}
		}
	}
	for _, text := range texts {
		for _, re := range secretRes {
			if re.MatchString(text) {
				pat := re.String()
				if len(pat) > 40 {
					pat = pat[:40]
				}
				return fmt.Errorf("distillate text matches a secret pattern "+
					"(%s...); state files are committed forever - rephrase "+
					"without the secret", pat)
			}
		}
		for _, re := range markerRes {
			if re.MatchString(text) {
				return fmt.Errorf("distillate text contains an HTML-comment/marker "+
					"token (%s); it could break out of the AGENTS.md managed state "+
					"block - rephrase without it", re.String())
			}
		}
	}
	return nil
}

// mergeDeadEnds dedupes on (approach, why_failed). Priority is the new
// distillate's own ends, then pruned negatives NEWEST first - so what falls off
// the cap is the oldest knowledge rather than the freshest.
func mergeDeadEnds(newEnds []any, prunedFiles []string) ([]any, int) {
	var prunedEnds []any
	for i := len(prunedFiles) - 1; i >= 0; i-- { // newest pruned first
		name := filepath.Base(prunedFiles[i])
		raw, err := os.ReadFile(prunedFiles[i])
		if err != nil {
			// Reported, never silently skipped: a dropped dead end is
			// knowledge the next session pays to relearn.
			fmt.Fprintf(os.Stderr, "warning: dead_ends lost from corrupt %s: %v\n", name, err)
			continue
		}
		var d map[string]any
		if err := json.Unmarshal(raw, &d); err != nil {
			fmt.Fprintf(os.Stderr, "warning: dead_ends lost from corrupt %s: %v\n", name, err)
			continue
		}
		if ends, ok := d["dead_ends"].([]any); ok {
			prunedEnds = append(prunedEnds, ends...)
		}
	}
	seen := map[string]bool{}
	merged := []any{}
	for _, end := range append(append([]any{}, newEnds...), prunedEnds...) {
		m, _ := end.(map[string]any)
		key := fmt.Sprintf("%v\x00%v", m["approach"], m["why_failed"])
		if seen[key] {
			continue
		}
		seen[key] = true
		merged = append(merged, end)
	}
	if len(merged) > deadEndCap {
		return merged[:deadEndCap], len(merged) - deadEndCap
	}
	return merged, 0
}

func unresolvedEffectCount(pl plane) int {
	entries, err := os.ReadDir(pl.effects())
	if err != nil {
		return 0
	}
	var names []string
	for _, e := range entries {
		if strings.HasSuffix(e.Name(), ".effects.ndjson") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	n := 0
	for _, name := range names {
		raw, err := os.ReadFile(filepath.Join(pl.effects(), name))
		if err != nil {
			continue
		}
		for _, line := range strings.Split(string(raw), "\n") {
			if strings.TrimSpace(line) == "" {
				continue
			}
			// A line that will not parse counts as UNRESOLVED, not as absent.
			// Treating malformed as resolved would let a corrupt effects log
			// quietly report a clean plane.
			status := "malformed"
			var entry map[string]any
			if json.Unmarshal([]byte(line), &entry) == nil {
				status, _ = entry["status"].(string)
			}
			if status != "confirmed" && status != "compensated" {
				n++
			}
		}
	}
	return n
}

// checkLease refuses a write while another session's unexpired lease holds.
//
// Concurrent writers fork the chain, and a fork is expensive to unpick. But a
// lease that cannot be broken is worse than the fork it prevents: an expired
// lease, or an explicit --steal, yields rather than locking a solo maintainer
// out of their own repo.
func checkLease(pl plane, sessionID string, steal bool) error {
	raw, err := os.ReadFile(filepath.Join(pl.local(), "lease.json"))
	if err != nil {
		return nil // no lease held
	}
	var lease map[string]any
	if json.Unmarshal(raw, &lease) != nil || lease == nil {
		fmt.Fprintln(os.Stderr, "warning: corrupt lease file - overwriting")
		return nil
	}
	holder, _ := lease["session_id"].(string)
	expires, _ := lease["expires_at"].(float64)
	if holder == sessionID || expires <= float64(time.Now().Unix()) {
		return nil
	}
	human, _ := lease["expires_human"].(string)
	if human == "" {
		human = "?"
	}
	if steal {
		fmt.Fprintf(os.Stderr,
			"warning: lease STOLEN from session '%s' (held until %s)\n", holder, human)
		return nil
	}
	return fmt.Errorf("state plane is leased by session '%s' until %s - "+
		"concurrent writers fork the chain; wait, or pass --steal to take over "+
		"deliberately", holder, human)
}

func writeLease(pl plane, sessionID string) error {
	if err := os.MkdirAll(pl.local(), 0o755); err != nil {
		return err
	}
	if sessionID == "" {
		sessionID = "(anonymous)"
	}
	expires := time.Now().Add(leaseTTLSeconds * time.Second)
	host, _ := os.Hostname()
	b, err := canonicalBytes(map[string]any{
		"session_id":    sessionID,
		"host":          host,
		"acquired_at":   nowUTC(),
		"expires_at":    float64(expires.Unix()),
		"expires_human": expires.UTC().Format("2006-01-02T15:04:05Z"),
	})
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(pl.local(), "lease.json"), b, 0o644)
}

func distillateFilesSorted(pl plane) []string { return distillateFiles(pl) }

// writeCheckpoint is the propose/dispose write path.
//
// Everything above the "write phase" marker is pure computation over the
// proposal and the existing plane. Nothing is created, unlinked or overwritten
// until both instances have passed their schemas.
func writeCheckpoint(pl plane, proposal map[string]any, keep int, steal bool) error {
	if keep < 1 {
		return fmt.Errorf("--keep must be >= 1")
	}
	for _, field := range []string{"session_id", "control", "distillate"} {
		if _, ok := proposal[field]; !ok {
			return fmt.Errorf("proposal missing '%s'", field)
		}
	}
	session, _ := proposal["session_id"].(string)
	if err := checkLease(pl, session, steal); err != nil {
		return err
	}

	atCommit, err := headCommit(pl.root)
	if err != nil {
		return fmt.Errorf("cannot read HEAD: %v", err)
	}
	created := nowUTC()

	var prevSHA any // JSON null for genesis, not "" - see sameNullableString
	seq := 0
	if exists(pl.checkpoint) {
		h, err := sha256File(pl.checkpoint)
		if err != nil {
			return err
		}
		prevSHA = h
		raw, err := os.ReadFile(pl.checkpoint)
		if err != nil {
			return err
		}
		var cur map[string]any
		if err := json.Unmarshal(raw, &cur); err != nil {
			return fmt.Errorf("current checkpoint is not valid JSON: %v", err)
		}
		n, ok := cur["seq"].(float64)
		if !ok {
			return fmt.Errorf("current checkpoint has no numeric seq")
		}
		seq = int(n) + 1
	}

	// ---- propose: everything validates before any write ----
	existing := distillateFilesSorted(pl)
	var pruned []string
	if cut := len(existing) - (keep - 1); cut > 0 {
		pruned = existing[:cut]
	}
	pending := filepath.Join(pl.distillates, "pending-dead-ends.json")

	distBody := map[string]any{}
	if b, ok := proposal["distillate"].(map[string]any); ok {
		for k, v := range b {
			distBody[k] = v
		}
	}
	var pendingEnds []any
	if raw, err := os.ReadFile(pending); err == nil {
		var p map[string]any
		if json.Unmarshal(raw, &p) == nil {
			pendingEnds, _ = p["dead_ends"].([]any)
		}
	}
	ownEnds, _ := distBody["dead_ends"].([]any)
	merged, dropped := mergeDeadEnds(append(append([]any{}, ownEnds...), pendingEnds...), pruned)
	distBody["dead_ends"] = merged

	distillate := map[string]any{}
	for k, v := range distBody {
		distillate[k] = v
	}
	distillate["distillate_version"] = "1"
	distillate["seq"] = float64(seq)
	distillate["session_id"] = session
	distillate["created_at"] = created
	distillate["at_commit"] = atCommit

	distSchema, err := loadSchema(pl.root, "distillate")
	if err != nil {
		return err
	}
	if err := validateSchema(distillate, distSchema, distSchema, "$"); err != nil {
		return fmt.Errorf("distillate: %v", err)
	}
	if err := scanSecrets(distillate); err != nil {
		return err
	}
	distBytes, err := canonicalBytes(distillate)
	if err != nil {
		return err
	}
	distSHA := sha256Hex(distBytes)

	// Prospective decisions content, hashed BEFORE anything is written: the
	// checkpoint records the hash the ledger WILL have, so a checkpoint that
	// never lands leaves no ledger claim behind it.
	taskRefs, _ := distillate["task_refs"].([]any)
	if taskRefs == nil {
		taskRefs = []any{}
	}
	var decisionLines []string
	learned, _ := distillate["learned"].([]any)
	for _, item := range learned {
		m, _ := item.(map[string]any)
		if kind, _ := m["kind"].(string); kind != "decision_ref" {
			continue
		}
		line, err := canonicalLine(map[string]any{
			"at_commit":  atCommit,
			"claim":      m["claim"],
			"created_at": created,
			"evidence":   m["evidence"],
			"intents":    taskRefs,
			"seq":        float64(seq),
			"session_id": session,
		})
		if err != nil {
			return err
		}
		decisionLines = append(decisionLines, line+"\n")
	}
	existingDecisions, _ := os.ReadFile(pl.decisions)
	prospectiveDecisions := append(append([]byte{}, existingDecisions...),
		[]byte(strings.Join(decisionLines, ""))...)

	intentsIndex := map[string]any{}
	if entries, err := os.ReadDir(pl.intents()); err == nil {
		var names []string
		for _, e := range entries {
			if strings.HasSuffix(e.Name(), ".intent.json") {
				names = append(names, e.Name())
			}
		}
		sort.Strings(names)
		for _, name := range names {
			stem := strings.TrimSuffix(name, ".intent.json")
			if !safeIDRe.MatchString(stem) {
				return fmt.Errorf("unsafe intent filename: %s", name)
			}
			h, err := sha256File(filepath.Join(pl.intents(), name))
			if err != nil {
				return err
			}
			intentsIndex[stem] = h
		}
	}
	control, _ := proposal["control"].(map[string]any)
	if control == nil {
		return fmt.Errorf("proposal 'control' is not an object")
	}
	activeIntents, _ := control["active_intents"].([]any)
	for _, intent := range activeIntents {
		s := fmt.Sprintf("%v", intent)
		if !safeIDRe.MatchString(s) {
			return fmt.Errorf("unsafe intent id in control: '%s'", s)
		}
	}

	checkpoint := map[string]any{
		"checkpoint_version": "1",
		"seq":                float64(seq),
		"prev_sha256":        prevSHA,
		"created_at":         created,
		"at_commit":          atCommit,
		"session_id":         session,
		"worktree":           worktreeState(pl.root),
		"control":            control,
		"state_index": map[string]any{
			"intents":                  intentsIndex,
			"decisions_sha256":         sha256Hex(prospectiveDecisions),
			"latest_distillate_sha256": distSHA,
			"unresolved_effects":       float64(unresolvedEffectCount(pl)),
		},
	}
	cpSchema, err := loadSchema(pl.root, "checkpoint")
	if err != nil {
		return err
	}
	if err := validateSchema(checkpoint, cpSchema, cpSchema, "$"); err != nil {
		return fmt.Errorf("checkpoint: %v", err)
	}
	cpBytes, err := canonicalBytes(checkpoint)
	if err != nil {
		return err
	}
	cpSHA := sha256Hex(cpBytes)

	// ---- write phase: both instances valid, nothing written until now ----
	if dropped > 0 {
		fmt.Fprintf(os.Stderr, "note: %d merged dead_end(s) dropped at the schema "+
			"cap of %d (oldest first)\n", dropped, deadEndCap)
	}
	if err := os.MkdirAll(pl.distillates, 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(
		filepath.Join(pl.distillates, fmt.Sprintf("%d-%s.json", seq, distSHA[:12])),
		distBytes, 0o644); err != nil {
		return err
	}
	for _, f := range pruned {
		os.Remove(f)
	}
	os.Remove(pending)
	if len(decisionLines) > 0 {
		if err := os.MkdirAll(filepath.Dir(pl.decisions), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(pl.decisions, prospectiveDecisions, 0o644); err != nil {
			return err
		}
	}
	if err := os.MkdirAll(pl.checkpoints, 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(pl.checkpoint, cpBytes, 0o644); err != nil {
		return err
	}
	if err := os.WriteFile(
		filepath.Join(pl.checkpoints, fmt.Sprintf("%d-%s.json", seq, cpSHA[:12])),
		cpBytes, 0o644); err != nil {
		return err
	}
	if err := writeLease(pl, session); err != nil {
		return err
	}

	msg := fmt.Sprintf("checkpoint %d written at %s (%s); distillate %s",
		seq, atCommit[:12], cpSHA[:12], distSHA[:12])
	if len(pruned) > 0 {
		msg += fmt.Sprintf("; pruned %d distillate(s)", len(pruned))
	}
	fmt.Println(msg)
	fmt.Printf("remember (STATE.md step 4): git add %s && git commit -m \"state: checkpoint %d\"\n",
		stateDirName, seq)
	return nil
}

func cmdCheckpoint(args []string) {
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		fmt.Fprintln(os.Stderr, "not a doctrine repo")
		os.Exit(2)
	}
	proposalPath := flagOf(args, "proposal")
	if proposalPath == "" {
		fmt.Fprintln(os.Stderr,
			"usage: doctrineos checkpoint --proposal <file.json> [--keep N] [--steal]")
		os.Exit(2)
	}
	raw, err := os.ReadFile(proposalPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error: proposal:", err)
		os.Exit(2)
	}
	var proposal map[string]any
	if err := json.Unmarshal(raw, &proposal); err != nil {
		fmt.Fprintf(os.Stderr, "error: proposal %s: unparseable (%v)\n", proposalPath, err)
		os.Exit(2)
	}
	keep := defaultKeep
	if k := flagOf(args, "keep"); k != "" {
		if _, err := fmt.Sscanf(k, "%d", &keep); err != nil {
			fmt.Fprintln(os.Stderr, "error: --keep must be an integer")
			os.Exit(2)
		}
	}
	if err := writeCheckpoint(newPlane(root), proposal, keep, hasFlag(args, "steal")); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}
