package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Config is doctrine.toml - the entire committed install surface.
//
// Parsed by a deliberately minimal TOML reader rather than a dependency.
// The zero-dependency property is load-bearing here, not aesthetic: this
// binary is a governance tool that an agent runs unattended, and every
// transitive package is supply-chain surface a reviewer has to clear. The
// config shape is fixed and tiny (strings, string arrays, two sections), so
// ~70 lines of parser buys back the whole dependency tree.
type Config struct {
	Version string   // [doctrine] version
	SHA256  string   // [doctrine] sha256   - pins the exact corpus
	Packs   []string // [packs]    enable
	Deliver string   // [profile]  delivery
	Merge   string   // [profile]  merge
	Local   string   // [local]    extend  - repo-owned, committed
	Path    string   // where this file was found
}

// ParseConfig reads the supported subset of TOML: [section] headers,
// key = "string", and key = ["a", "b"]. Comments and blanks are skipped.
// Anything it does not understand is IGNORED rather than fatal - an unknown
// key from a newer version must not brick an older binary mid-task.
func ParseConfig(path string) (*Config, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	cfg := &Config{Path: path}
	section := ""
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.Trim(line, "[]")
			continue
		}
		eq := strings.Index(line, "=")
		if eq < 0 {
			continue
		}
		key := strings.TrimSpace(line[:eq])
		val := strings.TrimSpace(line[eq+1:])
		if i := strings.Index(val, " #"); i >= 0 { // trailing comment
			val = strings.TrimSpace(val[:i])
		}
		switch {
		case strings.HasPrefix(val, "["): // array
			items := []string{}
			for _, p := range strings.Split(strings.Trim(val, "[]"), ",") {
				if s := strings.Trim(strings.TrimSpace(p), `"`); s != "" {
					items = append(items, s)
				}
			}
			if section == "packs" && key == "enable" {
				cfg.Packs = items
			}
		default:
			s := strings.Trim(val, `"`)
			switch section + "." + key {
			case "doctrine.version":
				cfg.Version = s
			case "doctrine.sha256":
				cfg.SHA256 = s
			case "profile.delivery":
				cfg.Deliver = s
			case "profile.merge":
				cfg.Merge = s
			case "local.extend":
				cfg.Local = s
			}
		}
	}
	return cfg, sc.Err()
}

// FindConfig walks up from start looking for doctrine.toml, then falls back
// to .Doctrine.md so a v1 repo is still recognised as governed. Returns the
// repo root and the config (nil if only the v1 marker was found).
func FindConfig(start string) (root string, cfg *Config, governed bool) {
	d := start
	for {
		tomlPath := filepath.Join(d, "doctrine.toml")
		if _, err := os.Stat(tomlPath); err == nil {
			c, err := ParseConfig(tomlPath)
			if err == nil {
				return d, c, true
			}
		}
		if _, err := os.Stat(filepath.Join(d, ".Doctrine.md")); err == nil {
			return d, nil, true // v1 repo: governed, unpinned
		}
		parent := filepath.Dir(d)
		if parent == d {
			return "", nil, false
		}
		d = parent
	}
}

// CorpusDir is where the materialised corpus lives inside the repo. Repo-
// relative on purpose: the agent reads it with ordinary paths, so no host
// sandbox, additionalDirectories entry, or Windows junction is involved.
func CorpusDir(root string) string { return filepath.Join(root, ".doctrine") }

func (c *Config) String() string {
	if c == nil {
		return "(v1 repo, unpinned)"
	}
	return fmt.Sprintf("%s packs=%v profile=%s", c.Version, c.Packs, c.Deliver)
}
