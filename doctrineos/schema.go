package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"unicode/utf8"
)

// A minimal JSON-Schema validator, covering exactly the constructs the
// state-plane schemas use - and no more.
//
// This is the gap the tamper oracle exposed: Python validates every
// checkpoint against checkpoint.schema.json, and the first Go port did not.
// All nine tamper verdicts still agreed, because every mutation I chose broke
// a hash. But a checkpoint that is structurally malformed WITHOUT breaking a
// hash - a missing required field, a wrong type, an unknown field - would
// have been caught by Python and waved through by Go. Shipping a verifier
// quietly weaker than its reference is the overclaim this project exists to
// prevent, so the rule is ported rather than dropped.
//
// Deliberately not a general-purpose implementation. A full draft-2020-12
// validator is a large dependency-shaped thing; the schemas here use $ref to
// local $defs, anyOf, const, enum, type, required, properties,
// additionalProperties, propertyNames, items, maxItems, minLength, pattern,
// format: date-time, and minimum. That list is the whole surface, and a
// validator that covers only what the schemas use cannot drift from them.

type schemaError struct{ msg string }

func (e schemaError) Error() string { return e.msg }

var rfc3339Re = regexp.MustCompile(
	`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$`)

// validateSchema mirrors doctrine_state.validate, including the JSON-path in
// each message, so a failure reads the same from either implementation.
func validateSchema(instance any, schema, root map[string]any, path string) error {
	if root == nil {
		root = schema
	}
	if ref, ok := schema["$ref"].(string); ok {
		if !strings.HasPrefix(ref, "#/$defs/") {
			return schemaError{fmt.Sprintf("%s: unsupported $ref %s", path, ref)}
		}
		defs, _ := root["$defs"].(map[string]any)
		name := ref[strings.LastIndex(ref, "/")+1:]
		sub, ok := defs[name].(map[string]any)
		if !ok {
			return schemaError{fmt.Sprintf("%s: unknown $def %s", path, name)}
		}
		schema = sub
	}

	if anyOf, ok := schema["anyOf"].([]any); ok {
		var errs []string
		for _, s := range anyOf {
			sm, _ := s.(map[string]any)
			if err := validateSchema(instance, sm, root, path); err == nil {
				return nil
			} else {
				errs = append(errs, err.Error())
			}
		}
		return schemaError{fmt.Sprintf("%s: matched no anyOf branch (%s)",
			path, strings.Join(errs, "; "))}
	}

	if c, ok := schema["const"]; ok && !jsonEqual(instance, c) {
		return schemaError{fmt.Sprintf("%s: expected const %s", path, pyRepr(c))}
	}
	if e, ok := schema["enum"].([]any); ok {
		found := false
		for _, v := range e {
			if jsonEqual(instance, v) {
				found = true
				break
			}
		}
		if !found {
			return schemaError{fmt.Sprintf("%s: %s not in %s",
				path, pyRepr(instance), pyReprList(e))}
		}
	}

	switch schema["type"] {
	case "object":
		obj, ok := instance.(map[string]any)
		if !ok {
			return schemaError{path + ": expected object"}
		}
		if req, ok := schema["required"].([]any); ok {
			for _, r := range req {
				name, _ := r.(string)
				if _, present := obj[name]; !present {
					return schemaError{fmt.Sprintf("%s: missing required '%s'", path, name)}
				}
			}
		}
		// Iterate keys in SORTED order, never in map order.
		//
		// Go randomises map iteration deliberately. Python walks a dict in
		// insertion order and raises on the first failure, so with two bad
		// fields Python always names the same one while Go would name a
		// different one between runs of the identical input. A verifier whose
		// output changes when nothing changed cannot be evidence of anything.
		//
		// Sorted order is also the document order here, because canonical
		// bytes are written with sort_keys=True - so for any checkpoint that
		// is canonical (and a non-canonical one is already a finding) this
		// reproduces Python's choice exactly rather than merely being stable.
		keys := make([]string, 0, len(obj))
		for k := range obj {
			keys = append(keys, k)
		}
		sort.Strings(keys)

		if pn, ok := schema["propertyNames"].(map[string]any); ok {
			for _, key := range keys {
				// Python: f"{path}(key {key!r})" - repr, not %q. The two agree
				// on plain keys and diverge the moment one contains a quote,
				// which is exactly when the message matters most.
				if err := validateSchema(key, pn, root,
					fmt.Sprintf("%s(key %s)", path, pyRepr(key))); err != nil {
					return err
				}
			}
		}
		props, _ := schema["properties"].(map[string]any)
		addl, hasAddl := schema["additionalProperties"]
		for _, key := range keys {
			val := obj[key]
			if ps, ok := props[key].(map[string]any); ok {
				if err := validateSchema(val, ps, root, path+"."+key); err != nil {
					return err
				}
				continue
			}
			if hasAddl {
				if as, ok := addl.(map[string]any); ok {
					if err := validateSchema(val, as, root, path+"."+key); err != nil {
						return err
					}
					continue
				}
				if b, ok := addl.(bool); ok && !b {
					return schemaError{fmt.Sprintf(
						"%s: unknown field '%s' rejected (additionalProperties: false)", path, key)}
				}
			}
		}
	case "array":
		arr, ok := instance.([]any)
		if !ok {
			return schemaError{path + ": expected array"}
		}
		if mi, ok := schema["maxItems"].(float64); ok && float64(len(arr)) > mi {
			return schemaError{fmt.Sprintf("%s: %d items exceeds maxItems %d",
				path, len(arr), int(mi))}
		}
		if items, ok := schema["items"].(map[string]any); ok {
			for i, it := range arr {
				if err := validateSchema(it, items, root,
					fmt.Sprintf("%s[%d]", path, i)); err != nil {
					return err
				}
			}
		}
	case "string":
		s, ok := instance.(string)
		if !ok {
			return schemaError{path + ": expected string"}
		}
		// Count RUNES, not bytes. Python's len() on a str counts characters,
		// Go's len() on a string counts bytes, and the two agree only while
		// the input stays ASCII. "café" is 4 to Python and 5 to Go, so a
		// minLength of 5 accepts it here and rejects it there - the two
		// implementations disagreeing about the same file, in a direction that
		// depends on which bound is being checked. Nothing in the current
		// oracle cases is non-ASCII, so this was found by reading rather than
		// by testing, and a case now covers it.
		n := float64(utf8.RuneCountInString(s))
		if ml, ok := schema["minLength"].(float64); ok && n < ml {
			return schemaError{fmt.Sprintf("%s: shorter than %d", path, int(ml))}
		}
		if ml, ok := schema["maxLength"].(float64); ok && n > ml {
			return schemaError{fmt.Sprintf("%s: longer than %d", path, int(ml))}
		}
		if pat, ok := schema["pattern"].(string); ok {
			// Python uses re.fullmatch; Go's MatchString is a search, so the
			// anchors are added explicitly. Without them a pattern like
			// ^[a-f0-9]{64}$ would still match, but one WITHOUT anchors would
			// pass on a substring - which is how a validator silently stops
			// validating.
			re, err := regexp.Compile("^(?:" + pat + ")$")
			if err != nil {
				return schemaError{fmt.Sprintf("%s: bad pattern %s", path, pat)}
			}
			if !re.MatchString(s) {
				return schemaError{fmt.Sprintf("%s: does not match %s", path, pat)}
			}
		}
		if f, _ := schema["format"].(string); f == "date-time" && !rfc3339Re.MatchString(s) {
			return schemaError{path + ": not an RFC3339 date-time"}
		}
	case "integer":
		// JSON has no integer type; encoding/json gives float64. An integer is
		// a float64 with no fractional part - and a bool must not qualify,
		// matching Python's explicit isinstance(bool) exclusion (a bool lands
		// in a different case of this type switch, so it fails here anyway).
		//
		// KNOWN, BOUNDED DIVERGENCE: Python's json gives int for `30` and
		// float for `30.0`, so it rejects `"seq": 30.0` as "expected integer".
		// Go decodes both to float64(30) and accepts. Distinguishing them
		// would mean decoding with UseNumber() and inspecting the literal
		// text, which would also change the canonical-bytes path.
		//
		// It is left as-is because the record is still refused, just by a
		// different rule: Go re-encodes float64(30) as `30`, which does not
		// match the stored `30.0`, so the canonical-bytes check fires. Both
		// implementations reject the file; only the stated reason differs.
		// Recorded here rather than left for someone to rediscover.
		f, ok := instance.(float64)
		if !ok || f != math.Trunc(f) {
			return schemaError{path + ": expected integer"}
		}
		if m, ok := schema["minimum"].(float64); ok && f < m {
			return schemaError{fmt.Sprintf("%s: below minimum %d", path, int(m))}
		}
	case "null":
		if instance != nil {
			return schemaError{path + ": expected null"}
		}
	}
	return nil
}

// jsonEqual compares two decoded JSON values by value AND type.
//
// The first version compared fmt.Sprintf("%v", ...) of each side, which is
// wrong in a way that loosens the schema: the number 1 and the string "1" both
// render as `1`, so an enum of integers would have accepted the string. A
// validator that accepts more than its schema says is worse than no validator,
// because it reports success.
//
// One deliberate difference from Python: there, `True == 1` is true, so a
// bool would satisfy an integer enum. That is a quirk of Python's numeric
// tower rather than anything the schemas intend, and replicating it would mean
// hand-writing a bug. Types are compared strictly here.
func jsonEqual(a, b any) bool {
	switch av := a.(type) {
	case string:
		bv, ok := b.(string)
		return ok && av == bv
	case float64:
		bv, ok := b.(float64)
		return ok && av == bv
	case bool:
		bv, ok := b.(bool)
		return ok && av == bv
	case nil:
		return b == nil
	}
	return false // objects/arrays never appear as const or enum members here
}

// pyRepr renders a decoded JSON value the way Python's !r would.
//
// Every schema error message is compared against the Python implementation
// byte for byte by the differential oracle, and the oracle caught this: Python
// wrote `'TAMPERED' not in ['clean', 'dirty']` where Go wrote
// `TAMPERED not in [clean dirty]`. Both refused the record, so verdicts
// agreed - but two tools describing the same defect in two different ways is
// how a reader stops trusting either.
func pyRepr(v any) string {
	switch t := v.(type) {
	case string:
		// Python prefers single quotes, switching to double only when the
		// string contains a single quote and no double quote.
		if strings.Contains(t, "'") && !strings.Contains(t, `"`) {
			return `"` + t + `"`
		}
		return "'" + strings.ReplaceAll(t, "'", `\'`) + "'"
	case bool:
		if t {
			return "True"
		}
		return "False"
	case nil:
		return "None"
	case float64:
		if t == math.Trunc(t) && math.Abs(t) < 1e16 {
			return fmt.Sprintf("%d", int64(t))
		}
		return fmt.Sprintf("%v", t)
	}
	return fmt.Sprintf("%v", v)
}

// pyReprList renders a []any the way Python renders a list of reprs.
func pyReprList(xs []any) string {
	parts := make([]string, 0, len(xs))
	for _, x := range xs {
		parts = append(parts, pyRepr(x))
	}
	return "[" + strings.Join(parts, ", ") + "]"
}

// loadSchema reads a state-plane schema from the corpus. Missing schema is a
// hard error rather than a skip: a verifier that silently stops validating
// when its rules go missing is worse than one that refuses to run.
func loadSchema(root, name string) (map[string]any, error) {
	p := filepath.Join(root, ".Doctrine", "state-plane", "schemas", name+".schema.json")
	b, err := os.ReadFile(p)
	if err != nil {
		// The hint matters more than the path. "Schema not found" reads as a
		// corrupt state plane; the actual cause is almost always an install
		// that never placed .Doctrine/ at the repo root.
		return nil, fmt.Errorf(
			"schema not found: %s (is .Doctrine/ installed at the repo root?)", p)
	}
	var s map[string]any
	if err := json.Unmarshal(b, &s); err != nil {
		return nil, fmt.Errorf("schema %s is not valid JSON: %v", p, err)
	}
	return s, nil
}
