# Domain Pack — Conversational AI

<!-- G1 artifact. A deployment-pattern security-review archetype: overlays
     skills/ai-security.md with what is DISTINCT about chat/assistant platforms. -->

> Security-review archetype for **conversational AI** — chatbots, assistants, and
> copilots where a human converses with a model. Load with `skills/ai-security.md`.
> What is distinct: the **user's input is the primary injection vector**, the system
> prompt is a secret to protect, and the conversation itself is often **PII**. The
> model mostly *answers* (vs an agent that acts), so the risks center on
> injection/jailbreak, disclosure, unsafe output, and overreliance.

## 1. Regime (adds to `skills/ai-security.md`)

OWASP LLM Top 10 (Prompt Injection, Sensitive-Info Disclosure, Insecure Output
Handling, Overreliance), content-safety obligations; EU AI Act "limited risk" =
**transparency** (users told they're talking to AI). GDPR for conversation PII.

## 2. Canonical entities & interoperability

- **Entities:** `Conversation`, `Turn`, `SystemPrompt` (secret), `Guardrail`
  (input + output filters), `Moderation` verdict, `Session`, `RetrievedContext` (RAG).
- **Interop:** the LLM API, a moderation/safety API, the RAG store. Retrieved context
  is an **indirect** injection surface even when the user seems trusted.

## 3. Domain acceptance criteria (added to the task's own)

1. Given user input, when processed, then **direct prompt injection** is defended
   (input never silently overrides the system prompt) and tested with a jailbreak corpus.
2. Given the system prompt / instructions / secrets, when the model runs, then they
   are **not leakable** via crafted prompts (system-prompt-extraction tested).
3. Given the conversation, when stored/logged/analyzed, then **PII is minimized,
   consented, and access-controlled** — transcripts are sensitive; not sent to a
   third-party model or analytics without a DPA + redaction.
4. Given model output, when shown or used, then it is **content-moderated** and, if it
   flows into code/links/markup, **sanitized** (insecure-output-handling).
5. Given the assistant, when a user could over-rely on it (medical/legal/financial),
   then **uncertainty + a human-escalation path** are surfaced; users are told it is AI.

## 4. Threat / harm model

- **Assets:** the system prompt + secrets, users' conversation PII, brand/safety, the
  RAG corpus.
- **Untrusted inputs:** user messages (primary), **retrieved documents** (indirect
  injection), prior turns.
- **Worst plausible harm:** (a) jailbreak → the bot emits harmful/prohibited content
  or leaks its system prompt/secrets; (b) PII in a transcript breached or sent to an
  unvetted model; (c) unsafe output (a poisoned link, injected markup/code) acted on;
  (d) a user harmed by acting on a confident hallucination. Reputational + privacy + safety.

## 5. Gate overlay

- **G0:** transparency + safety obligations; PII inventory of the conversation.
- **G1:** system-prompt/secret isolation, input+output guardrails, session isolation,
  RAG-as-untrusted, and PII minimization are **design constraints**.
- **G5:** the **conversational sign-off** — `roles/security-reviewer.md`
  (injection/jailbreak red-team, output sanitization) **plus** `roles/compliance-officer.md`
  (transcript PII, transparency, moderation). Any may veto.
- **G6:** moderation live; incident path for a jailbreak/leak; retention on transcripts.

## 6. Specialist roles (all existing — no new roles)

| Role | Pulled in when… |
|------|-----------------|
| `roles/security-reviewer.md` (+ `skills/ai-security.md`) | injection/jailbreak, output handling, prompt-leak |
| `roles/compliance-officer.md` | transcript PII, transparency, content safety |
| `roles/ml-engineer.md` | prompt/RAG/guardrail wiring |

## 7. Glossary

- **Jailbreak** — a prompt that bypasses the model's safety/instructions.
- **System-prompt extraction** — coaxing the model to reveal its hidden instructions.
- **Guardrail** — an input or output filter (moderation, PII redaction, policy).
- **Grounding / RAG** — answering from retrieved content (an indirect-injection surface).
- **Overreliance** — a user acting on unverified model output.

## 8. Non-negotiables (domain)

1. **Never let user input silently override the system prompt** — defend and test injection.
2. **Never make the system prompt or secrets leakable** — isolate; test extraction.
3. **Never treat a transcript as non-PII** — minimize, consent, redact before any model/analytics.
4. **Never use model output unsanitized** where it becomes code/links/markup.
5. **Never hide that it's AI**, and always give a human-escalation path where over-reliance harms.
