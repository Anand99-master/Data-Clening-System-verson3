"""
modules/rules_manager.py — Phase 4: Custom Rules

Lets the user build up their own {column: {from: to}} standardization
rules interactively (instead of only accepting auto-suggested case
variants) and persist them to config/cleaning_rules.json so they carry
over to the next session/file.
"""

import json
import os

DEFAULT_RULES_PATH = os.path.join("config", "cleaning_rules.json")


def load_rules(path: str = DEFAULT_RULES_PATH) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(rules: dict, path: str = DEFAULT_RULES_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def add_rule(rules: dict, column: str, from_value: str, to_value: str) -> dict:
    rules = dict(rules)
    rules.setdefault(column, {})
    rules[column][from_value] = to_value
    return rules


def remove_rule(rules: dict, column: str, from_value: str) -> dict:
    rules = dict(rules)
    if column in rules and from_value in rules[column]:
        del rules[column][from_value]
        if not rules[column]:
            del rules[column]
    return rules
