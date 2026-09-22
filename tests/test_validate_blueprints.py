"""Tests für scripts/validate_blueprints.py."""

from pathlib import Path

import validate_blueprints as vb

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED_BLUEPRINT = (
    REPO_ROOT
    / "blueprints"
    / "automation"
    / "to3ias"
    / "leistung_unterschritten_ausschalten.yaml"
)


def test_collect_inputs_finds_nested_references():
    body = {
        "trigger_variables": {"power_sensor": {"__input__": "power_sensor"}},
        "actions": [
            {"target": {"entity_id": {"__input__": "target_entity"}}},
        ],
    }
    assert vb.collect_inputs(body) == {"power_sensor", "target_entity"}


def test_collect_inputs_ignores_plain_values():
    body = {"mode": "single", "conditions": []}
    assert vb.collect_inputs(body) == set()


def test_collect_templates_finds_jinja_strings():
    body = {
        "triggers": [
            {"value_template": "{{ states('sensor.x') | float(0) < 5 }}"},
        ],
        "mode": "single",
    }
    found = vb.collect_templates(body)
    assert len(found) == 1
    path, template = found[0]
    assert path == "triggers[0].value_template"
    assert "states('sensor.x')" in template


def test_shipped_blueprint_is_valid():
    assert vb.validate(SHIPPED_BLUEPRINT) == []


def test_validate_reports_missing_fields(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        "blueprint:\n"
        "  name: ''\n"
        "  description: ''\n"
        "  domain: automation\n"
        "  input: {}\n"
        "triggers: []\n"
        "actions: []\n",
        encoding="utf-8",
    )
    errors = vb.validate(bad_yaml)
    assert any("name" in e for e in errors)
    assert any("description" in e for e in errors)
    assert any("ohne Trigger" in e for e in errors)
    assert any("ohne Aktion" in e for e in errors)


def test_validate_reports_undeclared_input(tmp_path):
    bad_yaml = tmp_path / "undeclared.yaml"
    bad_yaml.write_text(
        "blueprint:\n"
        "  name: Test\n"
        "  description: Test\n"
        "  domain: automation\n"
        "  input: {}\n"
        "triggers:\n"
        "  - trigger: state\n"
        "    entity_id: !input some_entity\n"
        "actions: []\n",
        encoding="utf-8",
    )
    errors = vb.validate(bad_yaml)
    assert any("some_entity" in e and "nicht deklariert" in e for e in errors)


def test_validate_reports_invalid_jinja(tmp_path):
    bad_yaml = tmp_path / "bad_template.yaml"
    bad_yaml.write_text(
        "blueprint:\n"
        "  name: Test\n"
        "  description: Test\n"
        "  domain: automation\n"
        "  input: {}\n"
        "triggers:\n"
        "  - trigger: template\n"
        "    value_template: '{{ states(  '\n"
        "actions: []\n",
        encoding="utf-8",
    )
    errors = vb.validate(bad_yaml)
    assert any("Jinja-Fehler" in e for e in errors)
