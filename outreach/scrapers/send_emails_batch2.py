"""
Batch 2 cold emails — real estate/property contacts found via Google Maps research.
"""

import requests

API_KEY = 're_dMHzfeWu_Cc6a4nX2Kgs9Hn4UhGbDpyAU'
FROM = 'Jaylen @ Creek Pressure Washing <us@creekpressurewashing.com>'

EMAILS = [
    {
        'to': 'rick@webberland.com',
        'subject': 'pressure washing for listings and rental properties',
        'body': """Hi Rick,

We're Creek Pressure Washing, a local crew out of Cowley County. We work with real estate offices on exterior cleaning before listings go live — driveways, siding, decks, and walkways. Makes a difference in listing photos.

Also handle rental property turns if you manage any residential units.

Interested in a quote?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'darrell@webberland.com',
        'subject': 'exterior cleaning before listings',
        'body': """Hi Darrell,

We do pressure washing for real estate agents and property owners in Cowley County. Driveways, siding, decks — good for listings that need curb appeal before photos or showings.

Worth a conversation?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
]


def send(email):
    resp = requests.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
        json={'from': FROM, 'to': [email['to']], 'subject': email['subject'], 'text': email['body']},
    )
    if resp.status_code == 200:
        print(f'  SENT   {email["to"]}  (id: {resp.json().get("id", "?")})')
        return True
    else:
        print(f'  FAILED {email["to"]}  {resp.status_code}: {resp.text[:200]}')
        return False


if __name__ == '__main__':
    print(f'Sending {len(EMAILS)} emails via Resend...\n')
    sent = 0
    for email in EMAILS:
        if send(email):
            sent += 1
    print(f'\nDone. {sent}/{len(EMAILS)} sent.')
