# Transcript Review & Export

This project contains video transcripts from the YouTube channel **Gary's Economics**. The speaker is **Gary Stevenson**, a British former trader based in London who discusses economics, inequality, housing, and tax policy.

## Project goal

Produce reviewed, corrected versions of all transcripts in SRT format. The auto-generated VTT transcripts contain frequent errors (garbled words, mishearings, americanisms, dropped words). Each transcript needs to be reviewed and exported as a clean SRT file.

## Folder structure

- **`transcripts/`** — Auto-extracted transcripts. Each video has its own subfolder (named `YYYY-MM-DD-video-title`) containing a `transcript.vtt` and a `meta.json`.
- **`revisions/`** — All reviewed transcripts, organised by stage in the review pipeline. Filename format: `youtubeID__date_video_title.srt`.
  - **`revisions/0_agency_reviewed/`** — Transcripts reviewed by the agency. These serve as the gold standard for quality.
  - **`revisions/1_AI_reviewed/`** — AI-reviewed transcripts in SRT format. New AI-reviewed transcripts go here.
    - **`revisions/1_AI_reviewed/multi_speaker/`** — Transcripts with more than one speaker (e.g., interviews, panel appearances). These require human review to verify speaker identification.
  - **`revisions/2_To_be_reviewed_by_volunteers/`** — Corrections documents (`.md` files) for volunteers to review. This folder is shared with volunteers directly.
    - **`revisions/2_To_be_reviewed_by_volunteers/done/`** — Corrections documents that have already been reviewed by a volunteer. Moved here to avoid duplicate work.
  - **`revisions/3_volunteer_reviewed/`** — Transcripts that have been through both AI and volunteer review. These are ready for export.
  - **`revisions/TRANSCRIPT_STATUS.md`** — Tracks which transcripts have been reviewed and which are next. Consult this to find the next transcript to review.

## Review workflow

The full process for getting transcripts reviewed and into production:

1. **AI reviews the transcript** — The AI reviews the raw VTT transcript following the correction instructions below, producing a clean SRT file in `revisions/1_AI_reviewed/`.

2. **AI generates a corrections document** — The AI creates a `.md` file in `revisions/2_To_be_reviewed_by_volunteers/` with:
   - A link to the YouTube video at the top
   - The full transcript grouped into paragraphs of flowing text — **not** one line per cue
   - Each paragraph preceded by a single timestamp (`HH:MM:SS`) indicating where it starts in the video
   - Sentences are never split across paragraphs — keep whole sentences together, grouping by natural topic or paragraph breaks in the speech
   - Corrected or added **words** marked in bold, removed words in ~~strikethrough~~, unchanged text shown without markup
   - Do **not** bold added punctuation (commas, periods, etc.) — just insert it normally. Only bold word-level changes.
   - See `revisions/2_To_be_reviewed_by_volunteers/done/EiblHqbpXHs__2020-07-14_How_COVID-19_Makes_the_Rich_Richer.md` for an example.

3. **Volunteers review** — Volunteers watch the video, read along with the corrections document, and edit it where they spot issues. They send the edited file back (by email, most likely).

4. **AI incorporates volunteer revisions** — We place the edited files in a local folder and ask the AI to apply the volunteer's changes to the already-reviewed SRT transcript. The final result goes in `revisions/3_volunteer_reviewed/`.

5. **Export to chatbot repo** — The final reviewed SRT is copied to [`garyseconomics/chatbot/docs/video_transcripts/to_be_imported`](https://github.com/garyseconomics/chatbot/tree/main/docs/video_transcripts/to_be_imported).

## Exporting VTT to SRT

When asked to export a reviewed `.vtt` to `.srt`, apply these format changes:

1. Remove the `WEBVTT` header and any metadata lines (`Kind:`, `Language:`, etc.)
2. Add sequential cue numbers (1, 2, 3...) before each timestamp
3. Replace `.` with `,` in timestamps (e.g., `00:00:06.640` → `00:00:06,640`)
4. Replace `-->` with ` --> ` (SRT uses the same arrow format)
5. Strip `&nbsp;` entities from the text — SRT does not use them
6. Keep a blank line between each cue block
7. End the file with a blank line

## Reviewing a VTT transcript

When asked to review a `.vtt` file, first check `meta.json` for the `is_automatic_transcript` field. Auto-generated transcripts (`true`) require extensive correction — garbled words, missing punctuation, wrong capitalisation, and filler words throughout. Non-automatic transcripts (`false`) are typically already clean and may need only format conversion.

Read the entire file and fix the following categories of errors, ordered by importance:

### 1. Garbled words and mishearings

Auto-transcription often mangles proper nouns, economic terminology, and multi-word phrases into similar-sounding nonsense. These are the highest-priority fixes because they destroy meaning.

**Names are the most severely mangled category.** A single name can be garbled differently each time it appears. Always cross-reference names against `meta.json` (title, description) and common figures in UK politics and economics.

Examples of garbled names from past reviews:
- "Um Karma" / "Kisarma" / "Kistama" / "Karma" → "Keir Starmer"
- "Mark Cary" / "Mark car" → "Mark Carney"
- "British Senate" / "that" → "Rishi Sunak"
- "a golden sack" → "Goldman Sachs"
- "LSC" → "LSE"
- "Christian G Murphy" → "Krishna Guru-Murthy"
- "macaron" → "Macron"
- "Freriedman" → "Friedman"
- "the same bat" → "Usain Bolt"

Examples of garbled economic and political terms:
- "well through equality" → "wealth inequality"
- "how's price" → "house price"
- "living stands" / "living stand" → "living standards"
- "rates attack" → "rates of tax"
- "spread Bank platform" → "spread betting platform"
- "through the room" → "through the roof"
- "bifocated" → "bifurcated"
- "Co" / "Co model" → "COVID" / "COVID model"

Examples of other garbled phrases:
- "you w Inn anything" → "you won't own anything"
- "well our families" → "well off families"
- "Master economics" → "maths or economics"
- "pum" → "palladium"
- "10 million1 million p in assets" → "£10 million, £100 million in assets"

**How to catch these:** Read each sentence for meaning. If a phrase doesn't make sense in context, sound it out and figure out what was actually said. Pay special attention to:
- Names of politicians, economists, institutions, and think tanks (Keir Starmer, Mark Carney, Goldman Sachs, IEA, Bank of England, LSE, etc.)
- Economic terms (quantitative easing, fiscal policy, wealth inequality, national insurance, living standards, etc.)
- British place names, media outlets, and cultural references (Channel 4, LBC, GB News, Novara Media, etc.)

### 2. Punctuation

Auto-generated transcripts have little or no punctuation. Add punctuation to make the text readable:

- **Periods** at sentence boundaries. The auto-transcript often runs sentences together — split them with periods and capitalise the next word.
- **Commas** at clause boundaries, after introductory words ("So,", "Now,", "Today,"), around parenthetical phrases ("Dave, in the comments,"), in lists ("rent, mortgage, food, bills"), and before conjunctions joining independent clauses.
- **Question marks** on all questions ("Why are living standards collapsing?").
- **Ellipsis** (...) when Gary trails off mid-thought or pauses before changing direction ("if you go to... I mean,").
- **Quotation marks** around quoted speech or when Gary is voicing someone else's words ("Why don't you do something?").

### 3. British English

Gary is British. The auto-transcription sometimes americanises his speech.
- "mom" → "mum"
- "labor" → "Labour" (also a proper noun — always capitalised)
- "realize" → "realise", "recognize" → "recognise", "criticize" → "criticise"
- "depoliticizing" → "depoliticising", "systemized" → "systemised"
- "math" → "maths"

### 4. Missing or dropped words

Auto-transcription often drops small words that are needed for the sentence to be grammatically correct or faithful to what was said.
- Missing articles: "the media", "the other day"
- Missing prepositions: "was for younger generations" not "was the younger generation", "growth in inequality" not "growth inequality"
- Missing pronouns: "where I hope I'll convince you" not "where hope I'll convince you"
- Missing words that complete a phrase: "£500,000 flat in London" not "£500,000 in London"

### 5. Capitalisation

Auto-transcription frequently gets capitalisation wrong — capitalising common nouns mid-sentence and failing to capitalise proper nouns.

**Capitalise:**
- Sentence beginnings
- Politicians and public figures: Keir Starmer, Rishi Sunak, Mark Carney, Nigel Farage
- Political parties: Labour, Conservative, Reform (when referring to the party)
- Institutions: Bank of England, Goldman Sachs, LSE, Financial Times
- Titles of works and video titles: "The Rest Is Politics", "The Squeeze Out"
- Historical events: Second World War, COVID
- "Prime Minister" when used as a title

**Lowercase:**
- Common nouns the VTT incorrectly capitalises: trader, university, pub, boom, millionaire, financial, rising
- General adjectives: "modern age" not "Modern Age", "general concept" not "General concept"

### 6. Filler words and speech disfluencies

Remove filler words and speech disfluencies. The transcript should be clean and readable.

- **Remove** "um", "uh" throughout
- **Remove** stuttered repetitions: "this is this is not" → "this is not", "they can they can" → "they can", "I'm not I'm not talking" → "I'm not talking"
- **Remove** stuttered words: "and and you will" → "and you will", "of of the rest" → "of the rest"
- **Keep** "you know" only when it functions as a rhetorical aside, and set it off with commas: "you know,"
- Use informal contractions when spoken: "wanna" not "want to", "gonna" not "going to" — but only where they were clearly spoken that way

### 7. Formatting

**Currency:** Add the £ symbol where Gary is clearly talking about British pounds: "10 million" → "£10 million", "100,000" → "£100,000".

**Numbers:** Spell out small numbers in running speech where it reads more naturally: "5 years" → "five years". Keep large or precise figures as digits: "£500,000", "90%".

**Hyphens:** Use hyphens for compound modifiers and standard compounds: left-wing, far-right, working-class, well-funded, loss-making, UK-specific, hand-wringing.

**"the Beatles" rule:** Lowercase "the" in band/organisation names when it's part of running text: "the Beatles", "the Financial Times", "the Bank of England".

### 8. Minor phrasing accuracy

- "right" vs "alright" — use whichever was actually spoken
- "cause" vs "because" — use the informal version if that's what was said
- Preserve the exact phrasing even if grammatically imperfect — this is speech, not writing

### 9. Speaker identification

Some videos feature guests — interviews, podcast appearances, or panel discussions. Identify whether the transcript has more than one speaker.

**How to detect multiple speakers:**
- Check `meta.json` for clues: the `fulltitle` and `description` often name guests or hosts (e.g., "Gary on LBC with Tom Swarbrick", "Gary on Novara Media with Michael Walker").
- Read the transcript for conversational patterns: questions followed by answers, changes in perspective or tone, introductions ("thanks for joining us"), and turn-taking cues.

**If the transcript has multiple speakers:**
- Add speaker labels to each cue using the format `[Speaker Name] text goes here`. Use the speaker's real name when known from `meta.json`, or `[Host]`/`[Guest]` as a fallback.
- Gary Stevenson should always be labelled as `[Gary]`.
- Place the reviewed file in `revisions/1_AI_reviewed/multi_speaker/` instead of `revisions/1_AI_reviewed/`. These files need human review to verify that speaker turns are attributed correctly.

**If the transcript has only one speaker (Gary):** no labels are needed.

### 10. End-of-video fragments

YouTube videos often include short preview clips of other videos at the end (the "watch next" end screen). These appear in the transcript as disconnected fragments after the main video content ends — typically after a natural sign-off or closing statement. **Remove these cues entirely.** They are not part of the video's actual content.

**How to spot them:** Look for an abrupt topic change or jump in timestamps near the end of the transcript, especially after the speaker has clearly wrapped up (e.g., "let's make things change," "share the message"). The fragments often lack context and may reference completely different subjects.

### General principles

- **Do not change timestamps.** Only fix the text content.
- **Do not reformat or restructure cues.** Keep the same cue boundaries.
- **Preserve `&nbsp;` spacing** if present in the original VTT.
- **When uncertain, prefer the reading that makes more semantic sense** in the context of economics and British current affairs.
- **Read surrounding context** before correcting — a word that looks wrong in isolation may make sense in the full sentence across cue boundaries.

