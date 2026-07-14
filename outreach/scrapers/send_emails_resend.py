"""
Send 8 property manager cold emails via Resend API.
"""

import requests
import json

API_KEY = 're_dMHzfeWu_Cc6a4nX2Kgs9Hn4UhGbDpyAU'
FROM = 'Jaylen @ Creek Pressure Washing <us@creekpressurewashing.com>'

EMAILS = [
    {
        'to': 'aaron@wisepropertymng.com',
        'subject': 'exterior cleaning for your properties',
        'body': """Hi Aaron,

Saw that Wise Property Management handles residential properties in the area. We're a local crew out of Cowley County that does pressure washing for property managers. Driveways, parking lots, building exteriors, and tenant turns.

Interested?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'michelle@hometownsaleslease.com',
        'subject': 'pressure washing for your listings',
        'body': """Hi Michelle,

We work with property managers in the area on exterior cleaning before tenant turns and listings. Local crew out of Cowley County. Driveways, siding, and parking areas.

Interested?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'angela@albright-realty.com',
        'subject': 'exterior cleaning for property listings',
        'body': """Hi Angela,

We do pressure washing for property managers and real estate offices in Cowley County. Driveways, siding, decks, and exteriors. Good fit for listings that need a refresh before photos or showings.

Interested?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'rick@arkcitypropertyshop.com',
        'subject': 'pressure washing for your properties',
        'body': """Hi Rick,

We're a local crew out of Cowley County doing exterior pressure washing for property managers and rental owners. Parking lots, driveways, building exteriors, and tenant turns.

Interested?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'chmpropertygroup@icloud.com',
        'subject': 'exterior cleaning for your properties',
        'body': """Hi,

We're Creek Pressure Washing, a local crew out of Cowley County. We do pressure washing for property managers handling driveways, parking lots, and building exteriors. Good fit for seasonal cleaning and tenant turns.

Interested?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'walnuttowers@livemillennia.com',
        'subject': 'exterior cleaning for Walnut Towers',
        'body': """Hi,

We're Creek Pressure Washing, a local crew out of Cowley County. We service apartment communities with pressure washing for parking lots, sidewalks, building facades, and breezeways.

Interested in a quote for Walnut Towers?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'meadowwalk@parawestmanagement.com',
        'subject': 'pressure washing for Meadow Walk',
        'body': """Hi,

We're Creek Pressure Washing, a local crew out of Cowley County. We do exterior cleaning for apartment communities. Parking lots, breezeways, sidewalks, and building exteriors.

Interested in a quote for Meadow Walk?

Jaylen
Creek Pressure Washing LLC
(620) 291-4583
creekpressurewashing.com""",
    },
    {
        'to': 'gwarkansascity@belmontmgt.net',
        'subject': 'exterior cleaning for your Arkansas City properties',
        'body': """Hi,

We're Creek Pressure Washing, a local crew out of Cowley County serving the Arkansas City area. We handle pressure washing for apartment communities and commercial properties. Parking lots, walkways, and building exteriors.

Interested?

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
