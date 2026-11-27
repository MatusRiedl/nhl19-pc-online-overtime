"""The player's photo on the Roster card, and Photo...: a picture the player picks for him (v1.00.0, owner 2026-11-25).

The card shows the photo NHL 19 would show after Patch: the player's own pick (photos.keep_yours), else the people pack's
(the people pack, the photos drawn on this PC: found by name and birth date, as art.rebind_portraits binds them), else
NHL 19's own portrait of his art id, else none. Photo... keeps a picked picture by person in the cache and makes the
pack Patch serves (patch.write_yours); a roster saved after that carries it too (install.run's `portraits`).
"""
import base64
import collections
import io
import os
import threading
import zipfile

from overtime_core import art, clubdata, gamefiles, gnf, photos

from . import paths, patch
from .registry import Part

IMAGE_KINDS = ('Pictures (*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif)',)
KEEP = 400      # pictures the card keeps in memory

SAID = {
    'yours': 'Your photo. NHL 19 shows it after Patch, with Patch\'s player photos on.',
    'pack': 'From the player photos pack. NHL 19 shows it with Patch\'s player photos on.',
    'game': 'NHL 19\'s own photo.',
    'none': 'No photo. Photo... gives him one of yours.',
}


def match(people, first, last, y, m, d):
    """The art id of a person among `people` rows: by name and birth date, else name and day, else last name and
    birth date with a first name that fits (art.player_portraits' rules for one player); None."""
    name = clubdata._key(first, last)
    exact, by_day, by_date = {}, collections.defaultdict(set), collections.defaultdict(set)
    for n, py, pm, pd, a in people:
        exact[n, py, pm, pd] = a
        by_day[n, pm, pd].add(a)
        by_date[py, pm, pd].add((n, a))
    if (name, y, m, d) in exact:
        return exact[name, y, m, d]
    if len(by_day[name, m, d]) == 1:
        return next(iter(by_day[name, m, d]))
    lk, fk = clubdata._key(last), clubdata._key(first)
    same = {a for n, a in by_date[y, m, d] if lk and n.endswith(lk) and n != lk and art._first_names_fit(fk, n[:-len(lk)])}
    return same.pop() if len(same) == 1 else None


def data_url(webp):
    return 'data:image/webp;base64,' + base64.b64encode(webp).decode('ascii')


def gnf_webp(data):
    """A game portrait (GNF) as WebP bytes, its picture part (the top 256 rows of 512 x 340)."""
    img = gnf.to_image(data)
    img = img.crop((0, 0, img.width, min(img.height, photos.KEEP)))
    out = io.BytesIO()
    img.save(out, 'WEBP', quality=85, method=4)
    return out.getvalue()


class PhotoCtl(Part):
    CALLS = {'roster_photo': 'photo', 'roster_photo_pick': 'pick', 'roster_photo_path': 'from_path',
             'roster_photo_remove': 'remove'}

    def __init__(self, ctl):
        super().__init__(ctl)
        self._pictures = collections.OrderedDict()      # (source, path, mtime, id) -> data URL
        self._rows = {}                                   # pack path -> (mtime, people rows)
        self._shift = (None, 0)                           # (id of the roster's database, its year shift)
        self._mem = threading.Lock()

    def roster_changed(self):
        self._shift = (None, 0)

    # --- reading -----------------------------------------------------------------------------------------------------
    @staticmethod
    def _cache():
        return paths.app_dir('cache')

    def _people(self, path):
        """The `people` rows of one pack, read once per change of the file."""
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return []
        hit = self._rows.get(path)
        if hit and hit[0] == mtime:
            return hit[1]
        try:
            rows = art.listing(path).info.get('people') or []
        except art.ArtError:
            rows = []
        self._rows[path] = (mtime, rows)
        return rows

    def _year_shift(self, s, packs):
        """How far the roster's birth years sit behind the real ones (art.year_shift_of against the people pack)."""
        if self._shift[0] == id(s.db):
            return self._shift[1]
        rows = self._people(packs[0]) if packs else []
        shift = art.year_shift_of(s.db, rows) if rows else 0
        self._shift = (id(s.db), shift)
        return shift

    def _person(self, s, pi, packs):
        """(first, last, (name key, y, m, d), bio) of a card's player, or None."""
        try:
            _, b = s.bio(int(pi))
        except (TypeError, ValueError, IndexError, KeyError):
            return None
        if b is None:
            return None
        t, row = s.db[art.BIOS], s.bio(int(pi))[0]
        first, last = t.get(row, 'firstname'), t.get(row, 'lastname')
        y = art.YEAR_BASE + t.get(row, 'year') + self._year_shift(s, packs)
        m, d = t.get(row, 'month') + 1, t.get(row, 'day') + 1
        return first, last, (clubdata._key(first, last), y, m, d), {'artid': t.get(row, 'artid'),
                                                                       'hasportrait': t.get(row, 'hasportrait')}

    def _remember(self, key, make):
        with self._mem:
            if key in self._pictures:
                self._pictures.move_to_end(key)
                return self._pictures[key]
        try:
            url = make()
        except Exception:  # noqa: BLE001 - a picture that does not read: shown as none
            url = ''
        with self._mem:
            self._pictures[key] = url
            while len(self._pictures) > KEEP:
                self._pictures.popitem(last=False)
        return url

    def photo(self, pi):
        """{src (data URL or ''), from: yours / pack / game / none, note, yours: bool} of a card's player."""
        c = self.ctl
        cache = self._cache()
        packs = patch.people_packs(cache)
        with c.lock:
            s = c.session
            who = self._person(s, pi, packs) if s is not None else None
            game_dir = c.game_dir
        if who is None:
            return {'src': '', 'from': 'none', 'note': '', 'yours': False}
        first, last, person, bio = who
        folder = patch.yours_folder(cache)
        mine = photos.yours(folder)
        hit = match([[*p, a] for p, (a, _k) in mine.items()], first, last, *person[1:])
        if hit is not None:
            mine_person = next(p for p, (a, _k) in mine.items() if a == hit)
            webp = photos.yours_picture(folder, mine_person)
            if webp:
                return {'src': data_url(webp), 'from': 'yours', 'note': SAID['yours'], 'yours': True}
        for path in reversed([p for p in packs if os.path.basename(p) != patch.YOURS_PEOPLE_PACK]):
            artid = match(self._people(path), first, last, *person[1:])
            if artid is None:
                continue

            def make(path=path, artid=artid):
                with zipfile.ZipFile(path) as z:
                    return data_url(gnf_webp(z.read(art.PORTRAIT.format(artid))))
            url = self._remember(('pack', path, os.path.getmtime(path), artid), make)
            if url:
                return {'src': url, 'from': 'pack', 'note': SAID['pack'], 'yours': False}
        if bio['hasportrait'] and bio['artid'] < 20000 and game_dir:
            def make_game(artid=bio['artid']):
                return data_url(gnf_webp(gamefiles.read_latest(game_dir, art.PORTRAIT.format(artid))[0]))
            url = self._remember(('game', game_dir, 0, bio['artid']), make_game)
            if url:
                return {'src': url, 'from': 'game', 'note': SAID['game'], 'yours': False}
        return {'src': '', 'from': 'none', 'note': SAID['none'], 'yours': False}

    # --- Photo... -----------------------------------------------------------------------------------------------------
    def pick(self, pi):
        """Photo...: Windows' picker for a picture, then from_path. {type: true} in browser mode."""
        pick = getattr(self.ctl.host, 'pick', None)
        path = pick(False, '', IMAGE_KINDS) if pick else None
        if path is None:
            return {'type': True}
        if not path:
            return {'cancelled': True}
        return self.from_path(pi, path)

    def _fail(self, text):
        self.ctl.say(text, 'bad')
        return {'ok': False, 'error': text}

    def from_path(self, pi, path):
        """A picked picture as the player's photo: drawn, kept by person, made into the pack Patch serves."""
        c = self.ctl
        cache = self._cache()
        packs = patch.people_packs(cache)
        with c.lock:
            s = c.session
            who = self._person(s, pi, packs) if s is not None else None
            game_dir = c.game_dir
        if who is None:
            return self._fail('Pick a player first.')
        if not game_dir:
            return self._fail('Pick NHL 19 in Setup first: the photo is made like the game\'s own.')
        path = (path or '').strip().strip('"')
        try:
            with open(path, 'rb') as f:
                data = f.read(photos.PICK_MAX + 1)
        except OSError as err:
            return self._fail(f'The picture could not be read: {err.strerror or err}.')
        try:
            picture = photos.fit_photo(data)
            photos.keep_yours(patch.yours_folder(cache), who[2], picture)
            patch.write_yours(cache, game_dir)
        except photos.PhotoError as err:
            return self._fail(str(err))
        except (OSError, gnf.GnfError) as err:
            return self._fail(f'The photo could not be made: {err}.')
        c.say(f'{who[0]} {who[1]}: your photo is kept. Press Patch, then NHL 19 shows it (player photos on).', 'good')
        c.changed('roster')
        return {'ok': True}

    def remove(self, pi):
        """Take the player's own photo away (the pack's or none shows again after Patch)."""
        c = self.ctl
        cache = self._cache()
        packs = patch.people_packs(cache)
        with c.lock:
            s = c.session
            who = self._person(s, pi, packs) if s is not None else None
            game_dir = c.game_dir
        if who is None:
            return self._fail('Pick a player first.')
        folder = patch.yours_folder(cache)
        hit = match([[*p, a] for p, (a, _k) in photos.yours(folder).items()], who[0], who[1], *who[2][1:])
        person = next((p for p, (a, _k) in photos.yours(folder).items() if a == hit), None)
        if person is None or not photos.drop_yours(folder, person):
            return self._fail('He has no photo of yours.')
        try:
            if game_dir:
                patch.write_yours(cache, game_dir)
        except (OSError, gnf.GnfError) as err:
            return self._fail(f'The photos pack could not be made again: {err}.')
        c.say(f'{who[0]} {who[1]}: your photo is gone. Press Patch to take it out of NHL 19 too.', 'good')
        c.changed('roster')
        return {'ok': True}
