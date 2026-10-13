"""
Generates the synthetic demo documents. Only needed if you change the numbers.
    pip install pillow && python assets/make_bill.py

If you change a bill, also update DEMO_BILLS in backend/llm.py and BILLS in
frontend/sandbox/index.html so mock mode and the sandbox agree with the picture.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent


def font(size, bold=False):
    names = (["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
             if bold else ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def bill(path, cid, units, energy, fixed, duty, total, due, prev):
    W, H = 900, 1180
    img = Image.new("RGB", (W, H), "#fbfaf6")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 150], fill="#1f4e79")
    d.text((40, 32), "DEMO ELECTRICITY", font=font(46, True), fill="white")
    d.text((40, 95), "Distribution Company Ltd.  ·  SYNTHETIC BILL FOR DEMO ONLY", font=font(20), fill="#cfe0f0")
    d.text((40, 180), "ELECTRICITY BILL  —  Sep 2026", font=font(30, True), fill="#1f2a37")
    rows = [
        ("Consumer Name", "Smt. Lakshmi Devi (sample)"),
        ("Consumer ID", cid),
        ("Address", "H.No 1-2-3, Sample Colony, Hyderabad"),
        ("Billing Period", "01 Sep 2026 – 30 Sep 2026"),
        ("Meter Reading", f"Prev {prev:,}  ·  Curr {prev + units:,}"),
        ("Units Consumed", f"{units:,} kWh"),
        ("Energy Charges", f"₹ {energy:,.2f}"),
        ("Fixed Charges", f"₹ {fixed:,.2f}"),
        ("Electricity Duty", f"₹ {duty:,.2f}"),
    ]
    y = 250
    for k, v in rows:
        d.text((40, y), k, font=font(24), fill="#5b6470")
        d.text((360, y), v, font=font(24, True), fill="#1f2a37")
        y += 52
        d.line([40, y - 12, W - 40, y - 12], fill="#e3e0d7", width=1)
    y += 20
    d.rectangle([40, y, W - 40, y + 190], outline="#c0392b", width=4, fill="#fff4f2")
    d.text((70, y + 25), "TOTAL AMOUNT PAYABLE", font=font(26, True), fill="#c0392b")
    d.text((70, y + 70), f"₹ {total:,.2f}", font=font(60, True), fill="#1f2a37")
    d.text((540, y + 40), "DUE DATE", font=font(24, True), fill="#c0392b")
    d.text((540, y + 80), due, font=font(36, True), fill="#1f2a37")
    d.text((40, H - 90), "Pay at: sandbox.saathi.local  ·  This is a synthetic document for the Saathi prototype.",
           font=font(18), fill="#8a8f96")
    img.save(HERE / path)
    return img


def letter(path):
    W, H = 900, 1180
    img = Image.new("RGB", (W, H), "#fdfcf8")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill="#7a1f1f")
    d.text((40, 40), "OFFICE OF THE DEMO PENSION DISBURSING AUTHORITY", font=font(26, True), fill="#7a1f1f")
    d.text((40, 80), "Synthetic letter for the Saathi prototype — not a real notice", font=font(18), fill="#8a8f96")
    d.text((40, 140), "Ref: DPDA/LC/2026/00417                                  Date: 01 Oct 2026", font=font(20), fill="#1f2a37")
    d.text((40, 200), "To,\nSmt. Lakshmi Devi (sample)\nPPO No: DEMO-PPO-55120\nHyderabad", font=font(22), fill="#1f2a37", spacing=8)
    d.text((40, 360), "Subject: Submission of Annual Life Certificate", font=font(24, True), fill="#1f2a37")
    body = ("Madam,\n\n"
            "As per the rules governing payment of pension, every pensioner is required\n"
            "to submit an Annual Life Certificate in the month of November each year.\n\n"
            "You are requested to submit your Life Certificate on or before\n"
            "30 November 2026 at the branch of your pension-paying bank or at any\n"
            "authorised digital life certificate centre.\n\n"
            "Please carry your Aadhaar card and PPO number at the time of submission.\n\n"
            "Kindly note that in case the Life Certificate is not received by the due\n"
            "date, payment of pension shall be kept in abeyance until the certificate\n"
            "is submitted.")
    d.text((40, 420), body, font=font(21), fill="#1f2a37", spacing=10)
    d.text((560, 1000), "Sd/-\nPension Officer (Demo)", font=font(22), fill="#1f2a37", spacing=8)
    img.save(HERE / path)


normal = bill("demo_bill.png", "DEMO123", 210, 735, 60, 45, 840, "15 Oct 2026", 4120)
normal.filter(ImageFilter.GaussianBlur(9)).rotate(7, fillcolor="#444").save(HERE / "demo_bill_blurry.png")
bill("demo_bill_large.png", "DEMO456", 1420, 5980, 120, 400, 6500, "20 Oct 2026", 18350)
letter("demo_letter.png")
print("wrote demo_bill.png, demo_bill_blurry.png, demo_bill_large.png, demo_letter.png")
