# Character Behavior Model

> Status: DRAFT v0.1 — pending review
> Scope: how a character's *personality* influences generated scenes, and how
> composite pose/expression are assembled from the tag library.
> Relationship: extends `Scene Specification v1.0` (§5 Override System),
> `Scene Model` (relationship graph), and `Coverage Engine` (balancing weights).

---

## 1. Purpose

The program is a tool for **describing a character**; the engine's job is to
*translate that description into scenes*. The user thinks "she is shy and quiet",
not "I need more `shy` tags for LoRA". Therefore:

- The **Character Profile** is the source of truth for *what is canonical for this
  character* (appearance, wardrobe, personality).
- The engine must let personality influence **expressions, poses, and actions** —
  not only wardrobe, as it does today (see §9 Implementation Status).

This document defines the data model and engine contract for that influence.

---

## 2. Sources of Truth (hierarchy)

Consistent with `Scene Specification v1.0` §5.1. Four sources contribute to a
final scene; they do **not** replace each other — they *multiply* (see §6):

| # | Source | Role | Lives in |
|---|--------|------|----------|
| 1 | **Scene Rules** | Laws of the *world*: what is physically/logically possible (no swimsuit in a library, cooking only in a kitchen). Hard filters. | `scene-rules/*.toml` |
| 2 | **Character Profile** | Laws of the *character*: what is canonical for this person. Narrows the world down to the character via **weights and bans**. | `character-profiles/*.yaml` |
| 3 | **Run Config / UI Overrides** | The *director's* order for one session. Highest priority; may override 1 and 2 intentionally. | UI flags (`force_tags`, `ignore_*`, `validator_mode`) |
| 4 | **Coverage Engine** | *Dataset balancing*: boosts under-represented categories to close gaps. Affects selection **probabilities**, not permissibility. | `coverage_tracker.py` |

**Character personality is part of source #2.** It is *not* part of the Coverage
Engine: Coverage answers "the dataset lacks library scenes, generate more",
personality answers "this character rarely shouts". They are orthogonal and
multiply (§6).

---

## 3. Tag Library as Slots

### 3.1 Principle

The tag library (`prompt-library/`) is a **dumb, open vocabulary**: plain `.txt`
files, one tag per line. It carries **no logic**. The user may add any tag at any
time, and the program must pick it up everywhere automatically (UI included).

Logic lives **outside** the library:
- **Structure** (which slot a tag belongs to) = the *file/folder* it sits in.
- **Relationships** (conflicts/requires/prefers between tags) = `scene-rules`.

### 3.2 Slots

A *slot* is one aspect of the scene that takes **exactly one tag**, chosen from
one library file. The library is already structured this way:

| Domain | Slot | Library file |
|--------|------|--------------|
| Pose | `base` | `03_pose/base.txt` |
| Pose | `head` | `03_pose/head.txt` |
| Pose | `arms` | `03_pose/arms.txt` |
| Pose | `legs` | `03_pose/legs.txt` |
| Face | `mood` | `05_expression/mood.txt` |
| Face | `eyes` | `05_expression/eyes_expr.txt` |
| Face | `mouth` | `05_expression/mouth.txt` |
| Action | `action` | `04_action/*.txt` |
| Atmosphere* | `lighting` | `07_lighting/*.txt` |
| Atmosphere* | `weather` | `10_weather/*.txt` |

\* Atmosphere axis is **optional** and can be disabled per profile (§5.4).

### 3.3 Tolerance to unknown tags

A tag with **no** described relationships simply participates in random selection
for its slot, without special constraints (graceful degradation). It is "counted
everywhere" (slot pool, UI, coverage) the moment it is added to a file. Fine
consistency appears only where relationships are explicitly described.

---

## 4. Composite Pose & Expression

### 4.1 Pose = base + head + arms + legs

`Scene.pose` becomes a composite of four slots instead of a single string.
One tag is chosen per slot. This lets the engine keep components mutually
consistent (e.g. `arms` cannot be both `in pockets` and `holding object`).

### 4.2 Face = mood + eyes + mouth

The current single `Scene.expression` string is replaced by a composite face:
three slots (`mood`, `eyes`, `mouth`), one tag each. Consistency between them
(e.g. `open mouth` → `screaming`, not `gentle smile`) is enforced by
relationships (§7), not by chance.

### 4.3 Prompt assembly

In `to_structured_prompt`, composite fields are flattened into the prompt as a
comma-joined list (order: base → legs → arms → head for pose; mood → eyes → mouth
for face), exactly as `outfit_*` and `props` are today.

---

## 5. Character Personality Model

### 5.1 Weights over slots

Personality is a set of **weights and bans over slot tags**. For each slot, the
profile assigns a weight to individual tags:

- `prefer` → high weight (boost).
- `avoid` → weight ≈ 0 (soft ban; the world's hard `EXCLUDES` still wins).
- unmentioned → neutral default weight.

### 5.2 Modes (for complex characters)

A character may have **multiple modes**, each with its own weight vector, and a
switching probability between scenes. This expresses cases a single slider cannot:

- **Stable** character = one mode, narrow weights.
- **Variable** character = one mode, wide/flat weights.
- **Bipolar** character = two modes (`up`, `down`), each with peaked weights,
  switching with some probability per scene.

A mode is the unit of weight vectors. "Normal" = one mode; complexity = more modes.

### 5.3 Axes

Each mode carries weight vectors for these axes:
`expression` (mood/eyes/mouth), `pose` (base/head/arms/legs), `action`,
and optionally `atmosphere`.

### 5.4 Atmosphere axis (optional)

Personality may bias lighting/weather (a quiet character → soft light, rain,
muted tones). This axis is **off by default** and toggleable per profile, to keep
the base version simple.

### 5.5 UI layers (base vs extended)

The data model is always the full weight-vector model. The UI is a *layer* over it:

- **Base layer**: archetype + 3–4 trait sliders (e.g. reserved↔open,
  calm↔expressive, gentle↔fierce). A slider is a **preset/macro** that writes the
  weight vector under the hood.
- **Extended layer**: a "show what's under the hood" mode exposing the editable
  weight vector per slot, plus mode management (add mode, switching probability).

This split lets us ship a simple base version and keep power without two data
models. (Base/extended separation is finalized closer to release.)

---

## 6. Integration into the Scene Builder

### 6.1 PreferenceResolver

A new component that, for each slot, resolves the final per-tag weight from all
sources. Replaces the current ad-hoc selection blocks in `build_scene`.

### 6.2 Final weight formula

For each candidate tag in a slot:

final_weight(tag) =
character_weight(tag | active_mode) # source 2: personality
× world_filter(tag | location, action) # source 1: scene rules (hard ban = 0)
× coverage_weight(tag) # source 4: dataset balancing

- `avoid` in personality → `character_weight ≈ 0` → tag never chosen (0 × anything = 0),
  regardless of coverage. This is intentional: character canon is not overridden by balancing.
- `prefer` → `character_weight > 1` (boost), consistent with the existing world
  idiom (`avoid_*` × 0.1, `preferred` × 3–5 already in `build_scene`).
- Run Config overrides (§2, source 3) are applied last and may force/exclude tags
  directly, bypassing the formula.

### 6.3 Mode selection

At the start of each `build_scene` call, the active mode is sampled from the
profile's modes by their `weight` (switching probability). Then §6.2 runs for
that mode.

### 6.4 Slot selection

For each slot, the engine samples **one** tag from the slot's pool using the
final weights (weighted random), then the validator (§7) checks cross-slot
consistency and rejects the scene if violated (regeneration loop, as today).

---

## 7. Consistency Rules

### 7.1 Where relationships live

Cross-slot relationships (`conflicts` / `requires` / `prefers`) are described in
`scene-rules` (TOML), **not** in the library. This is a first implemented subset of
the relationship graph from `Scene Model` (REQUIRES/EXCLUDES/PREFERS).

### 7.2 Examples

```toml
# scene-rules/relationships/pose.toml
[pose.arms]
"hands in pockets" = { conflicts = ["holding object", "holding cup", "holding book"] }
"holding object"   = { conflicts = ["hands in pockets", "arms crossed"] }

[pose.base_to_legs]
"lying"  = { prefers = ["legs together", "knees up"], conflicts = ["standing on one leg"] }
"sitting" = { conflicts = ["legs spread wide"] }

# scene-rules/relationships/face.toml
[face.mood_to_mouth]
"peaceful" = { prefers = ["gentle smile", "soft smile"], conflicts = ["open mouth", "screaming"] }
"angry"    = { prefers = ["frown", "clenched jaw"], conflicts = ["gentle smile"] }

```

### 7.3 Priority Rules

Some consistency is expressed as priority, not enumerated pairs, so it works
for any tag:
- Prop dictates arms: if a holding X prop is present, the arms slot is
reserved for a holding-compatible tag; hands in pockets cannot be drawn.
- Action dictates pose/face: actions carry prefers_pose_* / prefers_face_*
(extending the existing prefers_poses / prefers_expressions in action TOMLs).

### 7.4 Validator

validate_scene gains cross-slot checks for composite pose and face, using §7.2
relationships. Invalid combinations are rejected and regenerated (existing loop).
This also activates the currently dead camera → pose check (it reads
scene.pose, which does not exist yet — §4 adds it).

## 8. Profile Format

The old flat expression_filter / pose_filter lists are deprecated (§10).
New personality block:

```toml
personality:
  modes:
    - id: default
      weight: 1.0                      # mode probability (single mode = 1.0)
      axes:
        expression:
          mood:  {shy: 0.8, gentle_smile: 0.6, looking_away: 0.5, shouting: 0.0}
          eyes:  {looking_away: 0.6, downcast_eyes: 0.5}
          mouth: {gentle_smile: 0.6, soft_smile: 0.4}
        pose:
          base:  {sitting: 0.7, standing: 0.3, lying: 0.2}
          arms:  {hands_in_lap: 0.5, holding_book: 0.3, hands_in_pockets: 0.0}
          legs:  {legs_together: 0.5, knees_up: 0.3}
        action:
          {reading: 0.8, studying: 0.6, running: 0.05, shouting: 0.0}
        # atmosphere:                  # optional, off by default
        #   lighting: {soft_light: 0.7, window_light: 0.5}
        #   weather:  {rain: 0.4, overcast: 0.4}
  presets_applied: [quiet_intellectual]   # which macros wrote the vectors (for UI)
  ```

A bipolar character adds up / down modes with weight: 0.5 each.

## 9. Implementation Status

| Piece | Status |
| :--- | :--- |
| Wardrobe whitelist influences outfit | ✅ Implemented (`_choose_smart_outfit`) |
| `fixed_traits` / `character_trigger` in prompt | ✅ Implemented |
| Coverage weights (location/action/weather/camera/outfit) | ✅ Implemented |
| World soft-weight idiom (`avoid_*` ×0.1, `preferred` ×N) | ✅ Implemented |
| `Scene.pose` (composite base/head/arms/legs) | ⬜ To add |
| Composite face (mood/eyes/mouth) replacing single `expression` | ⬜ To add |
| `config_loader` reads personality block | ⬜ To add |
| `PreferenceResolver` (character × world × coverage) | ⬜ To add |
| Mode selection / switching | ⬜ To add |
| Cross-slot relationships in `scene-rules` + validator checks | ⬜ To add |
| Atmosphere axis (optional) | ⬜ To add (toggleable) |
| Relationship graph / Dynamic Seeding / Visibility Model (from `Scene Model`) | ⏳ Planned (north star; this work implements the slot-relationship subset) |

## 10. Migration

The program is pre-release with a single user. The old expression_filter /
pose_filter flat-list format is deprecated and not migrated. Existing
profiles (Luna.yaml, 1111test.yaml) will be rebuilt against the new
personality block. No import path is provided; old fields are dropped.

## 11. Open Questions

1. Exact default neutral weight for unmentioned tags (1.0? configurable?).
2. Weight scale/clamping for character weights (mirror Coverage's 0.05–0.15 caps,
or a separate range to keep avoid a true zero?).
3. Whether prefers_face_* / prefers_pose_* in action TOMLs are authored now or
deferred (validator + priority rules may cover most cases initially).

---

