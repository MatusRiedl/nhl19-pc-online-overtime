"""The player's photo on the Roster card and Photo... (app/photo_ctl.py, photos' own-photo store; owner 2026-11-25:
the Roster tab showed no photos, and a player could not give one of his own, also to his own created player)."""
import io
import json
import os
import zipfile

import pytest

from overtime_core import art, clubdata, photos
from overtime_roster.app import controller as C, jobs, patch, photo_ctl, sources


def png(colour=(200, 40, 40), size=(300, 400)):
    from PIL import Image
    out = io.BytesIO()
    Image.new('RGB', size, colour).save(out, 'PNG')
    return out.getvalue()


def test_a_picked_picture_is_fitted_or_refused():
    from PIL import Image
    webp = photos.fit_photo(png())               # no head to find: the whole picture, fitted to the height
    img = Image.open(io.BytesIO(webp))
    assert img.format == 'WEBP' and img.size == (photos.SIZE[0], photos.KEEP)
    for bad, said in ((b'', 'empty'), (b'not a picture', 'not a picture')):
        with pytest.raises(photos.PhotoError, match=said):
            photos.fit_photo(bad)


def test_own_photos_are_kept_by_person_with_their_own_art_ids(tmp_path):
    folder = str(tmp_path / 'yours')
    mcdavid, own = ('connormcdavid', 1997, 1, 13), ('myplayer', 2001, 5, 5)
    assert photos.keep_yours(folder, mcdavid, b'one') == art.YOURS_ARTIDS.start
    assert photos.keep_yours(folder, own, b'two') == art.YOURS_ARTIDS.start + 1
    assert photos.keep_yours(folder, mcdavid, b'three') == art.YOURS_ARTIDS.start      # a new pick keeps his art id
    assert photos.yours_picture(folder, mcdavid) == b'three'
    assert photos.drop_yours(folder, mcdavid) and not photos.drop_yours(folder, mcdavid)
    assert photos.yours_picture(folder, mcdavid) is None and set(photos.yours(folder)) == {own}
    # the drawn photos never take one of these art ids
    assert not set(art.YOURS_ARTIDS) & {art.PEOPLE_ARTIDS.stop - 1, art.PEOPLE_ARTIDS.start}


def test_the_card_finds_a_person_as_the_patch_binds_him():
    key = clubdata._key
    people = [[key('Mitch', 'Marner'), 1997, 5, 5, 40308], [key('Pathrik', 'Westerholm'), 1992, 1, 6, 11617],
              [key('Late', 'Feed'), 2005, 1, 1, 40002]]
    assert photo_ctl.match(people, 'Mitch', 'Marner', 1997, 5, 5) == 40308
    assert photo_ctl.match(people, 'Mitchell', 'Marner', 1997, 5, 5) == 40308     # a first name that fits
    assert photo_ctl.match(people, 'Late', 'Feed', 2006, 1, 1) == 40002           # the feed's year is off
    assert photo_ctl.match(people, 'Ponthus', 'Westerholm', 1992, 1, 6) == 11617  # the people pack's own twin row
    assert photo_ctl.match(people, 'Oscar', 'Westerholm', 1992, 1, 6) is None     # another first name
    assert photo_ctl.match(people, 'No', 'Body', 2000, 1, 1) is None


@pytest.mark.game
def test_photo_on_the_card_then_your_own_then_back(game_dir, tmp_path, monkeypatch):
    home = tmp_path / 'home'
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(home))
    monkeypatch.setattr(jobs, 'run', lambda work, done=None, failed=None, expected=(): done and done(work()))
    monkeypatch.setattr(sources, 'BUILD_PACKS', str(tmp_path / 'exe-packs'))
    monkeypatch.setattr(sources, 'REPO_PACKS', str(tmp_path / 'repo-packs'))
    monkeypatch.delenv(patch.ART_ENV, raising=False)

    class Host:
        picked = None

        def register(self, name, fn):
            pass

        def changed(self, *names):
            pass

        def log(self, msg):
            pass

        def send(self, *a):
            pass

        def pick(self, folder, start='', kinds=()):
            return self.picked

    c = C.Controller(Host(), game_dir=game_dir, save_dir=str(tmp_path / 'saves'))
    c.load_source(sources.GAME_ID)
    s = c.session
    by_name = {s.name(b): pi for pi in s.player_row for b in [s.bio(pi)[1]] if b is not None}
    pi = by_name['Connor McDavid']
    first = c.calls['roster_photo'](pi)
    assert first['from'] in ('game', 'none') and not first['yours']      # no people pack here: NHL 19's own or none
    if first['from'] == 'game':
        assert first['src'].startswith('data:image/webp;base64,')

    picture = tmp_path / 'me.png'
    picture.write_bytes(png())
    c.host.picked = str(picture)
    assert c.calls['roster_photo_pick'](pi) == {'ok': True}
    mine = c.calls['roster_photo'](pi)
    assert mine['from'] == 'yours' and mine['yours'] and mine['src'].startswith('data:image/webp;base64,')
    cache = photo_cache()
    pack = patch.yours_people(cache)
    assert pack and pack in patch.art_pack_paths(cache)[0]
    with zipfile.ZipFile(pack) as z:
        info = json.loads(z.read(art.MANIFEST))
    (row,) = info['people']
    assert row[0] == 'connormcdavid' and row[4] == art.YOURS_ARTIDS.start
    assert art.PORTRAIT.format(art.YOURS_ARTIDS.start) in info['files']
    files, people = patch.served_portraits(game_dir, cache, serving=True)
    assert art.PORTRAIT.format(art.YOURS_ARTIDS.start) in files and row in people

    c.host.picked = ''
    assert c.calls['roster_photo_pick'](pi) == {'cancelled': True}
    c.host.picked = str(tmp_path / 'missing.png')
    assert 'could not be read' in c.calls['roster_photo_pick'](pi)['error']
    assert c.calls['roster_photo_remove'](pi) == {'ok': True}
    assert c.calls['roster_photo'](pi)['from'] == first['from'] and not os.path.isfile(pack)
    assert c.calls['roster_photo_remove'](pi)['ok'] is False
    assert c.calls['roster_photo']('x')['from'] == 'none'


def photo_cache():
    from overtime_roster.app import paths
    return paths.app_dir('cache')
