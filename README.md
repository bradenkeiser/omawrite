# Omawrite

A dead-simple Markdown writing app built with Qt Quick and C++ that automatically follows system dark/light mode.

<img width="2948" height="3227" alt="screenshot-2026-06-23_15-24-08" src="https://github.com/user-attachments/assets/4e930c0d-edda-4046-b444-a59eff523329" />
<img width="2948" height="3227" alt="screenshot-2026-06-23_15-23-23" src="https://github.com/user-attachments/assets/8ced7c26-961b-4ded-b263-84403001a951" />


## Install

Install via the Omarchy Package Repository via the `omawrite` package. It's installed by default in new installations of Omarchy (from Quattro forward).

## Shortcuts

- `Ctrl+S` saves. Unsaved documents use the XDG desktop portal file picker.
- `Ctrl+Shift+S` saves as.
- `Ctrl+O` opens a Markdown file through the portal picker.
- `Ctrl+P` opens the system print dialog.
- `Ctrl+N` opens a new Omawrite window.
- `Ctrl+Z`, `Ctrl+Shift+Z`, and `Ctrl+Y` handle undo and redo.
- `Super+F` toggles fullscreen. Qt maps this key as `Meta+F`.
- `Ctrl+F` searches the document. Use `Enter` or `Ctrl+G` for the next match and `Shift+Enter` for the previous match.
- `Ctrl+H` opens find and replace.
- `Ctrl+B`, `Ctrl+I`, and `Ctrl+K` insert bold, italic, and link Markdown.
- `Ctrl+?` shows the keyboard shortcut reference.

Unsaved drafts are recovered after an abnormal exit. Omawrite also watches open files
and warns before an external change can replace local work.

The font button in the footer picks the writing font from any installed text font,
and Omawrite remembers the choice. IBM Plex Mono is the default.

Text follows the desktop text size — `omarchy display text size`, or GNOME's
`text-scaling-factor` — and re-flows without a restart. The default of 12px leaves
Omawrite at the size it is designed around; larger and smaller sizes scale from there.

## Requirements

- Qt 6: `qt6-base`, `qt6-declarative`, `qt6-quickcontrols2`
- `xdg-desktop-portal` and a portal backend

The IBM Plex Mono font is bundled under the SIL Open Font License 1.1; see
`fonts/OFL.txt`. The font is copyright IBM Corp.

## Saving to Joplin or Obsidian

Start a document with a header line and Ctrl+S saves it to a Joplin notebook or an Obsidian folder instead of a local file:

```
jop - mus - pol                      → Joplin › musings › polished
jop - hl - eng                       → Joplin › homelab › elec_eng
obs - aidea - [VPC peering notes]    → Obsidian › AWS_IDEA › VPC peering notes.md
```

- `jop` or `obs` picks the app; each following part is one folder deeper, separated by `-`, `/` or spaces.
- `[title]` sets the note title; otherwise the first `# heading` is used, else a timestamp.
- The header line is stripped from the saved note. Edit the header and save again to move the note.
- Each part is matched against the folders at that level: an alias, the exact name, a prefix (`mus`), word prefixes (`aidea` → AWS_IDEA), then letters in order (`hl` → homelab). A tie is refused rather than guessed.
- Folders are only created when written as `+name` (`jop - hl - +eng`).
- An existing note with the same title is never overwritten.
- The footer shows the resolved destination, or why it can't resolve, as you type the header.

Joplin is reached through its Web Clipper service on `localhost:41184`. The API token is read from `OMAWRITE_JOPLIN_TOKEN`, else the macOS Keychain (`security add-generic-password -a joplin -s omawrite-joplin -w <token>`), else `secret-tool lookup service omawrite-joplin`. The Obsidian vault is the open vault listed in Obsidian's `obsidian.json`, or the `obsidian/vault` setting. Aliases live in the settings file under `[aliases/joplin]` and `[aliases/obsidian]`, e.g. `songs=tunestolearn`.

### Building on macOS

```sh
brew install qt
mkdir build && cd build
$(brew --prefix qt)/bin/qmake CONFIG+=sdk_no_version_check ../omawrite.pro && make
open omawrite.app
```
