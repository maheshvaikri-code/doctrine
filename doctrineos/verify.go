package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// Chain verification: can a later session tell an honest record from an
// edited one?
//
// Ported from tools/doctrine_state.py's verify_findings. The assertions are
// deliberately identical, in the same order, because the differential oracle
// compares FINDINGS - a port that reaches the same verdict by a different
// route is a port that will drift.
//
// What this can and cannot prove is worth stating, because overclaiming here
// would be the exact defect the doctrine exists to prevent: the chain is
// TAMPER-EVIDENT, not tamper-proof. It catches a record edited after it was
// committed. It cannot catch a record forged and committed in one step -
// there is no prior state to diff against - which is why a release-bound
// merge still needs a human reading the diff.

var checkpointFileRe = regexp.MustCompile(`^(\d+)-[0-9a-f]{12}\.json$`)

type plane struct {
	root        string
	stateDir    string
	checkpoint  string // .doctrine-state/checkpoint.json
	checkpoints string // .doctrine-state/checkpoints/
	distillates string
	decisions   string
}

func newPlane(root string) plane {
	s := filepath.Join(root, ".doctrine-state")
	return plane{
		root:        root,
		stateDir:    s,
		checkpoint:  filepath.Join(s, "checkpoint.json"),
		checkpoints: filepath.Join(s, "checkpoints"),
		distillates: filepath.Join(s, "distillates"),
		decisions:   filepath.Join(s, "decisions", "DECISIONS.ndjson"),
	}
}

func exists(p string) bool { _, err := os.Stat(p); return err == nil }

func sha256File(p string) (string, error) {
	b, err := os.ReadFile(p)
	if err != nil {
		return "", err
	}
	return sha256Hex(b), nil
}

func seqOf(name string) int {
	m := checkpointFileRe.FindStringSubmatch(name)
	if m == nil {
		return -1
	}
	n, _ := strconv.Atoi(m[1])
	return n
}

// verifyFindings returns the same findings the Python implementation would,
// in the same order. Empty findings means the chain is intact.
//
// The error return is a DIFFERENT KIND OF ANSWER from a finding, and keeping
// them apart matters. A finding says "your chain is bad." An error says "I
// could not check." Reporting a missing schema as a finding - which this did
// at first - tells a reader their evidence has been tampered with when the
// real problem is an incomplete install, sending them to audit a chain that
// was never in question.
func verifyFindings(pl plane) ([]string, error) {
	var findings []string
	var files []string

	if exists(pl.checkpoints) {
		entries, _ := os.ReadDir(pl.checkpoints)
		names := make([]string, 0, len(entries))
		for _, e := range entries {
			names = append(names, e.Name())
		}
		sort.Strings(names)
		for _, name := range names {
			full := filepath.Join(pl.checkpoints, name)
			info, err := os.Stat(full)
			if err != nil {
				continue
			}
			// merge-archived fork heads live outside the linear chain
			if info.IsDir() && name == "forks" {
				continue
			}
			if checkpointFileRe.MatchString(name) {
				files = append(files, full)
			} else if name != ".gitignore" {
				kind := "file"
				if info.IsDir() {
					kind = "directory"
				}
				findings = append(findings, fmt.Sprintf("stray %s in checkpoints/: %s", kind, name))
			}
		}
	}
	sort.Slice(files, func(i, j int) bool {
		return seqOf(filepath.Base(files[i])) < seqOf(filepath.Base(files[j]))
	})

	// Fork detection BEFORE the linear walk. Two clones reunited by git
	// produce duplicate seq numbers; walking such a history linearly reports
	// a cascade of bogus "broken chain" findings that hide the real cause.
	bySeq := map[int][]string{}
	for _, f := range files {
		s := seqOf(filepath.Base(f))
		bySeq[s] = append(bySeq[s], filepath.Base(f))
	}
	var forkedSeqs []int
	for s, names := range bySeq {
		if len(names) > 1 {
			forkedSeqs = append(forkedSeqs, s)
		}
	}
	if len(forkedSeqs) > 0 {
		sort.Ints(forkedSeqs)
		for _, s := range forkedSeqs {
			names := bySeq[s]
			sort.Strings(names)
			findings = append(findings, fmt.Sprintf(
				"CHAIN FORKED at seq %d: %s - resolve with: doctrine_state merge --loser <file>",
				s, strings.Join(names, ", ")))
		}
		return findings, nil // a linear walk is meaningless on a fork
	}

	if exists(pl.checkpoint) && len(files) == 0 {
		return append(findings, "checkpoint.json exists but checkpoints/ history is empty - history wiped or never copied"), nil
	}
	if len(files) == 0 {
		return findings, nil // genuinely empty plane
	}

	// Load the schema ONCE, before the walk. A missing schema is fatal, not
	// a skip: the first Go port simply had no schema check, and every tamper
	// verdict still agreed - which is exactly how a verifier can look healthy
	// while validating less than its reference.
	schema, schemaErr := loadSchema(pl.root, "checkpoint")
	if schemaErr != nil {
		return nil, schemaErr
	}

	prevFile := ""
	for _, f := range files {
		base := filepath.Base(f)
		raw, err := os.ReadFile(f)
		if err != nil {
			findings = append(findings, fmt.Sprintf("%s: unreadable: %v", base, err))
			prevFile = f
			continue
		}
		var data map[string]any
		if err := json.Unmarshal(raw, &data); err != nil {
			findings = append(findings, fmt.Sprintf("%s: not valid JSON: %v", base, err))
			prevFile = f
			continue
		}
		if err := validateSchema(data, schema, schema, "$"); err != nil {
			findings = append(findings, fmt.Sprintf("%s: schema: %s", base, err.Error()))
		}
		expectedSeq := 0
		if prevFile != "" {
			expectedSeq = seqOf(filepath.Base(prevFile)) + 1
		}
		// Echo the RAW seq value, not a coerced one. A failed type assertion
		// yields 0, so a checkpoint carrying seq as the string "30" reported
		// `seq 0 != expected 30` here while Python reported `seq 30 != expected
		// 30`. Both refuse the record, so the differential oracle's verdicts
		// still agreed - but the Go message points the reader at a wrong number
		// and hides the actual defect, which is the type. Agreeing on the
		// verdict while disagreeing on the reason is how a port starts to drift.
		gotSeq, seqIsNum := data["seq"].(float64)
		if !seqIsNum || int(gotSeq) != expectedSeq {
			findings = append(findings, fmt.Sprintf("%s: seq %s != expected %d",
				base, formatJSONNumber(data["seq"]), expectedSeq))
		}
		// prev_sha256 is taken over the PREDECESSOR FILE's bytes, not over a
		// re-encoding of its parsed content. Hashing the re-encoding would
		// pass even when the stored file had been edited into non-canonical
		// form - which is precisely the tampering this is meant to catch.
		var expectedPrev any
		if prevFile != "" {
			h, err := sha256File(prevFile)
			if err == nil {
				expectedPrev = h
			}
		}
		gotPrev := data["prev_sha256"]
		if !sameNullableString(gotPrev, expectedPrev) {
			findings = append(findings, fmt.Sprintf(
				"%s: broken chain - prev_sha256 does not match predecessor's canonical bytes", base))
		}
		if canon, err := canonicalBytes(data); err != nil || string(raw) != string(canon) {
			findings = append(findings, fmt.Sprintf("%s: not canonical bytes", base))
		}
		prevFile = f
	}

	if !exists(pl.checkpoint) {
		return append(findings, "checkpoint.json missing while history exists"), nil
	}
	head, err1 := os.ReadFile(pl.checkpoint)
	tail, err2 := os.ReadFile(prevFile)
	if err1 != nil || err2 != nil || string(head) != string(tail) {
		return append(findings, "checkpoint.json != latest history copy"), nil
	}

	var current map[string]any
	if err := json.Unmarshal(head, &current); err != nil {
		return append(findings, "checkpoint.json is not valid JSON"), nil
	}
	idx, _ := current["state_index"].(map[string]any)
	if idx == nil {
		return append(findings, "checkpoint.json has no state_index"), nil
	}

	actualDecisions := sha256Hex(nil)
	if exists(pl.decisions) {
		if h, err := sha256File(pl.decisions); err == nil {
			actualDecisions = h
		}
	}
	if s, _ := idx["decisions_sha256"].(string); s != actualDecisions {
		findings = append(findings, "state_index.decisions_sha256 desync")
	}

	var latest any
	if ds := distillateFiles(pl); len(ds) > 0 {
		if h, err := sha256File(ds[len(ds)-1]); err == nil {
			latest = h
		}
	}
	if !sameNullableString(idx["latest_distillate_sha256"], latest) {
		findings = append(findings, "state_index.latest_distillate_sha256 desync")
	}
	return findings, nil
}

// formatJSONNumber renders a decoded JSON value the way Python's f-string
// would. encoding/json hands back every number as float64, and "%v" on
// float64(30) prints "30" - but float64(1e21) prints "1e+21" where Python
// prints the digits. Whole numbers are therefore formatted as integers, and
// anything that is not a number is printed as-is, which is what makes a
// string seq show up as itself rather than as a coerced zero.
func formatJSONNumber(v any) string {
	if f, ok := v.(float64); ok && f == math.Trunc(f) && math.Abs(f) < 1e15 {
		return strconv.FormatInt(int64(f), 10)
	}
	return fmt.Sprintf("%v", v)
}

// sameNullableString compares values that may legitimately be JSON null -
// the genesis checkpoint has prev_sha256: null, and an empty plane has no
// latest distillate. Treating null as "" would make a genesis record look
// like a broken link.
func sameNullableString(a, b any) bool {
	as, aok := a.(string)
	bs, bok := b.(string)
	if !aok && !bok {
		return true // both null/absent
	}
	return aok && bok && as == bs
}

var distillateRe = regexp.MustCompile(`^(\d+)-[0-9a-f]{12}\.json$`)

func distillateFiles(pl plane) []string {
	if !exists(pl.distillates) {
		return nil
	}
	entries, _ := os.ReadDir(pl.distillates)
	var out []string
	for _, e := range entries {
		if !e.IsDir() && distillateRe.MatchString(e.Name()) {
			out = append(out, filepath.Join(pl.distillates, e.Name()))
		}
	}
	sort.Slice(out, func(i, j int) bool {
		return seqOf(filepath.Base(out[i])) < seqOf(filepath.Base(out[j]))
	})
	return out
}

func cmdVerify() {
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		fmt.Println("not a doctrine repo")
		os.Exit(1)
	}
	pl := newPlane(root)
	findings, err := verifyFindings(pl)
	if err != nil {
		// Exit 2, not 1. Exit 1 means "I checked and the chain is bad"; exit 2
		// means "I could not check at all". An agent reading only the exit code
		// must be able to tell those apart, and it matches the Python CLI.
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(2)
	}
	if len(findings) > 0 {
		fmt.Printf("VERIFY FAILED (%d):\n", len(findings))
		for _, f := range findings {
			fmt.Println("  -", f)
		}
		os.Exit(1)
	}
	n := 0
	if exists(pl.checkpoints) {
		entries, _ := os.ReadDir(pl.checkpoints)
		for _, e := range entries {
			if checkpointFileRe.MatchString(e.Name()) {
				n++
			}
		}
	}
	if n == 0 {
		fmt.Println("nothing to verify: no checkpoints")
	} else {
		fmt.Printf("verify OK: %d checkpoint(s), chain intact, state_index hashes match\n", n)
	}
}
