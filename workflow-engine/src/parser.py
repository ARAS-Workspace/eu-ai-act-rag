# SPDX-License-Identifier: MIT
#
#  █████╗ ██████╗  █████╗ ███████╗
# ██╔══██╗██╔══██╗██╔══██╗██╔════╝
# ███████║██████╔╝███████║███████╗
# ██╔══██║██╔══██╗██╔══██║╚════██║
# ██║  ██║██║  ██║██║  ██║███████║
# ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
# Copyright (C) 2026 Riza Emre ARAS <r.emrearas@proton.me>
#
# Licensed under the MIT License.
# See LICENSE and THIRD_PARTY_LICENSES for details.

"""Formex XML parser — extracts articles, recitals, and annexes.

Parses Formex 4 XML structure (verified against actual EU AI Act XML):
  ACT > ENACTING.TERMS > DIVISION > ARTICLE > PARAG > ALINEA
  ACT > PREAMBLE > GR.CONSID > CONSID > NP
  ANNEX (separate files) > TITLE + CONTENTS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from src.logger import get_logger
from src.result import Fail, Ok, Result

log = get_logger(__name__)


@dataclass
class Item:
    letter: str
    text: str


@dataclass
class Paragraph:
    number: str
    text: str
    items: list[Item] = field(default_factory=list)


@dataclass
class Article:
    number: str
    title: str
    chapter: str
    chapter_title: str
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class Recital:
    number: str
    text: str


@dataclass
class Annex:
    number: str
    title: str
    content: str


@dataclass
class ParsedDocument:
    articles: list[Article] = field(default_factory=list)
    recitals: list[Recital] = field(default_factory=list)
    annexes: list[Annex] = field(default_factory=list)


def _text(element: etree._Element | None) -> str:
    """Extract all text content from an element, stripping whitespace."""
    if element is None:
        return ""
    return (etree.tostring(element, method="text", encoding="unicode") or "").strip()


def _element_to_text(element: etree._Element) -> str:
    """Convert an element and its children to plain text, preserving structure."""
    parts: list[str] = []

    if element.text and element.text.strip():
        parts.append(element.text.strip())

    for child in element:
        tag = child.tag if isinstance(child.tag, str) else ""

        if tag == "P":
            parts.append(_text(child))
        elif tag == "LIST":
            parts.append(_parse_list(child))
        elif tag == "NP":
            no_p = _text(child.find("NO.P"))
            txt = _text(child.find("TXT"))
            parts.append(f"{no_p} {txt}" if no_p else txt)
        elif tag == "NOTE":
            pass  # Skip footnotes in body text
        else:
            t = _text(child)
            if t:
                parts.append(t)

        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())

    return "\n\n".join(p for p in parts if p)


def _parse_list(list_el: etree._Element) -> str:
    """Parse a LIST element into formatted text."""
    items: list[str] = []
    for item_el in list_el.findall("ITEM"):
        np = item_el.find("NP")
        if np is not None:
            no_p = _text(np.find("NO.P"))
            txt = _text(np.find("TXT"))
            items.append(f"{no_p} {txt}" if no_p else txt)
        else:
            items.append(_text(item_el))
    return "\n\n".join(items)


def _parse_paragraph(parag: etree._Element) -> Paragraph:
    """Parse a PARAG element."""
    no = _text(parag.find("NO.PARAG")).rstrip(".")
    alinea = parag.find("ALINEA")

    items: list[Item] = []
    text_parts: list[str] = []

    if alinea is not None:
        # ALINEA can contain plain text, P elements, or LIST
        for child in alinea:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag == "P":
                text_parts.append(_text(child))
            elif tag == "LIST":
                for item_el in child.findall("ITEM"):
                    np = item_el.find("NP")
                    if np is not None:
                        letter = _text(np.find("NO.P")).strip("()")
                        txt = _text(np.find("TXT"))
                        items.append(Item(letter=letter, text=txt))
                    else:
                        items.append(Item(letter="", text=_text(item_el)))
            elif tag == "NP":
                pass  # Already captured via NO.PARAG
            elif tag == "NOTE":
                pass  # Skip footnotes
            else:
                t = _text(child)
                if t:
                    text_parts.append(t)

        if alinea.text and alinea.text.strip():
            text_parts.insert(0, alinea.text.strip())
    else:
        text_parts.append(_text(parag))

    return Paragraph(number=no, text="\n\n".join(text_parts), items=items)


def parse_articles(root: etree._Element) -> list[Article]:
    """Parse all ARTICLE elements from the ACT."""
    articles: list[Article] = []

    # Build division context map
    div_map: dict[str, tuple[str, str]] = {}
    for div in root.iter("DIVISION"):
        ti = _text(div.find("TITLE/TI"))
        sti = _text(div.find("TITLE/STI"))
        for art in div.findall("ARTICLE"):
            ident = art.get("IDENTIFIER", "")
            # Use the closest chapter (not section)
            parent = div.getparent()
            if parent is not None and parent.tag == "DIVISION":
                p_ti = _text(parent.find("TITLE/TI"))
                p_sti = _text(parent.find("TITLE/STI"))
                div_map[ident] = (p_ti, p_sti)
            else:
                div_map[ident] = (ti, sti)

    for art_el in root.iter("ARTICLE"):
        number = _text(art_el.find("TI.ART")).replace("Article", "").strip()
        title = _text(art_el.find("STI.ART"))
        ident = art_el.get("IDENTIFIER", "")
        chapter, chapter_title = div_map.get(ident, ("", ""))

        paragraphs = [_parse_paragraph(p) for p in art_el.findall("PARAG")]

        articles.append(Article(
            number=number,
            title=title,
            chapter=chapter,
            chapter_title=chapter_title,
            paragraphs=paragraphs,
        ))

    log.info("Parsed %d articles", len(articles))
    return articles


def parse_recitals(root: etree._Element) -> list[Recital]:
    """Parse all CONSID elements from the PREAMBLE."""
    recitals: list[Recital] = []

    for consid in root.iter("CONSID"):
        np = consid.find("NP")
        if np is None:
            continue
        number = _text(np.find("NO.P")).strip("()")
        txt_el = np.find("TXT")
        text = _text(txt_el) if txt_el is not None else _element_to_text(np)
        recitals.append(Recital(number=number, text=text))

    log.info("Parsed %d recitals", len(recitals))
    return recitals


def parse_annex(xml_path: Path) -> Result[Annex]:
    """Parse a single ANNEX file."""
    try:
        tree = etree.parse(str(xml_path))  # noqa: S320
    except etree.XMLSyntaxError as exc:
        return Fail(error=f"Annex XML parse error: {exc}", context=str(xml_path))

    root = tree.getroot()
    ti = _text(root.find("TITLE/TI"))
    sti = _text(root.find("TITLE/STI"))
    title = f"{ti} — {sti}" if sti else ti

    # Extract annex number from title (e.g., "ANNEX III" → "III")
    number = ti.replace("ANNEX", "").strip() if "ANNEX" in ti else ti

    contents_el = root.find("CONTENTS")
    content = _element_to_text(contents_el) if contents_el is not None else ""

    return Ok(data=Annex(number=number, title=title, content=content))


def parse_document(source_dir: Path) -> Result[ParsedDocument]:
    """Parse the complete Formex document from extracted XML files."""
    doc = ParsedDocument()

    # Main ACT file
    act_files = sorted(source_dir.glob("*.000101.fmx.xml"))
    if not act_files:
        return Fail(error=f"No main ACT file found in {source_dir}")

    act_path = act_files[0]
    try:
        tree = etree.parse(str(act_path))  # noqa: S320
    except etree.XMLSyntaxError as exc:
        return Fail(error=f"ACT XML parse error: {exc}", context=str(act_path))

    root = tree.getroot()
    doc.articles = parse_articles(root)
    doc.recitals = parse_recitals(root)

    # Annex files (*.01XXXX.fmx.xml, excluding toc and doc)
    annex_files = sorted(
        f for f in source_dir.glob("*.fmx.xml")
        if ".toc." not in f.name and ".doc." not in f.name and ".000101." not in f.name
    )
    for annex_path in annex_files:
        result = parse_annex(annex_path)
        if result.ok:
            doc.annexes.append(result.data)
        else:
            log.warning("Skipping annex %s: %s", annex_path.name, result.error)

    log.info(
        "Parsed document: %d articles, %d recitals, %d annexes",
        len(doc.articles), len(doc.recitals), len(doc.annexes),
    )
    return Ok(data=doc)