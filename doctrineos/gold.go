package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// The gold ladder: which builds are promotable, and on what evidence.
//
// Ported from tools/doctrine_gold.py. Only the DECISION LOGIC is ported here -
// path safety, content pinning, and chain topology. The git and GPG surfaces
// are I/O plumbing that a differential oracle cannot meaningfully compare, and
// porting them would mean reimplementing git rather than a rule.
//
// The rule this file exists to enforce, in one line: EXISTENCE IS NOT EVIDENCE.
// An earlier version checked that a council verdict and its sign-offs were
// present on disk, which an empty file satisfies. "No verdict, no gold" has to
// mean bytes, so every reference is pinned to a sha256 of its content.

// maxStateFileBytes bounds any parsed state artifact, mirroring
// doctrine_state.MAX_STATE_FILE_BYTES. Kept identical on purpose: a bound that
// differs between the two implementations means one of them accepts a file the
// other refuses, which is a disagreement about what is even readable.
const maxStateFileBytes = 5_000_000

// normalizeEOL folds CRLF before comparing worktree bytes to git's blob.
//
// git show returns the raw blob; core.autocrlf=true - the Git for Windows
// installer default - converts the WORKTREE copy on checkout. Comparing the
// two raw made a fresh, untouched clone accuse itself of forging its own
// security sign-off. Records are canonical LF by construction, so folding both
// sides to LF cannot hide a real edit: a change to the content survives it.
func normalizeEOL(b []byte) []byte {
	return []byte(strings.ReplaceAll(string(b), "\r\n", "\n"))
}

// safeRepoPath resolves a record-referenced path, refusing escapes.
//
// A gold record names the files that justify a promotion. Those names come out
// of a JSON document, so they are untrusted input: "../../etc/passwd" or a
// symlink pointing outside the tree would otherwise let a record pin - and
// appear to verify against - a file that is not part of the repo at all.
//
// Symlinks are resolved BEFORE the containment test, not after. Testing the
// literal path first and following the link later would check the wrong thing:
// the link's own location is inside the repo, which is exactly what makes it a
// useful way out.
func safeRepoPath(repo, rel, what string) (string, error) {
	root, err := filepath.Abs(repo)
	if err != nil {
		return "", fmt.Errorf("%s '%s' escapes the repo root", what, rel)
	}
	if resolved, err := filepath.EvalSymlinks(root); err == nil {
		root = resolved
	}
	cand := filepath.Join(root, rel)
	// EvalSymlinks fails on a path that does not exist yet; that is not an
	// escape, and the caller reports "not on disk" for it a moment later.
	if resolved, err := filepath.EvalSymlinks(cand); err == nil {
		cand = resolved
	}
	relToRoot, err := filepath.Rel(root, cand)
	if err != nil || relToRoot == ".." || strings.HasPrefix(relToRoot, ".."+string(filepath.Separator)) {
		return "", fmt.Errorf("%s '%s' escapes the repo root", what, rel)
	}
	return cand, nil
}

// HashedRef is {path, sha256} for a referenced file.
type HashedRef struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
}

// hashedRef pins a referenced file to the hash of its CONTENT.
//
// A whitespace-only file is refused, and that refusal is the whole point: an
// empty file satisfies an existence check, so a gate written as "the sign-off
// is present" passes on `touch security-signoff.md`. An empty file is not a
// sign-off.
func hashedRef(repo, rel, what string) (HashedRef, error) {
	p, err := safeRepoPath(repo, rel, what)
	if err != nil {
		return HashedRef{}, err
	}
	data, err := os.ReadFile(p)
	if err != nil {
		return HashedRef{}, fmt.Errorf("%s not on disk: %s", what, rel)
	}
	if len(strings.TrimSpace(string(data))) == 0 {
		return HashedRef{}, fmt.Errorf(
			"%s is empty: %s - an empty file is not a sign-off", what, rel)
	}
	return HashedRef{Path: rel, SHA256: sha256Hex(data)}, nil
}

// goldEntry is one record on disk, with the hash of its own bytes and the
// predecessor it claims.
type goldEntry struct {
	path    string
	name    string
	sha     string
	prev    string
	genesis bool // prev_gold_sha256 was null or absent
}

// loadChain orders gold records by walking prev_gold_sha256 links.
//
// The invariants are deliberately strict - exactly one genesis, every prev
// resolving to exactly one record, no forks, every record reachable - because
// each looser alternative has a way to hide a record. Anything else is a broken
// ladder, and a broken ladder is not a ladder you climb carefully; it is one
// you stop trusting.
func loadChain(repo string) ([]string, error) {
	goldDir := filepath.Join(repo, "docs", "releases", "gold")
	dirEntries, err := os.ReadDir(goldDir)
	if err != nil {
		return nil, nil // no gold directory is not an error, just no chain
	}
	var names []string
	for _, e := range dirEntries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") &&
			e.Name() != "MANIFEST.json" { // the deletion anchor, not a link
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)

	var entries []goldEntry
	for _, name := range names {
		p := filepath.Join(goldDir, name)
		// Bound the read before parsing, matching load_json. An unbounded
		// parse of an untrusted artifact is a memory-exhaustion primitive, and
		// gold records are exactly the kind of file an attacker gets to write.
		if info, statErr := os.Stat(p); statErr == nil && info.Size() > maxStateFileBytes {
			return nil, fmt.Errorf(
				"gold record %s: %d bytes exceeds the %d-byte state-file bound",
				p, info.Size(), maxStateFileBytes)
		}
		raw, err := os.ReadFile(p)
		if err != nil {
			return nil, fmt.Errorf("gold record %s: %v", p, err)
		}
		sha := sha256Hex(raw)

		// A record that will not parse is REFUSED, not reinterpreted.
		//
		// This branch previously fell through to prev="", so a corrupt file
		// was reported as "broken rollback chain" - blaming the ladder for a
		// broken rung and sending the reader to audit links that were fine.
		// Caught by the differential oracle, which had no malformed-record
		// case until one was written for it.
		var probe any
		if err := json.Unmarshal(raw, &probe); err != nil {
			return nil, fmt.Errorf("gold record %s: unparseable (%v)", p, err)
		}
		rec, isObject := probe.(map[string]any)
		if !isObject {
			// Python: `rec.get(...) if isinstance(rec, dict) else ""`. Valid
			// JSON that is not an object gets prev "", which is not genesis
			// and matches no record, so it surfaces as a broken link.
			entries = append(entries, goldEntry{p, name, sha, "", false})
			continue
		}
		v, present := rec["prev_gold_sha256"]
		if !present || v == nil {
			entries = append(entries, goldEntry{p, name, sha, "", true})
			continue
		}
		s, _ := v.(string)
		entries = append(entries, goldEntry{p, name, sha, s, false})
	}
	if len(entries) == 0 {
		return nil, nil
	}

	shas := map[string]bool{}
	for _, e := range entries {
		shas[e.sha] = true
	}
	var genesis []goldEntry
	for _, e := range entries {
		if e.genesis {
			genesis = append(genesis, e)
		}
	}
	if len(genesis) != 1 {
		return nil, fmt.Errorf(
			"gold chain topology: %d genesis record(s), expected exactly 1",
			len(genesis))
	}

	childOf := map[string]goldEntry{}
	for _, e := range entries {
		if e.genesis {
			continue
		}
		if !shas[e.prev] {
			return nil, fmt.Errorf(
				"%s: prev_gold_sha256 matches no gold record on disk - broken rollback chain",
				e.name)
		}
		if prior, dup := childOf[e.prev]; dup {
			return nil, fmt.Errorf(
				"gold chain fork: %s and %s both claim the same predecessor %s",
				e.name, prior.name, e.prev[:12])
		}
		childOf[e.prev] = e
	}

	ordered := []string{genesis[0].path}
	cursor := genesis[0].sha
	for {
		next, ok := childOf[cursor]
		if !ok {
			break
		}
		ordered = append(ordered, next.path)
		cursor = next.sha
	}
	if len(ordered) != len(entries) {
		return nil, fmt.Errorf(
			"gold chain topology: %d record(s) unreachable from genesis",
			len(entries)-len(ordered))
	}
	return ordered, nil
}

// cmdGoldPin is the oracle-facing surface for content pinning: given a
// repo-relative path, print its {path, sha256} or the refusal.
//
// It exists because the first version of the gold oracle compared Python's
// hashed_ref against ITSELF and reported perfect agreement - a section that
// could not fail, in a harness written to catch exactly that. Go needed a
// surface before the comparison could be real.
func cmdGoldPin(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "usage: doctrineos gold-pin <repo-relative-path>")
		os.Exit(2)
	}
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		root = cwd
	}
	ref, err := hashedRef(root, args[0], "sign-off")
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	b, _ := json.Marshal(ref)
	fmt.Println(string(b))
}

// cmdGoldChain is the oracle-facing surface: print the ordered chain, or the
// topology error that refuses it.
func cmdGoldChain() {
	cwd, _ := os.Getwd()
	root, _, governed := FindConfig(cwd)
	if !governed {
		fmt.Fprintln(os.Stderr, "not a doctrine repo")
		os.Exit(2)
	}
	ordered, err := loadChain(root)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	if len(ordered) == 0 {
		fmt.Println("no gold records")
		return
	}
	for _, p := range ordered {
		fmt.Println(filepath.Base(p))
	}
}
