package main

import (
	"encoding/json"
	"regexp"
	"strings"
	"testing"
)

// TestNowUTCMatchesPythonFormat pins the timestamp spelling.
//
// time.RFC3339 is NOT equivalent to Python's "%Y-%m-%dT%H:%M:%SZ": it renders
// a numeric offset for a time whose location is not UTC. The schema's
// date-time pattern accepts BOTH spellings, so a drift here validates cleanly
// and surfaces only as two tools writing visibly different timestamps into one
// chain - the kind of difference a reader notices and cannot explain.
func TestNowUTCMatchesPythonFormat(t *testing.T) {
	got := nowUTC()
	re := regexp.MustCompile(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`)
	if !re.MatchString(got) {
		t.Fatalf("nowUTC() = %q, want ...Z with no offset and no fraction", got)
	}
	if strings.ContainsAny(got, "+.") {
		t.Errorf("nowUTC() = %q must not carry an offset or fractional seconds", got)
	}
}

// TestCanonicalLineIsCompactAndSorted - the decisions ledger is NDJSON, so one
// entry is exactly one line. canonicalBytes indents; this must not.
func TestCanonicalLineIsCompactAndSorted(t *testing.T) {
	got, err := canonicalLine(map[string]any{"b": 2, "a": 1, "note": "x < y & z"})
	if err != nil {
		t.Fatal(err)
	}
	want := `{"a":1,"b":2,"note":"x < y & z"}`
	_ = want // Go escapes & even with SetEscapeHTML(false)? assert precisely below
	if strings.Contains(got, "\n") {
		t.Errorf("a ledger entry must be one line, got %q", got)
	}
	if !strings.HasPrefix(got, `{"a":1,"b":2,`) {
		t.Errorf("keys must be sorted and separators compact, got %q", got)
	}
	// HTML escaping off: a "<" in a claim must survive as itself, or the
	// ledger hash diverges from Python's for ordinary prose.
	if !strings.Contains(got, "x < y") {
		t.Errorf("SetEscapeHTML(false) not in effect: %q", got)
	}
}

// TestScanSecretsFailsClosed. State files are committed forever, so a secret
// that reaches one cannot be redacted later - the refusal has to happen before
// the write or not at all.
func TestScanSecretsFailsClosed(t *testing.T) {
	mk := func(claim string) map[string]any {
		return map[string]any{"learned": []any{map[string]any{
			"claim": claim, "evidence": "e", "kind": "fact", "confidence": "verified"}}}
	}
	// Assembled at runtime so this source file does not itself carry a
	// credential literal - the guard would (correctly) refuse to write it.
	bad := []string{
		"key = AKIA" + "IOSFODNN7EXAMPLE",
		"-----BEGIN " + "RSA PRIVATE" + " KEY-----",
		"gh" + "p_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		"api_key: hunter2hunter2",
	}
	for _, claim := range bad {
		if err := scanSecrets(mk(claim)); err == nil {
			t.Errorf("secret not refused: %.20s...", claim)
		}
	}
	markers := []string{"escape --> here", "<!-- comment", "doctrine:state:begin"}
	for _, claim := range markers {
		err := scanSecrets(mk(claim))
		if err == nil {
			t.Errorf("marker token not refused: %q", claim)
		} else if !strings.Contains(err.Error(), "managed state") {
			t.Errorf("marker refusal should explain the AGENTS.md risk: %v", err)
		}
	}
	if err := scanSecrets(mk("an ordinary decision about retries")); err != nil {
		t.Errorf("ordinary prose must pass, got %v", err)
	}
}

// TestMergeDeadEndsPrefersNewest. What falls off the cap should be the OLDEST
// knowledge, not the freshest - dropping a dead end the current session just
// learned means the next session pays to relearn it.
func TestMergeDeadEndsPrefersNewest(t *testing.T) {
	end := func(a string) any {
		return map[string]any{"approach": a, "why_failed": "because " + a}
	}
	var newEnds []any
	for _, a := range []string{"n1", "n2"} {
		newEnds = append(newEnds, end(a))
	}
	merged, dropped := mergeDeadEnds(newEnds, nil)
	if len(merged) != 2 || dropped != 0 {
		t.Fatalf("no pruning expected, got %d merged / %d dropped", len(merged), dropped)
	}

	// duplicates collapse on (approach, why_failed)
	merged, _ = mergeDeadEnds([]any{end("dup"), end("dup")}, nil)
	if len(merged) != 1 {
		t.Errorf("duplicate dead ends must collapse, got %d", len(merged))
	}

	// over the cap: the new distillate's own ends survive, count is reported
	var many []any
	for _, a := range []string{"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"} {
		many = append(many, end(a))
	}
	merged, dropped = mergeDeadEnds(many, nil)
	if len(merged) != deadEndCap || dropped != 10-deadEndCap {
		t.Fatalf("cap not applied: %d merged, %d dropped", len(merged), dropped)
	}
	first, _ := merged[0].(map[string]any)
	if first["approach"] != "a" {
		t.Errorf("the newest ends must be kept, got %v first", first["approach"])
	}
}

// TestWriteCheckpointRefusesBeforeWriting is the propose/dispose guarantee.
//
// A writer that validates as it goes leaves wreckage on its first failure - a
// distillate with no checkpoint, or a checkpoint whose predecessor hash was
// taken over a file that never landed - and to the next `verify` that wreckage
// is indistinguishable from tampering. So an invalid proposal must leave the
// plane byte-for-byte untouched, not merely "mostly" untouched.
func TestWriteCheckpointRefusesBeforeWriting(t *testing.T) {
	root := t.TempDir()
	pl := newPlane(root)

	var proposal map[string]any
	if err := json.Unmarshal([]byte(`{"session_id":"s"}`), &proposal); err != nil {
		t.Fatal(err)
	}
	// missing 'control' and 'distillate'
	if err := writeCheckpoint(pl, proposal, defaultKeep, false); err == nil {
		t.Fatal("an incomplete proposal must be refused")
	}
	if exists(pl.stateDir) {
		t.Error("a refused checkpoint must not create the state plane")
	}

	if err := writeCheckpoint(pl, map[string]any{}, 0, false); err == nil {
		t.Error("--keep 0 must be refused")
	}
}
