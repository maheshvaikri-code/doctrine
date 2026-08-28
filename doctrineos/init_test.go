package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestSyncTreeIsHonestAboutWhatItDid.
//
// The previous implementation rewrote every file on every run and reported
// "materialised (N files)" either way. An agent could not tell a fresh install
// from a no-op - in the one step of init that was not honest about skipping,
// while every other step said "exists, left alone" or "already wired".
func TestSyncTreeIsHonestAboutWhatItDid(t *testing.T) {
	src, dst := t.TempDir(), filepath.Join(t.TempDir(), "corpus")
	write := func(dir, rel, body string) {
		p := filepath.Join(dir, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write(src, "skills/a.md", "alpha")
	write(src, "roles/b.md", "beta")

	// first run: everything is new
	st, err := syncTree(src, dst, false)
	if err != nil {
		t.Fatal(err)
	}
	if st.written != 2 || st.updated != 0 || st.identical != 0 {
		t.Fatalf("first run: %+v, want 2 written", st)
	}
	if !strings.Contains(st.summary(), "materialised (2 files)") {
		t.Errorf("first run summary = %q", st.summary())
	}

	// second run: nothing changed, so nothing may be rewritten
	st, err = syncTree(src, dst, false)
	if err != nil {
		t.Fatal(err)
	}
	if st.written != 0 || st.updated != 0 || st.identical != 2 {
		t.Fatalf("re-run must be a no-op, got %+v", st)
	}
	if !strings.Contains(st.summary(), "all current") {
		t.Errorf("a re-run must say so, got %q", st.summary())
	}

	// a changed source file is updated, and only that one
	write(src, "skills/a.md", "alpha v2")
	st, err = syncTree(src, dst, false)
	if err != nil {
		t.Fatal(err)
	}
	if st.updated != 1 || st.identical != 1 || st.written != 0 {
		t.Fatalf("one file changed, got %+v", st)
	}
	got, _ := os.ReadFile(filepath.Join(dst, "skills", "a.md"))
	if string(got) != "alpha v2" {
		t.Errorf("changed file not updated: %q", got)
	}
}

// TestSyncTreeReportsStaleFiles.
//
// This is a CORRECTNESS check, not tidiness: LoadResources walks the corpus
// directory and activates every .md carrying frontmatter, so a file left
// behind by an older version still fires. The repo would be running resources
// its pinned version does not ship, and nothing would say so.
func TestSyncTreeReportsStaleFiles(t *testing.T) {
	src, dst := t.TempDir(), filepath.Join(t.TempDir(), "corpus")
	if err := os.MkdirAll(filepath.Join(src, "skills"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(src, "skills", "keep.md"), []byte("k"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := syncTree(src, dst, false); err != nil {
		t.Fatal(err)
	}

	// a resource the current version does not ship
	leftover := filepath.Join(dst, "skills", "removed-in-this-version.md")
	if err := os.WriteFile(leftover, []byte("stale"), 0o644); err != nil {
		t.Fatal(err)
	}

	st, err := syncTree(src, dst, false)
	if err != nil {
		t.Fatal(err)
	}
	if len(st.stale) != 1 || st.stale[0] != "skills/removed-in-this-version.md" {
		t.Fatalf("stale file not reported: %+v", st.stale)
	}
	if _, err := os.Stat(leftover); err != nil {
		t.Error("stale files must NOT be deleted without --prune")
	}

	// --prune deletes exactly those, and nothing else
	st, err = syncTree(src, dst, true)
	if err != nil {
		t.Fatal(err)
	}
	if len(st.stale) != 0 {
		t.Errorf("--prune must clear the stale list, got %v", st.stale)
	}
	if _, err := os.Stat(leftover); !os.IsNotExist(err) {
		t.Error("--prune must delete the stale file")
	}
	if _, err := os.Stat(filepath.Join(dst, "skills", "keep.md")); err != nil {
		t.Error("--prune must not touch current files")
	}
}

// TestHooksWireTheActivationEngine.
//
// `init` wired `check` and `gate --done` but nothing that calls `context`, so
// a governed repo materialised a corpus no turn ever consulted - an activation
// model with no activation. This pins all three, and pins the merge behaviour
// that keeps a consumer's own hooks intact.
func TestHooksWireTheActivationEngine(t *testing.T) {
	root := t.TempDir()

	// a repo that already has its own unrelated hook
	claude := filepath.Join(root, ".claude")
	if err := os.MkdirAll(claude, 0o755); err != nil {
		t.Fatal(err)
	}
	existing := `{"hooks":{"PostToolUse":[{"matcher":"Write","hooks":[{"type":"command","command":"my-formatter"}]}]}}`
	if err := os.WriteFile(filepath.Join(claude, "settings.json"), []byte(existing), 0o644); err != nil {
		t.Fatal(err)
	}

	if err := ensureHooks(root); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(claude, "settings.json"))
	if err != nil {
		t.Fatal(err)
	}
	got := string(b)

	for _, want := range []string{
		"doctrineos check",          // PreToolUse - refusal
		"doctrineos gate --done",    // Stop - definition of done
		"doctrineos context --hook", // UserPromptSubmit - ACTIVATION
		"UserPromptSubmit",
		"my-formatter", // the consumer's own hook must survive
	} {
		if !strings.Contains(got, want) {
			t.Errorf("settings.json missing %q", want)
		}
	}

	// idempotent: a second init must not duplicate the wiring
	if err := ensureHooks(root); err != nil {
		t.Fatal(err)
	}
	b2, _ := os.ReadFile(filepath.Join(claude, "settings.json"))
	if strings.Count(string(b2), "doctrineos context --hook") != 1 {
		t.Error("re-running init duplicated the activation hook")
	}
}
