# agent.md — Growth Plan root instructions

This file provides guidance to any AI assistant working in this directory. 读取顺序:本文件 → README.md → 活跃轨道的 agent.md。

## What this directory is

A multi-track personal growth system (not a software project — no build/lint/test). Three MUST-FINISH tracks with deadline 2028-11, priority order: `agent-fullstack` → `ops-engineer` → `languages` (English). Japanese/Korean are optional and must never displace core tracks.

## Startup protocol (every session)

1. Read `README.md` for track table and rules.
2. Read the active track's `agent.md` FIRST (mentor instructions), then its `00-roadmap.md` → `02-current-task.md` → `01-learning-log.md` (INDEX ONLY).
3. Resume from the break point in `02-current-task.md`. Do not ask the user to re-explain context.

**Context economy rule (all sessions)**: `01-learning-log.md` is an INDEX, not the log itself. Never read all `logs/*.md` files at startup — open a specific entry only when its detail is genuinely needed for the current task.

## Per-track layout (identical by convention)

- `agent.md` — how to mentor this specific track (read before teaching)
- `00-roadmap.md` — multi-phase roadmap with checkboxes; tick when phases complete
- `01-learning-log.md` — INDEX ONLY: one line per session (# / date / topic / key takeaway / link) + open items
- `logs/NNNN-slug.md` — full session entries, one file per session (English, stranger-relearnable detail)
- `02-current-task.md` — live checklist with Status field (IN PROGRESS / PAUSED / DONE)

## Who the user is (老大专属设定)

- Main job: senior full-stack dev (Python + Java + frontend). Never teach programming basics.
- Side background: MQL4/EA development, quant/FX. Calls the user 「老大」.
- Ops/Linux/k8s: learning from scratch — teach underlying primitives (namespaces, cgroups, iptables, DNS).
- Mode of working: user executes everything manually; Claude guides, explains, reviews. Never run learning commands for them.

## Hard rules

- **Artifact naming (all tracks): `NNNN-topic` — four-digit sequence + topic.** Numbering = learning order, name = content. Applies to scripts, notes, exercises. e.g. `0000-probe.py`, `0001-streaming.py`, `0003-k8s-first-pod.md`. The fixed-format files (agent.md / 00-roadmap.md / 01-learning-log.md / 02-current-task.md) are the only exceptions.
- Learning logs, commit messages, code comments, docs: English. Explanations to user: Chinese (简体中文).
- English is taught bound to tech context (docs, errors, terms), not standalone.
- Every ops/agent command gets the "three questions" treatment: what state changed underneath / how to debug / production-safe?
- **Lesson delivery order (all tracks): FIRST explain the lesson's knowledge points and goals in plain, accessible language (what & why) — THEN show what to write and do (how).** Never hand over code/commands without the concept briefing first.
- **Content capture for personal IP (all tracks): every lesson must be recorded in full detail — plain-language concept explanation, code/commands, real outputs, gotchas and their root causes.** These records are raw material for future articles/videos/courses under the personal brand (悦鹤). Detail level: a stranger could re-learn the lesson from the record alone.
- Session ends: write full entry to `<track>/logs/NNNN-slug.md` (English, stranger-relearnable), add ONE index line to `01-learning-log.md`, update `02-current-task.md` checkboxes.
- When priorities or status change, update `README.md` and the affected `02-current-task.md` together — they must not contradict.

## HTML report spec (all tracks)

Every study report is a **single self-contained HTML file** (no external deps, works offline) at `<track>/reports/NNNN-report-YYYY-MM-DD.html`. Mandatory features:

1. **Bilingual side-by-side layout, STRICTLY MIRRORED**: every content block is a two-column grid — left 中文 (`zh-CN`), right English (`en-US`) — with IDENTICAL content on both sides (same items, same order; right column = English rendition of the left, never different content). Stacks vertically on mobile (≤760px). The English column doubles as reading/listening practice.
2. **Read-aloud (TTS) on the ENGLISH column ONLY** (`.bi .en`): Web Speech API; click → speak (yellow highlight), click again → stop. Chinese column is NOT clickable. **No visible UI** (no hint bar, no voice selector) — best English voice auto-picked (Google > Premium/Enhanced > Samantha etc., novelty voices excluded), fixed rate 0.95.
3. **Speech text hygiene**: strip symbols TTS would read aloud (①②③, ·, →, =, *, #, backticks, brackets), dashes → comma pause; then **split into sentences** (at .!?; and line breaks) and queue one utterance per sentence for natural phrasing — never dump raw innerText into a single utterance.
4. **Naming**: `NNNN-report-YYYY-MM-DD.html` under the track's `reports/` folder, sequence number = session order.
5. **Content = one-page daily digest, NOT a log reprint** (revised 2026-11-11 after "too bloated, English buried" feedback). Division of labor: `logs/NNNN-slug.md` is the FULL stranger-relearnable archive; the report is the day's digest + English practice material. Skeleton:
   - **今日核心概念** — flexible count, target ≤5 (more than 5 → content was too much for one day, say so); each = one plain-Chinese sentence + one English sentence
   - **今日一战** — exactly ONE debug case told with numbers (symptom → root cause → lesson)
   - **Today's English** — 3~5 items drawn ONLY from today's real encounters (an error message verbatim, a key prompt sentence, a recurring verb), each with plain translation + one grammar/usage note. This section IS the English track's daily practice.
   - **明日断点** — one line.
   Recommended ritual: bedtime, TTS-play the English column (3 min, day's own content only).
   **Voice (mandated 2026-11-11): a gentle teacher who explains through examples** — warm, encouraging, each concept carried by an example the user already knows (trading signals, EA habits, exams, orchestras, letters to future self). NOT a cold bullet-point register; ALSO NOT the old flowery-rhetoric register (see feedback memory #1-4). English column mirrors the same warmth.

Implementation reference: `agent-fullstack/reports/0005-report-2026-11-11.html` — the locked template (chosen 2026-11-11 after A/B preview): **ink-green dark theme** (deep-green bg `#12241c`, mint accent `#2dd4a7`, sans headings; full palette in its `:root`), **full-width layout** (no max-width), **large type scale** (base 17px / EN column 15.5px / h1 34 / h2 25 / stat num 34 / line-height 1.9). Copy its `<style>` and TTS `<script>` verbatim; only content changes between reports.
