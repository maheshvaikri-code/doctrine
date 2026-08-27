package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
)

// The state plane: external memory for an agent that resets to zero.
//
// This is the mechanism behind the memory half of the thesis. A human
// engineer carries yesterday forward; an agent starts from nothing every
// session, so continuity has to live outside it - hash-chained so that a
// later session can tell an honest record from an edited one.
//
// CANONICAL BYTES ARE THE WHOLE PORT.
//
// Every hash in the chain is taken over the canonical encoding of a
// checkpoint. If Go's encoder differs from Python's by a single byte - one
// escaped character, one key out of order, one missing newline - then every
// hash diverges, `verify` reports a broken chain, and the failure LOOKS
// EXACTLY LIKE TAMPERING. That is worse than having no chain at all: a
// checksum that cries wolf gets switched off, and then nothing is checked.
//
// Python's contract, read from tools/doctrine_state.py:
//
//	json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2,
//	           separators=(",", ": "))  + "\n"
//
// Go's encoder does NOT match that out of the box. Two deliberate
// corrections, each of which silently breaks the chain if omitted:
//
//  1. SetEscapeHTML(false). Go escapes <, > and & to <, >, &
//     by default - a legacy of embedding JSON in HTML. Python with
//     ensure_ascii=False writes them literally. Any checkpoint containing a
//     comparison operator, an HTML tag in a note, or a shell redirect in a
//     recorded command would hash differently.
//  2. Map ordering. Go sorts map[string]any keys when marshalling, which
//     matches sort_keys=True - but ONLY for maps. Struct fields marshal in
//     declaration order, so this code must carry state as maps, never as
//     structs, or the ordering guarantee quietly disappears.
//
// Verified byte-for-byte against the Python implementation by the
// differential oracle rather than by reading the documentation of either.
func canonicalBytes(v any) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false) // correction 1
	enc.SetIndent("", "  ")  // indent=2
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	// Encoder.Encode already appends the trailing newline Python adds by hand.
	return buf.Bytes(), nil
}

func sha256Hex(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

// cmdCanon is a debug surface, and it exists for one reason: it lets the
// differential oracle compare the two implementations' canonical output
// BYTE FOR BYTE instead of trusting that two JSON encoders agree. Reads JSON
// on stdin, writes canonical bytes on stdout.
//
// --hash prints the sha256 instead, which is what the chain actually stores.
func cmdCanon(args []string) {
	raw, err := io.ReadAll(io.LimitReader(os.Stdin, maxPayload))
	if err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos canon:", err)
		os.Exit(1)
	}
	// Decode into `any` so ordering comes from the map path, matching
	// Python's sort_keys. Numbers land as float64; the oracle covers that.
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos canon: input is not JSON:", err)
		os.Exit(1)
	}
	out, err := canonicalBytes(v)
	if err != nil {
		fmt.Fprintln(os.Stderr, "doctrineos canon:", err)
		os.Exit(1)
	}
	if hasFlag(args, "hash") {
		fmt.Println(sha256Hex(out))
		return
	}
	os.Stdout.Write(out)
}
