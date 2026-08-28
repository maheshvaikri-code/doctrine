package main

import (
	"os"
	"path/filepath"
	"testing"
)

// TestProvidesSeparatesRolesFromLenses.
//
// Roles and lenses BOTH cost `adopt`, but they compose differently: lenses
// stack (each adds load paths and narrows write scope), while roles are worn
// one at a time and announced (02-role-protocol). Emitting both under a single
// "adopt" list is an instruction to put on four hats at once.
//
// `provides` was in the activation spec from the start and simply was not
// parsed, so every resource was implicitly a skill and the distinction was
// unrepresentable.
func TestProvidesSeparatesRolesFromLenses(t *testing.T) {
	dir := t.TempDir()
	write := func(name, front string) {
		p := filepath.Join(dir, name)
		if err := os.WriteFile(p, []byte(front+"\n# body\n"), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write("db-lens.md", "---\non: [\"path:migrations/**\"]\ncost: adopt\nprovides: lens\n---")
	write("db-role.md", "---\non: [\"path:migrations/**\"]\ncost: adopt\nprovides: role\n---")
	write("db-skill.md", "---\non: [\"path:migrations/**\"]\ncost: read\n---")

	byName := map[string]Resource{}
	for _, r := range LoadResources(dir) {
		byName[r.Name] = r
	}
	if len(byName) != 3 {
		t.Fatalf("expected 3 resources, got %d", len(byName))
	}
	if got := byName["db-lens"].Provides; got != "lens" {
		t.Errorf("lens: provides = %q, want lens", got)
	}
	if got := byName["db-role"].Provides; got != "role" {
		t.Errorf("role: provides = %q, want role", got)
	}
	// A resource with no `provides` must still work - the field was added
	// later, and an older resource that silently became "" would fall out of
	// every branch of the output switch and vanish from the answer.
	if got := byName["db-skill"].Provides; got != "skill" {
		t.Errorf("absent provides must default to skill, got %q", got)
	}
}

// TestRolesStillObeyTheThresholdRule. A role costs `adopt`, so weak intent
// must never fire one: putting on a hat with authority and hands-off
// boundaries because someone typed a keyword is the "wrong signal, wrong
// price" failure the threshold rule exists to prevent.
func TestRolesStillObeyTheThresholdRule(t *testing.T) {
	role := Resource{Name: "database-engineer", Path: "roles/database-engineer.md",
		Cost: CostAdopt, Provides: "role",
		On: []string{"path:migrations/**", "intent:migration"}}

	fired := Resolve([]Resource{role}, TaskContext{Task: "do the migration now"})
	if len(fired) != 0 {
		t.Errorf("weak intent must not fire a role, got %v", fired)
	}
	fired = Resolve([]Resource{role}, TaskContext{Paths: []string{"migrations/1.sql"}})
	if len(fired) != 1 {
		t.Errorf("a deterministic path must fire the role, got %v", fired)
	}
}
