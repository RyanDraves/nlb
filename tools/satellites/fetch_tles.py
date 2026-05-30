"""Fetch the latest TLEs for the active GEO satellites from Space-Track.

Merges freshly-fetched two-line element sets into the blog's tles.json,
preserving any hand-maintained entries (e.g. the deorbited cubesat, whose
historical TLE Space-Track's current `gp` class no longer serves). Writes the
file deterministically so the monthly update PR produces a clean diff.

Space-Track requires authentication. Set the credentials via environment:

    SPACETRACK_IDENTITY  (account email)
    SPACETRACK_PASSWORD  (account password)
"""

import argparse
import datetime
import http.cookiejar
import json
import os
import sys
from urllib import error
from urllib import parse
from urllib import request

# The 5 active commercial GEO missions. The deorbited cubesat (55123) is
# intentionally excluded: it is frozen by hand in tles.json.
DEFAULT_NORAD_IDS = ['56371', '62454', '62455', '62456', '62457']

LOGIN_URL = 'https://www.space-track.org/ajaxauth/login'
# `gp` is the current general-perturbations element set; `3le` prepends a name
# line ("0 NAME") to each TLE.
QUERY_URL = (
    'https://www.space-track.org/basicspacedata/query/class/gp'
    '/NORAD_CAT_ID/{ids}/format/3le'
)


def fetch_3le(norad_ids: list[str], identity: str, password: str) -> str:
    """Log in to Space-Track and return the 3LE text for the given ids."""
    opener = request.build_opener(
        request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    login = parse.urlencode({'identity': identity, 'password': password}).encode()
    opener.open(LOGIN_URL, data=login, timeout=60).read()

    url = QUERY_URL.format(ids=','.join(norad_ids))
    with opener.open(url, timeout=60) as resp:
        return resp.read().decode('utf-8', 'replace')


def parse_3le(text: str) -> dict[str, dict[str, str]]:
    """Parse 3LE text into {norad_id: {name, tle1, tle2}}."""
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    out: dict[str, dict[str, str]] = {}
    for i in range(0, len(lines) - 2, 3):
        name_line, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
        if not line1.startswith('1 ') or not line2.startswith('2 '):
            continue
        name = (
            name_line[2:].strip() if name_line.startswith('0 ') else name_line.strip()
        )
        norad_id = line1[2:7].strip()
        out[norad_id] = {'name': name, 'tle1': line1, 'tle2': line2}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--out',
        required=True,
        help='Path to tles.json to read and rewrite in place.',
    )
    parser.add_argument(
        '--norad-ids',
        nargs='+',
        default=DEFAULT_NORAD_IDS,
        help='NORAD ids to refresh (defaults to the 5 active GEO missions).',
    )
    args = parser.parse_args()

    identity = os.environ.get('SPACETRACK_IDENTITY')
    password = os.environ.get('SPACETRACK_PASSWORD')
    if not identity or not password:
        print(
            'ERROR: set SPACETRACK_IDENTITY and SPACETRACK_PASSWORD',
            file=sys.stderr,
        )
        return 2

    try:
        with open(args.out, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    satellites: dict = data.get('satellites', {})

    try:
        fetched = parse_3le(fetch_3le(args.norad_ids, identity, password))
    except (error.URLError, TimeoutError) as exc:
        print(f'ERROR: Space-Track request failed: {exc}', file=sys.stderr)
        return 1

    missing = []
    for norad_id in args.norad_ids:
        if norad_id in fetched:
            satellites[norad_id] = fetched[norad_id]
            print(f'updated {norad_id}: {fetched[norad_id]["name"]}')
        else:
            # Keep the previously-known TLE (if any) and carry on.
            print(f'WARN: no element set returned for {norad_id}', file=sys.stderr)
            missing.append(norad_id)

    data['satellites'] = satellites
    data['updated'] = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace('+00:00', 'Z')
    )

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')

    if missing and len(missing) == len(args.norad_ids):
        print('ERROR: no element sets returned for any id', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
