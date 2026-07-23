# Domain Pack — IoT + AI (Edge AI)

<!-- G1 artifact. A deployment-pattern security-review archetype: overlays
     skills/ai-security.md with what is DISTINCT about AI on physical/edge devices. -->

> Security-review archetype for **AI on the edge** — models running on physical
> devices (sensors, cameras, gateways, vehicles, appliances). Load with
> `skills/ai-security.md`; composes with `domains/manufacturing.md` (OT) and
> `domains/transportation.md` (safety). What is distinct: the attacker can hold the
> **hardware**, the model ships **on-device** (extractable/tamperable), inputs are
> **physical** (sensors can be spoofed), and updates go **over the air** to a fleet.

## 1. Regime (adds to `skills/ai-security.md`)

MITRE ATLAS (physical/model-extraction techniques), IoT security baselines
(**ETSI EN 303 645**, **NIST IR 8259**), IEC 62443 (OT, via manufacturing), plus
device-class/regional cert. EU AI Act tier if the device makes consequential decisions.

## 2. Canonical entities & interoperability

- **Entities:** `Device` (+ hardware identity), `EdgeModel` (signed), `Firmware`,
  `Attestation`, `Telemetry`, `SensorInput`, `UpdateCampaign` (OTA).
- **Interop:** MQTT/CoAP, secure element / TPM for identity, signed OTA channel,
  fleet-management plane. Every sensor is an untrusted, potentially adversarial input.

## 3. Domain acceptance criteria (added to the task's own)

1. Given a device, when it joins/communicates, then it has a **hardware-rooted
   identity + attestation** — no spoofed/cloned devices; mutual auth, not shared secrets.
2. Given the on-device model, when deployed, then it is **integrity-protected**
   (signed, verified at load) and its confidentiality considered — assume a determined
   attacker can read flash; do not ship secrets or a high-value model unprotected.
3. Given OTA updates, when pushed, then they are **signed, verified, rollback-safe,
   and staged** across the fleet — a compromised update channel cannot brick or
   backdoor devices.
4. Given sensor input, when it drives a decision, then **physical/adversarial spoofing**
   is considered (adversarial patches, replayed/forged signals) and bounded by a safe
   fallback (compose the manufacturing/transportation safety packs).
5. Given telemetry, when collected, then it is **minimized + encrypted** and privacy
   of any person it observes is honored.

## 4. Threat / harm model

- **Assets:** device fleet integrity, the on-device model (IP + behavior), physical
  safety of whatever the device controls, telemetry privacy, the OTA channel.
- **Untrusted inputs:** all sensor data, network peers, physical access, the update
  channel if unauthenticated.
- **Worst plausible harm:** (a) a forged OTA or model swap **backdoors a whole fleet**;
  (b) model extracted from a device (IP theft) or reverse-engineered to craft evasions;
  (c) an adversarial physical input (patch/spoofed signal) causes a wrong, unsafe
  actuation; (d) telemetry surveillance. Harm is physical + fleet-scale + IP.

## 5. Gate overlay

- **G0:** device threat model incl. **physical access**; safety class if it actuates.
- **G1:** hardware identity/attestation, signed model + signed OTA + rollback,
  sensor-spoofing resistance with a safe fallback, and telemetry minimization are
  **design constraints**.
- **G5:** the **edge-AI sign-off** — `roles/security-reviewer.md` (device identity,
  model/OTA integrity, extraction) **plus** `roles/risk-officer.md` (physical-safety /
  functional-safety, via the manufacturing/transportation packs) **plus** `roles/sre.md`
  (fleet OTA reliability). Any may veto.
- **G6:** OTA rollback rehearsed; fleet attestation monitored.

## 6. Specialist roles (all existing — no new roles)

| Role | Pulled in when… |
|------|-----------------|
| `roles/security-reviewer.md` (+ `skills/ai-security.md`) | device identity, model/OTA integrity, extraction |
| `roles/risk-officer.md` | physical/functional safety (compose manufacturing/transportation) |
| `roles/sre.md` | fleet OTA + reliability |
| `roles/ml-engineer.md` | the edge model + quantization/robustness |

## 7. Glossary

- **Attestation** — cryptographic proof a device is genuine and running trusted code.
- **OTA** — Over-The-Air update (a fleet-scale attack surface if unsigned).
- **Model extraction** — recovering a model's weights/behavior from a device or queries.
- **Adversarial physical input** — a patch/signal engineered to fool a sensor/model.
- **Secure element / TPM** — hardware root of trust for identity + keys.

## 8. Non-negotiables (domain)

1. **Never trust a device without hardware-rooted identity + attestation.**
2. **Never ship an unsigned model or unsigned OTA** — verify at load; keep rollback safe.
3. **Assume the attacker holds the hardware** — no unprotected secrets or high-value
   model on device.
4. **Never let a spoofed sensor input drive an unsafe actuation** — safe fallback required.
5. **Never collect telemetry beyond what's needed** — minimize, encrypt, respect privacy.
