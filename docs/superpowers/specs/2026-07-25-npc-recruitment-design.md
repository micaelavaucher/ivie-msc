# NPC Recruitment / Party Mechanic — Design

Status: approved for planning
Date: 2026-07-25

## Context

IVIE has no existing notion of a party, recruitment, or mutable NPC relationship
state. `Character` (`src/ivie/core/world.py`) is a plain data holder (`name`,
`descriptions`, `location`, `inventory`, `interaction`) with no runtime state
that changes over the course of play — the only things in the whole codebase
that mutate over time are `World.puzzle_states`, `Location.visited`, and
`Hint.given`. The per-turn LLM update loop (`WorldUpdate`, produced by
`process_player_input_structured` in `game_logic.py`) can move items, unblock
passages, resolve puzzles, and move the player, but has no slot for relationship
or NPC-state changes — those only ever exist today as narration text with zero
mechanical effect.

The closest existing "task with completion state + reward" abstraction is
`Puzzle` (`proposed_by_character`, `rewards: List[PassageReward|ItemReward|ObjectiveReward]`,
tracked via `World.puzzle_states: dict[str, 'not_proposed'|'proposed'|'solved']`).
This design reuses that abstraction rather than inventing a parallel one.

Completability verification (`generation_pipeline.py`) is rule-based, not a
STRIPS/PDDL planner: `verify_location_connectivity` is a pure graph-reachability
DFS, and `verify_objective_completability` is a shallow existence/placement
check per objective type. There is no precondition-chain solver.

## Goals

- Let world generation flag a subset of NPCs as recruitable.
- Give recruitable NPCs a coarse "feeling toward the player" that can shift.
- Let the player recruit an NPC directly if feeling is already high enough, or
  via a challenge (existing Puzzle mechanism) if not.
- Let recruiting one NPC ripple to affect a small, fixed set of other NPCs
  (rival/ally) via a lightweight, symmetric tag — not a general relationship graph.
- Establish where all of the above plugs into the existing generation pipeline
  and verification stages, and confirm what (if anything) verification needs to
  change.

## Non-goals (explicitly deferred)

- Concrete "assist during quest" mechanics for what a party member actually
  does once recruited. Out of scope for this design; flagged as a follow-up.
- Crucial vs. helpful tiering of recruitable NPCs. Dropped — all recruitable
  NPCs are optional bonus content, never required to complete the objective.
- LLM-freeform feeling deltas from dialogue nuance. Feeling changes only
  through the discrete ripple mechanism (§3 below), never a per-turn LLM-proposed
  delta.
- Relationship tags beyond `rival`/`ally`, or a per-pair strength/magnitude field.
- A general NPC-NPC relationship graph, or asymmetric/directional reactions.

## 1. Data model

Recruitment fields go directly on `Character` (`world.py`) — there is no
separate "NPC" type in this codebase; NPCs are just `Character` instances that
aren't `world.player`.

```python
class FeelingLevel(str, Enum):   # ordered, low -> high
    HOSTILE = "hostile"
    WARY = "wary"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    DEVOTED = "devoted"

class Character(Component):
    def __init__(self, ..., recruitable=False, feeling=FeelingLevel.NEUTRAL,
                 recruited=False, recruitment_puzzle: Optional[str] = None):
        ...
        self.recruitable = recruitable                  # set at generation time, immutable at runtime
        self.feeling = feeling                           # mutated only by the ripple mechanism (§3)
        self.recruited = recruited                        # runtime flag, set by the recruit action (§2)
        self.recruitment_puzzle = recruitment_puzzle       # name of their challenge Puzzle, if any
```

`World` gains one field:

```python
self.npc_relationships: list[NPCRelationship] = []   # symmetric pair tags, see §3
```

"Party" is a derived view, not separately tracked state:
`party = [c for c in world.characters.values() if c.recruited]`.

There is no `crucial`/`helpful` tier. Recruitable NPCs are always optional —
this is what keeps §4 (verification) simple: recruiting an NPC can never gate
objective completion.

## 2. Feeling threshold & challenge condition

Recruiting NPC `X` (where `X.recruitable` and not `X.recruited`) succeeds when
either of two independent, disjunctive conditions holds:

```
X.feeling >= config.recruitment.feeling_threshold
    OR
world.puzzle_states[X.recruitment_puzzle] == 'solved'
```

There is no interaction between the two — feeling is never incremented by
solving the challenge puzzle, and the puzzle is not required if feeling is
already high enough. An NPC generated already at `FRIENDLY`/`DEVOTED` needs no
challenge at all; one generated at `NEUTRAL` or below needs `recruitment_puzzle`
set and solved.

This reuses the existing `Puzzle` / `puzzle_states` / `rewards` machinery
directly via a new reward type, added to the `PuzzleReward` union in
`structured_data_models.py`:

```python
class RecruitCharacterReward(BaseModel):
    character_name: str
```

resolved the same way `PassageReward`/`ItemReward` are today when a puzzle is
solved.

**Detecting "ask to recruit":** a new short-circuit stage in `game_logic.py`,
`check_recruitment_request(message, world)`, inserted into the game loop
alongside the existing `check_character_puzzle_mention` (same keyword/mention
detection pattern already used there for puzzle proposals). On a recruit-intent
message naming a recruitable NPC:

- Precondition above already true → set `recruited = True`, fire the ripple
  effect (§3), short-circuit with a success narration.
- Has an unsolved, unproposed `recruitment_puzzle` → propose it, reusing the
  existing puzzle-proposal short-circuit path verbatim (same as any other
  character-proposed puzzle).
- Puzzle already proposed but unsolved → fall through to the normal LLM turn
  loop; the existing puzzle-solving flow handles it exactly like any other
  puzzle.
- Neither condition is satisfiable yet (no puzzle defined, feeling below
  threshold) → short-circuit with a rejection narration.

Feeling is never mutated by dialogue or freeform LLM output — its only
mutation path is the ripple mechanism below.

## 3. NPC-to-NPC relationships (social ripple)

Minimal and flat — a list of tagged pairs, not a graph:

```python
class RelationshipTag(str, Enum):
    RIVAL = "rival"
    ALLY = "ally"

class NPCRelationship:   # plain class, stored on World, not duplicated per-character
    character_a: str
    character_b: str
    tag: RelationshipTag
```

Trigger: whenever a character becomes `recruited`, scan
`world.npc_relationships` for pairs involving them. For each counterpart NPC
still present in `world.characters`, shift their `feeling` one step on the
`FeelingLevel` ladder — up for `ALLY`, down for `RIVAL`, clamped at the ends
(`HOSTILE`/`DEVOTED`).

A single tag on an unordered pair covers both directions: recruiting either
member shifts the other's feeling using the same tag. If the counterpart is
later recruited too, nothing further fires (already-recruited NPCs are simply
not checked against the recruitment precondition again). No `strength` field,
no decay, no chained/transitive inference. Extending this later (e.g. adding a
strength int, or more tags) is additive, not a rework.

## 4. Impact on completability verification

Because recruitable NPCs are always optional, **`verify_objective_completability`
and `verify_location_connectivity` need no changes** — a recruitable-but-
unrecruited NPC is just a normal `Character` for existence/reachability
purposes, exactly as today. Dropping the crucial/helpful tier is what makes
this true: nothing about recruitment state can ever be load-bearing for the
objective.

The one real touch point is `verify_puzzle_rewards_and_fix`
(`generation_pipeline.py`), which already validates that `ItemReward`s
reference real items and auto-fabricates missing ones. It gets a parallel
branch for `RecruitCharacterReward`:

- `character_name` doesn't resolve to any generated character → treated as a
  generation error, triggers the existing retry-generation path. (Unlike
  missing items, a whole missing NPC should not be auto-fabricated.)
- Resolves, but that character's `recruitable` is `False` → auto-fix by
  flipping it to `True` (cheap, safe, same spirit as existing auto-repair for
  rewards).

That is the entire verification delta. It does not push the verifier toward
real precondition-chain planning — consistent with recruitment being strictly
optional.

## 5. Generation pipeline & config

- **Step 3 (Details)**: `GeneratedCharacter` (`structured_data_models.py`)
  gains `recruitable: bool = False` and `initial_feeling: FeelingLevel = NEUTRAL`.
  `GeneratedWorld` gains `npc_relationships: List[GeneratedRelationship] = []`,
  same shape as the runtime class (`character_a`, `character_b`, `tag`), so the
  LLM can tag rivalries/alliances between key characters it has already
  generated in the same step.
- **Step 4 (Puzzles)**: for any recruitable NPC generated below the feeling
  threshold, the LLM may add a puzzle proposed by that character whose reward
  is `RecruitCharacterReward` — no restructuring of the step, just a new
  reward option alongside the existing ones.
- **`world_builder.py`**: construction reads these new fields onto `Character`
  and `World.npc_relationships`, following the same pattern used for every
  other field today.
- **`config.ini`**: new `[Recruitment]` section, matching the existing
  string/range-value conventions used by `[Size_World]`/`[Models]`:

```ini
[Recruitment]
enabled = true
feeling_threshold = friendly
```

## Open questions for implementation planning

- Exact wording/detection approach for `check_recruitment_request` (keyword
  match vs. a small LLM classifier) — `check_character_puzzle_mention` should
  be reviewed as the precedent to follow or deviate from.
- Where `initial_feeling` and `npc_relationships` should be constrained during
  generation (e.g. should relationship tags only be allowed between two
  `recruitable` characters, or any two key characters?).
