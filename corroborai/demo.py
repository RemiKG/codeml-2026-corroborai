"""Entirely synthetic public fixture. No sponsor records or learned labels."""
import csv
import io
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils.datetime import to_excel

SOURCE_HEADERS = ["Matricule", "NomFamille", "PrénomUsuel", "DateEmbaucheRécente", "TypeAffectation", "DateEntréePoste", "DateSortiePoste", "CodePoste", "IntituléPoste", "CodeEmploi", "IntituléEmploi", "ÉchelleSalariale", "CodeImputation", "CodeDirection", "LibelléDirection", "CodeSite", "LibelléSite", "CatégorieEmploi", "EstPermanent", "EstTempsPlein", "CodeStatutEmploi", "CodeRaisonStatut", "DateRetourAnticipée", "CodeSuspensionAccès", "HeuresNormeHebdo", "HeuresNormeQuotidienne"]
TARGET_HEADERS = ["personId", "givenName", "surname", "contactEmail", "onboardDate", "siteName", "siteCode", "divisionId", "divisionName", "divisionCode", "positionId", "positionName", "positionCode", "statusReasonCode", "expectedReturnDate", "detailedStatus", "contractTypeCode", "isPrimaryAssignment", "isTemporaryAssignment", "assignmentStartDate", "assignmentEndDate", "termEndDate", "payGradeId", "weeklyHoursOverride", "dailyHoursOverride"]
POSITION_HEADERS = ["IdentifiantPoste", "IdentifiantEmploi", "CodeDirectionAffectée", "DateEffetAffectation", "CodeBudget", "IndicateurGestion", "CodePosteSecondaire", "MatriculeGestionnaire", "HeuresSemaineContrat", "HeuresJourContrat", "JoursTravailléesSemaine"]


def xlsx(sheets):
    wb = Workbook(); wb.remove(wb.active)
    for title, rows in sheets.items():
        ws = wb.create_sheet(title)
        for row in rows:
            ws.append(row)
    out = io.BytesIO(); wb.save(out)
    return out.getvalue()


def demo_mapping():
    mapping = [["Description", "Source", "Destination", "Rule"]]
    names = {"givenName": "PrénomUsuel", "surname": "NomFamille", "onboardDate": "DateEmbaucheRécente", "personId": "Matricule", "siteName": "LibelléSite", "siteCode": "CodeSite", "divisionId": "CodeDirection", "divisionName": "LibelléDirection", "divisionCode": "CodeImputation", "positionId": "CodeEmploi", "positionName": "IntituléEmploi", "positionCode": "CodeEmploi", "statusReasonCode": "CodeRaisonStatut", "expectedReturnDate": "DateRetourAnticipée", "detailedStatus": "CodeSuspensionAccès", "contractTypeCode": "CatégorieEmploi", "isPrimaryAssignment": "TypeAffectation", "isTemporaryAssignment": "TypeAffectation", "assignmentStartDate": "DateEntréePoste", "assignmentEndDate": "DateSortiePoste", "termEndDate": "DateSortiePoste", "payGradeId": "ÉchelleSalariale", "weeklyHoursOverride": "HeuresNormeHebdo", "dailyHoursOverride": "HeuresNormeQuotidienne", "contactEmail": "PrénomUsuel + NomFamille + Matricule"}
    for field in TARGET_HEADERS:
        mapping.append(["Synthetic demonstration field", names[field], field, "CorroborAI documented rule catalog version 1.0"])
    return xlsx({"Mapping": mapping, "Règles situation d'emploi": [["Synthetic access rules", "Status", "Reason", "Return"], ["00/01", "Actif", None, None], ["02/03/06/07", "Absence complète", "lookup", "source"]], "Jointure - Détail du poste": [["Synthetic join", "CodePoste -> IdentifiantPoste"]], "Jointure - Motif des situations": [["Synthetic join", "CodeRaisonStatut -> CodeCatégorieStatut"]]})


def make_files():
    """Expected destinations authored explicitly, independently of the engine."""
    people = [
        ("1001", "Exemple", "Camille", "P", "11", "501", "Services informatiques", "10", "Opérations", "00", "V"),
        ("1002", "Fiction", "Jordan", "P", "12", "502", "Services financiers", "20", "Finances", "00", "V"),
        ("1003", "Simulation", "Alex", "A", "13", "503", "Formation", "10", "Opérations", "02", "T"),
        ("1004", "Démo", "Robin", "P", "14", "504", "Soutien", "20", "Finances", "00", "Q"),
        ("1004", "Démo", "Robin", "S", "15", "505", "Coordination", "10", "Opérations", "00", "Q")]
    source = [SOURCE_HEADERS]
    position = [POSITION_HEADERS]
    for pid, surname, given, typ, post, role, role_name, unit, unit_name, access, cat in people:
        source.append([pid, surname, given, datetime(2020, 1, 1), typ, datetime(2024, 3, 1), None, post, "Synthetic post", role, role_name, "G1", "C" + unit, unit, unit_name, "S1", "Centre démonstration", cat, 1, 1, "ACTIVE" if access == "00" else "LEAVE", "ABS" if access == "02" else "NOT_IN_LOOKUP", datetime(2025, 2, 1) if access == "02" else None, access, 35, 7])
        for effective in [datetime(2024, 1, 1), datetime(2024, 2, 1)]:
            position.append([post, role, unit, str(int(to_excel(effective))), "DEMO", "0", "0", "DEMO_MANAGER", "35", "7", "5"])
    destination = [TARGET_HEADERS,
        ["1001", "Camille", "Exemple", "dev-08-v2_cexemple001@loto-quebec.com", datetime(2020, 1, 1), "Centre démonstration", "S1", "10", "10-Opérations", "C10", "501", "501-Services informatiques", "501", None, None, "Actif", "JWN", True, False, datetime(2024, 1, 1), None, None, "G1", 35, 7],
        ["1002", "Jordan", "Fiction", "jfiction002@loto-quebec.com", datetime(2020, 1, 1), "Centre démonstration", "S1", "20", "20-Finances", "C20", "502", "502-Services finaciers", "502", None, None, "Actif", "JWN", True, False, datetime(2024, 1, 1), None, None, "G1", 38, 7],
        ["1003", "Alex", "Simulation", "asimulation003@loto-quebec.com", datetime(2020, 1, 1), "Centre démonstration", "S1", "10", "10-Opérations", "C10", "503", "503-Formation", "503", "EXTABS", datetime(2025, 2, 1), "Absence complète", "KELH", False, True, datetime(2024, 1, 1), None, None, "G1", 35, 7],
        ["1004", "Robin", "Démo", "rdemo004@loto-quebec.com", datetime(2020, 1, 1), "Centre démonstration", "S1", "20", "20-Finances", "C20", "504", "504-Soutien", "504", None, None, "Actif", "TRSY", True, False, datetime(2024, 1, 1), None, None, "G1", 35, 7]]
    csv_rows = []
    for row in position:
        buffer = io.StringIO(); csv.writer(buffer, lineterminator="").writerow(row); csv_rows.append([buffer.getvalue()])
    return {"source": ("Synthetic_Source.xlsx", xlsx({"Employe_Source": source})),
            "destination": ("Synthetic_Destination.xlsx", xlsx({"Employe_Destination": destination})),
            "positions": ("Synthetic_Positions.xlsx", xlsx({"Feuil1": csv_rows})),
            "reasons": ("Synthetic_Reasons.xlsx", xlsx({"Sheet1": [["CodeCatégorieStatut", "CodeStatutSystèmeExterne", "CodeGestionAccès"], ["ABS", "EXTABS", "02"]]})),
            "mapping": ("Synthetic_Mapping.xlsx", demo_mapping())}


def write_fixture(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    for name, content in make_files().values():
        (folder / name).write_bytes(content)
