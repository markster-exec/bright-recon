"""Export an Account Action Plan to a polished, branded PDF.

Pure: build_account_pdf(intel) -> bytes. fpdf2 core fonts (no system deps; works on
Streamlit Cloud). Text is sanitized to latin-1 so LLM unicode never breaks the render.
Design: slim header rule, hero with a confidence bar, tinted callout, eyebrow sections,
signal cards with category pills + green source links, page numbers.
"""
from __future__ import annotations

from fpdf import FPDF

from .crm import build_action_package
from .models import AccountIntel

INK = (24, 26, 31)
GREEN = (0, 196, 70)
GREEN_DK = (0, 150, 60)
MUTED = (122, 128, 138)
LINE = (226, 229, 234)
PANEL = (247, 249, 251)
PILLBG = (230, 248, 237)
WHITE = (255, 255, 255)

_REPL = {
    chr(0x2014): "-", chr(0x2013): "-", chr(0x2192): "->", chr(0x2022): "-", chr(0x2026): "...",
    chr(0x201C): '"', chr(0x201D): '"', chr(0x2018): "'", chr(0x2019): "'", chr(0x00D7): "x",
    chr(0x2122): "(TM)", chr(0x00A0): " ",
}


def _safe(text: str) -> str:
    for k, v in _REPL.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _conf_color(c: float):
    if c >= 0.6:
        return GREEN
    if c >= 0.35:
        return (224, 168, 0)
    return (200, 70, 60)


class _PDF(FPDF):
    def header(self) -> None:
        # slim green top rule + wordmark (no heavy bar)
        self.set_fill_color(*GREEN)
        self.rect(0, 0, 210, 2.2, "F")
        self.set_xy(self.l_margin, 9)
        self.set_font("helvetica", "B", 10)
        self.set_text_color(*INK)
        self.cell(0, 5, _safe("MARKSTER RECON"))
        self.set_font("helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 5, _safe("Account Action Plan"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINE)
        self.set_line_width(0.2)
        self.line(self.l_margin, 16.5, 210 - self.r_margin, 16.5)
        self.set_y(22)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_draw_color(*LINE)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.set_y(-10)
        self.set_font("helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.cell(0, 5, _safe("Markster Recon  -  6 Bright Data products  -  Azure GPT-5.5  -  provenance on every signal"))
        self.cell(0, 5, _safe(f"Page {self.page_no()}"), align="R")


def _eyebrow(pdf: _PDF, text: str) -> None:
    pdf.ln(3.5)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(*GREEN_DK)
    pdf.cell(0, 4.5, _safe(text.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_text_color(*INK)


def _para(pdf: _PDF, text: str, size: float = 9.5, color=INK, lh: float = 4.8) -> None:
    pdf.set_font("helvetica", "", size)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, lh, _safe(text), new_x="LMARGIN", new_y="NEXT")


def _bullets(pdf: _PDF, items: list[str]) -> None:
    for it in items:
        y0 = pdf.get_y()
        pdf.set_fill_color(*GREEN)
        pdf.ellipse(pdf.l_margin + 0.4, y0 + 1.7, 1.4, 1.4, "F")
        pdf.set_xy(pdf.l_margin + 4, y0)
        pdf.set_font("helvetica", "", 9.5)
        pdf.set_text_color(*INK)
        pdf.multi_cell(0, 4.8, _safe(it), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.6)


def _confidence_block(pdf: _PDF, intel: AccountIntel) -> None:
    x, y, w = pdf.l_margin, pdf.get_y(), 210 - pdf.l_margin - pdf.r_margin
    pct = max(0, min(100, round(intel.confidence * 100)))
    col = _conf_color(intel.confidence)
    # label + big number
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, _safe("CONFIDENCE  (coverage x signal strength)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(*INK)
    pdf.cell(20, 8, f"{pct}%")
    # meta to the right of the number
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(x + 24, y + 5.5)
    pdf.cell(0, 6, _safe(f"{len(intel.signals)} signals   |   LLM: {intel.llm_used}   |   {intel.generated_at[:10]}"))
    pdf.ln(10)
    # bar
    by = pdf.get_y()
    pdf.set_fill_color(*LINE)
    pdf.rect(x, by, w, 2.6, "F")
    pdf.set_fill_color(*col)
    pdf.rect(x, by, w * pct / 100.0, 2.6, "F")
    pdf.ln(6)


def _signal_card(pdf: _PDF, category: str, conf: float, summary: str, url: str, method: str) -> None:
    # avoid splitting a card across the page break (keeps the panel border clean)
    if pdf.get_y() > 248:
        pdf.add_page()
    pdf.set_font("helvetica", "", 9)
    start = pdf.get_y()
    x, w = pdf.l_margin, 210 - pdf.l_margin - pdf.r_margin
    pad = 4
    # panel: render text first to know height -> use a fixed approach: print into temp by estimating
    # simpler: draw text, then a left accent bar spanning the block
    pdf.set_xy(x + pad, start + pad)
    # pill
    pdf.set_font("helvetica", "B", 7)
    pill_w = pdf.get_string_width(category.upper()) + 5
    pdf.set_fill_color(*PILLBG)
    pdf.set_text_color(*GREEN_DK)
    pdf.cell(pill_w, 5, _safe(category.upper()), align="C", fill=True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, _safe(f"   {round(conf*100)}% signal"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x + pad)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*INK)
    pdf.multi_cell(w - 2 * pad, 4.6, _safe(summary), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x + pad)
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(*GREEN_DK)
    pdf.multi_cell(w - 2 * pad, 4, _safe(f"source: {url}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x + pad)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 3.5, _safe(method), new_x="LMARGIN", new_y="NEXT")
    end = pdf.get_y()
    # draw panel border + left accent behind (re-draw under by using rects with no fill over? draw now as outline)
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.2)
    pdf.rect(x, start, w, end - start + pad)
    pdf.set_fill_color(*GREEN)
    pdf.rect(x, start, 1.4, end - start + pad, "F")
    pdf.set_y(end + pad + 2.5)


def build_account_pdf(intel: AccountIntel) -> bytes:
    pkg = build_action_package(intel)
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(16, 22, 16)
    pdf.add_page()

    # hero: company
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(*INK)
    pdf.cell(0, 12, _safe(intel.company), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    _confidence_block(pdf, intel)

    # one-liner callout (tinted panel)
    if intel.one_liner:
        x, y, w = pdf.l_margin, pdf.get_y(), 210 - pdf.l_margin - pdf.r_margin
        pdf.set_font("helvetica", "B", 11)
        pdf.set_xy(x + 5, y + 4)
        pdf.set_text_color(*INK)
        pdf.multi_cell(w - 10, 5.2, _safe(intel.one_liner), new_x="LMARGIN", new_y="NEXT")
        end = pdf.get_y()
        pdf.set_fill_color(*PANEL)
        pdf.rect(x, y, w, end - y + 4, "DF")  # fill behind
        # re-print text on top of fill (fill drew over it); simplest: print again
        pdf.set_xy(x + 5, y + 4)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*INK)
        pdf.multi_cell(w - 10, 5.2, _safe(intel.one_liner), new_x="LMARGIN", new_y="NEXT")
        pdf.set_fill_color(*GREEN)
        pdf.rect(x, y, 1.6, end - y + 4, "F")
        pdf.set_y(end + 6)

    _eyebrow(pdf, "The read - why this account, why now")
    _para(pdf, intel.the_read or "-")
    if intel.terrain:
        _eyebrow(pdf, "Terrain")
        _para(pdf, intel.terrain)
    if intel.routes:
        _eyebrow(pdf, "Routes to enter")
        _bullets(pdf, intel.routes)
    if intel.who_decides:
        _eyebrow(pdf, "Who shapes the decision")
        _bullets(pdf, intel.who_decides)

    _eyebrow(pdf, f"Live signals ({len(intel.signals)}) - each links to its source")
    for s in intel.signals:
        _signal_card(pdf, s.category, s.confidence, s.summary, s.provenance.source_url, s.provenance.method)

    if intel.evidence_gaps:
        _eyebrow(pdf, "Evidence gaps - verify before acting")
        _bullets(pdf, intel.evidence_gaps)

    _eyebrow(pdf, "Next actions - most urgent first")
    _bullets(pdf, [f"{i}. {a}" for i, a in enumerate(intel.next_actions, 1)])

    _eyebrow(pdf, "Agentic CRM action - what Recon writes to your CRM")
    if pkg.caveat:
        _para(pdf, f"NOTE: {pkg.caveat}", size=8.5, color=(180, 120, 0))
    _para(pdf, f"Task [{pkg.task.priority}]  -  {pkg.task.subject}", size=9.5)
    _para(pdf, f"Suggested due {pkg.task.due_date}", size=8.5, color=MUTED)

    return bytes(pdf.output())
