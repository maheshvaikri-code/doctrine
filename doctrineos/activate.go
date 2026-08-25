package main

import (
	"bufio"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// The activation engine.
//
// v1's routing table was 77 rows of prose the MODEL consulted: whether a skill
// loaded depended on the model reading a table and deciding. That is not a
// trigger, it is a suggestion - it costs tokens on every task whether or not
// anything fires, and it fires inconsistently because it is a fresh judgement
// call each time. Here activation is COMPUTED, and it explains itself.
//
// The threshold rule is the core of the design:
//
//	A signal may only auto-fire a resource whose cost is proportional to
//	that signal's reliability.
//
// Deterministic signals (repo facts, touched paths, tool payload, gate events)
// may fire anything, including a refusal. Weak signals (intent inferred from
// task text) may fire READS ONLY - putting a file in context is cheap and
// reversible; dispatching agents or refusing a write is neither.

type Reliability int

const (
	Weak          Reliability = iota // S6 intent - reads only
	Declared                         // S4 class/profile - reads, dispatch, templates
	Deterministic                    // S1/S2/S3/S5 - anything, including refusal
)

// Cost is what a resource asks the host to spend when it activates.
type Cost string

const (
	CostRead    Cost = "read"    // put a file in context
	CostAdopt   Cost = "adopt"   // take on a lens (checks + tool grant + write scope)
	CostCompose Cost = "compose" // overlay a domain pack
	CostDispatch Cost = "dispatch" // spawn a fresh-context subagent
	CostRefuse  Cost = "refuse"  // deny a tool call
)

// maxReliabilityFor returns the cheapest signal class permitted to fire a
// resource of this cost. This is the threshold rule, in one function.
func minReliabilityFor(c Cost) Reliability {
	switch c {
	case CostRead:
		return Weak
	case CostAdopt, CostCompose, CostDispatch:
		return Declared
	case CostRefuse:
		return Deterministic
	}
	return Deterministic
}

// Resource is one activatable thing, declared in the file's own frontmatter
// so the contract cannot drift from what it activates.
type Resource struct {
	Path string   // repo-relative
	Name string   // basename without extension
	On   []string // signal expressions: "path:migrations/**", "intent:schema"
	Cost Cost
}

// TaskContext is everything the engine gets to reason from.
type TaskContext struct {
	Root     string
	Paths    []string // S2 - files this task touches
	Task     string   // S6 - the request text
	Class    string   // S4 - S | M | L | HOTFIX
	RepoFact map[string]bool
}

// Activation is one fired resource plus the reason, so a wrong trigger is
// diagnosable instead of mysterious. An engine that cannot explain itself is
// an engine nobody will trust enough to leave on.
type Activation struct {
	Resource Resource
	Signal   string
	Why      string
}

// matchGlob supports the `**/` prefix and `dir/**` subtree forms the corpus
// actually uses. filepath.Match alone does not cross separators.
func matchGlob(pattern, path string) bool {
	pattern, path = strings.ToLower(pattern), strings.ToLower(filepath.ToSlash(path))

	// `**/X/**` - a segment named X ANYWHERE, plus everything beneath it.
	// This case must be tested FIRST: an earlier version checked the `/**`
	// suffix before the `**/` prefix, so `**/auth/**` took the subtree branch
	// with a literal base of "**/auth" and never matched anything. Caught by
	// TestMatchGlob, not by reading the code.
	if strings.HasPrefix(pattern, "**/") && strings.HasSuffix(pattern, "/**") {
		mid := strings.TrimSuffix(strings.TrimPrefix(pattern, "**/"), "/**")
		for _, seg := range strings.Split(path, "/") {
			if ok, _ := filepath.Match(mid, seg); ok {
				return true
			}
		}
		return false
	}
	// `dir/**` - the directory itself and its subtree.
	if strings.HasSuffix(pattern, "/**") {
		base := strings.TrimSuffix(pattern, "/**")
		return path == base || strings.HasPrefix(path, base+"/")
	}
	// `**/tail` - any segment, or the basename.
	if strings.HasPrefix(pattern, "**/") {
		tail := pattern[3:]
		if ok, _ := filepath.Match(tail, filepath.Base(path)); ok {
			return true
		}
		for _, seg := range strings.Split(path, "/") {
			if ok, _ := filepath.Match(tail, seg); ok {
				return true
			}
		}
		return false
	}
	if ok, _ := filepath.Match(pattern, path); ok {
		return true
	}
	// a bare directory pattern covers its subtree
	if !strings.ContainsAny(pattern, "*?") {
		return path == pattern || strings.HasPrefix(path, pattern+"/")
	}
	return false
}

// evalSignal reports whether one signal expression fires, its reliability,
// and a human-readable reason.
func evalSignal(expr string, tc TaskContext) (bool, Reliability, string) {
	kind, arg, found := strings.Cut(expr, ":")
	if !found {
		return false, Weak, ""
	}
	switch kind {
	case "path": // S2 - deterministic
		for _, p := range tc.Paths {
			if matchGlob(arg, p) {
				return true, Deterministic, "path:" + arg + " matched " + p
			}
		}
	case "repo": // S1 - deterministic
		if tc.RepoFact[arg] {
			return true, Deterministic, "repo fact: " + arg
		}
	case "class": // S4 - declared
		for _, c := range strings.Split(arg, "|") {
			if strings.EqualFold(strings.TrimSpace(c), tc.Class) {
				return true, Declared, "class is " + tc.Class
			}
		}
	case "intent": // S6 - WEAK. reads only.
		low := strings.ToLower(tc.Task)
		for _, kw := range strings.Split(arg, "|") {
			kw = strings.TrimSpace(strings.ToLower(kw))
			if kw != "" && strings.Contains(low, kw) {
				return true, Weak, "task text contains \"" + kw + "\""
			}
		}
	}
	return false, Weak, ""
}

// parseFrontmatter reads a leading `---` block and pulls the activation
// contract out of it. A resource with no contract is unreachable, which the
// build is expected to reject - that is the defect class where three skills
// existed for weeks while being routed from nowhere.
func parseFrontmatter(path string) (Resource, bool) {
	f, err := os.Open(path)
	if err != nil {
		return Resource{}, false
	}
	defer f.Close()

	r := Resource{Path: path, Cost: CostRead,
		Name: strings.TrimSuffix(filepath.Base(path), filepath.Ext(path))}
	sc := bufio.NewScanner(f)
	if !sc.Scan() || strings.TrimSpace(sc.Text()) != "---" {
		return Resource{}, false
	}
	got := false
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "---" {
			break
		}
		key, val, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		switch key {
		case "on":
			for _, p := range strings.Split(strings.Trim(val, "[]"), ",") {
				if s := strings.Trim(strings.TrimSpace(p), `"`); s != "" {
					r.On = append(r.On, s)
					got = true
				}
			}
		case "cost":
			r.Cost = Cost(strings.Trim(val, `"`))
		}
	}
	return r, got
}

// LoadResources walks the materialised corpus and collects every resource
// that declares an activation contract.
func LoadResources(corpus string) []Resource {
	var out []Resource
	filepath.Walk(corpus, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(p, ".md") {
			return nil
		}
		if r, ok := parseFrontmatter(p); ok {
			out = append(out, r)
		}
		return nil
	})
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

// Resolve is the whole engine: deterministic, explicable, threshold-enforcing.
// Same context in, same set out - so it is testable, diffable, and cacheable.
func Resolve(res []Resource, tc TaskContext) []Activation {
	var fired []Activation
	for _, r := range res {
		best := Weak
		var bestWhy, bestSig string
		hit := false
		for _, sig := range r.On {
			ok, rel, why := evalSignal(sig, tc)
			if ok && (!hit || rel > best) {
				hit, best, bestWhy, bestSig = true, rel, why, sig
			}
		}
		if !hit {
			continue
		}
		// THE THRESHOLD RULE. A weak signal cannot buy an expensive action.
		if best < minReliabilityFor(r.Cost) {
			continue
		}
		fired = append(fired, Activation{Resource: r, Signal: bestSig, Why: bestWhy})
	}
	return fired
}
