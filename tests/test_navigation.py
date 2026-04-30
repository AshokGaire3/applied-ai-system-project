import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ui.navigation import DEFAULT_SERVICE, normalize_service


def test_normalize_service_accepts_known_value():
    assert normalize_service("Tasks") == "Tasks"


def test_normalize_service_falls_back_for_unknown_value():
    assert normalize_service("Unknown Page") == DEFAULT_SERVICE


def test_normalize_service_falls_back_for_empty_value():
    assert normalize_service("") == DEFAULT_SERVICE
