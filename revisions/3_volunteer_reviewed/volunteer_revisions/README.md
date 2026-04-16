# Volunteer Revisions

This folder holds the edited corrections documents that volunteers send back, plus the per-transcript `*__volunteer_changes.md` review files generated when applying their edits.

## Volunteer markup conventions

One of the volunteers wraps their edits in slashes (in their own words):

> If I've taken something out, it'll be surrounded by back slashes `\\like this\\`, if I've added something in, it'll be surrounded by forward slashes `//like this//`.

So in their files:
- `\\removed text\\` — text the volunteer removed (back slashes)
- `//added text//` — text the volunteer added (forward slashes)

These are layered on top of the AI's existing `~~strikethrough~~` (removed) and `**bold**` (added) markup from the corrections document. When applying volunteer edits:
- A `\\…\\` span around an AI bold (`\\**word**\\`) means the volunteer is reverting the AI's correction.
- A `//…//` span inside running text is a fresh volunteer addition.

## Other conventions seen from this volunteer

- `{incomprehensible}` (curly brackets) — used when two speakers talk over each other and a word can't be made out.
- They preserve "gonna" / "wanna" rather than expanding to "going to" / "want to" when that's what was actually said.
- They will punch in the second speaker's words after the first speaker's, even when the audio is simultaneous, to keep turns readable.
