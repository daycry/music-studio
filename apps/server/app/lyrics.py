"""Análisis puro de etiquetas; conserva el texto y usa rangos UTF-16."""

import re

_GROUPS = {
    "intro": "intro,introducción",
    "verse": "verse,verses,verso,versos,estrofa,estrofas",
    "pre-chorus": "pre-chorus,pre chorus,precoro,pre-coro,preestribillo",
    "chorus": "chorus,choruses,coro,coros,estribillo,estribillos",
    "post-chorus": "post-chorus,post chorus,postcoro,post-coro,postestribillo",
    "bridge": "bridge,puente",
    "hook": "hook,gancho",
    "break": "break,pausa",
    "instrumental": "instrumental",
    "solo": "solo",
    "outro": "outro,salida",
}
_ALIASES = {
    alias: kind for kind, aliases in _GROUPS.items() for alias in aliases.split(",")
}


def parse_lyrics(original: str) -> dict:
    """Clasifica cabeceras completas sin interpretar sus direcciones musicales."""
    offsets = [0]
    for char in original:
        offsets.append(offsets[-1] + (2 if ord(char) > 0xFFFF else 1))

    def span(start, end):
        return {"start": offsets[start], "end": offsets[end]}

    sections, annotations, warnings = [], [], []
    body_starts = []
    position = 0
    for match in re.finditer(r"[^\r\n]*(?:\r\n|\r|\n|$)", original):
        line = match.group()
        if not line:
            continue
        position = match.start()
        content = line.rstrip("\r\n")
        leading = re.match(
            r"(?:\ufeff)?[ \t]*" if position == 0 else r"[ \t]*", content
        ).end()
        candidate = content[leading:].rstrip(" \t")
        if not re.match(r"\**\[", candidate):
            continue
        whole = span(position, match.end())
        code = "MALFORMED_TAG"
        tag = re.fullmatch(r"(?:\[([^\[\]]*)\]|\*\*\[([^\[\]]*)\]\*\*)", candidate)
        if tag:
            group = 1 if tag.group(1) is not None else 2
            inner = tag.group(group)
            inner_start = position + leading + tag.start(group)
            separator = inner.find(" - ")
            structure = inner if separator < 0 else inner[:separator]
            trimmed = structure.strip(" \t")
            number, qualifier = None, None
            suffix = re.search(r"[ \t]+([^ \t]+)$", trimmed)
            alias = trimmed
            if suffix:
                token = suffix.group(1)
                if token.lower() == "final":
                    qualifier = "final"
                    alias = trimmed[: suffix.start()]
                elif re.fullmatch(r"[0-9]+", token):
                    if (
                        re.fullmatch(r"[1-9][0-9]*", token)
                        and len(token) <= 16
                        and int(token) <= 9007199254740991
                    ):
                        number = int(token)
                        alias = trimmed[: suffix.start()]
                    else:
                        alias = ""
            normalized = re.sub(r"[ \t]+", " ", alias.lower())
            kind = _ALIASES.get(normalized)
            if kind:
                alias_start = (
                    inner_start + len(structure) - len(structure.lstrip(" \t"))
                )
                directions = (
                    None
                    if separator < 0
                    else {
                        "text": inner[separator + 3 :],
                        "range": span(
                            inner_start + separator + 3, inner_start + len(inner)
                        ),
                    }
                )
                sections.append(
                    {
                        "kind": kind,
                        "alias": alias,
                        "aliasRange": span(alias_start, alias_start + len(alias)),
                        "number": number,
                        "qualifier": qualifier,
                        "headerRange": whole,
                        "bodyRange": None,
                        "directions": directions,
                        "empty": False,
                    }
                )
                body_starts.append((match.end(), position))
                continue
            if (
                alias
                and re.fullmatch(r"[^\W\d_]+(?:[ \t-]+[^\W\d_]+)*", alias)
                and all(char.isalpha() for char in alias if char not in " \t-")
            ):
                code = "UNKNOWN_TAG"
        annotations.append({"code": code, "range": whole, "text": line})
        warnings.append({"code": code, "range": whole})
    for index, section in enumerate(sections):
        start = body_starts[index][0]
        end = body_starts[index + 1][1] if index + 1 < len(sections) else len(original)
        section["bodyRange"] = span(start, end)
        section["empty"] = not original[start:end].strip(" \t\r\n")
        if section["empty"]:
            warnings.append({"code": "EMPTY_SECTION", "range": section["headerRange"]})
    warnings.sort(key=lambda item: (item["range"]["start"], item["code"]))
    return {
        "version": 1,
        "original": original,
        "sections": sections,
        "annotations": annotations,
        "warnings": warnings,
    }
