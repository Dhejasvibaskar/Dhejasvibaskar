"""Generate original, self-hosted GitHub profile SVGs. No personal access token needed."""
import io
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

from PIL import Image, ImageOps, ImageEnhance, ImageFilter

USER = os.environ.get('PROFILE_USERNAME', 'Dhejasvibaskar')
OUT = Path('assets')
QUERY = '''query($login:String!) {
  user(login:$login) {
    login avatarUrl(size:512)
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
    """Fine, full-color ASCII mosaic; sample a square with no forced purple tint."""
    n = 66
    diameter = 352
    cx, cy = 838, 265
    step = diameter / n
    square = ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'),
                          (512, 512), method=Image.Resampling.LANCZOS)
    # A small, upward-biased crop leaves the head and shoulders visible.
    square = square.crop((29, 11, 483, 465))
    square = ImageEnhance.Color(square).enhance(1.10)
    square = square.filter(ImageFilter.UnsharpMask(radius=1.5, percent=100, threshold=3))
    pixels = square.resize((n, n), Image.Resampling.LANCZOS)
    out = []
    for y in range(n):
        for x in range(n):
            dx = (x + .5 - n / 2) / (n / 2)
            dy = (y + .5 - n / 2) / (n / 2)
            if dx * dx + dy * dy > 1.0:
                continue
            r, g, b = pixels.getpixel((x, y))
            luminance = (.2126*r + .7152*g + .0722*b) / 255
            # Avoid making the bright background dominate the darker face.
            # Gamma lifts midtones and shadows, then compresses highlights.
            def lift(v):
                return min(255, round(24 + 218 * (v / 255) ** .68))
            color = f'#{lift(r):02x}{lift(g):02x}{lift(b):02x}'
            # Use simple, consistent light glyphs rather than large @/# blocks.
            char = '+' if luminance >= .33 else (':' if luminance >= .13 else '.')
            px = cx - diameter / 2 + (x + .5) * step
            py = cy - diameter / 2 + (y + .5) * step + 2.1
            out.append(f'<text x="{px:.2f}" y="{py:.2f}" fill="{color}">{char}</text>')
    return ''.join(out)


def hero(user, photo):
    cal = user['contributionsCollection']['contributionCalendar']
    repo_count = user['repositories']['totalCount']
    login = escape(user['login'])
    art = portrait(photo)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1050 580" width="1050" height="580" role="img" aria-labelledby="title desc">
<title id="title">J B Dhejasvi — Neural Identity</title><desc id="desc">AI and Data Science undergraduate, with a natural-color ASCII rendering of her GitHub avatar and current GitHub statistics.</desc>
<defs>
 <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#8b9bc0" stroke-opacity=".065"/></pattern>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#090e19"/><stop offset="1" stop-color="#0e101e"/></linearGradient>
 <radialGradient id="glow"><stop stop-color="#c5784d" stop-opacity=".14"/><stop offset="1" stop-color="#c5784d" stop-opacity="0"/></radialGradient>
 <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d2925d"/><stop offset="1" stop-color="#aa8cec"/></linearGradient>
 <pattern id="glyphs" width="5.5" height="5.5" patternUnits="userSpaceOnUse"><path d="M2.75 .7V4.8M.7 2.75H4.8" fill="none" stroke="#dce4f4" stroke-width=".85"/></pattern>
</defs>
<rect x="1" y="1" width="1048" height="578" rx="22" fill="url(#bg)" stroke="#443245" stroke-width="1.3"/>
<rect x="1" y="1" width="1048" height="578" rx="22" fill="url(#grid)"/>
<g font-family="monospace">
 <text x="40" y="43" font-size="12" letter-spacing="3" fill="#8d9fbd">NEURAL IDENTITY / 02</text>
 <text x="1010" y="43" text-anchor="end" font-size="12" fill="#8d9fbd">@{login}</text>
 <circle cx="838" cy="265" r="212" fill="url(#glow)"/>
 <circle cx="838" cy="265" r="191" fill="none" stroke="#644553" stroke-opacity=".62"/>
 <circle cx="838" cy="265" r="181" fill="none" stroke="url(#ring)" stroke-width="1.1" stroke-opacity=".85" stroke-dasharray="100 32 5 24 36 60 90 40">
   <animateTransform attributeName="transform" type="rotate" from="0 838 265" to="360 838 265" dur="38s" repeatCount="indefinite"/>
 </circle>
 <g font-size="6.35" text-anchor="middle" font-weight="600">{art}</g>
 <text x="40" y="125" fill="#e29a69" font-size="13" letter-spacing="3">HELLO, WORLD. I'M</text>
 <g font-size="74" font-weight="bold" fill="url(#glyphs)" stroke="#d4ddf1" stroke-width=".7" paint-order="stroke fill">
   <text x="38" y="213">J B</text>
   <text x="38" y="299">Dhejasvi</text>
 </g>
 <text x="42" y="354" fill="#e4e9f5" font-size="19" font-weight="bold">AI &amp; Data Science Undergraduate</text>
 <text x="42" y="384" fill="#9ba9c3" font-size="12">MACHINE LEARNING / DATA ANALYTICS</text>
 <text x="42" y="405" fill="#9ba9c3" font-size="12">COMPUTER VISION</text>
 <line x1="40" y1="478" x2="1010" y2="478" stroke="#2f394e"/>
 <g font-size="10" letter-spacing="1.8" fill="#92a1bc">
  <text x="42" y="512">PUBLIC REPOSITORIES</text>
  <text x="300" y="512">CONTRIBUTIONS / YEAR</text>
  <text x="570" y="512">LOCATION</text>
  <text x="805" y="512">STATUS</text>
 </g>
 <g fill="#e4e9f5" font-size="25" font-weight="bold">
  <text x="42" y="547">{repo_count}</text>
  <text x="300" y="547">{cal['totalContributions']}</text>
 </g>
 <text x="570" y="545" fill="#e4e9f5" font-size="15">Chennai, India</text>
 <circle cx="810" cy="540" r="3.5" fill="#e29a69"><animate attributeName="opacity" values="1;.3;1" dur="3s" repeatCount="indefinite"/></circle>
 <text x="821" y="545" fill="#e4e9f5" font-size="13">BUILDING &amp; LEARNING</text>
</g></svg>'''


def city(user):
    cal = user['contributionsCollection']['contributionCalendar']
    cells = [(w, d['weekday'], d['contributionCount'], d['date']) for w, week in enumerate(cal['weeks']) for d in week['contributionDays']]
    peak = max((c[2] for c in cells), default=0)
    active = sum(c[2]>0 for c in cells)
    blocks = []
    for w, d, count, date in sorted(cells, key=lambda c: (c[0]*1.8+c[1]*8, c[0])):
        x, y = 108+w*16.1-d*9, 108+w*1.8+d*8
        h = 0 if not count else 6+58*math.log1p(count)/math.log1p(max(1,peak))
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
    (OUT/'neural-identity.svg').write_text(hero(user, photo), encoding='utf-8')
    (OUT/'contribution-city.svg').write_text(city(user), encoding='utf-8')
    print('Generated both SVGs successfully.')


if __name__ == '__main__':
    main()
