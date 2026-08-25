package main

// The PreToolUse decision: refusal at the point of action.
//
// Scope is deliberately WRITES ONLY. v1 also analysed shell command text and
// four independent review rounds each found a new spelling that reached a
// protected file - because no static analysis of a Turing-complete shell is
// complete. That arm was retired (ADR-014); the containment answer is a layer
// down, and the permission answer belongs to the agent vendor, whose deny
// rules outrank any hook. What is left here is the part that is sound: one
// field names one file.

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

const maxPayload = 8 << 20 // a deeply nested decoy must not OOM the gate

// --- rule 1: credentials -------------------------------------------------
// High-precision provider formats only. A generic "looks like entropy" rule
// produces false denials, and a gate people switch off enforces nothing.
var secretPatterns = []struct {
	re   *regexp.Regexp
	what string
}{
	{regexp.MustCompile(`AKIA[0-9A-Z]{16}`), "AWS access key id"},
	{regexp.MustCompile(`ASIA[0-9A-Z]{16}`), "AWS temporary access key id"},
	{regexp.MustCompile(`gh[pousr]_[A-Za-z0-9]{36,}`), "GitHub token"},
	{regexp.MustCompile(`github_pat_[A-Za-z0-9_]{40,}`), "GitHub fine-grained token"},
	{regexp.MustCompile(`sk-ant-[A-Za-z0-9_-]{20,}`), "Anthropic API key"},
	{regexp.MustCompile(`sk-[A-Za-z0-9]{32,}`), "OpenAI-style API key"},
	{regexp.MustCompile(`xox[baprs]-[A-Za-z0-9-]{10,}`), "Slack token"},
	{regexp.MustCompile(`AIza[0-9A-Za-z_-]{35}`), "Google API key"},
	{regexp.MustCompile(`-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----`), "private key block"},
}

// --- rule 1b: a credential-shaped NAME assigned a literal value ----------
//
// The port hazard, now closed. Python expresses this with a matched-quote
// BACKREFERENCE - (['"])([^'"\n]{12,})\1 - and Go's regexp is RE2, which has
// no backreferences. Transliterating it was impossible; the correct port is
// explicit alternation per quote character, so the opening and closing quote
// still have to match without a backreference doing the work.
//
// This rule is worth the trouble: it is the one that fired on two drafts of
// this project's own test files while they were being written.
var secretAssignQuoted = regexp.MustCompile(
	`(?i)\b[A-Za-z0-9_]*(?:api[_-]?key|secret|passwd|password|token|private[_-]?key)` +
		`\s*[=:]\s*(?:'([^'\n]{12,})'|"([^"\n]{12,})")`)

// ...and the same assignment written WITHOUT quotes, which is how .env files
// and export/ENV lines are actually spelled.
var secretAssignBare = regexp.MustCompile(
	`(?im)(?:^|[ \t;&|])(?:export[ \t]+|ENV[ \t]+|set[ \t]+)?[A-Za-z0-9_]*` +
		`(?:api[_-]?key|secret|passwd|password|token|private[_-]?key)` +
		`[ \t]*=[ \t]*([^\s'"#]{12,})(?:$|[ \t;&|])`)

// Placeholders are how .env.example and documentation are SUPPOSED to look.
// A rule that denies them denies the correct way to write a template.
var placeholder = regexp.MustCompile(
	`(?i)^(?:x{3,}|\.{3,}|<.*>|\$\{?[a-z_]+\}?|your[_-]|changeme|` +
		`placeholder|redacted|example|dummy|fake|test[_-]?(?:key|token)|` +
		`os\.environ|process\.env|none|null)`)

// assignedSecret reports a credential-shaped assignment whose value is not a
// placeholder. Returns "" when nothing qualifies.
func assignedSecret(text string) string {
	for _, m := range secretAssignQuoted.FindAllStringSubmatch(text, -1) {
		for _, v := range m[1:] { // one group per quote style; the other is ""
			if v != "" && !placeholder.MatchString(v) {
				return v
			}
		}
	}
	for _, m := range secretAssignBare.FindAllStringSubmatch(text, -1) {
		if v := m[1]; v != "" && !placeholder.MatchString(v) {
			return v
		}
	}
	return ""
}

var protectedAlways = []struct{ pattern, why string }{
	{".git/*", "git's internal object store"},
	{"docs/releases/gold/*", "gold records are immutable (a correction is a NEW tag)"},
	{".doctrine-state/checkpoint.json", "the hash-chained state checkpoint"},
	{".doctrine-state/checkpoints/*", "the hash-chained state history"},
	{".env", "secrets never live in the repo"},
	{".env.*", "secrets never live in the repo"},
	{"**/.env", "secrets never live in the repo"},
	{"**/.env.*", "secrets never live in the repo"},
}

var protectedExempt = []string{
	".env.example", ".env.sample", ".env.template", ".env.dist",
	"**/.env.example", "**/.env.sample", "**/.env.template", "**/.env.dist",
}

type payload struct {
	ToolName  string          `json:"tool_name"`
	CWD       string          `json:"cwd"`
	ToolInput json.RawMessage `json:"tool_input"`
}

type toolInput struct {
	FilePath     string `json:"file_path"`
	NotebookPath string `json:"notebook_path"`
	Content      string `json:"content"`
	NewString    string `json:"new_string"`
}

type hookOut struct {
	HookEventName            string `json:"hookEventName"`
	PermissionDecision       string `json:"permissionDecision"`
	PermissionDecisionReason string `json:"permissionDecisionReason"`
}

func emit(decision, reason string) {
	out := map[string]hookOut{"hookSpecificOutput": {
		HookEventName:            "PreToolUse",
		PermissionDecision:       decision,
		PermissionDecisionReason: reason,
	}}
	b, _ := json.Marshal(out)
	os.Stdout.Write(b)
	os.Stdout.Write([]byte("\n"))
}

// matches mirrors the Python matcher, including the `dir/*`-covers-the-
// directory-itself clause. That clause exists because matching only children
// let `rm -rf docs/releases/gold` delete every record while each individual
// file was "protected".
func matches(rel, pattern string) bool {
	rel, pattern = strings.ToLower(rel), strings.ToLower(pattern)
	if ok, _ := filepath.Match(pattern, rel); ok {
		return true
	}
	if strings.HasSuffix(pattern, "/*") {
		base := strings.TrimSuffix(pattern, "/*")
		if strings.HasPrefix(rel, base+"/") || rel == base {
			return true
		}
	}
	if strings.HasPrefix(pattern, "**/") {
		if ok, _ := filepath.Match(pattern[3:], filepath.Base(rel)); ok {
			return true
		}
	}
	return false
}

func cmdCheck() {
	raw, err := io.ReadAll(io.LimitReader(os.Stdin, maxPayload))
	if err != nil {
		os.Exit(0) // a gate that cannot read its input must not brick the agent
	}
	var p payload
	if err := json.Unmarshal(raw, &p); err != nil {
		os.Exit(0)
	}
	cwd := p.CWD
	if cwd == "" {
		cwd, _ = os.Getwd()
	}
	root, _, governed := FindConfig(cwd)
	if !governed {
		os.Exit(0) // outside a governed repo the law is not in play
	}
	writeTools := map[string]bool{"Write": true, "Edit": true, "MultiEdit": true, "NotebookEdit": true}
	if !writeTools[p.ToolName] {
		os.Exit(0)
	}
	var ti toolInput
	if err := json.Unmarshal(p.ToolInput, &ti); err != nil {
		emit("deny", "DoctrineOS: the input to "+p.ToolName+" could not be read, so it cannot be checked. Denied by default.")
		return
	}
	target := ti.FilePath
	if target == "" {
		target = ti.NotebookPath
	}
	text := ti.Content + ti.NewString

	rel := ""
	if target != "" {
		abs := target
		if !filepath.IsAbs(abs) {
			abs = filepath.Join(root, abs)
		}
		if r, err := filepath.Rel(root, abs); err == nil {
			rel = filepath.ToSlash(r)
		}
	}

	exempt := false
	for _, e := range protectedExempt {
		if matches(rel, e) {
			exempt = true
			break
		}
	}

	if !exempt {
		for _, s := range secretPatterns {
			if s.re.MatchString(text) {
				emit("deny", fmt.Sprintf("DoctrineOS: this write contains what looks like a %s. Secrets never enter the repo. Nothing was written.", s.what))
				return
			}
		}
		if assignedSecret(text) != "" {
			emit("deny", "DoctrineOS: a credential-shaped name is assigned a literal value. Read it from the environment, or use a placeholder if this is a template. Nothing was written.")
			return
		}
	}
	if rel != "" && !exempt {
		for _, pp := range protectedAlways {
			if matches(rel, pp.pattern) {
				emit("deny", fmt.Sprintf("DoctrineOS: '%s' is protected - %s. Nothing was written.", rel, pp.why))
				return
			}
		}
	}
	emit("allow", "DoctrineOS: ordinary file, no credential, not a protected path.")
}
