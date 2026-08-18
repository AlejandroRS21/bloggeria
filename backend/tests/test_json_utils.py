"""Tests for robust JSON extraction from LLM responses."""
import json
import pytest

from aphra_blogger.llm.json_utils import extract_json


def test_bare_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_fenced_json():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_fenced_plain():
    assert extract_json('```\n{"a": 1}\n```') == {"a": 1}


def test_prose_around_json():
    txt = 'Here is your result:\n{"keywords": ["x", "y"]}\nHope it helps!'
    assert extract_json(txt) == {"keywords": ["x", "y"]}


def test_array_json():
    assert extract_json('[1, 2, 3]') == [1, 2, 3]


def test_prose_around_array():
    assert extract_json('Result: [1, 2, 3] done') == [1, 2, 3]


def test_raises_on_no_json():
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here at all")


def test_raises_on_none():
    with pytest.raises(json.JSONDecodeError):
        extract_json(None)
