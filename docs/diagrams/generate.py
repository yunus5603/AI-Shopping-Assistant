"""Generate the README diagrams as light and dark SVGs.

    python docs/diagrams/generate.py

Writes docs/diagrams/{architecture,cicd}-{light,dark}.svg. Edit the layout here
rather than the SVGs, so both themes stay in sync.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "card": "#ffffff",
        "card_border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#59636e",
        "line": "#8c959f",
        "group": "#f6f8fa",
        "group_border": "#d0d7de",
        "shadow": "#1f2328",
        "shadow_opacity": "0.06",
    },
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "card": "#161b22",
        "card_border": "#30363d",
        "text": "#e6edf3",
        "muted": "#9198a1",
        "line": "#6e7681",
        "group": "#11161d",
        "group_border": "#30363d",
        "shadow": "#000000",
        "shadow_opacity": "0.35",
    },
}

# Category accents, chosen to read on both backgrounds.
ACCENT = {
    "client": "#2f81f7",
    "app": "#8250df",
    "llm": "#e16f24",
    "data": "#1a7f37",
    "ci": "#2f81f7",
    "cd": "#e16f24",
}
ACCENT_DARK = {"data": "#3fb950", "app": "#a371f7"}


class Svg:
    def __init__(self, width: int, height: int, theme: str):
        self.w, self.h = width, height
        self.t = THEMES[theme]
        self.theme = theme
        self.parts: list[str] = []

    def accent(self, kind: str) -> str:
        if self.theme == "dark" and kind in ACCENT_DARK:
            return ACCENT_DARK[kind]
        return ACCENT[kind]

    def text(self, x, y, s, size=14, weight=400, color=None, anchor="start", spacing=None):
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color or self.t["text"]}" text-anchor="{anchor}"{ls}>{escape(s)}</text>'
        )

    def node(self, x, y, w, h, kind, title, lines=(), tag=None):
        a = self.accent(kind)
        t = self.t
        self._clip = getattr(self, "_clip", 0) + 1
        cid = f"c{self._clip}"
        self.parts.append(
            f'<rect x="{x}" y="{y + 2}" width="{w}" height="{h}" rx="12" fill="{t["shadow"]}" '
            f'opacity="{t["shadow_opacity"]}"/>'
            f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/></clipPath>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{t["card"]}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="4" fill="{a}" clip-path="url(#{cid})"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" '
            f'stroke="{t["card_border"]}"/>'
        )
        cy = y + 34
        if tag:
            self.text(x + 16, y + 26, tag.upper(), size=10, weight=700, color=a, spacing="0.08em")
            cy = y + 46
        self.text(x + 16, cy, title, size=15, weight=600)
        for i, line in enumerate(lines):
            self.text(x + 16, cy + 20 + i * 18, line, size=12.5, color=t["muted"])

    def group(self, x, y, w, h, label):
        t = self.t
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{t["group"]}" '
            f'stroke="{t["group_border"]}" stroke-dasharray="5 5"/>'
        )
        self.text(x + 18, y + 24, label.upper(), size=11, weight=700, color=t["muted"], spacing="0.08em")

    def arrow(self, d, label=None, lx=None, ly=None, anchor="middle", dashed=False):
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{self.t["line"]}" stroke-width="1.75" '
            f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"{dash}/>'
        )
        if label:
            self.label(lx, ly, label, anchor)

    def label(self, x, y, s, anchor="middle"):
        # Small pill behind the label so it never collides with lines.
        width = len(s) * 6.6 + 16
        left = {"middle": x - width / 2, "start": x - 8, "end": x - width + 8}[anchor]
        self.parts.append(
            f'<rect x="{left:.1f}" y="{y - 13}" width="{width:.1f}" height="19" rx="9.5" '
            f'fill="{self.t["bg"]}" stroke="{self.t["card_border"]}"/>'
        )
        self.text(x, y + 1, s, size=11.5, color=self.t["muted"], anchor=anchor)

    def render(self) -> str:
        t = self.t
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
            "<defs>"
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{t["line"]}"/></marker>'
            "</defs>"
            f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="18" fill="{t["bg"]}" '
            f'stroke="{t["border"]}"/>' + "".join(self.parts) + "</svg>\n"
        )


def legend(s: Svg, x, y, items):
    for label, kind in items:
        s.parts.append(f'<rect x="{x}" y="{y - 10}" width="12" height="12" rx="3" fill="{s.accent(kind)}"/>')
        s.text(x + 18, y, label, size=12, color=s.t["muted"])
        x += 18 + len(label) * 7 + 28


def architecture(theme: str) -> str:
    s = Svg(1180, 660, theme)
    W, H = 190, 104
    s.text(40, 52, "AI Shopping Assistant", size=22, weight=700)
    s.text(40, 76, "Retrieval-augmented answers from real customer reviews", size=14, color=s.t["muted"])

    # Online request path
    top = 170
    xs = [40, 270, 515, 740, 950]
    s.group(495, 120, 665, 180, "LangChain RAG chain")
    s.node(
        xs[0], top, W, H, "client", "Chat UI", ["Browser, vanilla JS", "renders as plain text"], tag="Client"
    )
    s.node(
        xs[1], top, W, H, "app", "Flask API", ["Gunicorn, POST /get", "input limits, sessions"], tag="Server"
    )
    s.node(
        xs[2],
        top,
        205,
        H,
        "llm",
        "Query rewrite",
        ["Follow-up → standalone", "Llama 3.3 · temp 0"],
        tag="Groq",
    )
    s.node(
        xs[3], top, 190, H, "data", "Retriever", ["Top-k similar reviews", "numbered [1] [2] …"], tag="Search"
    )
    s.node(xs[4], top, 190, H, "llm", "Answer", ["Grounded, cites sources", "Llama 3.3 70B"], tag="Groq")

    mid = top + H / 2
    s.arrow(f"M{xs[0] + W},{mid} H{xs[1] - 4}")
    s.arrow(f"M{xs[1] + W},{mid} H{xs[2] - 4}")
    s.arrow(f"M{xs[2] + 205},{mid} H{xs[3] - 4}")
    s.arrow(f"M{xs[3] + 190},{mid} H{xs[4] - 4}")
    # Streamed response back to the browser
    s.arrow(
        f"M{xs[4] + 95},{top} V100 H{xs[0] + 95} V{top - 4}",
        "SSE stream: sources first, then tokens",
        640,
        100,
    )

    # Session memory under Flask
    s.node(xs[1], 350, W, 76, "app", "Session memory", ["per browser, last 12 msgs"])
    s.arrow(f"M{xs[1] + 80},{top + H} V346", dashed=True)
    s.arrow(f"M{xs[1] + 110},350 V{top + H + 4}", dashed=True)
    s.label(xs[1] + 150, 330, "chat history", anchor="start")

    # Divider and offline ingestion
    s.parts.append(
        f'<line x1="40" y1="456" x2="{s.w - 40}" y2="456" stroke="{s.t["border"]}" stroke-dasharray="4 6"/>'
    )
    s.text(40, 486, "OFFLINE INGESTION", size=11, weight=700, color=s.t["muted"], spacing="0.08em")
    s.text(178, 486, "python -m flipkart.data_ingestion", size=12, color=s.t["muted"])
    by = 505
    s.node(40, by, W, 88, "data", "Reviews CSV", ["product, rating, review"])
    s.node(270, by, W, 88, "app", "Data converter", ["clean rows → Documents"])
    s.node(515, by, 205, 88, "llm", "Embeddings", ["HF bge-base-en-v1.5"])
    s.node(xs[3], by, 190, 88, "data", "AstraDB", ["serverless vector store"])
    bmid = by + 44
    s.arrow(f"M{40 + W},{bmid} H{270 - 4}")
    s.arrow(f"M{270 + W},{bmid} H{515 - 4}")
    s.arrow(f"M{515 + 205},{bmid} H{xs[3] - 4}")
    s.arrow(f"M{xs[3] + 95},{top + H} V{by - 4}", "similarity search", xs[3] + 95, 400)

    legend(s, 950, 540, [("Client", "client")])
    legend(s, 950, 562, [("App", "app")])
    legend(s, 950, 584, [("LLM / model", "llm")])
    legend(s, 950, 606, [("Data", "data")])
    return s.render()


def cicd(theme: str) -> str:
    s = Svg(1180, 330, theme)
    s.text(40, 52, "CI/CD pipeline", size=22, weight=700)
    s.text(40, 76, "GitHub Actions · .github/workflows/main.yaml", size=14, color=s.t["muted"])

    W, H, y = 150, 104, 120
    xs = [40, 220, 400, 630, 810, 990]  # extra gap before the main-only stage
    steps = [
        ("ci", "Trigger", ["pull request", "or push to main"], "Event"),
        ("ci", "Lint & test", ["ruff · pytest", "no API keys needed"], "CI"),
        ("ci", "Docker build", ["python:3.12-slim", "gunicorn image"], "CI"),
        ("cd", "Push to ECR", ["tags latest + SHA", "Amazon ECR"], "CD"),
        ("cd", "Deploy to EC2", ["self-hosted runner", "replace container"], "CD"),
        ("cd", "Smoke test", ["GET /health", "fail → logs"], "CD"),
    ]
    for x, (kind, title, lines, tag) in zip(xs, steps, strict=True):
        s.node(x, y, W, H, kind, title, lines, tag=tag)
    mid = y + H / 2
    for a, b in zip(xs, xs[1:], strict=False):
        s.arrow(f"M{a + W},{mid} H{b - 4}")
    s.label((xs[2] + W + xs[3]) / 2, mid - 22, "main only")

    def bracket(x1, x2, text, color):
        yb = y + H + 26
        s.parts.append(
            f'<path d="M{x1},{yb - 8} V{yb} H{x2} V{yb - 8}" fill="none" stroke="{color}" stroke-width="2" '
            'stroke-linecap="round"/>'
        )
        s.text((x1 + x2) / 2, yb + 24, text, size=13, weight=600, color=color, anchor="middle")

    bracket(xs[0], xs[2] + W, "Every pull request and push: must pass before anything ships", s.accent("ci"))
    bracket(xs[3], xs[5] + W, "Push to main only: build, ship, verify", s.accent("cd"))
    return s.render()


def main() -> None:
    for theme in THEMES:
        (OUT / f"architecture-{theme}.svg").write_text(architecture(theme))
        (OUT / f"cicd-{theme}.svg").write_text(cicd(theme))
    print(f"Wrote diagrams to {OUT}")


if __name__ == "__main__":
    main()
