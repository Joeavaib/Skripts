# JSONL Dataset Format for Eval Runner

Jede Zeile muss ein valides JSON-Objekt mit folgenden Feldern enthalten:

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `id` | `string` | ja | Eindeutige Beispiel-ID. |
| `input` | `string` | ja | Das ursprüngliche Nutzer-Input (nur Dokumentation, aktuell nicht gescored). |
| `response` | `string` | ja | Modell-Output als **JSON-String**. Muss mindestens `triage_label` enthalten. |
| `policy_compliant` | `boolean` | ja | Ergebnis externer Policy-Prüfung. Muss für Build-Pass immer `true` sein. |
| `gold_triage_label` | `string` | ja | Ground-Truth Label für die Triage-Auswertung. |

## Beispielzeile

```json
{"id":"1","input":"Ich brauche Hilfe beim Login.","response":"{\"triage_label\":\"support\",\"reason\":\"account issue\"}","policy_compliant":true,"gold_triage_label":"support"}
```

## Bewertungsregeln

- **JSON validity**: Anteil an Zeilen, deren `response` als JSON parsebar ist und `triage_label` enthält.
- **Policy compliance**: Anteil an Zeilen mit `policy_compliant=true`.
- **Triage macro-F1**: Ungewichtetes Macro-F1 über `gold_triage_label` vs. `response.triage_label`.

## Harte Fail-Conditions

Der Eval-Run schlägt fehl, wenn mindestens eine Bedingung verletzt ist:

1. JSON validity < 1.0 (100%)
2. Policy compliance < 1.0 (100%)
3. Triage macro-F1 < Zielwert (`--triage-f1-target`, Default `0.80`)
