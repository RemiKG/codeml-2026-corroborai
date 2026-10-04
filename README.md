# CorroborAI

**Evidence before exceptions.** A local HR → time-system reconciliation demonstrator by **SOTA Overfitters — Kenneth Chen & Ning Ye**, for CodeML 2026 / Loto-Québec - CorroborAI.

Load five workbooks, compare the 25 mapped fields, distinguish compliant values, rule-justified differences and anomalies, then inspect the evidence and export CSV/Excel. Unresolved cases stay in a separate review state. A local learned text index proposes reference labels for investigation; it cannot override identity, access, dates or any deterministic verdict.

The included demonstration is **entirely synthetic**. Sponsor employee extracts, real reports and learned sponsor vocabulary are not included and must remain local. No network call, cloud API, account or GPU is required during analysis.

## Run locally (Python 3.12)

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --port 8114
```

Open `http://127.0.0.1:8114` yourself. The server does not open a browser or modify global settings. Choose **Explore synthetic demo**, inspect the three verdict types, click the mismatched role label to see learned candidates and the baseline, then download Excel/CSV. Stop the server with Ctrl+C. Analysis is serialized and numerical threads are capped at two. Keep the server bound to loopback; it is not an internet deployment.

For Linux/macOS replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. A modern browser suffices for normal use; the installed Playwright dependency is for automated validation, and its Chromium download is needed only to run browser tests or render PDFs.

CLI demonstration and synthetic workbooks:

```powershell
.\.venv\Scripts\python.exe -m corroborai --demo --output ..\synthetic-report
.\.venv\Scripts\python.exe -m corroborai --write-demo ..\synthetic-inputs
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe evaluate_ai.py --output ..\synthetic-ai-evaluation.json
```

Outputs are `corroboration.json`, `corroboration.csv` and `corroboration.xlsx`. Excel includes Investigation, Justified, Audit and Run metadata sheets. Counts are **field/structural checks**, not people or independently labeled accuracy. The CLI prints aggregate counts only.

## Run the private sponsor package

Download the original approved challenge package separately. Keep it and its output outside any public repository. In the UI choose source, destination, position history, reasons and mapping. The CLI equivalent is:

```powershell
.\.venv\Scripts\python.exe -m corroborai `
  --source "C:\private\Employe_Source_Anonymise_VF.xlsx" `
  --destination "C:\private\Employe_Destination_Anonymise_VF.xlsx" `
  --positions "C:\private\détail_du_poste.xlsx" `
  --reasons "C:\private\Motif de la situation d'emploi.xlsx" `
  --mapping "C:\private\Mapping.xlsx" `
  --output "C:\private\corroborai-report"
```

The source headers and sheet names are validated. The position workbook stores one 11-field CSV record in column A; numeric effective dates are Excel serials using the workbook epoch. Native Excel dates and ISO dates are supported, and ambiguous date formats require review. Boolean values accept `true/false`, `1/0`, and the supplied French `Oui/Non` values. Identifiers remain text, including leading zeros. Formulas, unreviewed mapping changes, duplicate headers and malformed inputs fail explicitly.

The reviewed mapping is identified by a semantic cell-content SHA-256 signature in `rules/catalog.json`; workbook packaging changes do not affect it. This is **not** an interpreter for arbitrary new business rules. A modified mapping must be reviewed and tested before adding its signature. Both the original sponsor mapping and the authored synthetic mapping are recognized. Original input files are read-only; hashes are included in each report.

## Matching and uncertainty policy

1. Group by exact employee ID, then employment code. Match unique pairs and compare all mapped values, including assignment flags.
2. In a multiple-assignment group, use an unambiguous P/A/S type to anchor a one-to-one match. Never reuse a destination row or create a Cartesian join.
3. One remaining row on each side for the same person may be paired as **inferred**, preserving the role disagreement and a visible warning. Multiple unresolved rows remain review cases; unmatched rows are structural anomalies to investigate.

The rules cover names, derived email, site/department/role fields, contract branches, active/absence situations, assignment flags, pay grade, hours and historical date bounds. Only mapping targets are checked; unrelated custom attributes are ignored. Exact source/target rows, support rows, rule IDs and mapping cells accompany every decision. A real-world reviewer must still confirm the business meaning of a flagged anomaly.

Email uses the unaccented initial/name and the final three Matricule/personId digits. The documented optional destination prefix `dev-08-v2_` is accepted by default. Declare another known prefix with `--prefix` or the UI setting. Unknown suffix-matching prefixes require review; incorrect base digits or domains remain mismatches. No email is sent.

Assignment start is the earlier of source assignment start and the beginning of the applicable continuous administrative-unit period. The end is the earliest nonnull source end/next different unit date minus one day. Repeated rows for the same unit are coalesced. Multiple separated occurrences of a unit require a justified `--reference-date YYYY-MM-DD` or review, never an implicit “today.” Missing or contradictory history does not produce an invented date.

## Learned suggestions and evidence limits

The AI component is an unsupervised character TF-IDF index fitted on local reference labels; cosine retrieves candidate labels within the same field. No verdict labels are used. Suggestions display source references and a plain `difflib.SequenceMatcher` baseline. Names, email addresses and employee IDs are excluded from the index. Scores are similarities, not correctness probabilities. Suggestions never change a verdict.

See [docs/AI.md](docs/AI.md) for the frozen synthetic evaluation, exact denominators, abstention policy and limitations. Owner-authored tests are internal verification, not an independent human annotation exercise or a sponsor gold standard. The small synthetic retrieval test does not establish generalization to real HR records. No sponsor accuracy score is claimed.

## Source and tool disclosure

Business requirements: sponsor `consignes.pdf` pp.1–6 and `Mapping.xlsx`, supplied with the challenge; Loto-Québec Discord clarification dated October 3, 2026, 8:15 PM concerning personID and optional destination prefixes. These materials were read locally and are not redistributed here. Historical aliases in the mapping are interpreted explicitly in code and rule documentation; unsupported combinations abstain.

Implementation: Python, openpyxl, scikit-learn, NumPy/SciPy, standard-library HTTP/CSV/JSON; pytest and Playwright for verification. GPT-6 Astra through Codex assisted planning, implementation and testing. No external model processes the employee inputs. Existing dependency versions are pinned in `requirements.txt`; package licenses apply to those libraries. No pre-existing project code or fabricated commit history is presented as event work.

## Demo fallback and practical limits

If the browser cannot connect, run the CLI demo and open its Excel Investigation/Audit sheets. The public `demo/` inputs are synthetic and can be copied freely with this project; never replace them with the sponsor package. If a download URL expires after newer runs or a restart, compare again. Each server retains at most three runs in memory; restarting clears them. The local UI accepts at most 40 MB per request; individual XLSX and expanded sizes are bounded. This is a small-event prototype, not a production HR system.

Source: [github.com/RemiKG/codeml-2026-corroborai](https://github.com/RemiKG/codeml-2026-corroborai). See the [English presentation](presentation/PRESENTATION.pdf), its [editable HTML](presentation/PRESENTATION.html), and the [synthetic evaluation output](docs/SYNTHETIC_EVALUATION.json). Final Devpost submission remains manual. The public slides and interface image use synthetic records only.
