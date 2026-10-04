# CorroborAI — English slide source

Public presentation; all record examples are synthetic. Team: SOTA Overfitters, Kenneth Chen and Ning Ye. Seven slides, adaptable five-minute core; duration is a preparation target, not a sponsor-confirmed slot. The editable visual source is `PRESENTATION.html`; `PRESENTATION.pdf` is the ready-to-open version.

---

## 1. Evidence before exceptions

**CorroborAI**  
Explainable reconciliation for HR and time-system data.

SOTA Overfitters — Kenneth Chen & Ning Ye  
Loto-Québec · CodeML 2026

A field difference becomes a decision you can inspect.

---

## 2. Five inputs. One traceable path.

HR source + Time destination + Position history + Status reasons + Mapping.

Read only → Match assignments → Apply exact rules → Inspect uncertain labels → Export.

- Preserve multiple assignments for the same person.
- Check only the 25 mapped fields.
- Keep an explicit review state when evidence is insufficient.
- One engine serves the CLI and local browser interface.

---

## 3. Three verdicts, with evidence

**Synthetic examples — not sponsor records.**

| Check | Observed | Decision |
| --- | --- | --- |
| C00001 · givenName | Camille → Camille | Compliant |
| C00014 · contactEmail | expected `cexemple001@loto-quebec.com`; destination adds `dev-08-v2_` | Justified difference |
| C00037 · weeklyHoursOverride | source 35; destination 38 | Anomaly under the direct rule |

Email rule: unaccented initial + name + final three Matricule/personID digits. A declared destination prefix is optional. Each decision links to its original row and rule.

---

## 4. Live: load → inspect → export

Choose the five synthetic workbooks and run the comparison.

1. Inspect a compliant field.
2. Show why the email prefix is accepted.
3. Inspect 35 versus 38 weekly hours.
4. Open the uncertain role-label candidates.
5. Download and reopen Excel or CSV.

Synthetic run: 5 source assignment rows, 4 destination rows; 101 checks. One unmatched assignment remains visible. These are assignment and field counts, not employee accuracy.

---

## 5. Local learned candidates, bounded authority

TF-IDF character fragments → cosine candidates, fitted locally without verdict labels.

Synthetic query: `502-Services finaciers`  
Candidate to inspect: `502-Services financiers`.

| Frozen synthetic evaluation | TF-IDF | difflib |
| --- | ---: | ---: |
| Correct accepted top 1, 12 positives | 12/12 | 12/12 |
| Correct abstentions, 4 other queries | 3/4 | 1/4 |
| Wrong suggestions, all 16 | 1 | 3 |

Owner-authored cases. Fixed shared thresholds, no calibration. Small synthetic evaluation, not real HR accuracy. Suggestions never override a rule.

---

## 6. Trust comes with boundaries

**45 passing tests** · input errors, assignment cardinality, business branches, dates and exports.

- Original inputs stay unchanged; outputs preserve evidence.
- Historical bounds follow the selected continuous unit period.
- Empty input and unknown rule changes fail with explanations.
- Fresh-environment reproduction and real download checks completed.
- Sponsor data and learned vocabulary stay local.

Operational correctness still needs domain review. Unknown prefixes, histories and joins remain review cases. Anomaly ≠ expert-confirmed HR error.

---

## 7. Inspect the decision. Keep the evidence.

Executable local prototype · code and synthetic demo publicly available.

**github.com/RemiKG/codeml-2026-corroborai**

Deterministic decisions, explicit uncertainty and exportable proof for the person investigating the data.

Sources: supplied Loto-Québec instructions/mapping; sponsor clarification, October 3, 2026, 8:15 PM. Python/openpyxl/scikit-learn; Codex GPT-6 Astra assisted implementation. No external model receives employee inputs.
