// Command doctrineos governs how work gets done in a repository, and proves
// it afterwards.
//
// Design notes that are load-bearing rather than decorative:
//
//   - Static binary, no runtime. A Node shop, a Rust shop and a scratch
//     container must not need Python installed to run gates that have nothing
//     to do with their stack. For a human that is a tax; for an autonomous
//     agent it is a wall, and the wall is where autonomy ends.
//   - Every command is non-interactive and emits parseable output. The user
//     is an agent: it cannot answer a prompt and cannot "just look" at an
//     error.
//   - Failure is loud and actionable, never a silent degrade. An agent that
//     half-loads a corpus will confidently apply half a law.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const usage = `doctrineos - govern how work gets done, and prove it afterwards

  doctrineos init [--target dir]  make a repo governed (idempotent)
  doctrineos check              decide a PreToolUse payload (stdin JSON -> stdout JSON)
  doctrineos context [flags]    resolve which resources this task activates
  doctrineos gate --done        Definition-of-Done gate (Stop event)
  doctrineos status             what is pinned, installed, and materialised

context flags:
  --task "<text>"      the request, for intent signals (weak: reads only)
  --paths a,b,c        files this task touches (deterministic)
  --class S|M|L        declared task class
  --content            emit file contents instead of paths (for MCP hosts)
`

func main() {
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	switch os.Args[1] {
	case "check":
		cmdCheck()
	case "context":
		cmdContext(os.Args[2:])
	case "gate":
		cmdGate(os.Args[2:])
	case "init":
		cmdInit(os.Args[2:])
	case "status":
		cmdStatus()
	case "-h", "--help", "help":
		fmt.Print(usage)
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n\n%s", os.Args[1], usage)
		os.Exit(2)
	}
}

func flagOf(args []string, name string) string {
	for i, a := range args {
		if a == "--"+name && i+1 < len(args) {
			return args[i+1]
		}
		if strings.HasPrefix(a, "--"+name+"=") {
			return strings.TrimPrefix(a, "--"+name+"=")
		}
	}
	return ""
}

func hasFlag(args []string, name string) bool {
	for _, a := range args {
		if a == "--"+name {
			return true
		}
	}
	return false
}

// cmdContext is the activation engine's public face. It answers "what does
// this task need?" so the agent never scans the corpus - and it reports WHY,
// so a wrong trigger is diagnosable rather than mysterious.
func cmdContext(args []string) {
	cwd, _ := os.Getwd()
	root, cfg, governed := FindConfig(cwd)
	if !governed {
		fmt.Println(`{"governed":false}`)
		return
	}
	corpus := CorpusDir(root)
	if _, err := os.Stat(corpus); err != nil {
		// Loud and actionable. Never a silent degrade.
		fmt.Fprintf(os.Stderr,
			"doctrineos: corpus not materialised at %s\n  fix: doctrineos init\n", corpus)
		os.Exit(1)
	}

	var paths []string
	if p := flagOf(args, "paths"); p != "" {
		for _, s := range strings.Split(p, ",") {
			if s = strings.TrimSpace(s); s != "" {
				paths = append(paths, s)
			}
		}
	}
	tc := TaskContext{
		Root:     root,
		Paths:    paths,
		Task:     flagOf(args, "task"),
		Class:    flagOf(args, "class"),
		RepoFact: repoFacts(root),
	}

	fired := Resolve(LoadResources(corpus), tc)

	out := map[string]any{
		"governed": true,
		"version":  cfg.String(),
		"read":     []string{},
		"adopt":    []string{},
		"compose":  []string{},
		"why":      map[string]string{},
	}
	why := out["why"].(map[string]string)
	for _, a := range fired {
		rel, _ := filepath.Rel(root, a.Resource.Path)
		rel = filepath.ToSlash(rel)
		switch a.Resource.Cost {
		case CostAdopt:
			out["adopt"] = append(out["adopt"].([]string), a.Resource.Name)
		case CostCompose:
			out["compose"] = append(out["compose"].([]string), a.Resource.Name)
		default:
			out["read"] = append(out["read"].([]string), rel)
		}
		why[a.Resource.Name] = a.Why
	}
	if hasFlag(args, "content") {
		contents := map[string]string{}
		for _, a := range fired {
			if a.Resource.Cost == CostRead {
				if b, err := os.ReadFile(a.Resource.Path); err == nil {
					contents[a.Resource.Name] = string(b)
				}
			}
		}
		out["content"] = contents
	}
	b, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(b))
}

// repoFacts are S1 signals: cheap, deterministic, computed once.
func repoFacts(root string) map[string]bool {
	fact := map[string]bool{}
	probe := map[string]string{
		"python":     "pyproject.toml",
		"node":       "package.json",
		"go":         "go.mod",
		"rust":       "Cargo.toml",
		"ci-actions": ".github/workflows",
		"docker":     "Dockerfile",
		"terraform":  "main.tf",
	}
	for name, rel := range probe {
		if _, err := os.Stat(filepath.Join(root, rel)); err == nil {
			fact[name] = true
		}
	}
	return fact
}

// cmdGate is the Definition-of-Done check on the Stop event - the band v1
// left to narration. It FAILS OPEN on its own errors: a gate that bricks a
// session is worse than the gap it closes.
// gateDone is the Definition-of-Done decision, extracted from the command so
// it is testable without process exits. Returns the artifacts that are
// missing; empty means the turn may end.
//
// FAILS OPEN by construction: an unclassified task, a missing task name, or
// an S-class change owes nothing. A gate that blocks a session it cannot
// reason about is worse than the gap it closes.
func gateDone(root, class, task string) []string {
	class = strings.ToUpper(strings.TrimSpace(class))
	if class != "M" && class != "L" {
		return nil // S-class and unclassified work owes no artifact
	}
	if strings.TrimSpace(task) == "" {
		return nil
	}
	var missing []string
	for _, dir := range []string{"docs/reviews", "docs/qa"} {
		if _, err := os.Stat(filepath.Join(root, dir, task+".md")); err != nil {
			missing = append(missing, dir+"/"+task+".md")
		}
	}
	return missing
}

func cmdGate(args []string) {
	if !hasFlag(args, "done") {
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		os.Exit(0)
	}
	missing := gateDone(root, flagOf(args, "class"), flagOf(args, "task"))
	if len(missing) == 0 {
		os.Exit(0)
	}
	fmt.Printf(`{"decision":"block","reason":"DoctrineOS: this task declares done, but its evidence is missing: %s. Produce it, or restate the status honestly - \"blocked\" is a respectable status; a fabricated pass is not."}`+"\n",
		strings.Join(missing, ", "))
}

func cmdStatus() {
	cwd, _ := os.Getwd()
	root, cfg, governed := FindConfig(cwd)
	if !governed {
		fmt.Println("not a doctrine repo (no doctrine.toml or .Doctrine.md found)")
		os.Exit(1)
	}
	fmt.Println("root:    ", root)
	fmt.Println("pinned:  ", cfg.String())
	corpus := CorpusDir(root)
	if _, err := os.Stat(corpus); err == nil {
		n := len(LoadResources(corpus))
		fmt.Printf("corpus:   %s (%d activatable resources)\n", corpus, n)
	} else {
		fmt.Println("corpus:   NOT MATERIALISED -> doctrineos init")
	}
}
