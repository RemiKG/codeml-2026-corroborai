"""Conservative, traceable reconciliation. Mapping rules are not learned."""
from __future__ import annotations
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .io import InputError, ascii_text, boolean, day, key, number, plain, ref, sheet_rows, table, text, workbook
from .suggest import LabelIndex, MODEL_INFO

CATALOG_PATH = Path(__file__).resolve().parents[1] / "rules" / "catalog.json"
DIRECT = {
    "givenName": ("PrénomUsuel", "R01"), "surname": ("NomFamille", "R02"),
    "onboardDate": ("DateEmbaucheRécente", "R04"), "personId": ("Matricule", "R05"),
    "siteName": ("LibelléSite", "R06"), "siteCode": ("CodeSite", "R07"),
    "divisionId": ("CodeDirection", "R08"), "divisionCode": ("CodeImputation", "R10"),
    "positionId": ("CodeEmploi", "R11"), "positionCode": ("CodeEmploi", "R13"),
    "payGradeId": ("ÉchelleSalariale", "R20"), "weeklyHoursOverride": ("HeuresNormeHebdo", "R21"),
    "dailyHoursOverride": ("HeuresNormeQuotidienne", "R22")}
DERIVED = {"contactEmail": ("PrénomUsuel", "R03"), "divisionName": ("LibelléDirection", "R09"),
           "positionName": ("IntituléEmploi", "R12"), "statusReasonCode": ("CodeRaisonStatut", "R14"),
           "expectedReturnDate": ("DateRetourAnticipée", "R15"), "detailedStatus": ("CodeSuspensionAccès", "R16"),
           "contractTypeCode": ("CatégorieEmploi", "R17"), "isPrimaryAssignment": ("TypeAffectation", "R18"),
           "isTemporaryAssignment": ("TypeAffectation", "R18"), "assignmentStartDate": ("DateEntréePoste", "R19"),
           "assignmentEndDate": ("DateSortiePoste", "R23"), "termEndDate": ("DateSortiePoste", "R24")}
FIELDS = {**DIRECT, **DERIVED}
SOURCE_REQUIRED = sorted({s for s, _ in FIELDS.values()} | {"NomFamille", "CodeDirection", "CodeEmploi", "CodePoste", "EstPermanent", "EstTempsPlein"})
POSITION_REQUIRED = ["IdentifiantPoste", "IdentifiantEmploi", "CodeDirectionAffectée", "DateEffetAffectation"]
REASON_REQUIRED = ["CodeCatégorieStatut", "CodeStatutSystèmeExterne", "CodeGestionAccès"]
DATE_FIELDS = {"onboardDate", "expectedReturnDate", "assignmentStartDate", "assignmentEndDate", "termEndDate"}
NUM_FIELDS = {"weeklyHoursOverride", "dailyHoursOverride"}
BOOL_FIELDS = {"isPrimaryAssignment", "isTemporaryAssignment"}
LABEL_FIELDS = {"siteName", "divisionName", "positionName"}
DEPENDENCIES = {
    "contactEmail": ["PrénomUsuel", "NomFamille", "Matricule"],
    "divisionName": ["CodeDirection", "LibelléDirection"], "positionName": ["CodeEmploi", "IntituléEmploi"],
    "contractTypeCode": ["CatégorieEmploi", "EstPermanent", "EstTempsPlein"],
    "statusReasonCode": ["CodeSuspensionAccès", "CodeRaisonStatut"],
    "expectedReturnDate": ["CodeSuspensionAccès", "DateRetourAnticipée"],
    "assignmentStartDate": ["CodePoste", "CodeEmploi", "CodeDirection", "DateEntréePoste", "DateSortiePoste"],
    "assignmentEndDate": ["CodePoste", "CodeEmploi", "CodeDirection", "DateEntréePoste", "DateSortiePoste"],
    "termEndDate": ["CodePoste", "CodeEmploi", "CodeDirection", "DateEntréePoste", "DateSortiePoste"]}
RULE_CELLS = {"R01":"B2:D2","R02":"B3:D3","R03":"D4/D6; sponsor clarification 2026-10-03 8:15 PM","R04":"B7:D7","R05":"B8:D8","R06":"B9:D9","R07":"B10:D10","R08":"B11:D11","R09":"B12:D12","R10":"B13:D13","R11":"B14:D14","R12":"B15:D15","R13":"B16:D16","R14":"B17:D21; Règles situation d'emploi A1:D3","R15":"B22:D22; Règles situation d'emploi A1:D3","R16":"B23:D23; Règles situation d'emploi A1:D3","R17":"D24/B26/B39/B40","R18":"B41:D45","R19":"B46:D48","R20":"B49:D49","R21":"B51:D51","R22":"B52:D52","R23":"B53:D53","R24":"B56:D58"}


def normalize(value, field, epoch):
    if field in DATE_FIELDS:
        return day(value, epoch)
    if field in BOOL_FIELDS:
        return boolean(value)
    if field in NUM_FIELDS:
        return number(value)
    return text(value) if value is not None and text(value) else None


def mapping_info(raw, name):
    wb = workbook(raw, name)
    try:
        sheets = {}
        for sn in ["Mapping", "Règles situation d'emploi", "Jointure - Détail du poste", "Jointure - Motif des situations"]:
            rr = sheet_rows(wb, sn, name)
            canonical = []
            for n, row in enumerate(rr, 1):
                vals = [text(v).replace("\r\n", "\n") for v in row]
                while vals and not vals[-1]:
                    vals.pop()
                if any(vals):
                    canonical.append([n, vals])
            sheets[sn] = canonical
        signature = hashlib.sha256(json.dumps(sheets, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        if signature not in catalog["accepted_mapping_signatures"]:
            raise InputError("Mapping workbook has unreviewed rules or fields. Review the rule catalog before running; changed rules are never silently ignored.")
        return {"name": name, "sha256": hashlib.sha256(raw).hexdigest(), "rule_signature": signature,
                "bytes": len(raw), "catalog_version": catalog["version"], "fields": sorted(FIELDS)}
    finally:
        wb.close()


def load_inputs(files):
    specs = {"source": ("Employe_Source", SOURCE_REQUIRED, False),
             "destination": ("Employe_Destination", list(FIELDS), False),
             "positions": ("Feuil1", POSITION_REQUIRED, True),
             "reasons": ("Sheet1", REASON_REQUIRED, False)}
    if set(files) != set(specs) | {"mapping"}:
        raise InputError("Exactly source, destination, positions, reasons and mapping workbooks are required.")
    tables, meta = {}, {}
    for kind, (sheet, required, embedded) in specs.items():
        name, raw = files[kind]
        tables[kind], meta[kind] = table(raw, name, sheet, required, embedded)
    meta["mapping"] = mapping_info(files["mapping"][1], files["mapping"][0])
    if not tables["source"] or not tables["destination"]:
        raise InputError("Source and destination must each contain at least one assignment row.")
    return tables, meta


def target_type(row):
    try:
        flags = (boolean(row["isPrimaryAssignment"]), boolean(row["isTemporaryAssignment"]))
        return {(True, False): "P", (False, True): "A", (False, False): "S"}.get(flags)
    except InputError:
        return None


def match_assignments(source, destination):
    """Never reuse a row, merge duplicate assignments or cross person identifiers."""
    sg, dg = defaultdict(list), defaultdict(list)
    for row in source:
        sg[key(row["Matricule"])].append(row)
    for row in destination:
        dg[key(row["personId"])].append(row)
    pairs, residuals = [], []
    for pid in sorted(sg.keys() | dg.keys()):
        ss, dd = list(sg[pid]), list(dg[pid])
        if not pid:
            residuals.extend((r, None, "review_required", "Missing person identifier.") for r in ss)
            residuals.extend((None, r, "review_required", "Missing person identifier.") for r in dd)
            continue
        role_keys = {key(r["CodeEmploi"]) for r in ss} | {key(r["positionId"]) for r in dd}
        for role in sorted(role_keys):
            sr = [r for r in ss if key(r["CodeEmploi"]) == role]
            dr = [r for r in dd if key(r["positionId"]) == role]
            matched = []
            if len(sr) == len(dr) == 1:
                matched = [(sr[0], dr[0], "person_and_role_unique")]
            else:
                for typ in ("P", "A", "S"):
                    a = [r for r in sr if text(r["TypeAffectation"]) == typ]
                    b = [r for r in dr if target_type(r) == typ]
                    if len(a) == len(b) == 1:
                        matched.append((a[0], b[0], "person_role_unique_assignment_type"))
            for a, b, method in matched:
                pairs.append((a, b, method)); ss.remove(a); dd.remove(b)
        if len(ss) == len(dd) == 1:
            # Preserve the role mismatch as an explicit comparison, never hide it.
            pairs.append((ss.pop(), dd.pop(), "inferred_single_remaining_same_person"))
        if ss and dd:
            residuals.extend((r, None, "review_required", "Ambiguous remaining assignments; no arbitrary pairing.") for r in ss)
            residuals.extend((None, r, "review_required", "Ambiguous remaining assignments; no arbitrary pairing.") for r in dd)
        else:
            residuals.extend((r, None, "anomaly", "Source assignment has no destination counterpart under the documented matching policy.") for r in ss)
            residuals.extend((None, r, "anomaly", "Destination assignment has no source counterpart under the documented matching policy.") for r in dd)
    return pairs, residuals


def history_bounds(source, positions, as_of=None):
    rows = [r for r in positions if key(r["IdentifiantPoste"]) == key(source["CodePoste"])]
    if not rows:
        raise InputError("Position history is missing for this source post.")
    if any(key(r["IdentifiantEmploi"]) != key(source["CodeEmploi"]) for r in rows):
        raise InputError("Position history has a contradictory employment code; review its applicability.")
    dated = [(day(r["DateEffetAffectation"], r["_epoch"]), r) for r in rows]
    if any(d is None for d, _ in dated):
        raise InputError("Position history contains an empty effective date.")
    dated.sort(key=lambda pair: pair[0])
    if len({d for d, _ in dated}) != len(dated):
        raise InputError("Position history has duplicate effective dates; no arbitrary precedence.")
    runs = []
    for d, row in dated:
        unit = key(row["CodeDirectionAffectée"])
        if not runs or runs[-1]["unit"] != unit:
            if runs:
                runs[-1]["end"] = d - timedelta(days=1)
                runs[-1]["proof"].append(ref(row, ["DateEffetAffectation", "CodeDirectionAffectée"]))
            runs.append({"unit": unit, "start": d, "end": None, "proof": []})
        runs[-1]["proof"].append(ref(row, ["DateEffetAffectation", "CodeDirectionAffectée", "IdentifiantPoste"]))
    candidates = [r for r in runs if r["unit"] == key(source["CodeDirection"])]
    if as_of:
        candidates = [r for r in candidates if r["start"] <= as_of and (r["end"] is None or as_of <= r["end"])]
    if len(candidates) != 1:
        raise InputError("Current unit has zero or multiple historical periods; provide a justified reference date or review.")
    run = candidates[0]
    start = day(source["DateEntréePoste"], source["_epoch"])
    end = day(source["DateSortiePoste"], source["_epoch"])
    if start is None:
        raise InputError("Source assignment start date is missing.")
    if end is not None and end < start:
        raise InputError("Source assignment end precedes its start.")
    expected_start = min(start, run["start"])
    bounds = [d for d in (end, run["end"]) if d is not None]
    expected_end = min(bounds) if bounds else None
    if expected_end is not None and expected_end < expected_start:
        raise InputError("Computed assignment dates are contradictory.")
    return expected_start, expected_end, run["proof"]


def contract_code(row):
    cat = text(row["CatégorieEmploi"])
    if cat == "V":
        if not boolean(row["EstPermanent"]):
            raise InputError("Permanent category V with permanent=false is not covered by the mapping.")
        return "JWN" if boolean(row["EstTempsPlein"]) else "XFLR"
    codes = {"T": "KELH", "O": "WHX", "M": "CEGQ", "R": "CNZC", "J": "RMQ", "Z": "JAW", "Q": "TRSY"}
    if cat not in codes:
        raise InputError("Employment category has no documented contract branch.")
    return codes[cat]


def expected_value(row, field, tables, as_of=None):
    if field in DIRECT:
        return normalize(row[DIRECT[field][0]], field, row["_epoch"]), [], "Direct mapped value, with explicit type normalization."
    if field == "contactEmail":
        given, surname, pid = ascii_text(row["PrénomUsuel"]), ascii_text(row["NomFamille"]), key(row["Matricule"])
        if not given or not surname or len(pid) < 3 or not pid[-3:].isdigit():
            raise InputError("Cannot derive email: a name or the last three employee-code digits are missing.")
        return (given[0] + surname + pid[-3:] + "@loto-quebec.com").lower(), [], "Email constructed from unaccented initial/name and final three Matricule/personId digits."
    if field == "divisionName":
        return text(row["CodeDirection"]) + "-" + text(row["LibelléDirection"]), [], "Administrative code + '-' + administrative description."
    if field == "positionName":
        return text(row["CodeEmploi"]) + "-" + text(row["IntituléEmploi"]), [], "Employment code + '-' + employment description."
    if field == "contractTypeCode":
        return contract_code(row), [], "Documented category/permanent/full-time contract branch."
    if field in BOOL_FIELDS:
        typ = text(row["TypeAffectation"])
        if typ not in ("P", "A", "S"):
            raise InputError("Unknown assignment type; expected P, A or S.")
        return (typ == "P" if field == "isPrimaryAssignment" else typ == "A"), [], "P=primary, A=temporary, S=neither flag."
    if field in ("assignmentStartDate", "assignmentEndDate", "termEndDate"):
        start, end, proof = history_bounds(row, tables["positions"], as_of)
        return (start if field == "assignmentStartDate" else end), proof, "Minimum documented assignment/history bound; next different unit ends the prior period one day earlier."
    if field in ("detailedStatus", "statusReasonCode", "expectedReturnDate"):
        access = text(row["CodeSuspensionAccès"]).zfill(2)
        if access in ("00", "01"):
            return ("Actif" if field == "detailedStatus" else None), [], "Active access 00/01: status Actif; absence reason and return date are NULL."
        if access not in ("02", "03", "06", "07"):
            raise InputError("Access status not covered by the supplied situation table.")
        if field == "detailedStatus":
            return "Absence complète", [], "Access 02/03/06/07: full absence."
        if field == "expectedReturnDate":
            return day(row["DateRetourAnticipée"], row["_epoch"]), [], "Full absence retains expected return date."
        matched = [r for r in tables["reasons"] if key(r["CodeCatégorieStatut"]) == key(row["CodeRaisonStatut"])]
        if len(matched) != 1:
            raise InputError("Absence reason lookup is missing or ambiguous.")
        reason = matched[0]
        if text(reason["CodeGestionAccès"]).zfill(2) != access:
            raise InputError("Absence reason lookup contradicts the source access code.")
        return text(reason["CodeStatutSystèmeExterne"]), [ref(reason, REASON_REQUIRED)], "Absence reason translated through the supplied reference table."
    raise InputError("Unsupported mapped field.")


def reconcile(files, prefixes=("dev-08-v2_",), as_of=None, use_ai=True):
    started = time.perf_counter()
    tables, inputs = load_inputs(files)
    if any(not p or "@" in p or len(p) > 100 for p in prefixes):
        raise InputError("Prefixes must be nonempty local-part strings without @, at most 100 characters.")
    if isinstance(as_of, str):
        try:
            as_of = datetime.fromisoformat(as_of).date()
        except ValueError as exc:
            raise InputError("Reference date must be ISO YYYY-MM-DD.") from exc
    pairs, residuals = match_assignments(tables["source"], tables["destination"])
    results = []
    for source, target, method in pairs:
        for field, (source_field, rule) in FIELDS.items():
            result = {"person_id": key(source["Matricule"]), "assignment": key(source["CodeEmploi"]) + "/" + text(source["TypeAffectation"]),
                      "field": field, "source_value": plain(source[source_field]), "target_value": plain(target[field]),
                      "rule_id": rule, "rule_ref": {"file": inputs["mapping"]["name"], "sheet": "Mapping", "location": RULE_CELLS[rule], "note": "Cell locations reference the sponsor mapping; synthetic mapping uses the same catalog semantics."},
                      "source_ref": ref(source, DEPENDENCIES.get(field, [source_field])), "target_ref": ref(target, [field]),
                      "match_method": method, "analysis_origin": "deterministic", "supporting_refs": [], "suggestions": None,
                      "normalized_source": None, "normalized_target": None, "expected": None}
            try:
                expected, proof, explanation = expected_value(source, field, tables, as_of)
                actual = normalize(target[field], field, target["_epoch"])
                # The raw source of a transformed field has a different type (e.g. P -> bool).
                try:
                    before = normalize(source[source_field], field, source["_epoch"])
                except InputError:
                    before = text(source[source_field])
                result.update(expected=plain(expected), normalized_source=plain(before), normalized_target=plain(actual), supporting_refs=proof)
                email_prefix = None
                if field == "contactEmail":
                    actual = actual.lower() if actual else actual
                    if actual != expected:
                        email_prefix = next((p for p in prefixes if actual == p.lower() + expected), None)
                        if email_prefix:
                            actual = expected
                        elif actual and actual.endswith(expected) and actual.count("@") == 1:
                            raise InputError("Possible optional destination prefix is not in the declared prefix list; review/configure it explicitly.")
                if actual == expected:
                    result["verdict"] = "compliant" if before == actual and email_prefix is None else "justified_difference"
                    result["reason"] = explanation + (f" Declared destination-only prefix '{email_prefix}' accepted." if email_prefix else " Expected value is present.")
                else:
                    result["verdict"] = "anomaly"
                    result["reason"] = explanation + " Destination differs from the documented expected value."
            except InputError as exc:
                result.update(verdict="review_required", reason=str(exc))
            if method.startswith("inferred_"):
                result["reason"] += " Pairing is inferred from the sole remaining row for this person; confirm the assignment identity."
            results.append(result)
    for source, target, verdict, reason in residuals:
        row = source or target
        results.append({"person_id": key(row["Matricule"] if source else row["personId"]),
                        "assignment": key(row["CodeEmploi"] if source else row["positionId"]), "field": "__assignment__",
                        "verdict": verdict, "reason": reason, "rule_id": "MATCH", "rule_ref": {"file": "README.md", "location": "Matching and uncertainty policy"}, "source_ref": ref(source), "target_ref": ref(target),
                        "supporting_refs": [], "source_value": "present" if source else None, "target_value": "present" if target else None,
                        "expected": "one-to-one assignment counterpart", "normalized_source": None, "normalized_target": None,
                        "match_method": "unmatched", "analysis_origin": "deterministic", "suggestions": None})
    if use_ai:
        indexes, proofs = {}, {}
        for field in LABEL_FIELDS:
            labels = defaultdict(list)
            for row in tables["source"]:
                try:
                    value, _, _ = expected_value(row, field, tables, as_of)
                    if value:
                        labels[text(value)].append(ref(row, [FIELDS[field][0]]))
                except InputError:
                    pass
            indexes[field], proofs[field] = LabelIndex(labels), labels
        for result in results:
            field = result["field"]
            if field in LABEL_FIELDS and result["verdict"] in ("anomaly", "review_required"):
                suggestion = indexes[field].query(text(result["target_value"]))
                baseline = indexes[field].query(text(result["target_value"]), baseline=True)
                for suggestion_set in (suggestion, baseline):
                    for candidate in suggestion_set["candidates"]:
                        candidate["references"] = proofs[field][candidate["label"]]
                result["suggestions"] = {"learned": suggestion, "baseline": baseline}
                result["analysis_origin"] = "deterministic verdict; local AI investigation aid"
    for i, result in enumerate(results, 1):
        result["id"] = f"C{i:05d}"
    counts = dict(Counter(r["verdict"] for r in results))
    return {"metadata": {"version": "1.0.0", "created_at": datetime.now(timezone.utc).isoformat(), "inputs": inputs,
                         "mapped_fields": sorted(FIELDS), "assignment_pairs": len(pairs), "unmatched_assignment_rows": len(residuals),
                         "source_rows": len(tables["source"]), "destination_rows": len(tables["destination"]),
                         "result_rows": len(results), "verdict_counts": counts, "prefixes": list(prefixes), "reference_date": plain(as_of),
                         "ai": MODEL_INFO if use_ai else {"enabled": False}, "elapsed_seconds": round(time.perf_counter() - started, 4),
                         "privacy": "Local output contains input-derived values. Do not publish sponsor records or learned vocabulary.",
                         "scope": "Field/structural checks, not independently labeled employee accuracy. Mapping aliases and review policies are documented."},
            "results": results}
