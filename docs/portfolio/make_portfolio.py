import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Usage: python make_portfolio.py [--phone NUMBER] [--out FILE]
# The copy committed to git is built without --phone: a public repo is no place for a phone number.
args = sys.argv[1:]
PHONE = args[args.index("--phone") + 1] if "--phone" in args else None
OUT = args[args.index("--out") + 1] if "--out" in args else "Evgeni_Gavrilov_Aurora_Portfolio.pdf"
INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#4b5563")
ACCENT = colors.HexColor("#1d4ed8")
RULE = colors.HexColor("#d1d5db")
PANEL = colors.HexColor("#eff6ff")

base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=13.6, textColor=INK)
name = ParagraphStyle("name", parent=base, fontName="Helvetica-Bold", fontSize=20, leading=24)
role = ParagraphStyle("role", parent=base, fontSize=11, leading=14, textColor=MUTED)
h2 = ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=12.5, leading=15,
                    textColor=ACCENT, spaceBefore=11, spaceAfter=4)
small = ParagraphStyle("small", parent=base, fontSize=9.4, leading=12.4)
bullet = ParagraphStyle("bullet", parent=base, leftIndent=10, bulletIndent=0, spaceAfter=3)


def link(url, text=None):
    return f'<link href="{url}" color="#1d4ed8"><u>{text or url}</u></link>'


def rule():
    t = Table([[""]], colWidths=[(180 * mm - 12)], rowHeights=[1])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.6, RULE)]))
    return t


story = [
    Paragraph("Evgeni Gavrilov", name),
    Paragraph("Senior QA Engineer, in QA since 2015 &nbsp;·&nbsp; <b>test automation</b> with AI since 2023",
              role),
    Spacer(1, 2),
    Paragraph(" &nbsp;·&nbsp; ".join(
        ["gavrilov.evgeni85@gmail.com"] + ([PHONE] if PHONE else [])
        + [link("https://github.com/evg-g", "github.com/evg-g")]), small),
    Spacer(1, 6),
    rule(),
    Spacer(1, 4),
    Paragraph("Aurora: my portfolio project", h2),
    Paragraph(
        "I'm a senior QA engineer with over 10 years in QA (since 2015). Since 2023 I have focused on "
        "<b>test automation</b>, and I use AI every day to write, maintain, and run automated tests. "
        "Aurora shows how I do this on a "
        "full system: a small clinic app with a <b>FastAPI backend</b>, a <b>React web app</b>, and a "
        "<b>Python IoT agent</b> that watches medicine fridges. Every level of testing runs in CI, and a "
        "change can't merge until it passes. AI wrote most of the code; I decided what to test and checked "
        "every result.", base),
    Spacer(1, 6),
]

links = Table(
    [
        [Paragraph("<b>Portfolio</b>", small), Paragraph(link("https://github.com/evg-g/aurora"), small)],
        [Paragraph("<b>Live demo</b>", small),
         Paragraph(link("https://evg-g.github.io/appointments-web/")
                   + " &nbsp;(sign in: admin@aurora.test / password123)", small)],
        [Paragraph("<b>Test report</b>", small),
         Paragraph(link("https://evg-g.github.io/appointments-web/report/"), small)],
        [Paragraph("<b>QA toolkit</b>", small), Paragraph(link("https://github.com/evg-g/qa-ai-toolkit"), small)],
    ],
    colWidths=[28 * mm, (180 * mm - 12) - 28 * mm],
)
links.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), PANEL),
    ("TOPPADDING", (0, 0), (-1, -1), 3.2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story += [links, Paragraph("<b>Test automation</b>, every level in CI", h2)]

tiers = [
    ("Unit", "pytest, Vitest + Testing Library"),
    ("Integration", "real Postgres + Redis with testcontainers"),
    ("Contract", "OpenAPI drift tests, oasdiff breaking-change check"),
    ("API fuzzing", "Hypothesis, Schemathesis"),
    ("Mutation", "mutmut, kill rate at least 78% (nightly)"),
    ("Security", "authz matrix, JWT and injection tests; Trivy, gitleaks, CodeQL"),
    ("End-to-end", "Playwright on Chromium and WebKit"),
    ("Accessibility", "axe on every page, WCAG 2.2 AA, light and dark"),
    ("Visual + layout", "Playwright screenshots and layout rules"),
    ("Performance + load", "Lighthouse, bundle budget; Locust p95 gate"),
    ("Device, no hardware", "simulator, fault injection, 7-day soak on a fake clock"),
    ("Numbers", "API 388 tests, 91% coverage; web 83 unit + 86 browser; device 241"),
]
rows = []
for i in range(0, len(tiers), 2):
    row = []
    for label, text in tiers[i:i + 2]:
        row += [Paragraph(f"<b>{label}</b>", small), Paragraph(text, small)]
    rows.append(row)
grid = Table(rows, colWidths=[29 * mm, (180 * mm - 12) / 2 - 29 * mm, 29 * mm, (180 * mm - 12) / 2 - 29 * mm])
grid.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 2.4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
]))
story += [grid, Paragraph("How I work with AI", h2)]

for text in [
    "<b>A test only counts after I have seen it fail.</b> An AI agent turns each ticket into code and "
    "tests, and every test must fail first, then pass. A test that never failed may not check anything.",
    "<b>That rule found a real bug I was not looking for:</b> the API could answer \"saved\" when the "
    "database had not saved the change. I opened a ticket, and it was fixed and proven the same way.",
    "<b>I check what the AI cannot judge.</b> I run tests the way a user would, review screenshots, and "
    "ask for full re-checks before a release.",
]:
    story.append(Paragraph(text, bullet, bulletText="•"))

story.append(Paragraph("Bugs the tests caught", h2))
for text in [
    "43 high and critical CVEs (the Starlette library and the nginx base image), found by Trivy in CI and fixed.",
    "A local build could copy the device's private signing key into its image. Now a CI job fails if it does.",
    "The dashboard showed the wrong bookings when there were more than five. The visual test missed it; "
    "a new unit test now fails on the old code.",
    "Audit-log text failed the WCAG AA contrast check (4.08:1), found by the axe accessibility sweep.",
]:
    story.append(Paragraph(text, bullet, bulletText="•"))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                        topMargin=14 * mm, bottomMargin=12 * mm,
                        title="Aurora portfolio - Evgeni Gavrilov", author="Evgeni Gavrilov")
doc.build(story)
print(OUT)
