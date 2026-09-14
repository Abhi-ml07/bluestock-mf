import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import pandas as pd

from analytics import PERFORMANCE_FILE


PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_DIR = PROJECT_ROOT / "reports"


def build_report(output_path=None):
    performance = pd.read_csv(PERFORMANCE_FILE).sort_values("sharpe_ratio", ascending=False).head(10)
    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    table = performance[["scheme_name", "return_1yr_pct", "sharpe_ratio", "max_drawdown_pct", "risk_grade"]].to_html(index=False, classes="performance-table", border=0, float_format=lambda value: f"{value:.2f}")
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>body{{font-family:Arial,sans-serif;color:#18312f}}h1{{color:#0f766e}}table{{border-collapse:collapse;width:100%}}th,td{{padding:8px;border-bottom:1px solid #d8e2df;text-align:left}}th{{background:#e5f3ef}}</style></head><body><h1>Bluestock MF Weekly Summary</h1><p>Generated {generated_at}</p>{table}</body></html>"""
    output_path = Path(output_path or REPORT_DIR / "weekly_performance_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path, html


def send_report(html, subject="Bluestock MF Weekly Performance"):
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "REPORT_RECIPIENT"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing email settings: {', '.join(missing)}")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ["SMTP_USERNAME"]
    message["To"] = os.environ["REPORT_RECIPIENT"]
    message.set_content("Your email client does not support HTML reports.")
    message.add_alternative(html, subtype="html")
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and optionally email the weekly performance report.")
    parser.add_argument("--send", action="store_true", help="Send the report using SMTP environment variables.")
    args = parser.parse_args()
    path, html = build_report()
    if args.send:
        send_report(html)
    print(f"Report written to {path}")