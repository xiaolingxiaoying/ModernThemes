"""Small, dependency-free JSONC reader used by the theme builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsoncError(ValueError):
    pass


def _strip_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False

    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
        elif char == "/" and following == "/":
            output.extend((" ", " "))
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                output.append(" ")
                index += 1
        elif char == "/" and following == "*":
            output.extend((" ", " "))
            index += 2
            while index < len(text):
                if index + 1 < len(text) and text[index:index + 2] == "*/":
                    output.extend((" ", " "))
                    index += 2
                    break
                output.append("\n" if text[index] == "\n" else " ")
                index += 1
            else:
                raise JsoncError("Unterminated block comment")
        else:
            output.append(char)
            index += 1

    if in_string:
        raise JsoncError("Unterminated JSON string")
    return "".join(output)


def _strip_trailing_commas(text: str) -> str:
    chars = list(text)
    index = 0
    in_string = False
    escaped = False

    while index < len(chars):
        char = chars[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
        elif char == ",":
            lookahead = index + 1
            while lookahead < len(chars) and chars[lookahead].isspace():
                lookahead += 1
            if lookahead < len(chars) and chars[lookahead] in "]}":
                chars[index] = " "
        index += 1
    return "".join(chars)


def loads(text: str, *, source: str = "<string>") -> Any:
    try:
        return json.loads(_strip_trailing_commas(_strip_comments(text)))
    except (json.JSONDecodeError, JsoncError) as error:
        raise JsoncError(f"Unable to parse {source}: {error}") from error


def load(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise JsoncError(f"Unable to read {path}: {error}") from error
    return loads(text, source=str(path))
