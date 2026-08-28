package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// cmdInit makes a repo governed. Until this existed the install story was
// fiction - doctrine.toml and .doctrine/ were placed by hand.
//
// Idempotent by construction (A5): agents retry, and a second run must be a
// no-op rather than a duplicate or a clobber. Every step reports what it did
// or why it skipped, because an agent cannot infer success from silence.
func cmdInit(args []string) {
	cwd, _ := os.Getwd()
	root := cwd
	if r := flagOf(args, "target"); r != "" {
		root = r
	}
	version := flagOf(args, "version")
	if version == "" {
		version = "0.8.0"
	}
	// The corpus source: the kernel shipped beside the binary. In the real
	// product this resolves through ~/.doctrineos/store/<version>/ with a
	// sha256 check; for now it is the local kernel/ tree.
	exe, _ := os.Executable()
	src := filepath.Join(filepath.Dir(exe), "kernel")
	if _, err := os.Stat(src); err != nil {
		fmt.Fprintf(os.Stderr, "doctrineos: no kernel corpus beside the binary (%s)\n", src)
		os.Exit(1)
	}

	// 1. doctrine.toml - the entire committed install surface
	tomlPath := filepath.Join(root, "doctrine.toml")
	if _, err := os.Stat(tomlPath); err == nil {
		fmt.Println("  doctrine.toml       exists, left alone")
	} else {
		body := fmt.Sprintf(`[doctrine]
version = %q

[packs]
enable = ["core"]

[profile]
delivery = "solobuilder"
`, version)
		if err := os.WriteFile(tomlPath, []byte(body), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, "doctrineos:", err)
			os.Exit(1)
		}
		fmt.Println("  doctrine.toml       written")
	}

	// 2. materialise the corpus so the agent reads ordinary repo-relative
	//    paths - no host sandbox, no additionalDirectories, no junction.
	dst := filepath.Join(CorpusDir(root), "kernel")
	st, err := syncTree(src, dst, hasFlag(args, "prune"))
	if err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos:", err)
		os.Exit(1)
	}
	fmt.Printf("  .doctrine/          %s\n", st.summary())
	if len(st.stale) > 0 {
		// Loud, because this is a CORRECTNESS problem and not untidiness:
		// LoadResources walks the corpus directory and activates every .md
		// carrying frontmatter, so a file left behind by an older version
		// still fires. The repo would be running resources its pinned
		// version does not ship.
		fmt.Printf("\n  WARNING: %d file(s) in .doctrine/ are not part of version %s.\n",
			len(st.stale), version)
		fmt.Println("  They will still ACTIVATE - the corpus is scanned, not enumerated.")
		for _, s := range st.stale {
			fmt.Println("    -", s)
		}
		fmt.Println("  fix: doctrineos init --prune   (deletes exactly those files)")
	}

	// 3. gitignore the materialised corpus (thin mode). Managed block with
	//    markers so a later `doctrineos thin/vendor` can find its own edit
	//    instead of guessing.
	if err := ensureGitignore(root); err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos: gitignore:", err)
	} else {
		fmt.Println("  .gitignore          managed block present")
	}

	// 4. hook wiring
	if err := ensureHooks(root); err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos: hooks:", err)
	} else {
		fmt.Println("  .claude/settings.json  hooks wired")
	}

	fmt.Println("\n  commit: doctrine.toml, .gitignore, .claude/settings.json")
	fmt.Println("  next:   doctrineos status")
}

// copyStats is what syncTree actually did, kept separate per outcome so the
// report can say it. "materialised (300 files)" printed whether 300 files were
// written or none were: an agent could not tell a fresh install from a no-op,
// in the one step of init that was not honest about skipping.
type copyStats struct {
	written   int
	updated   int
	identical int
	stale     []string
}

func (s copyStats) summary() string {
	switch {
	case s.written > 0 && s.updated == 0 && s.identical == 0:
		return fmt.Sprintf("materialised (%d files)", s.written)
	case s.written == 0 && s.updated == 0:
		return fmt.Sprintf("verified (%d files, all current)", s.identical)
	default:
		return fmt.Sprintf("synced (%d new, %d updated, %d unchanged)",
			s.written, s.updated, s.identical)
	}
}

// syncTree materialises the corpus by VERIFYING before writing.
//
// The previous version rewrote every file on every run. That was wasteful, but
// the worse part was the reporting: an unconditional overwrite cannot tell you
// whether anything changed, so a re-run looked identical to a first install.
// Comparing content first makes the common case a no-op AND makes the report
// true.
//
// Files present in the destination but absent from the source are collected,
// not silently ignored: the corpus is SCANNED by the activation engine, so a
// leftover from an older version still fires. They are deleted only with
// --prune, because deletion is the caller's decision to make.
func syncTree(src, dst string, prune bool) (copyStats, error) {
	var st copyStats
	seen := map[string]bool{}

	err := filepath.Walk(src, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(src, p)
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		seen[filepath.ToSlash(rel)] = true

		want, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		if have, err := os.ReadFile(target); err == nil {
			if string(have) == string(want) {
				st.identical++
				return nil
			}
			if err := os.WriteFile(target, want, 0o644); err != nil {
				return err
			}
			st.updated++
			return nil
		}
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(target, want, 0o644); err != nil {
			return err
		}
		st.written++
		return nil
	})
	if err != nil {
		return st, err
	}

	// Anything in dst that src does not have.
	filepath.Walk(dst, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		rel, relErr := filepath.Rel(dst, p)
		if relErr != nil {
			return nil
		}
		if !seen[filepath.ToSlash(rel)] {
			st.stale = append(st.stale, filepath.ToSlash(rel))
		}
		return nil
	})
	sort.Strings(st.stale)

	if prune {
		for _, rel := range st.stale {
			if err := os.Remove(filepath.Join(dst, filepath.FromSlash(rel))); err != nil {
				return st, err
			}
		}
		st.stale = nil
	}
	return st, nil
}

const gitBegin = "# >>> doctrineos (managed) >>>"
const gitEnd = "# <<< doctrineos <<<"

func ensureGitignore(root string) error {
	p := filepath.Join(root, ".gitignore")
	cur, _ := os.ReadFile(p)
	if strings.Contains(string(cur), gitBegin) {
		return nil // idempotent
	}
	block := "\n" + gitBegin + "\n.doctrine/\n" + gitEnd + "\n"
	f, err := os.OpenFile(p, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(block)
	return err
}

// ensureHooks wires the binary into Claude Code without clobbering whatever
// the repo already had. It MERGES: existing hook events are preserved, and a
// PreToolUse group that already mentions doctrineos is left alone.
func ensureHooks(root string) error {
	dir := filepath.Join(root, ".claude")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	p := filepath.Join(dir, "settings.json")
	settings := map[string]any{}
	if b, err := os.ReadFile(p); err == nil {
		if err := json.Unmarshal(b, &settings); err != nil {
			// Refuse rather than overwrite: a malformed settings file is the
			// user's to fix, and silently replacing it would lose their config.
			return fmt.Errorf("%s is not valid JSON; fix or move it first", p)
		}
	}
	if strings.Contains(fmt.Sprint(settings), "doctrineos") {
		return nil // already wired
	}
	hooks, _ := settings["hooks"].(map[string]any)
	if hooks == nil {
		hooks = map[string]any{}
	}
	add := func(event, matcher, cmd string) {
		groups, _ := hooks[event].([]any)
		g := map[string]any{"hooks": []any{map[string]any{"type": "command", "command": cmd}}}
		if matcher != "" {
			g["matcher"] = matcher
		}
		hooks[event] = append(groups, g)
	}
	add("PreToolUse", "Write|Edit|MultiEdit|NotebookEdit", "doctrineos check")
	add("Stop", "", "doctrineos gate --done")
	// The activation engine's caller. Without it a governed repo materialises
	// a corpus that nothing ever consults - which is what shipped until now.
	add("UserPromptSubmit", "", "doctrineos context --hook")
	settings["hooks"] = hooks

	b, err := json.MarshalIndent(settings, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(p, append(b, '\n'), 0o644)
}
