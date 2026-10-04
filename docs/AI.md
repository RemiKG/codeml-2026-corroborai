# Local text suggestions: what is learned and what is measured

CorroborAI fits a **character n-gram TF-IDF** representation on local reference labels and ranks candidates by cosine similarity. Fitting is unsupervised: labels supply vocabulary and inverse document frequency, not verdicts. The index is rebuilt per run and stays in memory. No pretrained weight download, external model request, employee-name matching or identity prediction is used.

The decision aid appears only for unresolved or discrepant site, department and role descriptions. It shows up to three reference labels and their source rows. A reviewer can inspect a plausible typo or wrong-role candidate while seeing the exact code comparison and deterministic verdict. The learned component **cannot mark a discrepancy acceptable** or change an identity, date, contract, access decision or assignment match.

## Fixed comparison

`TfidfVectorizer(analyzer="char_wb", ngram_range=(3,5), strip_accents="unicode")`, cosine score threshold 0.30, top-two margin 0.03. The plain baseline is `difflib.SequenceMatcher` on the same reference labels, with the same predeclared thresholds. These thresholds are not statistically calibrated or claimed optimal for either method. Similarity scores across methods are not probabilities and need not be numerically comparable.

`tests/fixtures/retrieval_cases.json` was authored and hashed before the first evaluation. It contains a separate 3-query development subset and a 16-query evaluation subset. Queries are spelling, accent, word-omission and morphology perturbations, plus ambiguous/out-of-scope queries. All labels and queries are **synthetic and owner-authored**. Reference labels necessarily exist in the retrieval index, but exact self-queries are excluded from this evaluation. This does not represent unseen real-world HR validation or independent human annotation.

| Frozen evaluation result | TF-IDF / cosine | difflib |
| --- | ---: | ---: |
| Correct accepted top-1 suggestions, 12 positive queries | 12 / 12 | 12 / 12 |
| Expected label in top 3, 12 positive queries | 12 / 12 | 12 / 12 |
| Correct abstentions, 4 ambiguous/out-of-scope queries | 3 / 4 | 1 / 4 |
| Wrong accepted suggestions, all 16 queries | 1 / 16 | 3 / 16 |

Exact-rule-only review provides no candidate suggestions; all discrepancies still appear in its queue. On these synthetic queries the learned aid supplies candidate evidence and abstains more often than this fixed baseline. The sample is small and hand-designed, and shared thresholds may favor one method. The result does **not** establish general superiority or calibrated confidence. At least one deliberately ambiguous query still receives an unwarranted suggestion; the UI warns that candidates require inspection.

Reproduce with `python evaluate_ai.py --output ../synthetic-ai-evaluation.json`. The output includes every query, candidate scores, denominators, hash and annotation provenance. Development results remain separate. The capability smoke test used during setup is not part of these measurements.

## Supplied-data interpretation

The actual supplied-data run and reports are private. Suggestion coverage can be measured, but the correctness of those suggestions has no external gold labels. The private validation reports coverage and abstentions separately from the synthetic results. It also compares all deterministic verdicts with AI enabled and disabled: the aid cannot change them.

Owner-written rule expectations, tests and direct original-cell cross-checks are internal verification. They are not an independent annotator or sponsor answer key. Systematic source/destination differences may reflect genuine data errors or unresolved representation/anonymization issues; an automated mismatch is not proof of its operational cause. No “real HR accuracy” percentage is claimed.

Python/scikit-learn implementation and public synthetic fixtures are reproducible from the repository. The vocabulary and IDF weights fitted on sponsor inputs must remain local; do not commit a pickled real-data index or a report containing real records.
