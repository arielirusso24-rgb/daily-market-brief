# email_sender.py
"""Send the market brief as a clean, editorial HTML email.

Design goal: light, sober, FT-style. One accent (ink), restrained red/green
used only on numbers, generous whitespace. The Claude brief (markdown) is
rendered into real HTML - headings, bold, bullets - instead of dumped as raw
pre-wrapped text with literal asterisks.
"""

import os
import re
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

INK = "#1a1a1a"
BODY = "#374151"
MUTED = "#6b7280"
HAIR = "#e5e7eb"
SOFT = "#f9fafb"
GREEN = "#15803d"
RED = "#b91c1c"

DEFAULT_RECIPIENTS = ["arielirusso24@gmail.com", "lhaitog@gmail.com"]


# ---------------------------------------------------------------- markdown -->

def _color_numbers(text):
    """Tint signed percentages: green for gains, red for losses."""
    text = re.sub(r"(\+\d+(?:\.\d+)?%)",
                  rf'<span style="color:{GREEN};font-weight:600;">\1</span>', text)
    text = re.sub(r"(?<![\w>])(-\d+(?:\.\d+)?%)",
                  rf'<span style="color:{RED};font-weight:600;">\1</span>', text)
    return text


def _inline(text):
    """Escape + apply inline markdown (bold/italic) + tint percentages."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*",
                  rf'<strong style="color:{INK};font-weight:600;">\1</strong>', text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    return _color_numbers(text)


def _heading_html(text):
    label = _inline(text.rstrip(":"))
    return (f'<div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;'
            f'color:{INK};font-weight:600;border-bottom:1px solid {HAIR};'
            f'padding-bottom:6px;margin:26px 0 12px;">{label}</div>')


def markdown_to_html(md):
    """Convert the brief's markdown subset into inline-styled HTML."""
    out, in_list, first_para = [], False, True

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in md.split("\n"):
        stripped = raw.strip()
        if not stripped:
            close_list()
            continue

        if stripped in ("---", "***", "___"):
            close_list()
            continue

        # Heading: '## X', '### X', or a line that is entirely **bold**
        m_hash = re.match(r"^#{1,6}\s+(.*)$", stripped)
        m_bold = re.match(r"^\*\*(.+?)\*\*:?$", stripped)
        if m_hash or m_bold:
            close_list()
            out.append(_heading_html((m_hash or m_bold).group(1)))
            continue

        if stripped.startswith(("- ", "* ")):
            if not in_list:
                out.append('<ul style="margin:0 0 12px;padding-left:20px;">')
                in_list = True
            out.append(f'<li style="font-size:15px;line-height:1.65;color:{BODY};'
                       f'margin:0 0 9px;">{_inline(stripped[2:])}</li>')
            continue

        close_list()
        if first_para:
            first_para = False
            out.append(f'<p style="font-family:Georgia,\'Times New Roman\',serif;'
                       f'font-size:18px;line-height:1.6;color:{INK};margin:0 0 16px;">'
                       f'{_inline(stripped)}</p>')
        else:
            out.append(f'<p style="font-size:15px;line-height:1.7;color:{BODY};'
                       f'margin:0 0 12px;">{_inline(stripped)}</p>')

    close_list()
    return "\n".join(out)


# ------------------------------------------------------------ data sections -->

def _render_indices(market_data):
    """Light, hairline index cards from the market_data dict."""
    cards = []
    for name, data in market_data.items():
        if name.startswith("_") or not data.get("is_index"):
            continue
        pct = data.get("change_percent", 0)
        color = GREEN if pct >= 0 else RED
        arrow = "&#9650;" if pct >= 0 else "&#9660;"
        sign = "+" if pct >= 0 else ""
        short = name.split(" (")[0]
        cards.append(
            f'<td style="width:25%;padding:10px 8px;text-align:center;'
            f'border:1px solid {HAIR};border-radius:8px;">'
            f'<div style="font-size:11px;color:{MUTED};font-weight:600;">{html.escape(short)}</div>'
            f'<div style="font-size:16px;color:{INK};font-weight:600;margin-top:3px;">'
            f'${data.get("latest_price", 0):,.2f}</div>'
            f'<div style="font-size:13px;color:{color};font-weight:600;margin-top:1px;">'
            f'{arrow} {sign}{pct:.2f}%</div></td>'
        )
    if not cards:
        return ""
    # pad spacing cells between the 4 columns
    row = '<td style="width:8px;"></td>'.join(cards)
    return (f'<table style="width:100%;border-collapse:separate;border-spacing:0;'
            f'margin:4px 0 8px;"><tr>{row}</tr></table>')


def _mover_rows(stocks, positive):
    color = GREEN if positive else RED
    rows = []
    for s in stocks:
        pct = s.get("change_percent", 0)
        sign = "+" if pct >= 0 else ""
        name = html.escape((s.get("name") or "")[:22])
        rows.append(
            f'<div style="padding:8px 0;border-bottom:1px solid {SOFT};">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<span style="font-size:13px;color:{INK};font-weight:600;">{html.escape(s.get("symbol",""))}</span>'
            f'<span style="font-size:13px;color:{color};font-weight:600;">{sign}{pct:.2f}%</span></div>'
            f'<div style="font-size:11px;color:{MUTED};margin-top:1px;">{name}</div></div>'
        )
    return "".join(rows)


def _render_movers(market_data):
    gainers = market_data.get("_gainers", [])
    losers = market_data.get("_losers", [])
    if not gainers and not losers:
        return ""
    label = ('font-size:11px;letter-spacing:1px;text-transform:uppercase;'
             'font-weight:600;margin-bottom:6px;')
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:4px 0;"><tr>'
        f'<td style="width:50%;vertical-align:top;padding-right:14px;">'
        f'<div style="{label}color:{GREEN};">Top gainers</div>{_mover_rows(gainers, True)}</td>'
        f'<td style="width:50%;vertical-align:top;padding-left:14px;">'
        f'<div style="{label}color:{RED};">Top decliners</div>{_mover_rows(losers, False)}</td>'
        f'</tr></table>'
    )


def _render_headlines(headlines):
    if not headlines:
        return "<p style=\"color:%s;\">Limited headlines today.</p>" % MUTED
    items = []
    for h in headlines:
        title = html.escape(h.get("title", ""))
        source = html.escape(h.get("source", ""))
        link = html.escape(h.get("link", "#"))
        items.append(
            f'<div style="padding:9px 0;border-bottom:1px solid {SOFT};">'
            f'<span style="font-size:10px;letter-spacing:0.5px;text-transform:uppercase;'
            f'color:{MUTED};font-weight:600;">{source}</span>'
            f'<div style="margin-top:2px;"><a href="{link}" style="font-size:14px;'
            f'color:{INK};text-decoration:none;line-height:1.45;">{title}</a></div></div>'
        )
    return "".join(items)


def _section_label(text, color=INK):
    return (f'<div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;'
            f'color:{color};font-weight:600;border-bottom:1px solid {HAIR};'
            f'padding-bottom:6px;margin:26px 0 12px;">{text}</div>')


# ----------------------------------------------------------------- assembly -->

def build_email_html(market_data, headlines, brief, charts_html=""):
    """Return the full HTML document for the brief email."""
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    brief_html = markdown_to_html(brief) if brief else ""
    charts = (f'<div style="margin:18px 0;">{charts_html}</div>') if charts_html else ""

    pad = "padding:0 30px;"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#eef1f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<div style="max-width:620px;margin:0 auto;background:#ffffff;">

  <div style="{pad}padding-top:30px;padding-bottom:16px;border-bottom:2px solid {INK};">
    <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{MUTED};">Daily Market Brief</div>
    <div style="font-family:Georgia,'Times New Roman',serif;font-size:26px;color:{INK};font-weight:700;margin-top:6px;">{date_str}</div>
  </div>

  <div style="{pad}padding-top:18px;">{_render_indices(market_data)}</div>

  <div style="{pad}">{brief_html}{charts}</div>

  <div style="{pad}">{_section_label('At a glance &middot; biggest movers')}{_render_movers(market_data)}</div>

  <div style="{pad}padding-bottom:6px;">{_section_label('Headlines &middot; across the wires')}{_render_headlines(headlines)}</div>

  <div style="{pad}padding-top:24px;padding-bottom:28px;">
    <div style="border-top:1px solid {HAIR};padding-top:14px;font-size:11px;color:{MUTED};line-height:1.6;">
      Daily Market Brief &middot; S&amp;P 500 scan via yfinance &middot; multi-source RSS &middot; analysis by Claude<br>
      Automated &middot; delivered each morning, 30 minutes after the US market open.
    </div>
  </div>

</div>
</body></html>"""


def send_email_brief(subject, market_formatted, headlines_list, brief,
                     charts_html="", to_email=None, market_data=None):
    """Send the brief. Pass market_data (the dict from get_market_data) for the
    rich layout; market_formatted is kept for signature compatibility."""
    from_email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not from_email or not password:
        print("❌ Email credentials not found")
        return False

    recipients = DEFAULT_RECIPIENTS
    if to_email:
        recipients = [to_email] if isinstance(to_email, str) else to_email

    try:
        html_content = build_email_html(market_data or {}, headlines_list, brief, charts_html)

        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email sent successfully to {len(recipients)} recipients")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
