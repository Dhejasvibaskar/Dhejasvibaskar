"""Generate original, self-hosted GitHub profile SVGs. No personal access token needed."""
import io
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

from PIL import Image, ImageOps, ImageEnhance

USER = os.environ.get('PROFILE_USERNAME', 'Dhejasvibaskar')
OUT = Path('assets')
QUERY = '''query($login:String!) {
  user(login:$login) {
    login avatarUrl(size:256)
    repositories(privacy:PUBLIC, ownerAffiliations:OWNER) { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount } }
      }
    }
  }
}'''


def request(url, payload=None, token=None):
    headers = {'User-Agent': 'Neural-Identity-Profile/1.0'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urlopen(Request(url, data=payload, headers=headers), timeout=40) as response:
        return response.read()


def fetch_profile():
    token = os.environ['GITHUB_TOKEN']
    payload = json.dumps({'query': QUERY, 'variables': {'login': USER}}).encode()
    result = json.loads(request('https://api.github.com/graphql', payload, token))
    if result.get('errors') or not result.get('data', {}).get('user'):
        raise RuntimeError('GitHub API query failed: ' + json.dumps(result.get('errors', [])))
    return result['data']['user']


def portrait(image):
    # Clearer ASCII portrait: fewer cells, larger glyphs, stronger contrast.
    image = ImageOps.fit(image.convert('RGB'), (38, 26), method=Image.Resampling.LANCZOS)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.8)
    gray = ImageEnhance.Sharpness(gray).enhance(1.5)

    chars = " .:-=+*#%@"
    out = []

    start_x, start_y = 736, 104
    step_x, step_y = 6.8, 10.2

    for y in range(26):
        for x in range(38):
            dx, dy = (x - 18.5) / 18.8, (y - 12.5) / 13.0
            if dx * dx + dy * dy > 1:
                continue

            value = gray.getpixel((x, y))
            r, g, b = image.getpixel((x, y))

            # Brighter blend for better readability on dark background
            mix = 0.38 + 0.30 * (value / 255)
            rr = int(r * (1 - mix) + 233 * mix)
            gg = int(g * (1 - mix) + 221 * mix)
            bb = int(b * (1 - mix) + 250 * mix)
            color = f'#{rr:02x}{gg:02x}{bb:02x}'

            char = chars[round(value * (len(chars) - 1) / 255)]
            opacity = 0.58 + 0.35 * (value / 255)

            out.append(
                f'<text x="{start_x + x * step_x:.1f}" '
                f'y="{start_y + y * step_y:.1f}" '
                f'fill="{color}" font-size="10.2" font-weight="700" '
                f'opacity="{opacity:.2f}">{char}</text>'
            )

    return ''.join(out)


def hero(user, photo):
    cal = user['contributionsCollection']['contributionCalendar']
    repo_count = user['repositories']['totalCount']
    login = escape(user['login'])
    art = portrait(photo)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1050 430" width="1050" height="430" role="img" aria-labelledby="title desc">
<title id="title">J B Dhejasvi — Neural Identity</title><desc id="desc">AI and Data Science undergraduate, with an ASCII rendering of her public GitHub avatar.</desc>
<defs>
 <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#a78bfa" stroke-opacity=".07"/></pattern>
 <linearGradient id="background" x2="1" y2="1"><stop stop-color="#090d19"/><stop offset="1" stop-color="#12132b"/></linearGradient>
 <linearGradient id="type"><stop stop-color="#f4efff"/><stop offset="1" stop-color="#aa87ff"/></linearGradient>
 <radialGradient id="glow"><stop stop-color="#8152ef" stop-opacity=".20"/><stop offset="1" stop-color="#8152ef" stop-opacity="0"/></radialGradient>
</defs>
<rect x="1" y="1" width="1048" height="428" rx="22" fill="url(#background)" stroke="#4c3b71" stroke-width="1.5"/>
<rect x="1" y="1" width="1048" height="428" rx="22" fill="url(#grid)"/>
<g font-family="monospace">
 <text x="36" y="38" font-size="12" letter-spacing="3" fill="#a78bfa">NEURAL IDENTITY / 01</text>
 <text x="1014" y="38" text-anchor="end" font-size="12" fill="#8993b7">@{login}</text>
 <circle cx="848" cy="225" r="189" fill="url(#glow)"/>
 <circle cx="848" cy="225" r="155" fill="none" stroke="#3b315f"/>
 <circle cx="848" cy="225" r="165" fill="none" stroke="#9d78f9" stroke-width="1.2" stroke-opacity=".75" stroke-dasharray="90 35 5 30 20 45">
   <animateTransform attributeName="transform" type="rotate" from="0 848 225" to="360 848 225" dur="35s" repeatCount="indefinite"/>
 </circle>
 <g>{art}</g>
 <circle cx="41" cy="104" r="4" fill="#6ee7d1"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>
 <text x="54" y="108" fill="#6ee7d1" font-size="13" letter-spacing="3">HELLO, WORLD. I'M</text>
 <text x="32" y="186" font-size="70" font-weight="bold" fill="url(#type)">J B</text>
 <text x="32" y="261" font-size="70" font-weight="bold" fill="url(#type)">Dhejasvi</text>
 <text x="36" y="296" fill="#e4ddfa" font-size="19">AI &amp; Data Science Undergraduate</text>
 <text x="36" y="326" fill="#9d9ab9" font-size="12" letter-spacing=".8">MACHINE LEARNING / DATA ANALYTICS / COMPUTER VISION</text>
 <line x1="36" y1="364" x2="1014" y2="364" stroke="#3d3558"/>
 <text x="36" y="386" font-size="10" letter-spacing="1.5" fill="#9890b7">PUBLIC REPOSITORIES</text>
 <text x="36" y="410" font-size="21" fill="#e2d7ff">{repo_count}</text>
 <text x="310" y="386" font-size="10" letter-spacing="1.5" fill="#9890b7">CONTRIBUTIONS (PAST YEAR)</text>
 <text x="310" y="410" font-size="21" fill="#e2d7ff">{cal['totalContributions']}</text>
 <text x="1014" y="408" text-anchor="end" font-size="12" fill="#6ee7d1">CHENNAI, INDIA / BUILDING &amp; LEARNING</text>
</g></svg>'''


def city(user):
    cal = user['contributionsCollection']['contributionCalendar']
    cells = [(w, d['weekday'], d['contributionCount'], d['date']) for w, week in enumerate(cal['weeks']) for d in week['contributionDays']]
    peak = max((c[2] for c in cells), default=0)
    active = sum(c[2] > 0 for c in cells)
    blocks = []
    for w, d, count, date in sorted(cells, key=lambda c: (c[0] * 1.8 + c[1] * 8, c[0])):
        x, y = 108 + w * 16.1 - d * 9, 108 + w * 1.8 + d * 8
        h = 0 if not count else 6 + 58 * math.log1p(count) / math.log1p(max(1, peak))
        top = '#9e81f5' if count else '#20263b'
        side = '#5638a2' if count else '#20263b'
        front = '#392568' if count else '#20263b'
        if count:
            blocks.append(f'<polygon points="{x},{y-h} {x+13},{y+3-h} {x+13},{y+3} {x},{y}" fill="{front}" stroke="#151328" stroke-width=".4"/>')
            blocks.append(f'<polygon points="{x+13},{y+3-h} {x+22},{y-3-h} {x+22},{y-3} {x+13},{y+3}" fill="{side}" stroke="#151328" stroke-width=".4"/>')
        blocks.append(f'<polygon points="{x},{y-h} {x+9},{y-6-h} {x+22},{y-3-h} {x+13},{y+3-h}" fill="{top}" stroke="#111525" stroke-width=".65"><title>{escape(date)}: {count} contributions</title></polygon>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1050 335" width="1050" height="335" role="img" aria-labelledby="title desc">
<title id="title">The City I'm Building</title><desc id="desc">An isometric visualization of daily GitHub contributions during the past year. Taller purple blocks represent more contributions.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0b101e"/><stop offset="1" stop-color="#17122b"/></linearGradient></defs>
<rect x="1" y="1" width="1048" height="333" rx="22" fill="url(#bg)" stroke="#4c3b71" stroke-width="1.5"/>
<g font-family="monospace"><text x="35" y="40" fill="#e6dcff" font-size="24" font-weight="bold">THE CITY I'M BUILDING</text><text x="1015" y="40" text-anchor="end" fill="#a78bfa" font-size="11" letter-spacing="2">CONTRIBUTION MAP / 365 DAYS</text>
<text x="35" y="64" fill="#a7a0bd" font-size="12">One block per day. Height reflects activity.</text></g>
{''.join(blocks)}
<line x1="35" y1="288" x2="1015" y2="288" stroke="#3d3558"/>
<g font-family="monospace" font-size="12" fill="#b6a2e9"><text x="35" y="312">{cal['totalContributions']} CONTRIBUTIONS</text><text x="315" y="312">{active} ACTIVE DAYS</text><text x="1015" y="312" text-anchor="end" fill="#6ee7d1">GITHUB CALENDAR / AUTO-UPDATED</text></g>
</svg>'''


def main():
    user = fetch_profile()
    photo = Image.open(io.BytesIO(request(user['avatarUrl'])))
    OUT.mkdir(exist_ok=True)
    (OUT / 'neural-identity.svg').write_text(hero(user, photo), encoding='utf-8')
    (OUT / 'contribution-city.svg').write_text(city(user), encoding='utf-8')
    print('Generated both SVGs successfully.')


if __name__ == '__main__':
    main()
