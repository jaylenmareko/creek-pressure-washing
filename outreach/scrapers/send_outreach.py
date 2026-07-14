#!/usr/bin/env python3
"""
Creek Pressure Washing — Cold Email Sender
Reads top500-emails-*.csv, sends Template A via Resend API,
logs every send to outreach-log.csv.

Usage:
    pip install requests
    python send_outreach.py

Dry run (preview only, no sends):
    python send_outreach.py --dry-run
"""

import os, csv, sys, json, time, requests
from datetime import date, datetime
from glob import glob

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "..", "data")
LOG_FILE   = os.path.join(DATA_DIR, "outreach-log.csv")
SENT_FILE  = os.path.join(DATA_DIR, ".sent_emails.json")

RESEND_API_KEY = "re_dMHzfeWu_Cc6a4nX2Kgs9Hn4UhGbDpyAU"
FROM_EMAIL     = "Jaylen <jaylen@creekpressurewashing.com>"
REPLY_TO       = "jaylen@creekpressurewashing.com"

DRY_RUN = "--dry-run" in sys.argv

# ── Template A ────────────────────────────────────────────────────────────────

def build_email(business_name, category):
    if category in ("restaurants", "food", "cafes", "bakeries", "bars"):
        subject = f"Bid for exterior cleaning — {business_name}"
        body = f"""Hi,

I'd like to place a bid for exterior cleaning at {business_name}.

Creek Pressure Washing handles dumpster pads, entry walks, drive-throughs, and building fronts across South-Central Kansas.

I'll get you an estimate. Reply or call (620) 291-4583.

— Jaylen
Creek Pressure Washing LLC
jaylen@creekpressurewashing.com"""

    elif category in ("propertymgmt", "realestatesvcs"):
        subject = f"Bid for pressure washing — {business_name}"
        body = f"""Hi,

I'd like to place a bid for pressure washing at your properties.

Creek Pressure Washing does driveways, parking lots, and building exteriors — great fit for tenant turns and seasonal cleaning across South-Central Kansas.

I'll get you an estimate. Reply or call (620) 291-4583.

— Jaylen
Creek Pressure Washing LLC
jaylen@creekpressurewashing.com"""

    else:
        subject = f"Bid request — pressure washing for {business_name}"
        body = f"""Hi,

I'd like to place a bid for pressure washing services at {business_name}.

We're Creek Pressure Washing, based in South-Central Kansas — we handle parking lots, building exteriors, driveways, and loading areas.

I'll get you an estimate. Reply, call (620) 291-4583, or email jaylen@creekpressurewashing.com.

— Jaylen
Creek Pressure Washing LLC"""

    return subject, body


def send_email(to_email, subject, body):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": FROM_EMAIL, "to": [to_email], "reply_to": REPLY_TO,
              "subject": subject, "text": body},
        timeout=15,
    )
    return resp.status_code, resp.json()


def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE) as f: return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f: json.dump(list(sent), f)

def log_send(row, email, subject, status, error=""):
    exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","business_name","city","category","email","subject","status","error"])
        if not exists: w.writeheader()
        w.writerow({"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "business_name": row["business_name"], "city": row["city"],
                    "category": row["category"], "email": email,
                    "subject": subject, "status": status, "error": error})


def main():
    # Find the most recent top500 email file
    files = sorted(glob(os.path.join(DATA_DIR, "top500-emails-*.csv")), reverse=True)
    if not files:
        print("No top500-emails-*.csv found. Run find_emails_top500.py first.")
        sys.exit(1)

    input_file = files[0]
    print(f"Input: {input_file}")
    print(f"Dry run: {DRY_RUN}\n")

    with open(input_file, encoding="utf-8") as f:
        leads = [r for r in csv.DictReader(f) if r.get("emails","").strip()]

    print(f"Leads with emails: {len(leads)}")

    sent = load_sent()
    send_count = 0
    skip_count = 0

    for lead in leads:
        emails = [e.strip() for e in lead["emails"].split("|") if e.strip()]
        for email in emails[:1]:  # send to first email only per business
            if email in sent:
                skip_count += 1
                continue

            subject, body = build_email(lead["business_name"], lead["category"])

            if DRY_RUN:
                print(f"[DRY RUN] To: {email} | Subject: {subject}")
                print(f"  Business: {lead['business_name']} ({lead['city']})")
                continue

            status_code, resp = send_email(email, subject, body)
            if status_code in (200, 201):
                print(f"✓ Sent → {email} ({lead['business_name']})")
                sent.add(email)
                save_sent(sent)
                log_send(lead, email, subject, "sent")
                send_count += 1
            else:
                err = resp.get("message", str(resp))
                print(f"✗ Failed → {email} | {err}")
                log_send(lead, email, subject, "failed", err)

            time.sleep(1.5)  # ~40/min, well under Resend limits

    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Done. Sent: {send_count} | Skipped (already sent): {skip_count}")
    if not DRY_RUN: print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
