package main

import (
	"strings"
	"testing"
)

// TestPySplitLinesMatchesPython guards a bug that produced a DIFFERENT
// hydration bundle on a Windows checkout.
//
// Splitting on "\n" alone leaves every line's trailing "\r" attached, so
// rejoining with "\n" reproduces CRLF where Python's splitlines() has stripped
// it. The bundle is what the next agent believes and its hash goes in the
// header, so two implementations disagreeing here is an interop break, not a
// formatting nit.
//
// The real repo's files are LF, so the happy path matched and hid this. Only a
// fixture written through Python's own text mode exposed it.
func TestPySplitLinesMatchesPython(t *testing.T) {
	cases := []struct {
		in   string
		want []string
	}{
		{"a\nb", []string{"a", "b"}},
		{"a\r\nb", []string{"a", "b"}},         // CRLF - the bug
		{"a\rb", []string{"a", "b"}},           // lone CR
		{"a\nb\n", []string{"a", "b"}},         // no trailing empty element
		{"a\r\nb\r\n", []string{"a", "b"}},     // CRLF, trailing
		{"", nil},                              // empty -> no lines at all
		{"\n", []string{""}},                   // one empty line
		{"a\n\nb", []string{"a", "", "b"}},     // blank line preserved
		{"a\r\n\r\nb", []string{"a", "", "b"}}, // blank CRLF line preserved
	}
	for _, c := range cases {
		got := pySplitLines(c.in)
		if len(got) != len(c.want) {
			t.Errorf("pySplitLines(%q) = %q, want %q", c.in, got, c.want)
			continue
		}
		for i := range got {
			if got[i] != c.want[i] {
				t.Errorf("pySplitLines(%q)[%d] = %q, want %q", c.in, i, got[i], c.want[i])
			}
		}
		for _, line := range got {
			if strings.Contains(line, "\r") {
				t.Errorf("pySplitLines(%q) left a CR attached: %q", c.in, line)
			}
		}
	}
}

// TestExtractSectionsNormalisesCRLF is the end-to-end form of the same bug:
// a CRLF source file must yield an LF section, or the bundle differs.
func TestExtractSectionsNormalisesCRLF(t *testing.T) {
	lf := "# t\n\n## Prime Directive\nShip honestly.\n\n## Other\nignored\n"
	crlf := strings.ReplaceAll(lf, "\n", "\r\n")

	gotLF := extractSections(lf, []string{"Prime Directive"})
	gotCRLF := extractSections(crlf, []string{"Prime Directive"})

	if gotLF != gotCRLF {
		t.Errorf("CRLF and LF sources must extract identically:\n  lf  =%q\n  crlf=%q",
			gotLF, gotCRLF)
	}
	if strings.Contains(gotCRLF, "\r") {
		t.Errorf("extracted section still carries CR: %q", gotCRLF)
	}
	if !strings.Contains(gotLF, "Ship honestly.") || strings.Contains(gotLF, "ignored") {
		t.Errorf("wrong section extracted: %q", gotLF)
	}
}

// TestFitRecordsEveryTrim - a bundle that silently dropped half its content
// would read as complete to the next agent.
func TestFitRecordsEveryTrim(t *testing.T) {
	var trimmed []string
	small := "short"
	if got := fit("distillate", small, nil, &trimmed); got != small {
		t.Errorf("content within budget must pass through unchanged")
	}
	if len(trimmed) != 0 {
		t.Errorf("nothing was trimmed, yet a trim was recorded: %v", trimmed)
	}

	limit := budgets["effects"] * tokenChars
	full := strings.Repeat("x", limit+1)
	deg := "degraded form"
	if got := fit("effects", full, &deg, &trimmed); got != deg {
		t.Errorf("over budget must fall back to the degraded form, got %.20q", got)
	}
	if len(trimmed) != 1 || trimmed[0] != "effects" {
		t.Errorf("the trim must be recorded, got %v", trimmed)
	}

	// degraded ALSO over budget -> hard clip, and the clip is marked
	bigDeg := strings.Repeat("y\n", limit)
	got := fit("effects", full, &bigDeg, &trimmed)
	if !strings.HasSuffix(got, "\n[clipped]") {
		t.Errorf("a hard clip must announce itself, got %.30q...", got)
	}
}
