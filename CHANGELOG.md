# Changelog

What changed in each version, for players.

## 1.00.0 (not released yet)

The first full release.

### New

- **World of Chel player stats, skaters and goalies apart.** Multiplayer > Online > My games gets a World of Chel
  part with two sections, each shown once you have a game in that role:
  - **As skater**: games, record, goals, assists, points, +/-, shots, hits, power-play, short-handed and
    game-winning goals, then shooting %, takeaways, giveaways and blocked shots.
  - **As goalie**: games, record, shots against, saves, goals against, save %, goals-against average and shutouts,
    then breakaways, penalty shots and shootout (saves out of shots), desperation saves and poke checks.

  A game counts for the role you played in it, never for both. The numbers come from the game's own report at the
  end of each game.
- **Your line in each game.** My games tags each World of Chel game with your position (G for goalie) and shows
  your line, such as "SV 18/20 .900, GA 2" or "G 1 A 2 +1".
- **Every player's line in each match.** Under Matches, a World of Chel match lists each player's line under their
  side, goalies first. The player window shows the same two sections for any player.
- **The web leaderboard's player card** gets a Chel skater line and a Chel goalie line.
- **Ones (1v1v1) is back in World of Chel.** Pick Ones in the game's PLAY menu (Ones, Threes, Drop-in 3s,
  Drop-in 6s), or make a 1v1v1 lobby under Multiplayer > Lobby > CHEL. 2 to 4 players, every skater on the ice,
  places by goals. Two players can now start a game: the patch lets the game begin without a third.
- **Frame generation (Windows, NVIDIA RTX 40 and 50).** Setup > Boost gets a "Frame generation" row for the
  Overtime Native v3 emulator: NVIDIA DLSS frame generation draws extra frames between the game's own. RTX 40 cards:
  Off or 2x. RTX 50 cards: up to 4x. The first time you pick a level, the app downloads the NVIDIA files (about
  5 MB). On our RTX 5080, 2x showed about 217 frames a second for about 7% fewer game frames, with no added
  hitches. 2x is the setting we recommend.
- **Overtime Native v3 updated.** The emulator build adds frame generation. With frame generation off it runs as
  before and plays online with players still on the earlier v3.
- **New player: put yourself on any team.** Roster > New player... makes a player for any club of the NHL, AHL,
  ECHL, the European leagues, the Champions League and the CHL junior leagues, or the free agents: name, position, shoots, birth date and club. He signs with
  a number, a contract and a place in the lines, and his card opens for the rest (number, country, size, ratings,
  face, equipment). One Undo takes him back. Save keeps him in My edits: every roster update leaves him on his club
  (no NHL.com namesake takes him over), puts him back if a league update moved him, and makes him again in a new
  roster. A host roster lobby takes him online with the host's roster.
- **League maker: your own leagues, such as a KHL.** Roster > New league... puts a league of your clubs into one of
  NHL 19's club leagues (SHL, Liiga, DEL, Extraliga, National League, ICE Hockey League, HockeyAllsvenskan, OHL,
  QMJHL, WHL or ECHL). Name it, then type or paste its clubs, one a line ("name | city | nickname | ABBR"), or
  import a league file someone shared; Export... writes one. The clubs take the league's places one by one and keep
  their players and calendar: move players in with Move / trade and New player. One Undo takes it back. Save keeps
  the league in My edits, so every roster update keeps it; press Patch in Setup and NHL 19 shows its name in Play
  Now and Season's league list, and the clubs' names everywhere. Play Now and Season play it (make it on Overtime
  default or your updated roster: see Known limits).
- **Contract... on the player card works.** It opens his contract in Front office (cap hit, years left, one-way or
  two-way), with his club picked. A free agent still signs in Front office's Free agents group.
- **The tab line moved.** It now sits before Roster: Setup and Patch get NHL 19 ready, Roster onwards edit it.
- **Player photos on the Roster card, and your own.** The player card shows the photo NHL 19 shows after Patch:
  the player photos pack's, else the game's own. Click it to give any player a picture of yours (PNG, JPG or WebP),
  your own created player too; the head is found and fitted like the pack's photos. Press Patch and NHL 19 shows
  it (player photos on). The x on the photo takes yours away again. A roster you save carries the photos too, so a
  new player keeps his face in that roster.
- **Jerseys & gear, made plain.** Each gear colour is one row with a name (Black, Orange, Navy...), however many
  shades of it the jerseys wear. The team colours are yours to change now: pick a new primary, secondary or third
  colour and the gear in that colour follows it; black, white and grey gear stays. "Worn with each jersey" shows the
  helmet and gloves of Home, Away and Alternate. Apply writes it all as one change.
- **Edit rosters with an AI.** AI apps that speak MCP (Claude Desktop, Claude Code and others) can now work on
  your rosters through Overtime: find players, read and change their cards (ratings, number, position, country,
  size, contract), make new players, move players between clubs, put in a league, check the roster, take an edit
  back, then save it as a new roster. Setup > This program > Connect an AI... shows what to paste into the AI app
  for this copy of Overtime, with Copy buttons. The AI goes through the same checks as the Roster card, nothing
  reaches NHL 19 until it saves, and it never overwrites or deletes a roster. Advanced: `OvertimeNHL19.exe --mcp`
  starts the server on its own.
- **Direct P2P in lobbies (experimental).** For players far from our server: the host of a Versus, Shootout or
  Threes lobby can set Match rules > Connection to "Direct P2P (test)". The two games then connect straight to each
  other instead of through the Overtime server, which can lower the ping. Each game gets the other player's internet
  address, so the other player's Ready is their OK, and the lobby chat says so. The default stays "Server". If the
  two games cannot reach each other, the lobby goes back to the server by itself and the next game goes through it.
  World of Chel always plays through the server.

### Fixed

- **Gear colours change on every jersey.** Changing a gear colour changed only the alternate's helmets and gloves:
  each jersey's gear wears its own near-copy of the colour, and the list showed every copy as a row of its own. One
  row now reaches every shade. The team colours you change go into the roster with the rest (where NHL 19 shows
  them is still being checked).

- **Player photos on the right players.** Macklin Celebrini, Gavin McKenna, Quinn Hughes and about 250 other new
  players wore someone else's face: the photo pack was numbered for an older default roster. Patch now gives each
  player his photo by name and birth date (the people pack, NHL Legacy's pictures), whatever number the roster gave
  him. Twins no longer take their brother's photo when only one of them has one. Press Patch to get it.
- **32 clubs in Classic Franchise and Season.** With Seattle in the league, a new Classic Franchise or NHL Season
  now has all 32 clubs, and Utah and Seattle each play their own schedule (before, Seattle took Utah's place). It
  comes with the patch: the next Play brings it in.
- **Drop-in Threes room.** It offers G, LD, LW and C only, as Drop-in 3s does: a Threes side has no RW or RD, and
  those picks were seen in games where two players shared one skater (a server change, live since 2026-11-24).
- **The game's menus follow the app.** When the app opens (with NHL 19 closed) on a game an older Overtime patched,
  it brings the game's menus up to date by itself, so Ones shows in World of Chel's PLAY menu without pressing
  Patch. Before, the app said "Patched" while the game kept the older menus.
- **Patch page: an open section shows whole.** Roster update and the other sections open to their full size and the
  page scrolls as one, instead of a small box inside it that scrolled on its own.
- **Patch page: no more "32 teams in every mode: Coming".** 32 clubs in Classic Franchise and Season come with
  this version.
- **Frame generation says when its files are missing.** While the Overtime server does not offer NVIDIA's files,
  the row says so beside the greyed 2x to 4x.
- **DLSS says when it cannot run.** DLSS scales a smaller picture up to your screen, so at a Resolution above your
  screen's height (2160p on a 1440p screen, say) it has nothing to do and the game uses FSR 1. The app now says so
  when you pick DLSS or that Resolution, and the Picture block keeps a note until you pick a DLSS quality.
- **DLSS 5 and frame generation warn that they can crash.** On some PCs they can crash the game or reset the
  graphics driver. Both stay off unless you turn them on. Turning one on now says so, the Picture block keeps a
  note while one is on, and Multiplayer's checks show an amber "Picture" line with a Setup button: turn them off
  before online games, since a crash ends the match.

### How to get it

- The app updates itself. Stats start with the first World of Chel game after the server update: earlier games kept
  only their score, so they show no line.

### Known limits

- Penalty minutes are not shown yet.
- A player whose own end-of-game report never arrives (the game closed, a crash) gets no line for that game.
- **Ones:** a 1v1v1 lobby needs Overtime Roster 1.00.0 on every player's PC; older apps are told to update.
  Update and patch before you search Ones from the game's own menus too: an older patch can fail a two-player game.
  Our tests played full two-player games; three-player games and games started from a 1v1v1 lobby are new.
- **Ones idle rule:** the game itself drops a player who leaves the stick alone for about 16 seconds.
- **New player:** he starts with a stand-in face and a fringe player's ratings until you set them. Seattle and
  Coachella Valley (custom teams), the All-Star and national teams are not on the club list (it is the Move / trade
  window's). A
  server roster lobby plays the server's roster, which does not have him; a host roster lobby carries him.
- **League maker:** a league takes over one of the game's club leagues (NHL 19 has no room for more): its clubs
  keep that league's crests, logo, rink boards and schedule size, and the NHL and AHL cannot be taken. The name shows after Patch, and a server roster lobby plays the server's roster, without your league. Make it on
  Overtime default or your updated roster, not the Game roster (the window says so when the Game roster is open).
- **Seasons and the Game roster:** with a custom roster saved from the Game roster (2018-19) active in NHL 19, the
  game crashes when a new Season's team screen opens (a new Classic Franchise may too). The same goes for a custom
  roster you made in the game from its own roster before Overtime. Have a roster made from Overtime default or
  your updated roster active (Customize > Rosters) before you start one. This is older than 1.00.0.
- **Direct P2P** is new and not yet tested between two homes. Some home routers need UDP port 3659 forwarded to
  the PC (and NHL 19's emulator allowed in the firewall), or the games cannot reach each other; then the next game
  goes through the server. Both players need Overtime Roster 1.00.0 to see the setting.
- **Frame generation** is new and still in testing. It works only while the game window is in front: click another
  window and it pauses until you click the game again. 3x and 4x cost more game frames (4x about a fifth). With
  DLSS 5 on as well it is heavy: about 80 game frames a second and some hitches on our RTX 5080, so use DLSS 5 or
  frame generation, not both, unless your card has room. Online: a 30-minute match against the earlier v3 had no
  desync, but frame generation was paused in it, so online play with it drawing frames is not tested yet.

## 0.99.2 (2026-11-23)

### New

- **4K, 5K and 8K** under Resolution on Setup's Boost performance card (Kravickas's patches): 2160p (3840x2160),
  2880p (5120x2880) and 4320p (7680x4320). They set Additional DMem to 3500 MB (2160p), 6000 MB (2880p) and
  12000 MB (4320p); 720p and 1080p put your own value back. Each needs a stronger graphics card than the last.
  **8K is experimental**: it needs a lot of memory and may not run on every PC. Your resolution is your own: the
  other player in an online match keeps theirs.
- **Compute off** beside Resolution (Kravickas's patch): turns the game's compute-shader mesh features off (cloth
  physics, compute blend shapes) for a slight speed gain. Off by default. **Offline only**: app lobby matches play
  with the game's own compute features whatever you pick. Turn it off before you search online from the game's
  own menus.

### Changed

- **PS4 Pro mode is your own in online matches.** App lobby matches no longer turn PS4 Pro mode off: each player
  plays with their own setting (Setup > Emulator settings > PS4 Pro mode, on by default), so matches look like your
  offline games. A PS4 Pro / base PS4 pair plays together, as the real consoles did. The server leaves the
  setting out of every lobby's match setup, so players still on 0.99.1 keep their own too.
- **Each player's build in the lobby.** Every player row names the shadPS4 build that player's game plays on
  (Overtime Native v3, Kravickas, ...), once they have pressed Ready. Each player picks their own on Setup's
  Boost performance card.
- **Lighter match logs.** The log a lobby match writes for a report no longer holds the emulator's network chatter
  (about 200 lines a second, nine in ten of its lines).
- **Roster update: 2027-28 waits for its calendar.** The Season choice offers 2025-26 and 2026-27. NHL.com lists no
  2027-28 games yet (the NHL puts out a season's calendar in the summer before it), so that pick could only stop.
  If you had 2027-28 picked, it starts as 2026-27.

### Fixed

- **The roster update says why it stopped.** When NHL.com has no calendar for the season, or NHL.com itself failed
  (no answer in time, a certificate this PC could not check, ...), the card says that instead of "NHL.com did not
  answer", and offers the offline copy only when it can help.
- **No quiet fallback in a lobby match.** When the shadPS4 build chosen on the Boost card can't be had (not on its
  server, a download that failed), the Game card now says which shadPS4 the match plays on instead of starting
  it quietly (DLSS and the Picture options come only with the Overtime Native v3 build).

### Thanks

- Kravickas for PR #4, both commits: the faster downloads and his build's updates in 0.99.0, and now the 4K, 5K and
  8K resolutions and Compute off.

### How to get it

- The app updates itself. A patched game takes a new resolution or Compute off at its next start; no Patch needed.

### Known limits

- 8K was not tried on every graphics card; if NHL 19 does not start at 4320p, pick a lower resolution.
- Compute off can't be checked in open matchmaking from the game's own menus: a game played with it on can fall out
  of sync there.

## 0.99.1 (2026-11-23)

### New

- **World of Chel: Player stats for the lobby**: the host of a CHEL lobby picks the stat level of created players
  on the Multiplayer tab's World of Chel card: Stock (EA's player classes, as before 0.99.0), 75, 80, 85, 90, 95
  or 99 (the default). Every created player in the lobby's game, on both teams, plays at that level. Players the
  game brings in from outside your lobby keep 99. Changing it clears Ready for everyone. Only the host needs
  0.99.1; friends on 0.99.0 play the host's level too.

## 0.99.0 (2026-11-23)

### New

- **Overtime Native v3** is the new default build on Windows: Overtime Native v2, faster, plus optional picture
  options. The GPU no longer stops to wait on every read back to the game, and the build is tuned to how NHL 19
  runs. On one PC (RTX 5080, Ryzen 7 9800X3D, 1440p, no frame cap) a match ran at 160-200 fps against about
  120-130, and the slowest 1 % of frames at 54-81 fps against 36-44, with far fewer hitches (an earlier test build
  of the same change put about 155 fps on a 165 Hz screen, against 131). Capped at 60, it now holds 60 through a
  match. Players on v2 move to v3 once. v2, v1 and Kravickas's build stay selectable.
- **Play online on the build you choose**: Ready and Play use the build picked on the Boost card, and every build in
  its list plays with every other one. Lobbies no longer compare shadPS4 builds; the patch and the roster still
  have to match. **Linux and Mac players now meet Windows players.**
- **Picture options** on Setup's Boost performance card (Overtime Native v3), all off until you turn them on:
  - Upscaler: Off, FSR 1 or DLSS (NVIDIA RTX cards).
  - DLSS quality (with DLSS on): Performance, Quality or DLAA and so on, named for your screen. It sets the game's
    render resolution (720p, 1080p or 1440p) that DLSS scales up to your screen.
  - DLSS 5: NVIDIA's neural rendering model over the picture (RTX 20 to 50).
  - The first time you turn DLSS or DLSS 5 on, the app downloads NVIDIA's file from the Overtime server (Download
    beside it gets it again). If the server has none, add your own `nvngx_dlss.dll` or `nvngx_dlssnr.dll` with
    "Add DLSS file" or "Add DLSS 5 file".
  - They cost frames: on an RTX 5080 at 1440p a match ran at about 88 fps with DLSS and DLSS 5 both on, against
    160-200 with them off.
- **Shader cache fixes in Overtime Native v3**: a shader cache left by an older build, another graphics card or a
  driver change is rebuilt instead of being ignored (with v2 such a cache meant no shader cache at all, on every
  start). v3 keeps its cache in folders of its own (one for when DLSS or DLSS 5 is on), so v2's and Kravickas's
  build's caches stay as they are and turning a picture option on or off keeps the cache. Also fixes against
  stutter, from upstream shadPS4.
- **Faster downloads and NHL.com reads** (public PR #4 by Kravickas): packs download in parallel and NHL.com rosters
  load in parallel, with the checks and retries kept.
- **Kravickas build from his GitHub releases** (PR #4): the Boost card's "Get newest" takes his newest build and checks
  GitHub's sha256. Play keeps the build that is already there.
- **The game PKG installs its 1.60 update by itself**: pick the game PKG in Setup's "Find game"; when the update
  1.60 PKG is in the same folder, it installs right after the game. No second pick.
- **Move / trade players** (Roster tab, player card): move a player to another club or to free agency, or swap
  players between clubs, with one Undo. **Bring in game moves** (Players card): take the trades you made in NHL 19
  from one of your roster saves into the app's roster. Save, then play that roster in NHL 19; no Patch needed.
- **World of Chel: created players at 99** in every attribute. Our server gives no XP, so created players now start
  maxed. Comes in on your next Ready or Play.

### Fixed

- **Linux: the window opens on newer systems.** On Fedora and other systems newer than Ubuntu 22.04 the app showed in
  the task bar with no window. It carried its own old copies of system libraries (libstdc++, fontconfig and others),
  and your graphics driver could not load beside them. It now uses your system's copies.

### Thanks

- Kravickas for PR #4 and for his DLSS branch: Overtime Native v3's motion inputs and the DLSS 5 pass are his work.
- The upstream shadPS4 authors whose fixes are in Overtime Native v3: Sergey K. (#4929), SpacyRainbow (#5577),
  k3n0b1 (#5692), River Zhou (#5583) and nikmparis217-ux (#5155).
- thegh0sts (NHL 19 PS4 port for Windows), whose port made the same change as #5577, and HajDEO (nhl24pc), whose
  fork's fixes we checked v3 against.

### How to get it

- The app updates itself and downloads Overtime Native v3 on the next Play. No Patch needed.

### Known limits

- Overtime Native v3 is Windows only for now; Linux and macOS stay on v2.
- The first match on Overtime Native v3 builds its shader cache, so it can stutter a little once (and once more the
  first time DLSS or DLSS 5 is on).
- In a lobby, 0.99.0 players meet only 0.99.0 players. Open matchmaking can still pair a 0.98.0 player with a
  0.99.0 player, so update before you play.
- On an Intel CPU, a shadPS4 build that is not in the Boost card's list and lacks the cross-CPU fix meets only
  players with the same setup.
- A Mac has not played an online match against a Windows PC yet (Apple chips run shadPS4 through Rosetta 2).
- DLSS and DLSS 5 were tested on an RTX 5080 only. DLSS 5 can draw faint coloured streaks on the ice, and with no
  frame cap its frame pacing is a little less even than before.
- Frame generation is not in this version.
- World of Chel: update to play CHEL. A player on 0.98.0 and a player on 0.99.0 in one CHEL game have different
  ratings for created players, and the game can fall out of sync.

## 0.98.0 (2026-11-20)

### New

- **Match settings for Drop-in lobbies**: the host of a Drop-in 6s or 3s lobby picks period length, skill level,
  game style, penalties, fighting, injuries, icing, offsides and tie break on the World of Chel card. Skill level and
  game style start at All-Star and Competitive. Only the period length is confirmed in a World of Chel match so far;
  the card marks the others with *.
- **Support strip**: Buy me a coffee and Discord sit under the tab row on every tab.

### Fixed

- **The host's own roster**: edits the host makes after pressing Ready now go with the next Ready (before, they never
  reached the online game). The lobby card shows which roster Ready sends.
- **Mac**: Finder's hidden files (.DS_Store and the like) no longer make the app refuse a game or patch folder.

### How to get it

- The app updates itself. No new packs, no Patch needed.

### Known limits

- Single gameplay sliders cannot be set online: the game style picks the whole slider set.

## 0.97.0 (2026-11-19)

### New

- **Sharper NHL 27 jerseys**: jerseys are now made from NHL 27's full-size pictures, so crests, stripes and numbers
  look clearly sharper than in 0.96. The 32 NHL main kits also keep NHL 27's size for numbers and socks. Thirds,
  international and club jerseys get the sharper jersey too.
- **The Seattle Kraken's own centre ice**: Seattle's home rink shows the Kraken logo at centre ice instead of a blank
  ring.
- **Utah's Mammoth crest** in the match preview before the game and in the scorebug, instead of the "UTAH EST. 2024"
  wordmark.

### Fixed

- **Be a Pro with 32 teams in every start**: a Start in the CHL or Memorial Cup career no longer crashes at the first
  NHL sim. Seattle is in the league with Coachella Valley as its farm team. Press Patch once; a career saved with the
  crash needs a new career.
- **Cross-CPU fix for more copies of the game**: an eboot.bin of v1.60 backported to firmware 5.05 now gets the
  Cross-CPU fix too, so lobbies with players on the plain v1.60 eboot are no longer refused. It comes in at the next
  Ready or Play, no Patch needed.

### How to get it

- The app updates itself. Then Setup marks five packs "newer": the pack card fetches the jerseys and the art, and the
  three alternates rows (NHL, international, clubs) each need their own Download. Then press Patch.

### Known limits

- Classic Franchise and NHL Season still build 31 clubs; 32 teams there come later.
- The code now has groundwork for Linux, Steam Deck and macOS, but there is no Linux or Mac download yet.

## 0.96.0 (2026-11-17)

### New

- **World of Chel lobbies in the app**: host a Drop-in 6s, Drop-in 3s or Drop-in Threes lobby, everyone picks Home or
  Away, and the game starts as soon as everyone is ready. The host can also run a countdown (1, 2, 3 or 5 minutes):
  whoever is not ready at 0:00 waits on the bench for the next match. A side nobody picked is played by the CPU.
- **NHL 19 walks itself to the dressing room**: a lobby launch takes the game from the title screen to your mode's
  dressing room. Pick a position, press READY, then START MATCHMAKING.
- **See where everyone is**: each player in a running lobby shows where their NHL 19 is ("dressing room",
  "searching Drop-in 3s"), red for a wrong mode or a closed game.
- **A PC without a picture plays too**: with NULL GPU, a lobby launch takes a free position and readies up by itself.
- **Overtime Native v2**: a faster emulator build, now the default. Setup's Boost card has a dropdown: Overtime Native
  v2, Overtime Native v1 or Kravickas. Every lobby plays on v2: Ready switches you to it.
- **One Patch tab**: Update and Game patch are one tab now. One press of Patch updates your open roster with today's
  NHL rosters, saves it, then patches the game. Turn the roster update off to patch only.
- **Skip the first-run setup** (Patch tab, off by default, new): for a save folder with no profile yet, Patch writes a
  starter profile so NHL 19 skips its first-run questions.
- **The game window is called "NHL 19"**.

### Changed

- **New rank icons** and a leaner Multiplayer tab: every lobby is public (no join code), shorter how-to steps.
- A lobby closes itself when your NHL 19 closes after its game.
- **World of Chel**: the EASHL menu shows Threes, Drop-in 3s and Drop-in 6s (Ones and Online Seasons are hidden).
  The server now hosts World of Chel games itself, and lobby mates on the same position and side both get in.
- **Setup** asks only for the game; the emulator is "Renderer" under Folders. Pro-Am is not offered in lobbies.

## 0.95.1 (2026-11-13)

### Changed

- **The Puck Peak apps, top left**: the app you are in now lights up in its own colour with "You are here"; Blueline
  and Faceoff stay quiet until you point at them.
- **Clearer colours**: switches and checkboxes are green when on. Red is kept for tabs, what you picked and the main
  button on a card. Delete in the roster list stays grey until you point at it.
- **Setup**: Where is NHL 19? shows the game and the emulator on their own lines, with check marks for shadPS4,
  NHL 19, ShadNet and Network. Kravickas's Get newest and Source code are links beside the build choice. "Apply
  everywhere" is now "Also replays and cutscenes". Every roster has a tag (In game, Overtime Roster, Online). Discord
  and Buy me a coffee moved under the rosters.
- **The bar at the bottom** shows progress only while something runs; otherwise a green tick.

## 0.95.0 (2026-11-13)

### Added

- **The Puck Peak apps, top left**: Blueline (NHL Legacy on PC) and Faceoff (NHL 27 on PC) sit beside Overtime,
  which is greyed because you are in it. Hover a button to see what each app is; a click opens its page.

## 0.94.0 (2026-11-13)

### Changed

- **A new look at the top of the app**: the OVERTIME wordmark, brought to you by Puck Peak (the logo opens the site).
- **This page and the quick start** now describe Overtime as what it is: one standalone PC app that installs NHL 19,
  runs it on its own emulator build and takes you online. No separate shadPS4 setup, no port forwarding.

## 0.93.0 (2026-11-13)

### Fixed

- **Club teams show their new names in the game.** Where the 2026 roster puts another club on a slot, the game's menus
  now name it: IF Björklöven in the SHL, HC Pustertal Wölfe, Olimpija Ljubljana and Hockey Club Milano in the
  ICEHL (EBEL), and the other leagues' new clubs. Clubs that only changed their spelling show the new one too
  (Frölunda HC, Djurgårdens IF, Hydro Fehérvár AV19 and more). Press Patch with the roster switch on.
- **The default roster has every league's 2026 clubs.** Patch without Update used to give the club leagues their
  2018 teams and players; the roster inside the app now has the 2026 clubs of all leagues.

### Changed

- **World of Chel drop-in waits 5 minutes for players** before the puck drops (it was 60 seconds), and players who
  search in that time join the game. It still starts as soon as everyone is READY. (Server side, live already.)

## 0.92.0 (2026-11-13)

### Added

- **Overtime Native**, Overtime's own build of shadPS4 for NHL 19, first on Setup's Boost card and the default. It is
  the build a Multiplayer lobby starts. Play NHL 19 downloads it and keeps it current by itself. Source code (GPL-2.0):
  github.com/MatusRiedl/shadPS4, branch `overtime-nightly`.
- **Kravickas's fix for the "Out of order flip IRQ" crash** is in both builds. Overtime Native also keeps the game
  running if one still arrives.
- **NHL 19 starts at above-normal priority** with Windows power throttling off, on both builds, for steadier frames.

### Changed

- **Kravickas's build is second on the card**, now his newer test build. The Update button and the source button are
  for this build.
- **Frame rate defaults to Unlocked.** A Frame rate of 60 or 120 FPS moves to Unlocked once with this update; pick
  yours again on the Boost card and it stays.
- **Apply everywhere is on by default**, and switched on once with this update.
- **Log "Write at once" is off by default** (Game settings, Log), and switched off once with this update.
- **Your build moves to Overtime Native once** with this update. Pick Kravickas on the Boost card to go back.

## 0.91.1 (2026-11-13)

### Added

- **Apply everywhere switch**, right of Frame rate on Setup's Boost card. Off (the default), Kravickas's 60 FPS
  replays patch stays switched off in your patch file, and replays, celebrations, cutscenes and menus keep the game's
  own pace. On, they follow your frame rate, as in 0.91.0. On is experimental: NHL 19 might close by itself during a
  game (shadPS4's "Out of order flip IRQ" in `shad_log.txt`), and Setup says so next to the switch. No Patch needed:
  NHL 19 uses it from its next start.

### Changed

- **Frame rate defaults to 60 FPS**, the console's. A Frame rate of 120 FPS or Unlocked moves to 60 FPS once with
  this update; pick it again on the Boost card if you want it back.
- **Each player picks their own.** The 60 FPS replays patch no longer counts in the online patch check, and in a lobby
  match each game keeps its own switch instead of the host's. A lobby hosted on 0.91.0 refuses Ready from a player on
  0.91.1 ("both update Overtime Roster"): update both.

## 0.91.0 (2026-11-13)

### Added

- **Frame rate: 60 fps, 120 fps or Unlocked.** Pick it on Setup's Boost card under Resolution, or in Game settings,
  Graphics. It sets shadPS4's vblank, and cutscenes and menus follow it. New installs start at 120 fps.
- **NHL 19's own icon** on the emulator window, the taskbar and Alt+Tab, taken from your game when it starts.
- **World of Chel customization items are unlocked.** Customize Pro showed a padlock on every item but the default.

### Changed

- **Unlocked (9999) moves to 120 fps, once.** Unlocked crashed games for some players. The app switches it to 120 fps
  one time; if you pick Unlocked again afterwards, it stays.
- **Match rows** show only the period length and game style (for example "5 min · Full sim"). Matches found without a
  lobby show the game's own rules, and Versus matches are named.
- **World of Chel's PLAY menu has no Pro-Am tile**; the other three are centred.

Patch progress and speed, by Kravickas
([pull request 2](https://github.com/MatusRiedl/nhl19-pc-online-overtime/pull/2)):

- **Patch's progress bar follows the time.** It used to jump between fixed points and stand still for minutes at 62 %
  and 65 % while the jerseys were made and the art was written. Patch now measures its work first and moves the bar
  by the time each part takes on your PC, so 1 % is about 1 % of the time. It learns your PC's speed for the next
  Patch (`patch_speed.json` in the cache).
- **"[Patched 10.3 GB]" beside the %:** how much Patch has written so far.
- **A faster first Patch.** Jerseys are made about 20 % faster (the same textures, byte for byte), club logos use
  every core, and packs that were already checked (downloaded and matching their published checksum, or just made on
  your PC) are not unpacked again to check them. Each texture is still checked as it is written into the game files.
- **Patch again in seconds when the art didn't change.** Patch used to write and read back every art file on every
  press (over 15 GB with every pack on). Now a file that is the same as last time, and still as it was written, is
  kept. The first Patch after updating writes everything once, and a Patch cut off before its final check writes
  everything again.
- **3D jerseys are checked against your game once**, not on every Patch, until the game or the pack changes.

### Fixed

- **The Play button comes back** when NHL 19 closes after its first 3 minutes (it stayed on "running").

### Server (live already, no update needed)

- **Drop-in games take more players before the puck drops.** Two searchers start a game; players who search in the
  next moments join it, until everyone presses READY. New, being tested.
- Drop-in games of three or more players get a relay port per player, on the North American relay when everyone is
  in North America.

## 0.90.2 (2026-11-11)

### Added

- **Play NHL 19 button.** A green button at the top right of every tab starts the game. It is grey until the app has
  found NHL 19, and shows the download progress while it fetches the emulator.
- **Choose the emulator build: Nightly or Kravickas.** Nightly (the default) is the official shadPS4 pre-release
  `4788f0b` (2026-11-10), unchanged from its GitHub release; on a test PC it ran about 20 % faster than our previous
  build. Kravickas is the Overtime build of Kravickas's NHL19-Build from 0.90.0. Pick one under Setup, Boost; the app
  downloads it and keeps both. Source: https://github.com/shadps4-emu/shadPS4 and
  https://github.com/MatusRiedl/shadPS4/tree/overtime-ship-1.
- **Live matches.** Matches being played right now show in Online, Matches with a pulsing red LIVE dot and how many
  minutes they are in. The game sends the score only at the end, so a live row has no score.
- **My games, redone.** Goals for and against per game as a chart, meters for your rates, you-against-opponents bars,
  your recent form as W/L pills, and a Big view pop-up with the larger charts.
- **Ping readout in any online match.** The connection pill now also shows in a match found inside NHL 19 (not only
  in lobby matches), when the game was started from the app.

### Changed

- **Good emulator settings from the start.** The first time the app finds a game, it turns on PS4 Pro mode, direct
  memory access and the shader cache, sets extra DMem to 3500 MB (never lowers a bigger value) and vblank to 9999.
  These are set once; you can change any of them later in Game settings.
- **First-run Patch defaults.** A new install has teams, league, menus and server texts on, and of Updated assets
  only team art, 3D jerseys and player photos, which it downloads on its own after the first look.
- **Lobby matches no longer lock vblank to 60.** Each player keeps their own vblank; mixed values play fine.
- **Lobbies use the emulator build the server picks**, and the app gets it on its own. Update to 0.90.2 to keep
  joining lobby matches.
- Online: "History" is now "Online", "Recent matches" is now "Matches", and Ranks has its own section next to the
  leaderboard. The "Match review ready" banner and the CONFIRMED tag are gone.
- Setup: the Folders checks are folded away (open them to see each one); the Boost resolution buttons line up left.
- New splash screen.

## 0.90.1 (2026-11-11)

### Changed

- **Lobbies are Quick only for now.** CHEL lobbies are not ready yet, so the app no longer offers them: Host a lobby
  makes a Quick lobby (two players), the public list shows Quick lobbies only, and a CHEL lobby code says CHEL lobbies
  are not available yet. World of Chel itself is unchanged.

## 0.90.0 (2026-11-11)

### Added

- **World of Chel online.** The World of Chel tile is back: the hub, your CHEL player and customization (every item
  unlocked; level and XP are shown but lock nothing), drop-in 6s, 3s and 3-on-3, clubs, club seasons, Ones and Pro-Am
  run on the Overtime servers. Some modes are still being tested with real players; see the known issues below.
- **CHEL lobbies.** Create a Quick lobby (two players, as before) or a CHEL lobby for 1 to 12 players. The host picks
  the mode, and drop-in lobbies can split into Home and Away. The lobby list shows which kind each lobby is. In NHL 19,
  open World of Chel, pick the lobby's mode and press Play.
- **Every human game counts.** World of Chel games between people are rated in the same rank as Versus, Shootout and
  Threes. Games against the CPU only, and Pro-Am, are logged but not rated.
- **Rank icons.** Each rank has its own icon in the leaderboard, the ranks list, next to your rating and in the
  after-game pop-up.
- **Smoother emulator.** Lobby matches and Boost now use an Overtime build of shadPS4: Kravickas's NHL19-Build
  749170d plus earlier frame flips, steadier frame pacing and higher thread priority. On a test PC at unlocked vblank
  (average / 1% low / 0.1% low fps): 77 / 46 / 44 before, 94 / 71 / 66 now. The CPU math is unchanged, so Intel and AMD
  PCs still play in step. GPL source: https://github.com/MatusRiedl/shadPS4/tree/overtime-ship-1 (tag
  `overtime-ship-1`). Players on 0.90.0 meet players on the same emulator build only, so update together.

### Changed

- **"Keep the World of Chel tile" is on by default**, also for existing patches (re-patch once).
- Creating a CHEL lobby on a server that is not updated yet now says the server needs the update (Quick lobbies still
  work), instead of "the game mode is versus, shootout or threes".
- The app no longer says an older Kravickas build is "newer" when the server runs an Overtime build on top of it.

### Known issues

- Ones: PLAY NOW does not find a game yet. Pro-Am: the challenge list is empty. Club games: the dressing room fails
  before the search. Club Members: the screen does not load.
- A new profile fails the World of Chel player check until NHL 19 is restarted once after creating the CHEL player.
- Class and trait names show as "Class 13" and "Trait 6".

## 0.83.0 (2026-11-10)

### Added

- **No shadPS4 install needed.** Find game takes NHL 19's `eboot.bin` or its PKG. When there is no shadPS4 on the PC,
  the app downloads Kravickas's NHL19-Build (the build Boost and lobby matches already use) and plays on it. A shadPS4
  you already have is used as before.
- **Install from a PKG.** Pick the game PKG and the app installs it into a new folder next to the PKG; pick the 1.60
  update PKG and it goes into a `-patch` folder beside the game, which shadPS4 loads. DLC PKGs are refused, free space
  is checked first and nothing already there is overwritten. It uses shadPS4Plus's `pkg_extractor` (GPL-2.0, a
  separate program), downloaded from its GitHub release the first time and checked by its sha256.
- **Connection in the corner.** While a match runs, a small pill at the top right of the game shows the ping and the
  packet loss: green, yellow or red, and "NO PACKETS" or "NO DATA" when the link stops. Its switch, "Connection in
  the corner", is under "When the game starts" (on by default). Windows only.
- **Game settings, Controllers and Keyboard.** Setup → Boost performance has a Settings row. Game settings shows
  shadPS4's settings for NHL 19 in tabs, with a description of each one; settings Overtime needs are shown locked.
  Controllers maps the pad's buttons, sticks, deadzones and lightbar; Keyboard binds up to three keys, a combination
  or a mouse button per button, and the mouse as a stick. Press F8 in the game to use new bindings at once.
- **Fullscreen (Borderless) by default.** NHL 19 now opens borderless for everyone, from the next Patch or Play. Pick
  another display mode in Game settings and the app keeps it. Lobby matches play exclusive Fullscreen as borderless.
- **Newer Kravickas builds are announced.** The Overtime server checks Kravickas's NHL19-Build on GitHub. When a
  newer one is out, the Boost card says so; Overtime moves to it after a test.

### Changed

- **The same graphics settings for everyone.** Patch sets shadPS4's Readbacks mode to Precise and turns on Readback
  Linear Images in NHL 19's own shadPS4 settings, against graphical glitches. Play puts them back if they were
  changed, lobby matches always play with them, and Unpatch gives you your own values back.
- **The firewall rule is optional.** Matches go through the Overtime server, so the rule no longer decides whether
  you are ready. Multiplayer → Advanced still has "Allow..." for it: it only helps a direct link, used when the
  server cannot carry a match.
- **Multiplayer → Advanced in one grid.** Server, CPU, Reports and Firewall share the same columns; "Send the
  result..." is now "Send result...".
- ShadNet sign-in works on a PC that never ran shadPS4 (the app writes shadPS4's default users first).
- **Cleaner screens.** The Update tab no longer shows the steps row or the "patched by an older Overtime" line.
  Setup's roster card shows "13 free save slots from 15 total." and drops its hint line, and the Boost card says what
  it does: 60 FPS.

### Fixed

- With nothing picked yet, Setup said "shadPS4 and NHL 19 are ready" and Folders said "all found".

## 0.82.0 (2026-11-10)

0.80.1 and 0.81.0 were never published; what they had is in here. The texture encoder, 720p, the movable downloads
folder, the power-cut-safe writes and the faster Patch are Kravickas's work (pull request #1).

### Fixed

- **Intel and AMD PCs play each other online without drifting apart.** Two instructions the game uses in its movement
  math give slightly different answers on Intel and AMD CPUs, so the two games drifted apart (a goal not counted, then
  LOST CONNECTION). The game patch now has a **Cross-CPU fix** that makes those answers the same on every CPU, and on
  an Intel PC the app also turns on shadPS4's AMD math (its `redzone_patches` setting) when it installs the patch, so
  online play outside a lobby has it too. A 10th gen Intel against a Ryzen 7 9800X3D stayed in step for the whole
  test match.
- The app finds your saves when shadPS4's first player is not user 1000.
- **Sharper jerseys, club logos and photos made on this PC.** They were compressed with Pillow's own BCn writer, which
  picks a block's two colours badly, never gives BC3 alpha its own ends and cannot write BC7. A new encoder (numpy,
  in the exe) does it properly, checked against two decoders. Every texture keeps the game's own size, format, mips and
  header (checked byte for byte on the game's Czech jerseys). How close a made texture is to its picture (100 % =
  identical, from the average difference of every colour value), and how much smaller that difference got, measured on
  the national team pack (10 of each kind, at the game's sizes):
  - 3D jerseys 98.7 % to 99.8 % (the difference 84 % smaller), socks 98.6 % to 99.9 % (93 % smaller), the numbers
    99.2 % to 99.9 % (85 % smaller);
  - UI jerseys, logos and photos (the game's BC7 art) stay BC7 instead of turning into BC3: UI jerseys 99.7 % to 99.8 %
    (45 % smaller), a photo 98.9 % to 99.7 % (73 % smaller), a logo with soft edges 98.9 % to 99.6 % (61 % smaller);
  - the Czech chest logo on the game's own jersey textures 98.2 % to 99.5 % (home, 71 % smaller), 98.8 % to 99.4 %
    (away, 48 % smaller): no stair steps, specks or pink white;
  - a block of one colour (three quarters of a jersey) gets the best colour pair there is, from a table.
- **Mips made like the game's own.** Measured on NHL 19's own Czech jerseys, their mips are their full size scaled
  down with a bicubic filter in the stored colour numbers; the made ones were box-filtered, which is softer. The mips
  (what shows a few metres away: the screenshot's chest logo is mip 2) are now made that way, weighted by alpha, and
  the smallest ones are no longer darkened by black padding.
- The textures made before are made again once, at the first Update or Patch that makes them.
- **Nothing breaks when the power goes.** Every file the program writes now reaches the disk before it takes the old
  one's name: the patch files and their record, roster saves, settings, your edits, shadPS4's and QtLauncher's files,
  the downloads, the jerseys, club logos and photos made on this PC, the record of the packs checked, and the program
  itself when it updates. Before, a power cut right after a write could leave a file of the right size full of zeros,
  which Patch's quick check took as intact.
  - Settings were written in place: a cut while saving them lost them. Now whole or not at all.
  - Repairing a roster save swaps the whole folder, so its two files always belong together; a swap the power stopped
    halfway is put back at the next start.
  - A damaged patch record now says what to do instead of stopping the Game patch tab.
- Two match setups can no longer run over each other (a lobby match starting while the app still puts the last one
  back): each one is put back only by what made it.
- A lobby match keeps the text language your patch was made with (it fell back to English).
- Downloads and cache: a picked folder that already holds other files gets a folder of its own inside it, and moving
  away from such a folder leaves its other files where they are.

### Added

- The Game patch card's Online row checks the Cross-CPU fix after NHL 19 starts: "Cross-CPU: ready", or a red line
  not to play online in that session (with the reason).
- **3 min** in Period length, and **new lobbies start at 3-minute periods** (quick games). 4 to 20 minutes are still
  there.
- Each match game's log is kept (`%APPDATA%\OvertimeRoster\match\logs`, the newest 8), so a desync can be checked.
- **Check my CPU** (Multiplayer → Advanced, the CPU row): it downloads a small test program
  (`cpu-estimates.exe`; its source is `tools/cpu_estimates.py` in this repository), runs it for about a minute (two on
  a CPU with two kinds of cores) and says whether your CPU gives the same answers as the tested AMD or Intel CPUs. It
  runs only when you press it and sends nothing by itself; "Send the result..." asks first.
- **Reports, off unless you turn them on.** After a crash, or a match the server saw end early, the app can send the
  game's log so the problem can be found. It asks once after the update; Multiplayer → Advanced has the switch and a
  "Send a report" button that asks every time. Folder paths, user and computer names, your Online ID, IP and e-mail
  addresses are taken out of the log, and a password never goes. The Privacy list there says everything a report
  holds. Reports are kept for 30 days.
- **720p.** The Resolution choice (Boost performance card) has 720p next to 1080p and 1440p: Kravickas's
  "Resolution 1280x720 (16:9)" patch, for a weaker GPU. It renders below the game's own 1600x900 size, so it needs no
  memory patch and no Additional DMem (your own value stays). Built into the app like 1440p, nothing to download;
  a patched game takes it at its next start, no Patch needed.
- **Setup, Folders: Downloads and cache.** Where the downloaded packs and the files made on this PC (jerseys, club
  logos, photos, several GB with every pack) go, a folder like the others: Change... moves them to a folder you pick,
  for example on the drive NHL 19 is on, so nothing big stays on C:. Auto moves them back. On another drive every file
  is copied and checked first, the program switches to the new folder only once all are there, and only then removes
  the old ones; a copy that fails changes nothing. A folder inside NHL 19, its update or mods, shadPS4's data or the
  saves is refused. When the drive of the folder you picked is not there, the program uses its own folder until it is
  back.
- **Setup is wider on the left** (as the Game patch tab), the rosters on the right take less room. **Each folder is
  one line in a tile** like the Update tab's switches: its bar green when the folder is there and good (found or
  yours), red when it is not; the paths line up.

### Changed

- **Only finished matches count** (server update, 2026-11-10). A match that a player leaves or drops before the end
  counts for no one: it leaves the list, the board, the in-game Recent Games and every rating. This replaces the 1-0
  forfeit loss. A match with no result or only one report stays listed for an hour, so the result can still be
  entered or confirmed.
- **Everyone needs 0.82.0.** An older app and 0.82.0 are never paired, because only one of the two games would have
  the Cross-CPU fix. When one app is older, the lobby says who updates.
- **Games meet only games set up like them.** The app gives the game an online version that stands for its patch and
  shadPS4 build, so the server pairs only games that stay in step. Lobby matches always play on the same shadPS4 build
  (the Boost one). If a game started from Game patch → Start runs another build or has no Cross-CPU fix, Start says so.
- **The Boost and lobby shadPS4 build is the newest Kravickas NHL19-Build** (749170d, 2026-11-09): graphics, file and
  save fixes since the last one. Boost players get it as an update; lobby matches use it.
- **Patch reads the art once, then checks it at the end.** It used to unpack every texture of every art pack three
  times: a full check before writing, again to write it, and once more from the written archive. Now a pack zip
  checked in full once is not unpacked again until it changes (size or time; the record is `packs_checked.json` in
  the cache): each texture is unpacked once, checked against its pack's sha256 as it is written. At the end of
  Patch every written archive is read back whole and its sha256 compared with the one taken while writing; one that
  does not match is removed and Patch says so (press Patch again: the packs are still in the cache). 27 % less
  time on 560 MB of test art from the second Patch on (2.98 to 2.17 s, warm disk here).
- **Every core.** Jerseys, club logos and photos are made on every core the program may use. The game's archives and
  the packs are read on one thread and the packs are written in order, so they are byte for byte the ones one thread
  makes (checked with 1 and 6 workers). A texture made on its own splits its blocks over the cores instead.
- Making a texture takes longer: a jersey colour map (2048 x 2048, its mips included) about 2.7 s instead of 0.5 s
  on one core, a 512 x 340 BC7 photo about 1.4 s. A photo is made once and kept in the photo cache, next to its
  picture.
- **The art archive is read on every core while Patch writes it**: each texture is unpacked and checked against its
  pack on its own thread, written in order (byte for byte the archive one core writes). The game's normal and colour
  maps the jerseys cover are unpacked on the workers too, not on the one thread that reads the archives.
- The exe is about 10 MB larger (numpy).
- **A faster Update**: each team's look at the roster reads a table's column in one pass instead of one field at a
  time. Measured on tables of 11,000 players: 57 to 21 ms and 37 to 12 ms per team. The roster it writes is the same.
- **Texture blocks put in the PS4's order in one pass**, in an order worked out once per texture size (a 1024 x 1024
  BC3 texture with its mips: 45 to 14 ms to retile). The bytes are the same (checked on 3360 shapes).

### Known

- The Cross-CPU fix is made for the v1.60 `eboot.bin` (CUSA11126 and CUSA11116 have the same one). A game with
  another `eboot.bin` gets the patch without it and meets only games like its own; the Game patch card says so.
- Intel 12th to 14th gen (performance and efficiency cores) is not measured yet.

## 0.80.0 (2026-11-08)

### Added

- **Online Threes.** MULTIPLAYER, Match rules has **VERSUS | SHOOTOUT | THREES**: 3 on 3, one player a side, the other
  skaters are CPU. Once both are ready the game opens Threes online by itself. Threes games show in your history and
  the rating strip ("Threes w-l").
- **Ready makes both games match, for that match only.** In a lobby, Ready now sets up a match copy of the game on each
  side: the NHL 19 build of shadPS4 (its own copy, downloaded once), the host's online patch plus your own picture
  settings (1440p and the like stay yours), and the match timing. Your own shadPS4, rosters, data, art and settings are
  never changed: everything goes back when NHL 19 closes, or at the next start of the app after a crash.
- **No need to close NHL 19 before Ready.** If it is open, the app restarts it for the match (it asks the game to close
  first and waits up to 10 seconds).
- An unpatched game can play online: the Patch row says "Online ready: Ready sets up each match by itself".

### Changed

- **MULTIPLAYER has three columns:** you and the checks before a match, the lobby, then your rating and history.
- With a 0.80.0 partner, Ready no longer switches your own shadPS4 to the NHL 19 build or patches your game; the match
  copy does that instead.
- While a match setup is in place, Game patch waits ("press again after that") instead of writing over it.

### Known

- Both players need 0.80.0 for the match setup. With a 0.70.x partner the lobby works as before and names who updates.
- The match setup was tested in code and on the server, not yet in a two-player game over the internet.

## 0.70.8 (2026-11-08)

### Changed

- **Ready gets your game ready for online play by itself.** Before it tells the lobby, Ready switches NHL 19 to the
  NHL 19 build of shadPS4 (Boost performance, the build every online player uses; also a newer published one), brings
  the game patch up to this version and, on a game that was never patched, puts in only what online play needs (about
  a second, no roster or art). No button to press. The card shows what it is doing.
- **The patch check compares only what reaches the other game.** A 1440p game and a 1080p game, Be a Pro on or off, or
  the server written as a name or an address no longer count as "patch differs".

### Fixed

- A match the two players finished could end with "Failed to retrieve data" when an earlier try of the same two had
  been left early (server fix).
- Two different shadPS4 builds playing each other drift apart in play (repeated faceoffs, then the match ends): the
  lobby now says so before the game starts, and Ready fixes it on your side.

## 0.70.7 (2026-11-07)

### Added

- **Online Shootout.** MULTIPLAYER, Match rules has **VERSUS | SHOOTOUT** left of Roster: the lobby host picks the game
  before Ready. SHOOTOUT greys out the rules a shootout does not use and keeps skill level, game style and goalie
  control. Once both are ready the game opens Online Shootout by itself; pick a team, READY, play.
- Searching from the game's own Online Shootout menu with the default settings meets other shootout players only.
- **My games** shows Shootout numbers on their own (attempts, goals, scoring % and save %); the Versus per-game numbers
  count Versus games only, and game rows say "Shootout".
- One rating over Versus and Shootout; the win-loss record is kept per game.

### Known

- Played in the lab (two games on one network), not yet between two players over the internet.

## 0.70.6 (2026-11-07)

### Changed

- **A much faster Patch** (measured here on the real game, warm disk):
  - League, menus and database are prepared in 0.12 / 0.12 / 0.50 s instead of 0.88 / 0.44 / 1.66 s: each game
    archive's file list is read once per Patch, not 660 times.
  - The game's text (76,000 strings) decodes 4.7 times faster, same strings.
  - The Patch tab no longer hashes your patch files each time it opens (0.37 s before, about 0 now).
  - A second Patch no longer reads back 15.6 GB of art to check files it wrote itself (about 9 s warm, more on a cold
    disk or a hard drive); Patch and Unpatch compare size and time first and hash only when they differ.
  - Update reads the people pack's list, not its 5,900 photos (2 s before, 0.02 s now).
- The first Patch after updating still hashes the copied archives once; the speed-up shows from the second Patch on.
  Writing the files is unchanged, so a Patch is faster but not instant.

## 0.70.5 (2026-11-07)

### Fixed

- **Play uses the shadPS4 data folder you set.** shadPS4 reads the `user` folder inside the folder it is started from.
  With QtLauncher's layout (shadPS4 in `...\ShadPS4\NHL`, its data in `...\ShadPS4\user`) Play started it from the
  exe's folder, so shadPS4 made a fresh `%APPDATA%\shadPS4`: no Overtime patch, network and ShadNet off, no saves. The
  game asked to set NHL up again, showed no ShadNet id and never reached the server. Play now starts shadPS4 from the
  folder above `user`, as QtLauncher does. A data folder shadPS4 cannot use (not named `user`, not
  `%APPDATA%\shadPS4`) is refused in Setup and at Play.

### Changed

- **Faster Patch** (thanks to Kravickas): each pack and game archive stays open while the art layer reads it, instead
  of being opened again for every texture. Reading the people pack's 5,900 portraits went from 59 s to 2 s here.

## 0.70.4 (2026-11-07)

### Fixed

- **Portable shadPS4 is found.** Find game looks for shadPS4 next to the NHL 19 folder you pick (up to two folders
  above it), and for NHL 19 next to the shadPS4 you pick, instead of relying on `%APPDATA%` (empty when shadPS4 keeps a
  `user\` folder beside its exe). Saves follow shadPS4's Home Folder setting (shadPS4 Settings, Paths tab).
- **Texture mods on the EU game (CUSA11116).** Patch stopped with "art layer: ...teamlogos/hutcardheritage/t1.gnf ...
  archive is unknown" while applying logo packs. A texture whose folder this game lacks now goes into the archive of its
  nearest parent folder.
- **A game folder with only the update in it** is refused at the start with a clear message (the base game's
  `databigs\inxp_10.big` and others are missing), instead of the patch stopping halfway.

### Added

- **Folders list** (Setup, "Where is NHL 19?" card): shadPS4, NHL 19, shadPS4 data and Saves, each "found" or "yours".
  Change... sets one yourself (checked first), Auto finds it again. A folder you set is never replaced by what the
  program finds.
- **Lobby chimes:** a soft tone when your lobby opens, another when somebody joins, a third when you leave or the lobby
  closes.
- **MULTIPLAYER tab shines in gold**, and the Setup card is now called "Where is NHL 19?".

### Changed

- A lobby nobody joins closes after 30 minutes.

## 0.70.3 (2026-11-07)

### Added

- **60 fps replays, menus and cutscenes.** NHL 19 dropped to 30 fps on its own for menus, goal replays, celebrations and
  close-up cutscenes (live play was already 60). Kravickas's "60 FPS replays" patch is now part of the Overtime patch,
  on for everyone.
- **Resolution: 1080p or 1440p** (Setup, Boost performance card). 1080p is the game's own; 1440p renders at 2560x1440
  (Kravickas's resolution patch), sharper, needs a stronger GPU, and sets shadPS4's Additional DMem to 3500 MB. Back to
  1080p, or Unpatch, puts your own value back. Works with any shadPS4 build.
- **No re-patching:** update the app and press Play; the game picks up both on its next start.

Both patches are Kravickas's work (github.com/Kravickas/ps4_cheats), shipped with his OK.

## 0.70.2 (2026-11-07)

### Added

- **Hometown Remix jerseys (BETA).** A new switch in Game patch, Updated assets. Each NHL team gets its Hometown Remix
  jersey in place of one of its other jerseys (Vegas: the away jersey, Utah: the third, Seattle: the alternate). Made on
  your PC at Patch from retail photos, so colours, crest and stripes are close but not exact. Switch it off and Patch
  again, and the normal jerseys are back. Not finished: expect rough edges.

### Also in 0.70.1 (no more silent SIGN IN REQUIRED)

- **Game patch** writes shadPS4's two network switches into the game's "Network" section too, and fills empty ShadNet
  server fields there. Unpatch takes out what it added.
- **Lobby start** is refused, with words, when shadPS4 has no ShadNet sign-in for NHL 19; after the game boots, the card
  says so when the network is off or ShadNet refused the sign-in, instead of pressing through.
- **Setup:** one "Find game..." button (shadPS4QtLauncher.exe, shadPS4.exe or NHL 19's eboot.bin).
- **Game patch, "What's in your game now"** is a short verdict plus what is patched in and the Online row; less red in
  the app (card numbers and markers are metal).

## 0.70.0 (2026-11-07)

### Changed

- **Game patch, simpler.** The switches sit in three groups you can open: Teams and league, Menus and server texts, and
  Updated assets. Each group has its own switch (on: its main parts, off: everything in it), and you open a group to
  pick single parts. No more all-or-nothing art pack.
- **Updated assets download one by one.** Team art, 3D jerseys, player photos, the alternate and national team jerseys
  and the centre ice of every league each download when you switch them on. A dot before each name shows whether it is
  already in the game (green) or needs Patch (yellow).
- **Plain names.** "NHL 27" is gone from the app: Updated assets, Team art, 3D jerseys, Updated ratings and types. The
  default roster switch now just says what it does (all 32 teams; its "?" explains NHL 19 shipped with 31 in 2018,
  before Seattle). The World of Chel switch says it only keeps the tile (Overtime does not run World of Chel yet).
- **"What's in your game now"** (Game patch, right card) uses plain words: Patched in, files changed and intact,
  Check for damage, Backup copy of the game.
- **Update tab fits without scrolling:** the switches are compact tiles, with the season and data choices in one bar.

### Fixed

- **Real lines and captains** now shows on the Update tab (the switch was missing).

### Also in 0.60.3 and 0.60.4 (in-app updates)

- **ShadNet sign-in and sign-up in the app** (Multiplayer); your account is found without starting NHL 19 first.
- **Lobby host picks the roster:** the server roster, or the host's own open roster with its lines, uploaded at Ready.
- **Both players need the same game patch** before Ready in a lobby.
- **Forfeit:** a player who leaves or drops a match in play loses it 1-0 (server update).
- Multiplayer tab no longer crashes on the rank progress bar.

## 0.60.2 (2026-11-07)

### Fixed

- **Online Versus: a player quitting no longer freezes the other game.** When your opponent leaves mid-match, your game
  shows "Lost connection" and takes you out of the match instead of freezing on the ice. The match is not counted.
  (Server update: works on every app version.)
- **ShadNet showed as off** on PCs where shadPS4's settings files start with a byte-order mark (some editors save them
  that way).

### New

- **Online Versus: pick your team.** Both players can change their team on the Online Versus setup screen; before, each
  played their favourite team. (Server update.)
- **Multiplayer: a new lobby is in the public list by default.** Untick "Show it in the public list" for a private lobby.
- **Clean sheet:** the match history and standings start fresh with this release.

## 0.60.1 (2026-11-05)

### Changed

- **Update comes first.** The tabs now read Setup, Update, Game patch, and a strip on both tabs shows the order: Update, then
  Game patch, then in NHL 19 pick the new roster in Rosters > Active Rosters. Patch makes the club logos and jerseys for the
  roster NHL 19 plays, so patching before updating gave the old roster's logos.

## 0.60.0 (2026-11-05)

### New

- **Penticton Vees in the WHL** for 2026-27 (Play Now and Roster Management, like NHL Legacy), with their name, logo and roster.
- **Patch tab:** the patch explanation is a "?" next to the Patch button.
- **New app icon** (the app, its window and the splash).

### Fixed

- **Versus:** Stats Central no longer loads forever and Recent Games answers with a message instead of an empty reply (server update).
- **Logos:** the six clubs NHL 27 lacks keep their NHL 19 logos, the result says so, and all 32 AHL logos were checked in game.
- **Jerseys:** throwback rows read ALTERNATE instead of a stale "2016-17 HOME" (press Update again).
- **Utah:** helmets stay black with a roster made by this version (press Update again, then pick it in Rosters > Active Roster).
- **"Server not reachable":** the game gets the network settings it needs on more PCs.

## 0.50.1 (2026-11-04)

### Fixed

- **Club logos of the AHL clubs that moved.** Abbotsford, Henderson, Hamilton and Calgary kept their 2018 logos when the club logo pack
  arrived after Update, or when Patch ran in a later session of the app. Patch now makes the logos of the roster you play.
- **Update says when it skips the club logos.** It downloads the club logo pack first when it is missing, and the result says when it
  could not.
- **The result says when a club has no logo**, and Update says when new players got no photo because the photo pack is not in the game.

## 0.50.0 (2026-11-03)

NHL 19 now gets what NHL Legacy gets from the same data: the same people on the same clubs, their lines, letters, numbers,
contracts, attributes and photos.

### What is new

- **Same rosters as NHL Legacy.** The AHL, SHL, Liiga, DEL, Extraliga, NL, OHL, QMJHL and WHL now come from the leagues' own data. NHL 27
  is used only where that data has nothing: the ECHL, ICE Hockey League, HockeyAllsvenskan and the other European clubs.
- **Real numbers, letters and sizes.** A club's own list gives each player their number, height, weight, shot and C or A. Players nobody
  rates get a rating from Legacy's rule.
- **Real contracts.** Contract values follow the same list as NHL Legacy, and players without an NHL deal get a starter deal by league and rating.
- **Real lines where they exist.** Clubs with published lines play them. Clubs without, and Columbus and Winnipeg's forward lines today, are
  dealt by rating.
- **National teams.** The eight smaller teams are built by Legacy's rule. Canada, the USA and the other big teams come from the IIHF
  lists: NHL Legacy's own squads for those are not in the shared data, so those teams differ.
- **Player photos of every league.** A new pack of about 200 MB gives some 6,000 players of every league their photo.
- **Rink art from NHL 27.** A new switch on the Game patch tab: the IIHF emblem at centre ice and the IIHF puck in national team games, and NHL 27's pucks,
  board ads and league logos. National team games keep NHL 19's board ads.
- **Club logos and centre ice of every league.** Clubs that changed their logo since 2018 show their current one, made on your PC from a 43 MB pack.
- **Jerseys of every league, much smaller downloads.** The extra jerseys (NHL alternates, national teams, and now the AHL, ECHL, junior and
  European clubs) are made on your PC from small packs (13 to 169 MB instead of up to 1.2 GB each). The first Patch with them on takes longer
  (about 15 minutes with all three on; the club jerseys alone about 11); after that it is quick. NHL teams whose pants changed colour since 2018 wear the new colour.
- **The 2026 AHL.** Henderson Silver Knights, Abbotsford Canucks, Hamilton Hammers and Calgary Wranglers take the four slots of the clubs that
  moved, with their names, arenas, colours and jerseys, and every NHL team has its 2026 farm club. Coachella Valley, Seattle's farm club,
  gets its real players too and shows in the app's AHL list; in the game it plays in Season and Franchise only (NHL 19's Play Now has no
  place for it).
- **2026 arenas.** Every NHL team plays in its 2026 arena, and Buffalo, Columbus and the Islanders wear their current colours in the menus.
- **New players' photos.** A player new since the photo pack gets his photo downloaded when you press Update.
- **Changes by team.** The list of changes now starts with a section per team: who joined, left, was called up, signed or retired.

### Fixed

- **Players kept their NHL rights.** A prospect playing in junior or in Europe was cut from his NHL team's list. He stays on it now.
- **Free agents retired too young.** Every free agent no list named retired, 25-year-olds too. Now only those of 30 and more do, and last
  season's NHL players nobody signed are free agents you can sign.
- **Small clubs signed NHL stars.** An ECHL club short of a player signed the best free agents. Clubs now sign players of their own level,
  and junior clubs young players.
- **Call-ups.** An NHL team that cannot dress a full line-up calls up from its farm club before it signs a free agent.
- **Gear.** A goalie who changes team wears his new team's mask, a skater who comes to an NHL team gets a stick in its colours, and new
  players no longer wear their look-alike's gear.
- **Salaries without the 2026 cap.** With the 2026-27 salary cap switched off, contracts are scaled to NHL 19's own cap.

- **The roster you saved must be the active one.** Update saves a new roster but does not change which one NHL 19 plays. If yours is
  not active, the Update tab now says so in red, and tells you where: in NHL 19, Rosters > Active Rosters.
- **Lines were wrong after Update then Patch.** The default roster the Patch makes after an Update dealt its lines by rating. It now plays the
  real lines.
- **Photos went missing after an Update.** A roster saved by Update lost its photo flags, so many players showed no photo.
- **The European NHL 19 (CUSA11116).** Patch stopped with "eng_us-meta.xml not in ...". It now uses the English text file
  your game has. A folder with only the game's update gets a plain message saying which folder to pick.
- **"Server not reachable" on some PCs.** Overtime now also trusts the certificate list it carries, as NHL Legacy does, so a
  PC without Windows' newest certificates can reach the server. If it still says not reachable, the error log says why.
- **No Patch after changing network settings.** A new server address, or shadPS4's network switches turned off, is put
  right when you press Play. Changing other shadPS4 settings no longer asks you to Patch again.

## 0.40.0 (2026-11-02)

Update now takes the whole game: every league, player, calendar and national team.

### What is new

- **Real rosters for the big leagues.** SHL, Liiga, DEL, Extraliga, NL, OHL, QMJHL and WHL come from the leagues' own data, the same
  source as NHL Legacy. The AHL, ECHL, ICE Hockey League and HockeyAllsvenskan come from NHL 27. New players get ratings too.
- **New clubs.** A club that left a league makes room for one that has no place in the game: Wenatchee Wild, Newfoundland Regiment and
  others take the slot, with the old slot's logo and arena.
- **Real calendars.** 2026-27 schedules for the SHL, DEL, Extraliga, NL, OHL, QMJHL, WHL and ECHL, next to the NHL, AHL and Liiga.
  Clubs that have no slot in NHL 19 lose their games, and each league is evened out, so some play fewer games than in real life.
- **National teams.** 20 squads from the IIHF. Russia has played no IIHF event since 2022, so its team is the best Russians at clubs.

## 0.30.0 (2026-11-01)

Rosters of every club league from NHL 27, centre ice for the clubs of every league (not national teams), national team jerseys, and many fixes.

### What is new

- **Every club league from NHL 27.** The Update tab now rebuilds the SHL, Liiga, DEL, Extraliga, NL, ICE Hockey League, the
  European clubs, OHL, QMJHL, WHL, ECHL and HockeyAllsvenskan from NHL 27, as it did for the AHL. Clubs NHL 27 has under a new
  name take that name (Frolunda HC). Clubs it does not have keep their 2018 roster.
- **More jerseys and ice** (new switches on the Game patch tab): centre ice for the clubs of every league (45 MB), national team jerseys (149 MB)
  and NHL alternate jerseys (765 MB) from NHL 27. Switch one on and it downloads by itself, switch it off and it stays on your PC.
  Press Patch to put them in the game. Alternates take the place of a team's throwback jerseys.
- **Boost performance** (new on Setup): one button puts NHL 19 on Kravickas's NHL 19 build of shadPS4, for better performance and
  graphics. Thanks to Kravickas for allowing it. Disable puts your own shadPS4 back. Your saves stay the same.
- **My games** on the Multiplayer tab: your games with score, teams, opponent and box score, and your totals.
- **Your hand-set lines stay.** Lines you set in the Lines tab survive an update.
- **The app updates itself:** from this version on, Update now downloads, checks and restarts on its own. 0.20.0 updates to
  this version the way it always did.

- **A window that never comes up.** "Starting..." shows until the app is ready. If the window stays blank the app reloads it, then
  opens in your browser, with Try again and a start log to send us. Each start has its own browser folder.
- **A player who leaves pays for it.** When your game reported the result and the other player never did, it counts after an hour,
  unless their own report says otherwise. Results typed in the app still need both players.
- **Update warns you.** The result names a club short of 2 goalies or 18 skaters (the game hangs on it) and free agents who are also on a club.

### Fixed

- **Goalies stay goalies.** A real goalie is never matched to a skater with the same name and birth date.
- **Any shadPS4 works.** The app no longer asks for the NHL19-Build. Pick your emulator folder or `shadPS4.exe`; with QtLauncher, the
  version selected in it is found by itself. The app now opens on Setup.
- **The game closed when you picked a custom roster.** A first save on a PC without an online roster was written wrong. The
  app repairs such saves by itself when it starts, with a backup first.
- **Be a Pro with Seattle:** the first games now match Seattle's calendar.
- **Seattle in other leagues' Season lists** is gone.
- **A first save with no game save yet** now works, and saving is refused while shadPS4 is running.
- **Multiplayer tab:** it says why ShadNet does not connect and what to do next.
- **"Patched, with 1 problem"** no longer shows for a file this version builds itself.
- **Split installs:** `-UPDATE` and `-patch` are read the way shadPS4 mounts them.
- **CUSA11116** is recognised as well as CUSA11126.

### Known limits

- Not proven with two PCs yet: that the game sends its own result report, which a leaver's loss needs.
- Not run in the game yet: the league rebuilds, the national team jerseys, NHL alternates, centre ice for all leagues, kept lines,
  and a first save with no game save. If the game does not start, switch the packs off and press Patch again.
- With every pack on, Patch needs about 6 GB of free disk space.
- Boost performance does not work with a shadPS4 that keeps its saves in a `user` folder next to the exe. The button itself is new
  and has had little testing: if the game does not start, press Disable.
- A team with only home and away jerseys has no room for an alternate.
- The ALTERNATE label shows with the default roster; other rosters show the jersey's old name.
- This exe is not signed, so Windows may warn about it.

## 0.20.0 (2026-10-30)

A hotfix for players whose NHL 19 update sits in a folder of its own.

### Fixed

- **NHL 19 with the update in its own folder.** shadPS4 can install update 1.60 beside the game, as `CUSA11126-patch`
  (or `CUSA11126-UPDATE`) next to the base game `CUSA11126`. Overtime read only one of the two folders and stopped with
  errors like `nhl/data/kettle/loc/eng_us-meta.xml not in ...\CUSA11126-patch`. Now it reads the two together, as the
  emulator does, whichever of them is picked:
  - Setup lists the game once, as the base folder.
  - The game patch goes to `CUSA11126-mods`, the folder shadPS4 reads for that game. If 0.10.0 left a
    `CUSA11126-patch-mods` folder, delete it.
  - The Quick check and Verify every file cover both folders.
  - If you merged the update into the base folder by hand to get around this, that keeps working.
- **Calendar tab:** "My season" no longer says it comes after beta2. It is still to come.
- **Setup tab:** the Online card (server address, firewall) shows only on the Multiplayer tab now, not on both.

## 0.10.0 (2026-10-29)

The first public release. It includes everything from the closed betas (0.1.0-beta1 to beta4).

### What is new

- **Multiplayer tab** (closed beta): join or host a lobby on the Overtime server, the host picks the match rules and
  both games bake them in, the game starts with one press, and finished games land in your match history. Elo
  rating with nine ranks, a leaderboard in the app and on the public web board, lobby chat and an in-game overlay.
  - The app presses READY on Game Setup once the server sees your game there, instead of on a timer. If no search
    starts, the card tells you to press it.
  - The match rules use the game's own words (Competitive, Full Sim, Continuous OT, ...).
  - The History card says what the Overtime server keeps about you. "Show me on the web board" hides your name
    there.
  - The game gets the online roster itself: when you press PLAY in Online Versus, it downloads the current one if
    yours is older.
- **Update warns when NHL 19 needs the patch**: when the game is not patched, the patch has a problem, or an older
  Overtime patched it. "Go to Game patch" takes you there.
- **Seattle in Be a Pro.** Choose Team lists the Seattle Kraken and a career on Seattle plays, saves and loads. It
  needs the game patch with the league layer; with the league layer off, Be a Pro keeps the game's 31 teams.
- **Real 2026-27 calendars for the AHL and Liiga**, next to the NHL's:
  - AHL: all 32 clubs, 72 games each, each real club on its NHL parent's farm-team place (Coachella Valley on
    Seattle's). Official statistics provided by American Hockey League.
  - Liiga: the game's 15 clubs, 56 games each. Jokerit and K-Espoo have no place in NHL 19, so their games are left
    out.
  - The Calendar tab shows them: pick an AHL or Liiga club for its games, or "All AHL games" / "All Liiga games".
  - Every other league keeps the game's own calendar: no official schedule feed was found for the ECHL, OHL, WHL,
    QMJHL, SHL, HockeyAllsvenskan, DEL, Czech Extraliga, Swiss National League, ICE Hockey League, Champions League
    or the Spengler Cup.
  - **The calendars travel with the roster.** A new Franchise or Season takes its league calendars from the roster
    you have loaded in the game. The new default and online rosters carry them; an older saved or downloaded roster
    keeps the game's AHL and Liiga calendars until you run Update over it (Update writes them) or load the new online
    roster.
  - 32 Team Expansion Draft Franchise: Seattle and Utah each play their own real schedule in their own division, 84
    games each.
- **Photos and logos are a download now.** The Game patch tab has one "Photos, logos pack" card (about 155 MB):
  Download gets the four packs and switches them on, Remove deletes them. A fresh install starts with them off and
  Patch never downloads by itself. If you had the packs already, they stay on. Without the pack, Utah plays in the
  Coyotes' look and Seattle shows a stand-in crest (EA SPORTS) and kit; games play normally.
- **Sign free agents** from the Front office (Free agents group, Sign window, one Undo).
- **Photos switch**: put back the game's own player photos without undoing the rest of the patch.
- **Real equipment** from the NHL 27 pack (sock tuck, pants, tape colours, goalie neck guard).
- **Export to a folder** picks the game slot the folder is made for.
- The Lines tab shows each player's shooting or catching hand. Game patch sits before Update. Easier-to-read
  headings.
- Fixed: Patch brings the hub's Puck Peak news tile back where a beta patch had left it empty (press Patch once
  with 0.10.0; the Update tab asks for it).
- Fixed: Update no longer crashes on a roster save without the game's career tables.
- **Fewer refusals when you edit a roster.** The app now allows these edits: two teammates with the same number, more than three
  letters, an empty or doubled place in the lines. Save lists these as warnings and saves anyway. It still stops what
  breaks the game: a roster place for a missing player or team, one player on two teams, a skater in goal or a goalie
  in a skater's place, more rows than the game holds, or more than 40 players on a team.
  Roster keys out of order are put right on Save.

### Known limits

- **Be a Pro, Seattle and Utah dates.** Be a Pro keeps Seattle in the Central and Utah in the Pacific. Each team's
  divisional games match that, but Seattle plays Utah's real 2026-27 dates and Utah plays Seattle's. A 32 Team
  Expansion Draft Franchise is right.
- **Classic Franchise and NHL Season have 31 clubs.** The team lists show 32, but the game builds the league with
  Seattle in Utah's place: Utah is not in the league and Seattle plays Utah's real 82-game calendar. For both teams,
  start a Franchise with "32 Team Expansion Draft". This has been so since Overtime added Seattle; it is not new in
  0.10.0.
- Season mode lists Seattle (0 OVR) among the teams of other leagues too, for example the Liiga. It is not part of
  those leagues: the season plays with the league's own clubs.
- Multiplayer is a closed beta: the lobby trusts the name you give it, and a game between two separate PCs has not been
  played through yet.
- Lines you set by hand are not kept in My edits while Real lines and captains is on (as in beta4).
- The looser roster edits were checked in game on every NHL team at once (shared numbers, five letters, an empty and a
  doubled line place, cloned skaters): the roster loads, the hub runs and Play Now reaches team select. A full match
  with all of them together was not played before release.
