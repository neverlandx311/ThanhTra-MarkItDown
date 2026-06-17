import pytest

from src.converter import convert_text_to_markdown


def test_convert_text_to_markdown_basic():
    input_text = "Hello <World>\n\nThis is a test."
    expected = "Hello &lt;World&gt;\n\nThis is a test."
    assert convert_text_to_markdown(input_text) == expected


def test_convert_text_to_markdown_empty_line():
    input_text = "Line one\n\nLine three"
    expected = "Line one\n\nLine three"
    assert convert_text_to_markdown(input_text) == expected


def test_convert_text_to_markdown_type_error():
    with pytest.raises(TypeError):
        convert_text_to_markdown(None)
