# Domain Pack — Contact Center AI

<!-- G1 artifact. A deployment-pattern security-review archetype: overlays
     skills/ai-security.md with what is DISTINCT about voice/IVR + agent-assist. -->

> Security-review archetype for **contact-center AI** — voice bots / IVR, real-time
> transcription, and agent-assist. Load with `skills/ai-security.md`; composes with
> `domains/finance.md` (PCI in voice) and `domains/healthcare.md` (PHI on calls). What
> is distinct: the channel is **voice** (biometric + deepfake-spoofable), calls are
> **recorded PII/PCI/PHI** with consent law, and AI often **assists a human agent**
> whose override must be preserved.

## 1. Regime (adds to `skills/ai-security.md`)

Call-recording **consent** law (two-party states / GDPR), **PCI-DSS** for card data
spoken/entered on calls (compose `domains/finance.md`), PHI if healthcare (compose
`domains/healthcare.md`), TCPA/telecom rules; EU AI Act transparency (caller told it's AI)
and **biometric** categorization if voice-ID is used.

## 2. Canonical entities & interoperability

- **Entities:** `Call`, `Recording`, `Transcript` (real-time), `VoiceBiometric`,
  `AgentAssist` (suggestion to a human), `Consent`, `DTMF` capture, `Escalation`.
- **Interop:** telephony/SIP, STT/TTS, the CRM, a PCI-scoped payment capture path.
  The audio stream + transcript are sensitive data in motion.

## 3. Domain acceptance criteria (added to the task's own)

1. Given a call, when recorded/transcribed, then **consent is captured** per
   jurisdiction and the caller is **told it is AI**; recordings/transcripts are
   encrypted, minimized, and access-controlled.
2. Given card data on a call, when captured, then it stays **out of PCI scope of the
   AI** — DTMF masking / pause-resume so the model and recording never receive the PAN
   (compose `domains/finance.md`).
3. Given voice authentication, when used, then it resists **deepfake/replay voice
   spoofing** (liveness, multi-factor) — voice alone is not proof of identity.
4. Given **agent-assist** suggestions, when shown to a human agent, then the human
   **retains override**, suggestions are marked as AI, and a wrong suggestion cannot
   auto-act (no silent automation of a regulated action).
5. Given real-time transcription, when it flows to a model/analytics, then PHI/PII is
   redacted and third-party processors have a DPA/BAA.

## 4. Threat / harm model

- **Assets:** callers' voice PII/PHI + card data, recording/consent integrity, agent
  decisions, identity via voice.
- **Untrusted inputs:** caller audio (spoofable), DTMF, transcript text (injection into
  agent-assist), telephony metadata.
- **Worst plausible harm:** (a) a **deepfake voice** passes voice-ID → account takeover;
  (b) a PAN captured into the recording/model → PCI breach; (c) recording without
  consent → legal liability; (d) a wrong agent-assist suggestion auto-acted on a
  regulated decision; (e) PHI in a transcript leaked. Legal + fraud + privacy.

## 5. Gate overlay

- **G0:** consent regime + whether PCI/PHI is spoken; transparency obligation.
- **G1:** consent capture, DTMF-masking for PCI, deepfake-resistant voice auth,
  human-override on agent-assist, and transcript redaction are **design constraints**.
- **G5:** the **contact-center sign-off** — `roles/security-reviewer.md` (voice
  spoofing, PCI-in-voice, injection into assist) **plus** `roles/compliance-officer.md`
  (consent, PII/PHI, transparency). Any may veto.
- **G6:** consent + recording retention applied; escalation-to-human path tested.

## 6. Specialist roles (all existing — no new roles)

| Role | Pulled in when… |
|------|-----------------|
| `roles/security-reviewer.md` (+ `skills/ai-security.md`) | voice spoofing, PCI-in-voice, assist injection |
| `roles/compliance-officer.md` | consent, PII/PHI, transparency |
| `roles/ml-engineer.md` | STT/TTS, voice-ID, agent-assist models |

## 7. Glossary

- **Agent-assist** — AI suggestions surfaced to a human contact-center agent.
- **DTMF masking / pause-resume** — keeping spoken/keyed card data out of the recording + AI (PCI).
- **Voice biometric spoofing** — defeating voice-ID with a deepfake or replay.
- **Two-party consent** — both parties must consent to recording (some jurisdictions).

## 8. Non-negotiables (domain)

1. **Never record/transcribe without lawful consent** and telling the caller it's AI.
2. **Never let a PAN reach the recording or the model** — DTMF-mask / pause-resume (PCI).
3. **Never treat voice alone as proof of identity** — assume deepfake; require liveness/MFA.
4. **Never let agent-assist auto-act a regulated decision** — the human keeps override.
5. **Never send PHI/PII transcripts to an unvetted processor** — DPA/BAA + redaction.
