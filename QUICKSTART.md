# Quick start

**OVERTIME** is a standalone app for Windows, Linux, Steam Deck and Mac that plays **NHL 19** on your PC and brings it back online and up to today:
community servers, World of CHEL, Versus, Shootout and Threes, Seattle and Utah, the 2026-27 rosters and calendars,
and a full roster editor. A free community project, brought to you by [Puck Peak](https://www.puckpeak.com).

## You need

- Windows 10 or 11 (Linux, Steam Deck and Mac: [below](#linux-steam-deck-and-mac)), a graphics card that runs
  NHL 19 in shadPS4, and about 10 GB of free memory while playing.
- Your own NHL 19: **CUSA11126 with update 1.60**, as a game folder or as the game PKG plus the 1.60 update PKG.
  The app refuses other versions.
- Nothing else: the app downloads the emulator it plays on. A shadPS4 you already have works too.

## Set up (once)

1. Download `OvertimeNHL19.exe` from the [release page](../../releases/latest) and start it. Windows SmartScreen warns
   because it is not signed: choose **More info**, then **Run anyway**.
2. **Setup → Find game**: pick NHL 19's `eboot.bin`, or the game PKG. From a PKG the app installs the game into a new
   folder next to it; pick the 1.60 update PKG too and it goes beside the game.
3. The app then downloads the packs by itself (photos and logos, kits and gear, rinks: about 650 MB). When they
   are in, **Game patch**: press **Patch** and leave the switches as they are (every one is on; switch off what
   you do not want). Wait until it says "Patched".
4. Optional: **Setup → Boost performance** picks the emulator build (Overtime Native is the default), the
   resolution and the frame rate. **Settings** there maps your controller or keyboard.

## Linux, Steam Deck and Mac

The steps above are the same; only the download and the first start differ. The app checks your system on the
Setup tab and says what is missing.

- **Linux**: download `OvertimeNHL19-x86_64.AppImage`, make it executable (its Properties > Permissions, or
  `chmod +x OvertimeNHL19-x86_64.AppImage`) and start it. It needs glibc 2.39 or newer (Ubuntu 24.04, Fedora 40
  or newer), a Vulkan graphics driver and a 64-bit Intel (4th generation or newer) or AMD Ryzen CPU. The first
  time, the app offers to put itself in your app menu. The AppImage updates itself.
- **Steam Deck**: the same AppImage, in Desktop Mode (SteamOS 3.6 or newer). To play in Gaming Mode, open Steam in
  Desktop Mode, choose Games > Add a Non-Steam Game to My Library and tick the app; it is then in your Library
  under Non-Steam. No Deck has run it for us yet: tell us how it goes on the Discord.
- **Mac**: download `OvertimeNHL19-macos.dmg`, open it and drag the app to Applications. It needs macOS 26 or
  newer. The app is not signed, so macOS blocks the first start: open System Settings > Privacy & Security and
  press **Open Anyway** (macOS can ask again after an update). On a Mac with an Apple chip the app offers to
  install Apple's Rosetta, which the emulator needs (a minute, no restart). The app tells you when a new version
  is out; download the new dmg.
- Online, Linux and Mac players meet Windows players.

## Play

- Press the green **Play NHL 19** button at the top right. The first press downloads the emulator.
- **Offline**: Seattle and Utah are in Play Now, Be a Pro and the 32 Team Expansion Draft Franchise.
- **Online**: on the **Multiplayer** tab, sign in or sign up for ShadNet (free, once). Then in the game press PLAY in
  World of CHEL, Online Versus, Shootout or Threes. The game downloads the current online roster when yours is older.
- **Lobbies**: on the Multiplayer tab, one player creates a lobby and shares the code, the other joins with it. The
  host picks Versus, Shootout or Threes and the rules, both press **Ready**, and the app starts the game.

## Edit your roster

- **Update**: brings a roster up to today's NHL from NHL.com.
- **Roster, Lines, Strategy, Jerseys & gear, Front office**: change players, lines, strategies, jerseys, gear and
  contracts, and sign free agents. **Save** writes a new roster save (or updates the one you picked, after a backup).
- Save warns about unusual edits (two players with one number, more than three letters, an empty spot in the lines)
  and saves anyway. It stops only what would corrupt the roster or crash the game.

## Undo

Press **Unpatch** on the Game patch tab. NHL 19 is back as it was. Your game files were never changed.

## Help

Come to the Puck Peak Discord: **[gg.puckpeak.com](https://gg.puckpeak.com)**.
