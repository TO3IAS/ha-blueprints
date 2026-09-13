#!/usr/bin/env python3
"""Validiert alle Home-Assistant-Blueprints in diesem Repository.

Geprüft wird:
  * gültige YAML-Syntax (inklusive der HA-eigenen !input-Tags)
  * Pflichtfelder im blueprint-Block (name, description, domain)
  * jeder Input hat einen Namen und einen Selector
  * jedes per !input referenzierte Feld ist auch deklariert
  * alle Jinja-Templates lassen sich fehlerfrei parsen

Aufruf:  python scripts/validate_blueprints.py [pfad ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jinja2 import Environment, TemplateSyntaxError

VALID_DOMAINS = {"automation", "script", "template"}
REPO_ROOT = Path(__file__).resolve().parent.parent


class HALoader(yaml.SafeLoader):
    """SafeLoader, der die Home-Assistant-Tags !input und !secret versteht."""


def _construct_input(loader: HALoader, node: yaml.Node) -> dict:
    return {"__input__": loader.construct_scalar(node)}


def _construct_opaque(loader: HALoader, node: yaml.Node) -> str:
    return f"<{node.tag}>"


HALoader.add_constructor("!input", _construct_input)
HALoader.add_constructor("!secret", _construct_opaque)
HALoader.add_constructor("!include", _construct_opaque)


def collect_inputs(obj) -> set[str]:
    """Sammelt alle per !input referenzierten Namen."""
    found: set[str] = set()
    if isinstance(obj, dict):
        if set(obj) == {"__input__"}:
            found.add(obj["__input__"])
        else:
            for value in obj.values():
                found |= collect_inputs(value)
    elif isinstance(obj, list):
        for value in obj:
            found |= collect_inputs(value)
    return found


def collect_templates(obj, path: str = "") -> list[tuple[str, str]]:
    """Sammelt alle Strings, die nach einem Jinja-Template aussehen."""
    found: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            found += collect_templates(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            found += collect_templates(value, f"{path}[{index}]")
    elif isinstance(obj, str) and ("{{" in obj or "{%" in obj):
        found.append((path.lstrip("."), obj))
    return found


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=HALoader)
    except yaml.YAMLError as exc:
        return [f"YAML nicht lesbar: {exc}"]

    if not isinstance(data, dict) or "blueprint" not in data:
        return ["kein blueprint-Block gefunden"]

    meta = data["blueprint"]
    for field in ("name", "description", "domain"):
        if not meta.get(field):
            errors.append(f"blueprint.{field} fehlt")

    domain = meta.get("domain")
    if domain and domain not in VALID_DOMAINS:
        errors.append(f"blueprint.domain '{domain}' ist ungültig (erlaubt: {', '.join(sorted(VALID_DOMAINS))})")

    declared = meta.get("input") or {}
    if not isinstance(declared, dict):
        errors.append("blueprint.input muss eine Zuordnung sein")
        declared = {}

    for name, config in declared.items():
        if not isinstance(config, dict):
            errors.append(f"Input '{name}': muss eine Zuordnung sein")
            continue
        if not config.get("name"):
            errors.append(f"Input '{name}': Feld 'name' fehlt")
        if "selector" not in config:
            errors.append(f"Input '{name}': Selector fehlt")

    body = {key: value for key, value in data.items() if key != "blueprint"}
    used = collect_inputs(body)
    for name in sorted(used - set(declared)):
        errors.append(f"!input {name} wird verwendet, ist aber nicht deklariert")
    for name in sorted(set(declared) - used):
        errors.append(f"Input '{name}' ist deklariert, wird aber nirgends verwendet")

    env = Environment()
    for location, template in collect_templates(body):
        try:
            env.parse(template)
        except TemplateSyntaxError as exc:
            errors.append(f"Jinja-Fehler in {location}: {exc.message} (Zeile {exc.lineno})")

    if domain == "automation":
        has_trigger = bool(data.get("triggers") or data.get("trigger"))
        has_action = bool(data.get("actions") or data.get("action"))
        if not has_trigger:
            errors.append("Automation ohne Trigger")
        if not has_action:
            errors.append("Automation ohne Aktion")

    return errors


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(arg) for arg in argv]
    else:
        files = sorted((REPO_ROOT / "blueprints").rglob("*.yaml"))

    if not files:
        print("Keine Blueprints gefunden.")
        return 1

    failed = 0
    for path in files:
        errors = validate(path)
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        if errors:
            failed += 1
            print(f"FEHLER  {rel}")
            for error in errors:
                print(f"        - {error}")
        else:
            print(f"OK      {rel}")

    print(f"\n{len(files) - failed}/{len(files)} Blueprint(s) in Ordnung.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
