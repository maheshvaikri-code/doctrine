package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Hydration: handing the next session what this one learned.
//
// Ported from doctrine_state.build_bundle_body / cmd_hydrate. This is the
// read-back half of external memory - checkpoint.go writes the record, verify.go
// proves it honest, and this turns it into the text a fresh agent actually
// reads.
//
// Two properties carry the whole design:
//
//  1. THE BODY IS DETERMINISTIC. No timestamps, no map iteration, no anything
//     that varies between two runs over identical state. `hydrate --check`
//     builds it twice and compares hashes, which is only a meaningful check
//     because the body is supposed to be reproducible. A bundle that differs
//     run-to-run cannot be diffed, cached, or trusted as evidence of what a
//     session was told.
//
//  2. IT REFUSES TO HYDRATE FROM A BROKEN CHAIN. Loading context out of a
//     plane that fails verification would launder tampered state into the next
//     agent's context as though it were established fact - the exact laundering
//     the chain exists to prevent.

const tokenChars = 4 // 1 token ~ 4 chars, per HYDRATION.md budget accounting

// budgets caps each section. Invariants and control are listed but never
// trimmed: HYDRATION.md fixes the order and says earlier sections are never
// trimmed, because a bundle that drops its own invariants is worse than one
// that drops detail.
var budgets = map[string]int{
	"invariants": 800, "control": 200, "intents": 1200,
	"distillate": 1600, "decisions": 800, "effects": 400,
}

// fit budgets a section: full form if it fits, else the spec's degrade-to
// form, else a hard clip of the degraded form. Every trim is RECORDED - a
// bundle that silently dropped half its content would read as complete.
func fit(section, full string, degraded *string, trimmed *[]string) string {
	limit := budgets[section] * tokenChars
	if len(full) <= limit {
		return full
	}
	*trimmed = append(*trimmed, section)
	text := full
	if degraded != nil {
		text = *degraded
	}
	if len(text) <= limit {
		return text
	}
	cut := text[:limit]
	if i := strings.LastIndex(cut, "\n"); i >= 0 {
		cut = cut[:i]
	}
	return cut + "\n[clipped]"
}

// pySplitLines matches Python's str.splitlines() for the terminators these
// files actually carry: CRLF, LF, and a lone CR - with no trailing empty
// element for a trailing newline.
//
// Splitting on "\n" alone is NOT equivalent, and the difference is not
// cosmetic. On a Windows checkout every line keeps its trailing "\r", so
// rejoining with "\n" reproduces CRLF where Python has stripped it - which
// made Go and Python emit DIFFERENT hydration bundles from identical state.
// The bundle is what the next agent believes, and its hash goes in the
// header, so that is an interop break rather than a formatting nit.
//
// Found by the hydration oracle, on a fixture written with Python's own text
// mode. The real repo's files happen to be LF, so the happy path matched and
// hid it.
func pySplitLines(s string) []string {
	if s == "" {
		return nil
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	s = strings.TrimSuffix(s, "\n")
	if s == "" {
		return []string{""}
	}
	return strings.Split(s, "\n")
}

func extractSections(md string, headings []string) string {
	var out []string
	keep := false
	for _, line := range pySplitLines(md) {
		if strings.HasPrefix(line, "## ") {
			keep = false
			for _, h := range headings {
				if strings.Contains(line, h) {
					keep = true
					break
				}
			}
		}
		if keep {
			out = append(out, line)
		}
	}
	return strings.TrimSpace(strings.Join(out, "\n"))
}

// stalePrefix marks an artifact recorded at a commit that is no longer HEAD.
//
// Staleness is FLAGGED, never hidden and never auto-refreshed: the next agent
// is told "this was true at commit X" and can judge for itself. Silently
// presenting old state as current is how a session acts confidently on a fact
// that stopped being true three commits ago.
func stalePrefix(artifactCommit, head string, stale *[]string, label string) string {
	if artifactCommit != "" && artifactCommit != head &&
		!strings.HasPrefix(head, artifactCommit) {
		*stale = append(*stale, label)
		return fmt.Sprintf("STALE@%s ", truncate12(artifactCommit))
	}
	return ""
}

func truncate12(s string) string {
	if len(s) > 12 {
		return s[:12]
	}
	return s
}

func str(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func arr(v any) []any {
	if a, ok := v.([]any); ok {
		return a
	}
	return nil
}

func obj(v any) map[string]any {
	if m, ok := v.(map[string]any); ok {
		return m
	}
	return nil
}

func readJSONFile(p string) (map[string]any, error) {
	raw, err := os.ReadFile(p)
	if err != nil {
		return nil, err
	}
	if int64(len(raw)) > maxStateFileBytes {
		return nil, fmt.Errorf("%s: exceeds the %d-byte state-file bound", p, maxStateFileBytes)
	}
	var m map[string]any
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, fmt.Errorf("%s: unparseable (%v)", p, err)
	}
	return m, nil
}

// buildBundleBody returns (body, trimmed, stale). Deterministic by
// construction: no timestamps, and every collection is walked in a fixed
// order.
func buildBundleBody(pl plane) (string, []string, []string, error) {
	cp, err := readJSONFile(pl.checkpoint)
	if err != nil {
		return "", nil, nil, err
	}
	head, _ := headCommit(pl.root)
	trimmed := []string{}
	stale := []string{}
	var parts []string

	// 1 invariants - never trimmed, sourced from REPO.md/ROLE.md else the
	// doctrine slice.
	var invParts []string
	for _, name := range []string{"REPO.md", "ROLE.md"} {
		if raw, err := os.ReadFile(filepath.Join(pl.root, name)); err == nil {
			invParts = append(invParts, extractSections(string(raw), []string{"Invariant"}))
		}
	}
	inv := strings.TrimSpace(strings.Join(invParts, "\n\n"))
	if inv == "" {
		if raw, err := os.ReadFile(filepath.Join(pl.root, ".Doctrine.md")); err == nil {
			inv = extractSections(string(raw), []string{"Prime Directive", "Non-Negotiables"})
		}
	}
	if inv == "" {
		inv = "(no invariant source found)"
	}
	parts = append(parts, "## Invariants\n"+inv)

	// 2 control - never trimmed; staleness flagged like any artifact
	control := obj(cp["control"])
	if control == nil {
		return "", nil, nil, fmt.Errorf("checkpoint has no control block")
	}
	prefix := stalePrefix(str(cp["at_commit"]), head, &stale, "control")
	var gates []string
	for _, g := range arr(control["gates_passed"]) {
		gates = append(gates, fmt.Sprintf("%v", g))
	}
	gatesStr := strings.Join(gates, ",")
	if gatesStr == "" {
		gatesStr = "-"
	}
	seqNum, _ := cp["seq"].(float64)
	parts = append(parts, fmt.Sprintf(
		"## Control\n%sseq=%d at_commit=%s worktree=%s role=%s phase=%s brevity=%s gates=%s",
		prefix, int(seqNum), truncate12(str(cp["at_commit"])), str(cp["worktree"]),
		str(control["role"]), str(control["phase"]), str(control["brevity_mode"]), gatesStr))

	// 3 active intents - degrade to titles + acceptance criteria only
	var fullLines, degLines []string
	activeIntents := arr(control["active_intents"])
	for _, intentAny := range activeIntents {
		intent := fmt.Sprintf("%v", intentAny)
		if !safeIDRe.MatchString(intent) {
			return "", nil, nil, fmt.Errorf("unsafe intent id %q", intent)
		}
		p := filepath.Join(pl.intents(), intent+".intent.json")
		data, err := readJSONFile(p)
		if err != nil {
			line := fmt.Sprintf("- %s: MISSING intent file", intent)
			fullLines = append(fullLines, line)
			degLines = append(degLines, line)
			continue
		}
		pre := stalePrefix(str(data["at_commit"]), head, &stale, "intent:"+intent)
		title := str(data["title"])
		if title == "" {
			title = intent
		}
		headLine := fmt.Sprintf("- %s**%s** - %s", pre, intent, title)
		var acLines []string
		for _, a := range arr(data["acceptance_criteria"]) {
			acLines = append(acLines, fmt.Sprintf("  - AC: %v", a))
		}
		degLines = append(degLines, headLine)
		degLines = append(degLines, acLines...)
		fullLines = append(fullLines, headLine)
		fullLines = append(fullLines, acLines...)
		for _, k := range []string{"description", "constraints"} {
			if v, ok := data[k]; ok {
				fullLines = append(fullLines, fmt.Sprintf("  - %s: %v", k, v))
			}
		}
	}
	empty := "(no active intents)"
	fullText, degText := strings.Join(fullLines, "\n"), strings.Join(degLines, "\n")
	if fullText == "" {
		fullText = empty
	}
	if degText == "" {
		degText = empty
	}
	parts = append(parts, "## Active intents\n"+fit("intents", fullText, &degText, &trimmed))

	// 4 distillate - latest, plus dead_ends merged from every retained file.
	// Degrades to dead_ends + open_threads ONLY: the anti-thought-drift
	// payload is what must survive a budget squeeze, because repeating a
	// known-failed approach is the expensive failure.
	dists := distillateFiles(pl)
	if len(dists) > 0 {
		d, err := readJSONFile(dists[len(dists)-1])
		if err != nil {
			return "", nil, nil, err
		}
		var mergedEnds []any
		seen := map[string]bool{}
		for i := len(dists) - 1; i >= 0; i-- { // newest first across ALL retained
			dd, err := readJSONFile(dists[i])
			if err != nil {
				return "", nil, nil, err
			}
			for _, e := range arr(dd["dead_ends"]) {
				m := obj(e)
				key := fmt.Sprintf("%v\x00%v", m["approach"], m["why_failed"])
				if !seen[key] {
					seen[key] = true
					mergedEnds = append(mergedEnds, e)
				}
			}
		}
		pre := stalePrefix(str(d["at_commit"]), head, &stale, "distillate")
		dseq, _ := d["seq"].(float64)
		core := []string{
			fmt.Sprintf("%s(distillate seq %d)", pre, int(dseq)),
			"Dead ends:",
		}
		for _, e := range mergedEnds {
			m := obj(e)
			core = append(core, fmt.Sprintf("- %v -> %v", m["approach"], m["why_failed"]))
		}
		core = append(core, "Open threads:")
		for _, t := range arr(d["open_threads"]) {
			core = append(core, fmt.Sprintf("- %v", t))
		}
		full := append([]string{}, core...)
		full = append(full, "Learned:")
		for _, i := range arr(d["learned"]) {
			m := obj(i)
			full = append(full, fmt.Sprintf("- [%v/%v] %v (evidence: %v)",
				m["kind"], m["confidence"], m["claim"], m["evidence"]))
		}
		full = append(full, "Next actions:")
		for _, n := range arr(d["next_actions"]) {
			full = append(full, fmt.Sprintf("- %v", n))
		}
		coreText := strings.Join(core, "\n")
		parts = append(parts, "## Distillate\n"+
			fit("distillate", strings.Join(full, "\n"), &coreText, &trimmed))
	} else {
		parts = append(parts, "## Distillate\n(no distillates)")
	}

	// 5 decisions - scoped to the active intents; degrade to ids + one line
	active := map[string]bool{}
	for _, i := range activeIntents {
		active[fmt.Sprintf("%v", i)] = true
	}
	fullLines, degLines = nil, nil
	if len(active) > 0 {
		if raw, err := os.ReadFile(pl.decisions); err == nil {
			if int64(len(raw)) > maxStateFileBytes {
				return "", nil, nil, fmt.Errorf("decisions log exceeds the %d-byte bound",
					maxStateFileBytes)
			}
			for n, line := range pySplitLines(string(raw)) {
				if strings.TrimSpace(line) == "" {
					continue
				}
				var entry map[string]any
				if err := json.Unmarshal([]byte(line), &entry); err != nil {
					// The ledger is hash-verified, so an unparseable line is
					// COMMITTED corruption, not a transient read error. Refuse
					// rather than skip: silently dropping a decision is how the
					// next session re-litigates something already settled.
					return "", nil, nil, fmt.Errorf(
						"decisions log line %d unparseable (%v) - the log is "+
							"hash-verified, so this is committed corruption", n+1, err)
				}
				match := false
				for _, i := range arr(entry["intents"]) {
					if active[fmt.Sprintf("%v", i)] {
						match = true
						break
					}
				}
				if !match {
					continue
				}
				eseq, _ := entry["seq"].(float64)
				claim := str(entry["claim"])
				fullLines = append(fullLines, fmt.Sprintf("- (seq %d) %s [%s]",
					int(eseq), claim, str(entry["evidence"])))
				short := claim
				if len(short) > 80 {
					short = short[:80]
				}
				degLines = append(degLines, fmt.Sprintf("- D%d: %s", int(eseq), short))
			}
		}
	}
	empty = "(no matching decisions)"
	if len(active) == 0 {
		empty = "(no active intents - decisions omitted)"
	}
	fullText, degText = strings.Join(fullLines, "\n"), strings.Join(degLines, "\n")
	if fullText == "" {
		fullText = empty
	}
	if degText == "" {
		degText = empty
	}
	parts = append(parts, "## Decisions\n"+fit("decisions", fullText, &degText, &trimmed))

	// 6 unresolved effects - degrade to count + most recent
	entries := unresolvedEffectEntries(pl)
	if len(entries) > 0 {
		full := []string{fmt.Sprintf("unresolved effects: %d", len(entries))}
		for _, e := range entries {
			full = append(full, fmt.Sprintf("- %s: %s",
				effectField(e, "status", "?"), clip80(effectAction(e))))
		}
		deg := fmt.Sprintf("unresolved effects: %d\nmost recent: %s",
			len(entries), clip80(effectAction(entries[len(entries)-1])))
		parts = append(parts, "## Unresolved effects\n"+
			fit("effects", strings.Join(full, "\n"), &deg, &trimmed))
	} else {
		parts = append(parts, "## Unresolved effects\nunresolved effects: 0")
	}

	return strings.Join(parts, "\n\n") + "\n", trimmed, stale, nil
}

func effectField(e map[string]any, key, fallback string) string {
	if v, ok := e[key]; ok {
		return fmt.Sprintf("%v", v)
	}
	return fallback
}

// effectAction mirrors Python's e.get('action', e.get('raw', ”)).
func effectAction(e map[string]any) string {
	if v, ok := e["action"]; ok {
		return fmt.Sprintf("%v", v)
	}
	if v, ok := e["raw"]; ok {
		return fmt.Sprintf("%v", v)
	}
	return ""
}

func clip80(s string) string {
	if len(s) > 80 {
		return s[:80]
	}
	return s
}

// unresolvedEffectEntries returns the entries themselves, where
// unresolvedEffectCount returns only how many. Both walk the same files in the
// same order; the count is used inside a checkpoint's state_index and the
// entries here, and they must never disagree.
func unresolvedEffectEntries(pl plane) []map[string]any {
	var entries []map[string]any
	dirEntries, err := os.ReadDir(pl.effects())
	if err != nil {
		return nil
	}
	var names []string
	for _, e := range dirEntries {
		if strings.HasSuffix(e.Name(), ".effects.ndjson") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	for _, name := range names {
		raw, err := os.ReadFile(filepath.Join(pl.effects(), name))
		if err != nil {
			continue
		}
		for _, line := range pySplitLines(string(raw)) {
			if strings.TrimSpace(line) == "" {
				continue
			}
			var entry map[string]any
			if json.Unmarshal([]byte(line), &entry) != nil {
				short := line
				if len(short) > 80 {
					short = short[:80]
				}
				entry = map[string]any{"status": "malformed", "raw": short}
			}
			status, _ := entry["status"].(string)
			if status != "confirmed" && status != "compensated" {
				entries = append(entries, entry)
			}
		}
	}
	return entries
}

func cmdHydrate(args []string) {
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		fmt.Fprintln(os.Stderr, "not a doctrine repo")
		os.Exit(2)
	}
	pl := newPlane(root)
	if !exists(pl.checkpoint) {
		if hasFlag(args, "if-present") {
			fmt.Println("no state plane checkpoint - nothing to hydrate")
			return
		}
		fmt.Fprintln(os.Stderr, "no checkpoint.json - run checkpoint first")
		os.Exit(1)
	}

	// Never hydrate from a broken chain. Loading context out of a plane that
	// fails verification would launder tampered state into the next agent's
	// context as established fact.
	findings, err := verifyFindings(pl)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(2)
	}
	if len(findings) > 0 {
		fmt.Fprintf(os.Stderr, "refusing to hydrate: chain verification failed "+
			"(%d finding(s); run verify)\n", len(findings))
		os.Exit(1)
	}

	body, trimmed, stale, err := buildBundleBody(pl)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	sha1 := sha256Hex([]byte(body))

	// --body emits the raw bundle body and nothing else. --check already
	// proves byte-equality via the hash, but a hash tells you THAT two bodies
	// differ, never WHERE - and a diff is what makes a mismatch fixable.
	if hasFlag(args, "body") {
		os.Stdout.WriteString(body)
		return
	}

	if hasFlag(args, "check") {
		body2, _, _, err := buildBundleBody(pl)
		if err != nil {
			fmt.Fprintln(os.Stderr, "error:", err)
			os.Exit(1)
		}
		if sha2 := sha256Hex([]byte(body2)); sha1 != sha2 {
			fmt.Printf("DETERMINISM FAILED: %s != %s\n", sha1[:12], sha2[:12])
			os.Exit(1)
		}
		fmt.Printf("hydrate --check OK: bundle_sha256 %s stable\n", sha1[:12])
		return
	}

	sort.Strings(stale)
	sort.Strings(trimmed)
	headerFields := map[string]any{
		"at_commit":     cpField(pl, "at_commit"),
		"bundle_sha256": sha1,
		"checkpoint_seq": func() any {
			cp, _ := readJSONFile(pl.checkpoint)
			return cp["seq"]
		}(),
		"stale":   toAnySlice(stale),
		"trimmed": toAnySlice(trimmed),
	}
	withGenerated := map[string]any{"generated_at": nowUTC()}
	for k, v := range headerFields {
		withGenerated[k] = v
	}
	header, err := canonicalLine(withGenerated)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	if err := os.MkdirAll(pl.local(), 0o755); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	out := filepath.Join(pl.local(), "hydration.bundle.md")
	content := fmt.Sprintf("<!-- doctrine:hydration %s -->\n\n%s", header, body)
	if err := os.WriteFile(out, []byte(content), 0o644); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	msg := fmt.Sprintf("bundle written: %s (%d tokens est., sha %s",
		out, len(body)/tokenChars, sha1[:12])
	if len(trimmed) > 0 {
		msg += ", trimmed: " + strings.Join(trimmed, ",")
	}
	if len(stale) > 0 {
		msg += ", STALE: " + strings.Join(stale, ",")
	}
	fmt.Println(msg + ")")
}

func cpField(pl plane, key string) any {
	cp, err := readJSONFile(pl.checkpoint)
	if err != nil {
		return nil
	}
	return cp[key]
}

func toAnySlice(ss []string) []any {
	out := make([]any, 0, len(ss))
	for _, s := range ss {
		out = append(out, s)
	}
	return out
}
