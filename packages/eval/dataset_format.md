# Eval Dataset Format

Die Eval-Datasets sind als **JSONL** gespeichert (ein JSON-Objekt pro Zeile).

## Pflichtfelder

Jeder Datensatz benötigt:

- `id` *(string)*: Eindeutige ID.
- `prompt` *(string)*: Eingabe/Anfrage.
- `response` *(string)*: Modellantwort.
- `policy_tags` *(array[string])*: Relevante Policy-Kategorien.
- `triage_label` *("accept" | "review" | "reject")*: Basistag für Triage.

## CI-Gates

Der Eval-Runner prüft drei Gates:

1. **JSON validity**: Jede Zeile muss valides JSON-Objekt sein.
2. **Policy compliance**: Pflichtfelder + Typen + keine geblockten Substrings in `response`.
3. **Basis-Triage-Metrik**: `triage_quality_score` muss über `--min-triage-score` liegen.

## Beispiel

```json
{"id":"ex-1","prompt":"Summarize this text","response":"Short summary","policy_tags":["safety"],"triage_label":"accept"}
```
