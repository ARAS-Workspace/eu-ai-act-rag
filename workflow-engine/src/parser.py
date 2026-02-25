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

# noinspection PyProtectedMember
_XmlElement = etree._Element

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


def _text(element: _XmlElement | None) -> str:
    """Extract all text content from an element, stripping whitespace."""
    if element is None:
        return ""
    return (etree.tostring(element, method="text", encoding="unicode") or "").strip()


def _table_to_text(tbl: _XmlElement) -> str:
    """Extract readable text from a TBL element."""
    rows: list[str] = []
    for row in tbl.iter("ROW"):
        cells = [_text(cell) for cell in row.findall("CELL")]
        rows.append(" | ".join(c for c in cells if c))
    return "\n".join(rows) if rows else _text(tbl)


def _element_to_text(element: _XmlElement) -> str:
    """Convert an element and its children to plain text, preserving structure."""
    parts: list[str] = []

    if element.text and element.text.strip():
        parts.append(element.text.strip())

    for child in element:
        tag = child.tag if isinstance(child.tag, str) else ""

        if tag == "P":
            # If P has structured children (LIST, NP, etc.), recurse
            if any(hasattr(gc, "tag") and gc.tag in ("LIST", "NP", "GR.SEQ", "TBL") for gc in child):
                parts.append(_element_to_text(child))
            else:
                parts.append(_text(child))
        elif tag == "LIST":
            parts.append(_parse_list(child))
        elif tag == "NP":
            no_p = _text(child.find("NO.P"))
            txt = _text(child.find("TXT"))
            parts.append(f"{no_p} {txt}" if no_p else txt)
        elif tag == "GR.SEQ":
            ti = _text(child.find("TITLE/TI"))
            sti = _text(child.find("TITLE/STI"))
            title = f"{ti} — {sti}" if ti and sti else (ti or sti)
            if title:
                parts.append(f"\n### {title}\n")
            for sub in child:
                if sub.tag != "TITLE":
                    parts.append(_element_to_text(sub))
        elif tag == "TBL":
            parts.append(_table_to_text(child))
        elif tag == "ITEM":
            np = child.find("NP")
            if np is not None:
                no_p = _text(np.find("NO.P"))
                txt_el = np.find("TXT")
                txt = _text(txt_el) if txt_el is not None else _text(np)
                parts.append(f"{no_p} {txt}" if no_p else txt)
                nested = _find_nested_list(child, np)
                if nested is not None:
                    parts.append(_parse_list(nested))
                # QUOT.S inside NP > P (amendment articles)
                for p_el in np.findall("P"):
                    quot = p_el.find("QUOT.S")
                    if quot is not None:
                        parts.append(_element_to_text(quot))
            else:
                parts.append(_text(child))
        elif tag == "NOTE":
            pass  # Skip footnotes in body text
        else:
            t = _text(child)
            if t:
                parts.append(t)

        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())

    return "\n\n".join(p for p in parts if p)


def _find_nested_list(item_el: _XmlElement, np: _XmlElement | None) -> _XmlElement | None:
    """Find a nested LIST in ITEM, checking TXT > NP > NP/P > ITEM positions."""
    if np is not None:
        txt_el = np.find("TXT")
        if txt_el is not None:
            nested = txt_el.find("LIST")
            if nested is not None:
                return nested
        nested = np.find("LIST")
        if nested is not None:
            return nested
        # LIST inside P which is inside NP (common in annexes)
        p_el = np.find("P")
        if p_el is not None:
            nested = p_el.find("LIST")
            if nested is not None:
                return nested
    return item_el.find("LIST")


def _parse_list(list_el: _XmlElement) -> str:
    """Parse a LIST element into formatted text (recursive)."""
    items: list[str] = []
    for item_el in list_el.findall("ITEM"):
        np = item_el.find("NP")
        nested = _find_nested_list(item_el, np)

        if np is not None:
            no_p = _text(np.find("NO.P"))
            txt_el = np.find("TXT")
            txt = _text(txt_el) if txt_el is not None else _text(np)
            if nested is not None:
                if txt:
                    items.append(f"{no_p} {txt}" if no_p else txt)
                items.append(_parse_list(nested))
            else:
                items.append(f"{no_p} {txt}" if no_p else txt)
        else:
            alinea = item_el.find("ALINEA")
            if alinea is not None:
                a_nested = alinea.find("LIST")
                if a_nested is not None:
                    p_el = alinea.find("P")
                    if p_el is not None:
                        items.append(_text(p_el))
                    items.append(_parse_list(a_nested))
                else:
                    items.append(_element_to_text(alinea))
            elif nested is not None:
                items.append(_parse_list(nested))
            else:
                items.append(_text(item_el))
    return "\n\n".join(items)


def _collect_list_items(
    list_el: _XmlElement,
    parts: list[str],
    items: list[Item],
) -> None:
    """Recursively collect items from a LIST element.

    Adds items inline to parts (for correct ordering in text) and
    also populates the items list (for structured access).
    Checks TXT > NP > ITEM positions for nested LISTs.
    """
    for item_el in list_el.findall("ITEM"):
        np = item_el.find("NP")
        nested = _find_nested_list(item_el, np)

        if np is not None:
            letter = _text(np.find("NO.P")).strip("()")
            txt_el = np.find("TXT")
            txt = _text(txt_el) if txt_el is not None else _text(np)
            if nested is not None:
                if txt:
                    items.append(Item(letter=letter, text=txt))
                    parts.append(f"({letter}) {txt}")
                _collect_list_items(nested, parts, items)
            else:
                items.append(Item(letter=letter, text=txt))
                parts.append(f"({letter}) {txt}")
                # QUOT.S inside NP > P (amendment articles)
                for p_el in np.findall("P"):
                    quot = p_el.find("QUOT.S")
                    if quot is not None:
                        qt = _element_to_text(quot)
                        if qt:
                            parts.append(qt)
        else:
            alinea = item_el.find("ALINEA")
            if alinea is not None:
                a_nested = alinea.find("LIST")
                if a_nested is not None:
                    p_el = alinea.find("P")
                    if p_el is not None:
                        parts.append(_text(p_el))
                    _collect_list_items(a_nested, parts, items)
                else:
                    parts.append(_element_to_text(alinea))
            elif nested is not None:
                _collect_list_items(nested, parts, items)
            else:
                t = _text(item_el)
                if t:
                    items.append(Item(letter="", text=t))
                    parts.append(f"- {t}")


def _process_alinea_children(
    alinea: _XmlElement,
    parts: list[str],
    items: list[Item],
) -> None:
    """Process children of an ALINEA element, preserving document order."""
    if alinea.text and alinea.text.strip():
        parts.append(alinea.text.strip())

    for child in alinea:
        tag = child.tag if isinstance(child.tag, str) else ""
        if tag == "P":
            parts.append(_text(child))
        elif tag == "LIST":
            _collect_list_items(child, parts, items)
        elif tag == "NP":
            no_p = _text(child.find("NO.P"))
            txt = _text(child.find("TXT"))
            if txt:
                parts.append(f"{no_p} {txt}" if no_p else txt)
        elif tag == "NOTE":
            pass
        else:
            t = _text(child)
            if t:
                parts.append(t)


def _parse_paragraph(parag: _XmlElement) -> Paragraph:
    """Parse a PARAG element."""
    no = _text(parag.find("NO.PARAG")).rstrip(".")

    items: list[Item] = []
    text_parts: list[str] = []

    alineas = parag.findall("ALINEA")

    if alineas:
        for alinea in alineas:
            _process_alinea_children(alinea, text_parts, items)
    else:
        text_parts.append(_text(parag))

    return Paragraph(number=no, text="\n\n".join(text_parts), items=items)


def _find_chapter_context(element: _XmlElement) -> tuple[str, str]:
    """Walk up DIVISION ancestors to find the nearest CHAPTER-level title.

    Formex hierarchy: TITLE > CHAPTER > SECTION > ARTICLE
    We want the CHAPTER level, not the SECTION level.
    """
    current = element
    while current is not None:
        if current.tag == "DIVISION":
            ti = _text(current.find("TITLE/TI"))
            if ti and ("CHAPTER" in ti.upper() or "TITLE" in ti.upper()):
                sti = _text(current.find("TITLE/STI"))
                return ti, sti
        current = current.getparent()
    return "", ""


def parse_articles(root: _XmlElement) -> list[Article]:
    """Parse all ARTICLE elements from the ACT."""
    articles: list[Article] = []

    for art_el in root.iter("ARTICLE"):
        number = _text(art_el.find("TI.ART")).replace("Article", "").strip()
        title = _text(art_el.find("STI.ART"))

        parent_div = art_el.getparent()
        chapter, chapter_title = _find_chapter_context(parent_div)

        parags = art_el.findall("PARAG")
        if parags:
            paragraphs = [_parse_paragraph(p) for p in parags]
        else:
            # Articles without PARAG wrapper (e.g. Article 3 Definitions)
            # have ALINEA directly under ARTICLE
            items: list[Item] = []
            text_parts: list[str] = []
            for alinea in art_el.findall("ALINEA"):
                _process_alinea_children(alinea, text_parts, items)
            if text_parts or items:
                paragraphs = [Paragraph(number="", text="\n\n".join(text_parts), items=items)]
            else:
                paragraphs = []

        articles.append(Article(
            number=number,
            title=title,
            chapter=chapter,
            chapter_title=chapter_title,
            paragraphs=paragraphs,
        ))

    log.info("Parsed %d articles", len(articles))
    return articles


def parse_recitals(root: _XmlElement) -> list[Recital]:
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

    # Main ACT file — matches both Formex naming conventions:
    #   AI Act:  *.000101.fmx.xml
    #   GDPR:    *.01000101.xml
    act_files = sorted(
        f for f in source_dir.glob("*.xml")
        if "0101" in f.name and ".doc." not in f.name and ".toc." not in f.name
    )
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

    # Annex files — any XML that is not the main ACT, toc, or doc file
    act_names = {f.name for f in act_files}
    annex_files = sorted(
        f for f in source_dir.glob("*.xml")
        if ".toc." not in f.name
        and ".doc." not in f.name
        and f.name not in act_names
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