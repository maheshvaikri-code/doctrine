package main

import (
	"os"
	"path/filepath"
	"testing"
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
