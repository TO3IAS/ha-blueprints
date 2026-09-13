# Home Assistant Blueprints

[![Validate](https://github.com/TO3IAS/ha-blueprints/actions/workflows/validate.yml/badge.svg)](https://github.com/TO3IAS/ha-blueprints/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Eine Sammlung von Blueprints für [Home Assistant](https://www.home-assistant.io/).

## Blueprints

### Gerät bei Leistungsunterschreitung ausschalten

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FTO3IAS%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fto3ias%2Fleistung_unterschritten_ausschalten.yaml)

Schaltet eine Entität automatisch aus, sobald ein Leistungssensor für eine einstellbare
Dauer ununterbrochen unter einem Schwellwert liegt – zum Beispiel eine Waschmaschine,
die nach Programmende nur noch Standby zieht.

Eine **Einschalt-Karenzzeit** verhindert, dass das Gerät während der Anlaufphase
(Programmwahl, Wasser einlaufen, Aufheizen) sofort wieder ausgeschaltet wird.

📄 [`blueprints/automation/to3ias/leistung_unterschritten_ausschalten.yaml`](blueprints/automation/to3ias/leistung_unterschritten_ausschalten.yaml)

#### Optionen

| Option | Beschreibung | Standard |
| --- | --- | --- |
| Leistungssensor | Sensor mit der Leistungsaufnahme des Geräts. Jeder numerische Sensor ist möglich (W, VA, A). | – |
| Schwellwert | Unterhalb dieses Wertes gilt das Gerät als fertig. | `5` |
| Dauer der Unterschreitung | So lange muss die Leistung ununterbrochen darunter liegen. | `5 min` |
| Einschalt-Karenzzeit | So lange nach dem Einschalten wird nicht abgeschaltet (`0` = aus). | `5 min` |
| Zu schaltende Entität | Wird per `homeassistant.turn_off` ausgeschaltet. | – |

#### Funktionsweise

Der Trigger ist ein Template-Trigger, der drei Bedingungen gleichzeitig prüft:

1. die Entität ist eingeschaltet,
2. die Einschalt-Karenzzeit ist abgelaufen,
3. die Leistung liegt unter dem Schwellwert.

Über `for:` muss das durchgehend für die eingestellte Dauer gelten. Der Umweg über
ein Template statt eines `numeric_state`-Triggers ist Absicht: Ein `numeric_state`-Trigger
mit nachgelagerter Karenzzeit-Bedingung würde **einmal** während der Karenzzeit auslösen,
dort abgewiesen werden und danach nie wieder feuern, solange die Leistung nicht noch
einmal über den Schwellwert steigt. Ein Gerät, das eingeschaltet, aber nie gestartet
wird, bliebe so dauerhaft an.

#### Hinweise

- Die Karenzzeit wird ab der letzten Zustandsänderung der Entität gerechnet. Nach einem
  Neustart von Home Assistant beginnt sie erneut.
- Der Schwellwert sollte etwas über dem Standby-Verbrauch liegen – bei Waschmaschinen
  und Trocknern sind 3–5 W üblich.
- Je kürzer das Aktualisierungsintervall des Sensors, desto kürzer darf die Dauer
  gewählt werden. Bei Sensoren mit langsamer Aktualisierung sind mindestens 3–5 Minuten
  sinnvoll, damit einzelne Messausreißer nicht zum frühzeitigen Abschalten führen.
- Geräte mit Pausen im Programm (z. B. Waschmaschinen mit Einweichphase oder Wärmepumpen-
  trockner mit Knitterschutz) brauchen eine entsprechend längere Dauer.

## Installation

**Per Import-Button:** Auf das Badge oben klicken und den Dialog in Home Assistant bestätigen.

**Manuell:** Die YAML-Datei nach `config/blueprints/automation/to3ias/` kopieren und
unter *Entwicklerwerkzeuge → YAML → Blueprints neu laden* einlesen.

Danach unter *Einstellungen → Automationen & Szenen → Automation erstellen → Blueprint*
auswählen.

## Entwicklung

Prüfungen lokal ausführen – identisch zu dem, was die GitHub-Action macht:

```bash
pip install pyyaml jinja2 yamllint
yamllint .
python scripts/validate_blueprints.py
```

Das Skript prüft YAML-Syntax, Pflichtfelder im `blueprint`-Block, Selektoren, nicht
deklarierte oder ungenutzte `!input`-Referenzen sowie die Syntax aller Jinja-Templates.

## Struktur

```
.
├── .github/
│   ├── ISSUE_TEMPLATE/          Vorlagen für Fehler und Ideen
│   ├── pull_request_template.md
│   └── workflows/validate.yml   CI-Prüfung bei jedem Push
├── blueprints/
│   └── automation/to3ias/       Automations-Blueprints
├── scripts/
│   └── validate_blueprints.py   Validierung
├── CHANGELOG.md
└── LICENSE
```

## Lizenz

[MIT](LICENSE)
