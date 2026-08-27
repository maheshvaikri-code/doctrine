package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"unicode/utf8"
)

// TestThresholdRule is the load-bearing test of this project.
//
// The whole activation design rests on one claim: a signal may only auto-fire
// a resource whose cost is proportional to that signal's reliability. A weak
// signal (intent inferred from task text) may put a file in context; it may
// NOT make the agent adopt a lens, compose a domain overlay, dispatch agents,
// or refuse a write. If this test ever goes green while the rule is broken,
// the engine silently becomes v1's "the model decides" with extra steps.
func TestThresholdRule(t *testing.T) {
	skill := Resource{Name: "database", Path: "skills/database.md", Cost: CostRead,
		On: []string{"path:migrations/**", "intent:migration"}}
	lens := Resource{Name: "database-lens", Path: "lenses/database.md", Cost: CostAdopt,
		On: []string{"path:migrations/**", "intent:migration"}}
	refuse := Resource{Name: "danger", Path: "x.md", Cost: CostRefuse,
		On: []string{"intent:delete"}}
	res := []Resource{skill, lens, refuse}

	cases := []struct {
		name      string
		tc        TaskContext
		wantFired map[string]bool
	}{
		{
			name:      "deterministic path fires BOTH read and adopt",
			tc:        TaskContext{Paths: []string{"migrations/0007.sql"}},
			wantFired: map[string]bool{"database": true, "database-lens": true},
		},
		{
			name:      "weak intent fires the READ but NOT the adopt",
			tc:        TaskContext{Task: "add a column via a migration"},
			wantFired: map[string]bool{"database": true, "database-lens": false},
		},
		{
			name:      "weak intent can NEVER fire a refusal",
			tc:        TaskContext{Task: "please delete the old rows"},
			wantFired: map[string]bool{"danger": false},
		},
		{
			name:      "unrelated task fires nothing at all",
			tc:        TaskContext{Task: "update the README wording"},
			wantFired: map[string]bool{"database": false, "database-lens": false},
		},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := map[string]bool{}
			for _, a := range Resolve(res, c.tc) {
				got[a.Resource.Name] = true
			}
			for name, want := range c.wantFired {
				if got[name] != want {
					t.Errorf("%s: fired=%v want=%v", name, got[name], want)
				}
			}
		})
	}
}

// TestActivationExplainsItself - an engine that cannot say WHY it fired is an
// engine nobody will leave switched on, because a wrong trigger becomes a
// mystery instead of a diagnosis.
func TestActivationExplainsItself(t *testing.T) {
	res := []Resource{{Name: "db", Cost: CostRead, On: []string{"path:migrations/**"}}}
	fired := Resolve(res, TaskContext{Paths: []string{"migrations/0007.sql"}})
	if len(fired) != 1 {
		t.Fatalf("expected 1 activation, got %d", len(fired))
	}
	if fired[0].Why == "" {
		t.Error("activation carries no reason")
	}
	if fired[0].Signal != "path:migrations/**" {
		t.Errorf("signal not recorded: %q", fired[0].Signal)
	}
}

func TestMatchGlob(t *testing.T) {
	cases := []struct {
		pattern, path string
		want          bool
	}{
		{"migrations/**", "migrations/0007.sql", true},
		{"migrations/**", "migrations/sub/deep.sql", true},
		{"migrations/**", "migrations", true}, // the dir itself, not only children
		{"migrations/**", "src/migrations.go", false},
		{"**/*.sql", "db/schema.sql", true},
		{"**/auth/**", "src/auth/login.go", true},
		{".env*", ".env.local", true},
		{".env*", "env.local", false},
	}
	for _, c := range cases {
		if got := matchGlob(c.pattern, c.path); got != c.want {
			t.Errorf("matchGlob(%q,%q)=%v want %v", c.pattern, c.path, got, c.want)
		}
	}
}

// TestProtectedMatches guards the clause that exists because matching only
// children once let `rm -rf docs/releases/gold` remove every record while
// each individual file was "protected".
func TestProtectedMatches(t *testing.T) {
	cases := []struct {
		rel, pattern string
		want         bool
	}{
		{"docs/releases/gold/v1.json", "docs/releases/gold/*", true},
		{"docs/releases/gold", "docs/releases/gold/*", true}, // the directory itself
		{"docs/releases/notes.md", "docs/releases/gold/*", false},
		{"services/api/.env", "**/.env", true},
		{".doctrine-state/checkpoint.json", ".doctrine-state/checkpoint.json", true},
	}
	for _, c := range cases {
		if got := matches(c.rel, c.pattern); got != c.want {
			t.Errorf("matches(%q,%q)=%v want %v", c.rel, c.pattern, got, c.want)
		}
	}
}

// Fixtures are ASSEMBLED at runtime, never written as literals. The v1 guard
// refused an earlier draft of this file for containing a private-key marker -
// a correct refusal on a test fixture, and the cheapest fix is to not put the
// literal in the repo at all.
func TestSecretPatterns(t *testing.T) {
	hits := []string{
		"AKIA" + "IOSFODNN7EXAMPLE",
		"ghp_" + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		"sk-ant-" + "aaaaaaaaaaaaaaaaaaaaaa",
		"-----BEGIN " + "RSA PRIVATE" + " KEY-----",
	}
	for _, h := range hits {
		found := false
		for _, s := range secretPatterns {
			if s.re.MatchString("value = " + h) {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("credential not detected: %.14s...", h)
		}
	}
	misses := []string{"API_KEY=", "password: see the vault", "sk-short", "AKIA123"}
	for _, m := range misses {
		for _, s := range secretPatterns {
			if s.re.MatchString(m) {
				t.Errorf("false positive on %q via %s", m, s.what)
			}
		}
	}
}

// TestGateDoneFailsOpen - the Stop gate closes the mid-workflow band, but a
// gate that blocks a session it cannot reason about is worse than the gap.
func TestGateDoneFailsOpen(t *testing.T) {
	root := t.TempDir()
	if m := gateDone(root, "S", "anything"); m != nil {
		t.Errorf("S-class owes no artifact, got %v", m)
	}
	if m := gateDone(root, "", "anything"); m != nil {
		t.Errorf("unclassified owes no artifact, got %v", m)
	}
	if m := gateDone(root, "M", ""); m != nil {
		t.Errorf("no task name -> cannot reason -> must fail open, got %v", m)
	}
}

func TestGateDoneBlocksMissingEvidence(t *testing.T) {
	root := t.TempDir()
	missing := gateDone(root, "M", "add-column")
	if len(missing) != 2 {
		t.Fatalf("expected both review and qa missing, got %v", missing)
	}
	os.MkdirAll(filepath.Join(root, "docs", "reviews"), 0o755)
	os.WriteFile(filepath.Join(root, "docs", "reviews", "add-column.md"), []byte("ok"), 0o644)
	missing = gateDone(root, "M", "add-column")
	if len(missing) != 1 || missing[0] != "docs/qa/add-column.md" {
		t.Fatalf("expected only qa outstanding, got %v", missing)
	}
	os.MkdirAll(filepath.Join(root, "docs", "qa"), 0o755)
	os.WriteFile(filepath.Join(root, "docs", "qa", "add-column.md"), []byte("ok"), 0o644)
	if m := gateDone(root, "M", "add-column"); m != nil {
		t.Fatalf("evidence complete, gate should pass, got %v", m)
	}
}

func TestParseConfig(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "doctrine.toml")
	os.WriteFile(p, []byte(`
# a comment
[doctrine]
version = "0.8.0"
sha256  = "abc123"   # trailing comment

[packs]
enable = ["core", "security-operations"]

[profile]
delivery = "solobuilder"

[unknown-future-section]
some-new-key = "must not break an older binary"
`), 0o644)
	cfg, err := ParseConfig(p)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Version != "0.8.0" || cfg.SHA256 != "abc123" {
		t.Errorf("pin not parsed: %+v", cfg)
	}
	if len(cfg.Packs) != 2 || cfg.Packs[1] != "security-operations" {
		t.Errorf("packs not parsed: %v", cfg.Packs)
	}
	if cfg.Deliver != "solobuilder" {
		t.Errorf("profile not parsed: %q", cfg.Deliver)
	}
}

// TestFrontmatterContract - a resource with no [activate] contract must be
// reported as unreachable rather than silently existing. That is the defect
// class where three skills sat in the corpus for weeks, routed from nowhere.
func TestFrontmatterContract(t *testing.T) {
	dir := t.TempDir()
	good := filepath.Join(dir, "good.md")
	os.WriteFile(good, []byte("---\non: [\"path:x/**\"]\ncost: read\n---\n\n# Good\n"), 0o644)
	bad := filepath.Join(dir, "bad.md")
	os.WriteFile(bad, []byte("# No contract at all\n"), 0o644)

	if _, ok := parseFrontmatter(good); !ok {
		t.Error("a declared contract was not parsed")
	}
	if _, ok := parseFrontmatter(bad); ok {
		t.Error("a resource with NO contract must not be treated as activatable")
	}
	if got := len(LoadResources(dir)); got != 1 {
		t.Errorf("LoadResources found %d, want 1 (the contract-less file must be excluded)", got)
	}
}

// TestVerifySeparatesCannotRunFromFindings pins a distinction that is easy to
// collapse and expensive to get wrong.
//
// A FINDING says "your chain is bad." An ERROR says "I could not check." The
// first version of the schema wiring returned the missing schema as a finding,
// so an incomplete install rendered as `VERIFY FAILED (1)` - telling a reader
// their evidence had been tampered with and sending them to audit a chain that
// was never in question.
func TestVerifySeparatesCannotRunFromFindings(t *testing.T) {
	root := t.TempDir()
	pl := newPlane(root)

	// An empty plane has nothing to check and owes no error: there are no
	// checkpoints, so the schema is never needed.
	findings, err := verifyFindings(pl)
	if err != nil {
		t.Fatalf("empty plane must not error, got %v", err)
	}
	if len(findings) != 0 {
		t.Fatalf("empty plane must report no findings, got %v", findings)
	}

	// One checkpoint present, but no schema installed: that is cannot-run.
	cps := filepath.Join(root, ".doctrine-state", "checkpoints")
	if err := os.MkdirAll(cps, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(cps, "0-0123456789ab.json"),
		[]byte("{}\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	findings, err = verifyFindings(pl)
	if err == nil {
		t.Fatal("missing schema must be an error, not a finding")
	}
	if findings != nil {
		t.Fatalf("cannot-run must return no findings, got %v", findings)
	}
	if !strings.Contains(err.Error(), ".Doctrine/") {
		t.Errorf("error should point at the likely cause (install), got %q", err)
	}
}

// TestSchemaMessagesMatchPythonRepr guards the formatting the differential
// oracle compares. Verdicts agreeing is not enough: two tools that refuse the
// same record while describing it differently teach a reader to trust neither.
func TestSchemaMessagesMatchPythonRepr(t *testing.T) {
	for _, c := range []struct{ in, want string }{
		{"clean", "'clean'"},
		{"it's", `"it's"`},
		{"", "''"},
	} {
		if got := pyRepr(c.in); got != c.want {
			t.Errorf("pyRepr(%q) = %s, want %s", c.in, got, c.want)
		}
	}
	if got := pyRepr(true); got != "True" {
		t.Errorf("pyRepr(true) = %s, want True", got)
	}
	if got := pyRepr(nil); got != "None" {
		t.Errorf("pyRepr(nil) = %s, want None", got)
	}
	if got := pyRepr(float64(30)); got != "30" {
		t.Errorf("pyRepr(30.0) = %s, want 30 (not 30.0)", got)
	}
	if got := pyReprList([]any{"clean", "dirty"}); got != "['clean', 'dirty']" {
		t.Errorf("pyReprList = %s", got)
	}
}

// TestJSONEqualIsTypeAware pins the fix for a bug that LOOSENED the schema.
// Comparing fmt.Sprintf("%v", ...) made the number 1 equal to the string "1",
// so an enum of integers silently accepted strings - a validator accepting
// more than its schema allows, while reporting success.
func TestJSONEqualIsTypeAware(t *testing.T) {
	if jsonEqual(float64(1), "1") {
		t.Error("number 1 must not equal string \"1\"")
	}
	if jsonEqual(true, float64(1)) {
		t.Error("bool must not equal number")
	}
	if !jsonEqual(float64(1), float64(1)) || !jsonEqual("a", "a") || !jsonEqual(nil, nil) {
		t.Error("like values must compare equal")
	}
}

// TestStringLengthCountsRunesNotBytes pins a divergence found by READING the
// reference, not by running the oracle - none of its cases were non-ASCII.
//
// Python's len() on a str counts characters; Go's len() on a string counts
// bytes. They agree only while the input is ASCII, and disagree in opposite
// directions depending on which bound is checked: byte count >= rune count, so
// Go was too permissive on minLength and too strict on maxLength.
func TestStringLengthCountsRunesNotBytes(t *testing.T) {
	// "café" - 4 characters, 5 bytes. Python sees 4.
	const s = "caf\u00e9"
	if len(s) != 5 || utf8.RuneCountInString(s) != 4 {
		t.Fatalf("fixture assumption broken: %d bytes, %d runes",
			len(s), utf8.RuneCountInString(s))
	}

	// minLength 5 must REJECT a 4-character string, even though it is 5 bytes.
	schema := map[string]any{"type": "string", "minLength": float64(5)}
	if err := validateSchema(s, schema, schema, "$"); err == nil {
		t.Error("minLength 5 must reject a 4-character string (byte count would accept)")
	}
	// maxLength 4 must ACCEPT it, even though it is 5 bytes.
	schema = map[string]any{"type": "string", "maxLength": float64(4)}
	if err := validateSchema(s, schema, schema, "$"); err != nil {
		t.Errorf("maxLength 4 must accept a 4-character string, got %v", err)
	}
}

// TestHashedRefRefusesEmptyEvidence pins the rule the gold ladder exists for:
// EXISTENCE IS NOT EVIDENCE. A gate written as "the sign-off is present"
// passes on `touch security-signoff.md`, so the pin is over CONTENT.
func TestHashedRefRefusesEmptyEvidence(t *testing.T) {
	root := t.TempDir()
	write := func(name, content string) string {
		p := filepath.Join(root, name)
		if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
		return name
	}

	if _, err := hashedRef(root, write("good.md", "approved by security\n"), "sign-off"); err != nil {
		t.Errorf("real content must pin, got %v", err)
	}
	for _, c := range []struct{ name, content string }{
		{"empty.md", ""},
		{"spaces.md", "   \n\t\n"},
	} {
		_, err := hashedRef(root, write(c.name, c.content), "sign-off")
		if err == nil {
			t.Errorf("%s: an empty file is not a sign-off", c.name)
		} else if !strings.Contains(err.Error(), "not a sign-off") {
			t.Errorf("%s: unexpected message %q", c.name, err)
		}
	}
	if _, err := hashedRef(root, "absent.md", "sign-off"); err == nil {
		t.Error("absent file must be refused")
	}
}

// TestSafeRepoPathRefusesEscapes - a gold record names its own evidence, so
// those names are untrusted input. Without this, a record could pin (and
// appear to verify against) a file outside the repo entirely.
func TestSafeRepoPathRefusesEscapes(t *testing.T) {
	root := t.TempDir()
	for _, rel := range []string{"../outside.md", "../../etc/passwd", ".." + string(filepath.Separator)} {
		if _, err := safeRepoPath(root, rel, "sign-off"); err == nil {
			t.Errorf("%q must be refused as an escape", rel)
		}
	}
	for _, rel := range []string{"docs/x.md", "a/b/c.json", "."} {
		if _, err := safeRepoPath(root, rel, "sign-off"); err != nil {
			t.Errorf("%q is inside the repo, got %v", rel, err)
		}
	}
	// "..foo" starts with ".." but does not escape - a prefix test written as
	// strings.HasPrefix(rel, "..") would wrongly refuse it.
	if _, err := safeRepoPath(root, "..foo", "sign-off"); err != nil {
		t.Errorf("'..foo' is an ordinary name, got %v", err)
	}
}

// TestLoadChainTopology pins the invariants that make the ladder a ladder.
// Each loose alternative has a way to hide a record.
func TestLoadChainTopology(t *testing.T) {
	rec := func(prev any) []byte {
		b, _ := canonicalBytes(map[string]any{"tag": "v", "prev_gold_sha256": prev})
		return b
	}
	build := func(t *testing.T, files map[string][]byte) string {
		root := t.TempDir()
		gold := filepath.Join(root, "docs", "releases", "gold")
		if err := os.MkdirAll(gold, 0o755); err != nil {
			t.Fatal(err)
		}
		for name, data := range files {
			if err := os.WriteFile(filepath.Join(gold, name), data, 0o644); err != nil {
				t.Fatal(err)
			}
		}
		return root
	}

	genesis := rec(nil)
	child := rec(sha256Hex(genesis))

	t.Run("linear chain is ordered", func(t *testing.T) {
		root := build(t, map[string][]byte{"v1.0.0.json": genesis, "v1.1.0.json": child})
		got, err := loadChain(root)
		if err != nil {
			t.Fatal(err)
		}
		if len(got) != 2 || filepath.Base(got[0]) != "v1.0.0.json" {
			t.Fatalf("chain not ordered from genesis: %v", got)
		}
	})
	t.Run("two roots refused", func(t *testing.T) {
		root := build(t, map[string][]byte{"a.json": genesis, "b.json": rec(nil)})
		if _, err := loadChain(root); err == nil {
			t.Error("two genesis records must be refused")
		}
	})
	t.Run("fork refused", func(t *testing.T) {
		// Two DISTINCT records claiming the same predecessor.
		other, _ := canonicalBytes(map[string]any{"tag": "w", "prev_gold_sha256": sha256Hex(genesis)})
		root := build(t, map[string][]byte{
			"v1.0.0.json": genesis, "v1.1.0.json": child, "v1.2.0.json": other})
		_, err := loadChain(root)
		if err == nil || !strings.Contains(err.Error(), "fork") {
			t.Errorf("fork must be refused, got %v", err)
		}
	})
	t.Run("unparseable refused as unparseable, not as a broken chain", func(t *testing.T) {
		root := build(t, map[string][]byte{"v1.0.0.json": genesis, "bad.json": []byte("{not json")})
		_, err := loadChain(root)
		if err == nil {
			t.Fatal("a corrupt record must be refused")
		}
		if !strings.Contains(err.Error(), "unparseable") {
			t.Errorf("a corrupt file must not be reported as a chain defect: %v", err)
		}
	})
	t.Run("MANIFEST.json is not a link", func(t *testing.T) {
		root := build(t, map[string][]byte{
			"v1.0.0.json": genesis, "MANIFEST.json": []byte(`{"anchor":true}`)})
		got, err := loadChain(root)
		if err != nil || len(got) != 1 {
			t.Errorf("the deletion anchor must be skipped, got %v / %v", got, err)
		}
	})
}
