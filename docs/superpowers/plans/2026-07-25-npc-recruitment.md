# NPC Recruitment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let world generation flag a subset of NPCs as recruitable, give them a coarse feeling toward the player, let the player recruit them (directly if feeling is high enough, or via a reused Puzzle challenge otherwise), and let a small, sparse set of rival/ally tags between NPCs ripple a recruitment into other NPCs' feelings.

**Architecture:** Extends the existing incremental generation pipeline (`GeneratedCharacter`/`GeneratedWorld` Pydantic models → `create_world_from_llm_response` → runtime `World`/`Character`) with new recruitment fields, and extends the existing `Puzzle`/`puzzle_states` reward machinery with a new `RecruitCharacterReward` type instead of building a parallel task system. A new short-circuit stage in the game loop (mirroring the existing `check_character_puzzle_mention`) detects "ask to recruit" intent.

**Tech Stack:** Python 3.12, Pydantic v2 (`structured_data_models.py`), `configparser`, pytest (newly introduced — see Global Constraints).

**Spec:** `docs/superpowers/specs/2026-07-25-npc-recruitment-design.md`

## Global Constraints

- No crucial/helpful tier — every recruitable NPC is optional; recruitment must never gate `verify_objective_completability`.
- Feeling is a 5-step ordered `FeelingLevel` enum (`hostile < wary < neutral < friendly < devoted`), mutated ONLY by the relationship-ripple mechanism — never by freeform LLM/dialogue deltas.
- Recruiting NPC X succeeds when `X.feeling >= feeling_threshold` OR `X`'s dedicated challenge `Puzzle` is solved — these are independent, not sequential (solving the puzzle never increments feeling; high feeling never requires the puzzle).
- `npc_relationships` is a flat, sparse list of symmetric `rival`/`ally` tags — most NPC pairs have no entry, and that is the expected, correct state, not missing data.
- The narrator must never invent a social reaction between two characters that have no relationship tag; it may only reflect tagged pairs.
- This repo has no test infrastructure yet — Task 1 introduces pytest. All new logic must ship with tests using it.
- This repo has no packaging config; modules are imported as `from src.ivie...` (see `examples/example_worlds.py:8`), assuming the repo root is on `sys.path`. Tests must work with that same import style.

---

### Task 1: Test infrastructure + recruitment schema (Pydantic models)

**Files:**
- Create: `pytest.ini`
- Modify: `requirements.txt`
- Modify: `environment.yml`
- Modify: `src/ivie/llm/structured_data_models.py`
- Test: `tests/llm/test_structured_data_models.py`

**Interfaces:**
- Produces (used by later tasks):
  - `FeelingLevel(str, Enum)` — members `HOSTILE`, `WARY`, `NEUTRAL`, `FRIENDLY`, `DEVOTED` (`src/ivie/llm/structured_data_models.py`)
  - `RelationshipTag(str, Enum)` — members `RIVAL`, `ALLY`
  - `RewardType.RECRUIT_CHARACTER` new enum member (value `"recruit_character"`)
  - `RecruitCharacterReward(PuzzleReward)` — field `character_name: str`
  - `GeneratedRelationship(BaseModel)` — fields `character_a: str`, `character_b: str`, `tag: RelationshipTag`
  - `GeneratedCharacter.recruitable: bool` (default `False`)
  - `GeneratedCharacter.initial_feeling: FeelingLevel` (default `FeelingLevel.NEUTRAL`)
  - `GeneratedWorld.npc_relationships: List[GeneratedRelationship]` (default `[]`)
  - `GeneratedPuzzle.rewards: List[Union[PassageReward, ItemReward, ObjectiveReward, RecruitCharacterReward]]`
  - pytest is runnable from repo root as `pytest tests/... -v` with `from src.ivie...` imports working.

- [ ] **Step 1: Add pytest to dependencies**

Edit `requirements.txt`, append a line:
```
pytest==8.3.4
```

Edit `environment.yml`, add to the `pip:` list:
```yaml
      - pytest==8.3.4
```

- [ ] **Step 2: Add pytest.ini so `from src.ivie...` imports resolve**

Create `pytest.ini` at the repo root:
```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 3: Install pytest**

Run: `pip install pytest==8.3.4`
Expected: installs successfully (or is already satisfied).

- [ ] **Step 4: Write the failing tests**

Create `tests/llm/test_structured_data_models.py`:
```python
from src.ivie.llm.structured_data_models import (
    FeelingLevel,
    RelationshipTag,
    RewardType,
    RecruitCharacterReward,
    GeneratedRelationship,
    GeneratedCharacter,
    GeneratedPuzzle,
    GeneratedWorld,
    PuzzleType,
)


def test_feeling_level_has_five_ordered_members():
    assert [level.value for level in FeelingLevel] == [
        "hostile", "wary", "neutral", "friendly", "devoted",
    ]


def test_relationship_tag_has_rival_and_ally():
    assert {tag.value for tag in RelationshipTag} == {"rival", "ally"}


def test_generated_character_defaults_to_not_recruitable_and_neutral():
    character = GeneratedCharacter(name="Bystander", descriptions=["desc"], location="Town")
    assert character.recruitable is False
    assert character.initial_feeling == FeelingLevel.NEUTRAL


def test_generated_character_accepts_recruitable_and_feeling_overrides():
    character = GeneratedCharacter(
        name="Elder", descriptions=["desc"], location="Town",
        recruitable=True, initial_feeling=FeelingLevel.FRIENDLY,
    )
    assert character.recruitable is True
    assert character.initial_feeling == FeelingLevel.FRIENDLY


def test_recruit_character_reward_has_recruit_character_type_and_name():
    reward = RecruitCharacterReward(description="Elder joins the party", character_name="Elder")
    assert reward.reward_type == RewardType.RECRUIT_CHARACTER
    assert reward.character_name == "Elder"


def test_generated_puzzle_accepts_recruit_character_reward():
    puzzle = GeneratedPuzzle(
        name="Elder's Trust", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"],
        problem="p", answer="a", proposed_by_character="Elder",
        rewards=[RecruitCharacterReward(description="Elder joins", character_name="Elder")],
        relevance_to_objective="companion", hint="talk to Elder",
    )
    assert isinstance(puzzle.rewards[0], RecruitCharacterReward)
    assert puzzle.rewards[0].character_name == "Elder"


def test_generated_relationship_requires_two_characters_and_a_tag():
    relationship = GeneratedRelationship(character_a="A", character_b="B", tag=RelationshipTag.RIVAL)
    assert relationship.character_a == "A"
    assert relationship.character_b == "B"
    assert relationship.tag == RelationshipTag.RIVAL


def test_generated_relationship_accepts_tag_as_plain_string():
    relationship = GeneratedRelationship(character_a="A", character_b="B", tag="ally")
    assert relationship.tag == RelationshipTag.ALLY


def test_generated_world_npc_relationships_defaults_to_empty_list():
    assert GeneratedWorld.model_fields["npc_relationships"].default == []
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/llm/test_structured_data_models.py -v`
Expected: FAIL/ERROR — `ImportError: cannot import name 'FeelingLevel'` (none of the new symbols exist yet).

- [ ] **Step 6: Implement the schema additions**

In `src/ivie/llm/structured_data_models.py`, modify the `RewardType` enum (lines 31-34) to add the new member:
```python
class RewardType(str, Enum):
    PASSAGE = "passage"                 # Desbloquea un pasaje
    ITEM = "item"                       # Otorga un objeto
    OBJECTIVE_COMPLETION = "objective_completion"  # Completa directamente el objetivo
    RECRUIT_CHARACTER = "recruit_character"  # Recluta un personaje al grupo del jugador
```

Immediately after the `ItemActionType` class (after line 52, before the `#---- Reward Models` comment on line 54), add:
```python
class FeelingLevel(str, Enum):
    """A recruitable NPC's feeling toward the player, ordered low to high."""
    HOSTILE = "hostile"
    WARY = "wary"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    DEVOTED = "devoted"

class RelationshipTag(str, Enum):
    """A symmetric social tag between two characters, used for the party ripple effect."""
    RIVAL = "rival"
    ALLY = "ally"
```

After the `ObjectiveReward` class (after line 73, before `#---- Requirement Models`), add:
```python
class RecruitCharacterReward(PuzzleReward):
    """Recruits a character into the player's party."""
    reward_type: RewardType = Field(default=RewardType.RECRUIT_CHARACTER)
    character_name: str = Field(description="Name of the recruitable character this puzzle recruits. Note: this character must exist in the world and have recruitable=True")
```

Modify `GeneratedPuzzle.rewards` (line 111) to include the new reward type:
```python
    rewards: List[Union[PassageReward, ItemReward, ObjectiveReward, RecruitCharacterReward]] = Field(
        description="What you get when you solve this puzzle. Note: all reward items and locations must exist in the world"
    )
```

Modify `GeneratedCharacter` (lines 142-147) to add the two new fields:
```python
class GeneratedCharacter(BaseModel):
    name: str = Field(description="Unique name of the character")
    descriptions: List[str] = Field(description="List of character descriptions")
    location: str = Field(description="Location where this character is placed. CRITICAL LOGIC RULE: If this character holds an item or puzzle solution required to unlock a passage, they CANNOT be placed in the location behind that very passage or any location only accessible through it.")
    inventory: List[str] = Field(default=[], description="Items this character starts with. Note: all items must exist in the world")
    interaction: Optional[CharacterInteraction] = Field(default=None, description="How this character can help the player, or None if just decorative")
    recruitable: bool = Field(default=False, description="Whether the player can recruit this character into their party. Only a subset of characters should be recruitable.")
    initial_feeling: FeelingLevel = Field(default=FeelingLevel.NEUTRAL, description="This character's starting feeling toward the player. Only meaningful when recruitable=True.")
```

Immediately after the `GeneratedCharacter` class (before `class BlockedPassage`), add:
```python
class GeneratedRelationship(BaseModel):
    """A symmetric rivalry or alliance tag between two characters."""
    character_a: str = Field(description="Name of the first character in this relationship. Note: this character must exist in the world")
    character_b: str = Field(description="Name of the second character in this relationship. Note: this character must exist in the world")
    tag: RelationshipTag = Field(description="Whether these two characters are rivals or allies")
```

Modify `GeneratedWorld` (lines 198-207) to add the new field:
```python
class GeneratedWorld(BaseModel):
    locations: List[GeneratedLocation] = Field(description="All locations in the world. Note: all location connections must be bidirectional")
    items: List[GeneratedItem] = Field(description="All items in the world. Note: objective target items must be gettable=True")
    characters: List[GeneratedCharacter] = Field(description="All non-player characters. Note: all character locations must exist, and all character inventories must contain existing items")
    puzzles: List[GeneratedPuzzle] = Field(description="All puzzles in the world. Note: puzzle rewards must reference existing world elements")
    player: GeneratedCharacter = Field(description="The player character. Note: player location must exist in the world")
    objective: GeneratedObjective = Field(description="The main objective. Note: all objective components must exist and be accessible in the world")
    dependency_chains: List[DependencyChain] = Field(description="Possible paths to complete the objective. Note: all chains must be actually completable with the given world elements")
    world_theme: str = Field(description="Overall theme or setting of the world")
    narrative_context: str = Field(description="Background story that explains why everything is connected")
    npc_relationships: List[GeneratedRelationship] = Field(default=[], description="Rivalries or alliances between characters. Only include a pair here if the narrative actually motivates a rivalry or alliance - most character pairs should have no entry.")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/llm/test_structured_data_models.py -v`
Expected: PASS (9 passed)

- [ ] **Step 8: Commit**

```bash
git add pytest.ini requirements.txt environment.yml src/ivie/llm/structured_data_models.py tests/llm/test_structured_data_models.py
git commit -m "feat: add NPC recruitment schema (FeelingLevel, RelationshipTag, RecruitCharacterReward)"
```

---

### Task 2: Runtime Character/World recruitment model + social ripple

**Files:**
- Modify: `src/ivie/core/world.py`
- Test: `tests/core/test_world.py`

**Interfaces:**
- Consumes: `FeelingLevel`, `RelationshipTag` from `src/ivie/llm/structured_data_models.py` (Task 1)
- Produces (used by later tasks):
  - `world.py: FEELING_ORDER: list[FeelingLevel]`
  - `world.py: shift_feeling(level: FeelingLevel, steps: int) -> FeelingLevel`
  - `class NPCRelationship: __init__(self, character_a: str, character_b: str, tag: RelationshipTag)`
  - `Character.__init__` new keyword params: `recruitable: bool = False, feeling: FeelingLevel = FeelingLevel.NEUTRAL, recruited: bool = False, recruitment_puzzle: str = None`
  - `World.npc_relationships: list[NPCRelationship]` (instance attribute, starts `[]`)
  - `World.get_party(self) -> list[Character]`
  - `World.can_recruit(self, character_name: str, feeling_threshold: FeelingLevel) -> bool`
  - `World.recruit_character(self, character_name: str) -> bool`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_world.py`:
```python
from src.ivie.core.world import World, Character, Location, Puzzle, NPCRelationship, shift_feeling, FEELING_ORDER
from src.ivie.llm.structured_data_models import FeelingLevel, RelationshipTag


def _make_world_with_two_recruitable_npcs(tag):
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc_a = Character(name="Ally A", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.NEUTRAL)
    npc_b = Character(name="Ally B", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.NEUTRAL)
    world = World(player)
    world.add_location(town)
    world.add_character(npc_a)
    world.add_character(npc_b)
    world.npc_relationships.append(NPCRelationship(character_a="Ally A", character_b="Ally B", tag=tag))
    return world, npc_a, npc_b


def test_character_defaults_are_not_recruitable():
    town = Location(name="Town", descriptions=["desc"])
    character = Character(name="Bystander", descriptions=["desc"], location=town)
    assert character.recruitable is False
    assert character.feeling == FeelingLevel.NEUTRAL
    assert character.recruited is False
    assert character.recruitment_puzzle is None


def test_shift_feeling_moves_one_step_and_clamps_at_both_ends():
    assert shift_feeling(FeelingLevel.NEUTRAL, 1) == FeelingLevel.FRIENDLY
    assert shift_feeling(FeelingLevel.DEVOTED, 1) == FeelingLevel.DEVOTED
    assert shift_feeling(FeelingLevel.HOSTILE, -1) == FeelingLevel.HOSTILE


def test_can_recruit_true_when_feeling_meets_threshold():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    assert world.can_recruit("Elder", FeelingLevel.FRIENDLY) is True


def test_can_recruit_false_when_feeling_below_threshold_and_no_puzzle():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.NEUTRAL)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    assert world.can_recruit("Elder", FeelingLevel.FRIENDLY) is False


def test_can_recruit_true_when_challenge_puzzle_solved_even_if_feeling_is_low():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(
        name="Elder", descriptions=["desc"], location=town, recruitable=True,
        feeling=FeelingLevel.NEUTRAL, recruitment_puzzle="Elder's Trust",
    )
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    world.add_puzzle(Puzzle(name="Elder's Trust", descriptions=["desc"], problem="p", answer="a"))
    world.puzzle_states["Elder's Trust"] = 'solved'
    assert world.can_recruit("Elder", FeelingLevel.FRIENDLY) is True


def test_recruit_character_sets_recruited_flag_and_joins_party():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    assert world.recruit_character("Elder") is True
    assert npc.recruited is True
    assert world.get_party() == [npc]


def test_recruit_character_returns_false_if_already_recruited():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY, recruited=True)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    assert world.recruit_character("Elder") is False


def test_recruiting_ally_raises_counterparts_feeling_one_step():
    world, npc_a, npc_b = _make_world_with_two_recruitable_npcs(RelationshipTag.ALLY)
    world.recruit_character("Ally A")
    assert npc_b.feeling == FeelingLevel.FRIENDLY


def test_recruiting_rival_lowers_counterparts_feeling_one_step():
    world, npc_a, npc_b = _make_world_with_two_recruitable_npcs(RelationshipTag.RIVAL)
    world.recruit_character("Ally A")
    assert npc_b.feeling == FeelingLevel.WARY


def test_recruiting_with_no_relationship_tag_does_not_affect_other_npcs():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc_a = Character(name="A", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY)
    npc_b = Character(name="B", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.NEUTRAL)
    world = World(player)
    world.add_location(town)
    world.add_character(npc_a)
    world.add_character(npc_b)
    world.recruit_character("A")
    assert npc_b.feeling == FeelingLevel.NEUTRAL
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_world.py -v`
Expected: FAIL/ERROR — `ImportError: cannot import name 'NPCRelationship'`.

- [ ] **Step 3: Implement the runtime model**

In `src/ivie/core/world.py`, modify the imports at the top (lines 7-8):
```python
import re
from typing import Type

from ..llm.structured_data_models import FeelingLevel, RelationshipTag
```

Immediately after the imports, before `class Component:` (line 11), add:
```python
FEELING_ORDER = [FeelingLevel.HOSTILE, FeelingLevel.WARY, FeelingLevel.NEUTRAL, FeelingLevel.FRIENDLY, FeelingLevel.DEVOTED]


def shift_feeling(level: FeelingLevel, steps: int) -> FeelingLevel:
  """Move a FeelingLevel up or down the ladder, clamped at both ends."""
  index = FEELING_ORDER.index(level)
  new_index = max(0, min(len(FEELING_ORDER) - 1, index + steps))
  return FEELING_ORDER[new_index]

```

Modify `Character.__init__` (lines 165-180) to accept the new fields:
```python
class Character (Component):
  """A class to represent a character."""
  def __init__ (self, name:str, descriptions: 'list[str]', location:Location, inventory: 'list[Item]' = None, interaction=None,
                recruitable: bool = False, feeling: 'FeelingLevel' = FeelingLevel.NEUTRAL, recruited: bool = False,
                recruitment_puzzle: str = None):

    super().__init__(name, descriptions)
    """inherited from Component"""

    self.inventory = inventory or []
    """a set of Items the carachter has"""

    self.location = location
    """the location of the character"""

    self.visited_locations = {self.location.name: []}
    """a dictionary that contains the successive descriptions of the visited places"""
    
    self.interaction = interaction
    """interaction data from GeneratedCharacter, contains proposes_puzzle and other interaction info"""

    self.recruitable = recruitable
    """whether the player can recruit this character into their party, set at generation time"""

    self.feeling = feeling
    """this character's FeelingLevel toward the player; mutated only by the party relationship ripple"""

    self.recruited = recruited
    """whether this character has joined the player's party"""

    self.recruitment_puzzle = recruitment_puzzle
    """name of the Puzzle that, when solved, recruits this character regardless of feeling; or None"""
```

Immediately before `class World:` (line 218), add:
```python
class NPCRelationship:
  """A symmetric rivalry or alliance tag between two characters, used for the party social ripple effect."""
  def __init__(self, character_a: str, character_b: str, tag: RelationshipTag):
    self.character_a = character_a
    self.character_b = character_b
    self.tag = tag


```

In `World.__init__` (lines 220-256), add the new attribute right after `self.puzzle_states = {}` (line 255-256):
```python
    # Puzzle state tracking
    self.puzzle_states = {}
    """track the state of puzzles: 'not_proposed', 'proposed', 'solved'"""

    self.npc_relationships = []
    """list of NPCRelationship: sparse, symmetric rival/ally tags between characters"""
```

Immediately after `add_characters` (after line 448), before `render_world` (line 450), add the recruitment methods:
```python
  def get_party(self) -> 'list[Character]':
    """Return the characters currently recruited into the player's party."""
    return [character for character in self.characters.values() if character.recruited]

  def can_recruit(self, character_name: str, feeling_threshold: 'FeelingLevel') -> bool:
    """Check whether character_name can be recruited: their feeling already meets feeling_threshold,
    or their recruitment challenge puzzle has been solved. These are independent conditions."""
    character = self.characters.get(character_name)
    if character is None or not character.recruitable or character.recruited:
      return False

    feeling_ok = FEELING_ORDER.index(character.feeling) >= FEELING_ORDER.index(feeling_threshold)
    puzzle_ok = (character.recruitment_puzzle is not None and
                 self.puzzle_states.get(character.recruitment_puzzle) == 'solved')
    return feeling_ok or puzzle_ok

  def recruit_character(self, character_name: str) -> bool:
    """Mark character_name as recruited and apply the social ripple to related NPCs. Returns False if
    the character doesn't exist or is already recruited."""
    character = self.characters.get(character_name)
    if character is None or character.recruited:
      return False

    character.recruited = True
    self._apply_relationship_ripple(character_name)
    return True

  def _apply_relationship_ripple(self, recruited_character_name: str) -> None:
    for relationship in self.npc_relationships:
      if relationship.character_a == recruited_character_name:
        other_name = relationship.character_b
      elif relationship.character_b == recruited_character_name:
        other_name = relationship.character_a
      else:
        continue

      other = self.characters.get(other_name)
      if other is None:
        continue

      step = 1 if relationship.tag == RelationshipTag.ALLY else -1
      other.feeling = shift_feeling(other.feeling, step)

```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_world.py -v`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit**

```bash
git add src/ivie/core/world.py tests/core/test_world.py
git commit -m "feat: add recruitment state and social ripple to Character/World"
```

---

### Task 3: World builder wiring (GeneratedWorld → runtime World)

**Files:**
- Modify: `src/ivie/core/world_builder.py`
- Test: `tests/core/test_world_builder.py`

**Interfaces:**
- Consumes: `Character` new kwargs, `NPCRelationship`, `World.npc_relationships` (Task 2); `RecruitCharacterReward`, `GeneratedRelationship`, `FeelingLevel` (Task 1)
- Produces: `create_world_from_llm_response` now populates `Character.recruitable`, `Character.feeling`, `Character.recruitment_puzzle`, and `World.npc_relationships` from the generated data. No new public symbols — this wiring is exercised directly by its test and, later, indirectly by the real generation pipeline.

- [ ] **Step 1: Write the failing test**

Create `tests/core/test_world_builder.py`:
```python
from src.ivie.core.world_builder import create_world_from_llm_response
from src.ivie.llm.structured_data_models import (
    GeneratedWorld, GeneratedLocation, GeneratedCharacter, GeneratedPuzzle,
    GeneratedObjective, ObjectiveComponent, ObjectiveType, ComponentType, PuzzleType,
    RecruitCharacterReward, GeneratedRelationship, RelationshipTag, FeelingLevel,
)


def _build_generated_world_with_recruitment():
    location = GeneratedLocation(name="Village", descriptions=["desc"], items=[], connecting_locations=[])
    player = GeneratedCharacter(name="Hero", descriptions=["desc"], location="Village")
    elder = GeneratedCharacter(
        name="Elder", descriptions=["desc"], location="Village",
        recruitable=True, initial_feeling=FeelingLevel.NEUTRAL,
    )
    guard = GeneratedCharacter(
        name="Guard", descriptions=["desc"], location="Village",
        recruitable=True, initial_feeling=FeelingLevel.NEUTRAL,
    )
    puzzle = GeneratedPuzzle(
        name="Elder's Trust", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"],
        problem="p", answer="a", proposed_by_character="Elder",
        rewards=[RecruitCharacterReward(description="Elder joins", character_name="Elder")],
        relevance_to_objective="companion", hint="talk to Elder",
    )
    objective = GeneratedObjective(
        type=ObjectiveType.REACH_LOCATION,
        components=[ObjectiveComponent(name="Village", component_type=ComponentType.LOCATION, role_in_objective="destination")],
        description="Reach the village", success_conditions=["Player is in Village"],
    )
    return GeneratedWorld(
        locations=[location], items=[], characters=[elder, guard], puzzles=[puzzle],
        player=player, objective=objective,
        dependency_chains=[], world_theme="Test", narrative_context="Test",
        npc_relationships=[GeneratedRelationship(character_a="Elder", character_b="Guard", tag=RelationshipTag.ALLY)],
    )


def test_create_world_from_llm_response_wires_recruitment_fields():
    world = create_world_from_llm_response(_build_generated_world_with_recruitment())

    elder = world.characters["Elder"]
    guard = world.characters["Guard"]

    assert elder.recruitable is True
    assert elder.feeling == FeelingLevel.NEUTRAL
    assert elder.recruitment_puzzle == "Elder's Trust"
    assert guard.recruitment_puzzle is None

    assert len(world.npc_relationships) == 1
    relationship = world.npc_relationships[0]
    assert {relationship.character_a, relationship.character_b} == {"Elder", "Guard"}
    assert relationship.tag == RelationshipTag.ALLY
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_world_builder.py -v`
Expected: FAIL — `KeyError: 'Elder'` or `AttributeError` (recruitment fields not wired; `elder.recruitment_puzzle` doesn't exist as a populated value yet, defaults or missing).

- [ ] **Step 3: Implement the wiring**

In `src/ivie/core/world_builder.py`, modify the imports (lines 1-8):
```python
"""World builder helpers for generating and expanding worlds."""

import json
import jsonpickle
from typing import Dict

from .world import World, Location, Item, Character, Puzzle, NPCRelationship
from ..llm.structured_data_models import GeneratedWorld, WorldExpansion, RecruitCharacterReward, FeelingLevel
```

Immediately after `create_world_from_llm_response`'s `try:` block starts and before the `characters_list = []` loop (i.e., right after the `player_location.visited = True` block, before line 132), add a helper function above `create_world_from_llm_response` (right after the imports, before `def create_world_from_trace`):
```python
def _find_recruitment_puzzle_for_character(character_name: str, puzzles_dict: Dict[str, Puzzle]) -> str:
    for puzzle in puzzles_dict.values():
        for reward in puzzle.rewards:
            if isinstance(reward, RecruitCharacterReward) and reward.character_name == character_name:
                return puzzle.name
    return None

```

Modify the `characters_list` construction loop (lines 132-137):
```python
        characters_list = []
        for char_data in generated_world.characters:
            char_inventory = [items_dict[item_name] for item_name in getattr(char_data, 'inventory', []) if item_name in items_dict]
            char_location = locations_dict.get(getattr(char_data, 'location', None), player_location)
            character = Character(
                name=char_data.name, descriptions=char_data.descriptions, location=char_location,
                inventory=char_inventory, interaction=getattr(char_data, 'interaction', None),
                recruitable=getattr(char_data, 'recruitable', False),
                feeling=getattr(char_data, 'initial_feeling', FeelingLevel.NEUTRAL),
                recruitment_puzzle=_find_recruitment_puzzle_for_character(char_data.name, puzzles_dict),
            )
            characters_list.append(character)
```

Modify the `World` assembly block (lines 139-147) to also wire `npc_relationships`, right after the `for puzzle in puzzles_dict.values(): world.add_puzzle(puzzle)` loop:
```python
        world = World(player)
        for location in locations_dict.values():
            world.add_location(location)
        for item in items_dict.values():
            world.add_item(item)
        for character in characters_list:
            world.add_character(character)
        for puzzle in puzzles_dict.values():
            world.add_puzzle(puzzle)

        for relationship_data in getattr(generated_world, 'npc_relationships', []):
            world.npc_relationships.append(NPCRelationship(
                character_a=relationship_data.character_a,
                character_b=relationship_data.character_b,
                tag=relationship_data.tag,
            ))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_world_builder.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the full test suite so far to check for regressions**

Run: `pytest tests/ -v`
Expected: PASS (all tests from Tasks 1-3)

- [ ] **Step 6: Commit**

```bash
git add src/ivie/core/world_builder.py tests/core/test_world_builder.py
git commit -m "feat: wire recruitment fields and npc_relationships into world_builder"
```

---

### Task 4: Puzzle reward verification for RecruitCharacterReward

**Files:**
- Modify: `src/ivie/llm/generation_pipeline.py`
- Test: `tests/llm/test_generation_pipeline.py`

**Interfaces:**
- Consumes: `RecruitCharacterReward` (Task 1)
- Produces: `verify_puzzle_rewards_and_fix(world: GeneratedWorld) -> tuple[bool, GeneratedWorld]` now returns `(False, world)` when any `RecruitCharacterReward.character_name` doesn't match an existing character, and auto-fixes `recruitable=True` in place when it matches a character that wasn't marked recruitable. No new public symbols.

- [ ] **Step 1: Write the failing tests**

Create `tests/llm/test_generation_pipeline.py`:
```python
from src.ivie.llm.generation_pipeline import verify_puzzle_rewards_and_fix
from src.ivie.llm.structured_data_models import (
    GeneratedWorld, GeneratedLocation, GeneratedCharacter, GeneratedPuzzle,
    GeneratedObjective, ObjectiveComponent, ObjectiveType, ComponentType, PuzzleType,
    RecruitCharacterReward,
)


def _minimal_generated_world(characters, puzzles):
    return GeneratedWorld(
        locations=[GeneratedLocation(name="Town Square", descriptions=["desc"], items=[], connecting_locations=[])],
        items=[],
        characters=characters,
        puzzles=puzzles,
        player=GeneratedCharacter(name="Player", descriptions=["desc"], location="Town Square"),
        objective=GeneratedObjective(
            type=ObjectiveType.REACH_LOCATION,
            components=[ObjectiveComponent(name="Town Square", component_type=ComponentType.LOCATION, role_in_objective="destination")],
            description="Reach the town square", success_conditions=["Player is in Town Square"],
        ),
        dependency_chains=[], world_theme="Testing", narrative_context="A test world",
    )


def test_verify_puzzle_rewards_and_fix_auto_fixes_recruitable_flag():
    character = GeneratedCharacter(name="Elder", descriptions=["desc"], location="Town Square", recruitable=False)
    puzzle = GeneratedPuzzle(
        name="Elder's Trust", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"], problem="p", answer="a",
        proposed_by_character="Elder",
        rewards=[RecruitCharacterReward(description="Elder joins the party", character_name="Elder")],
        relevance_to_objective="unlocks companion", hint="talk to Elder",
    )
    world = _minimal_generated_world(characters=[character], puzzles=[puzzle])

    ok, fixed_world = verify_puzzle_rewards_and_fix(world)

    assert ok is True
    fixed_character = next(c for c in fixed_world.characters if c.name == "Elder")
    assert fixed_character.recruitable is True


def test_verify_puzzle_rewards_and_fix_fails_for_missing_character():
    puzzle = GeneratedPuzzle(
        name="Ghost Recruit", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"], problem="p", answer="a",
        rewards=[RecruitCharacterReward(description="joins", character_name="Nobody")],
        relevance_to_objective="x", hint="x",
    )
    world = _minimal_generated_world(characters=[], puzzles=[puzzle])

    ok, _ = verify_puzzle_rewards_and_fix(world)

    assert ok is False


def test_verify_puzzle_rewards_and_fix_still_creates_missing_item_rewards():
    from src.ivie.llm.structured_data_models import ItemReward

    puzzle = GeneratedPuzzle(
        name="Chest Puzzle", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"], problem="p", answer="a",
        rewards=[ItemReward(description="a coin", item_name="Gold Coin")],
        relevance_to_objective="x", hint="x",
    )
    world = _minimal_generated_world(characters=[], puzzles=[puzzle])

    ok, fixed_world = verify_puzzle_rewards_and_fix(world)

    assert ok is True
    assert any(item.name == "Gold Coin" for item in fixed_world.items)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/llm/test_generation_pipeline.py -v`
Expected: FAIL — `test_verify_puzzle_rewards_and_fix_fails_for_missing_character` fails because the function currently always returns `True`.

- [ ] **Step 3: Implement the verification branch**

In `src/ivie/llm/generation_pipeline.py`, replace the `verify_puzzle_rewards_and_fix` function body (lines 717-801):
```python
def verify_puzzle_rewards_and_fix(world: GeneratedWorld) -> tuple[bool, GeneratedWorld]:
    from .structured_data_models import GeneratedItem, ItemReward, RecruitCharacterReward
    
    # Track changes made
    items_created = []
    all_ok = True
    
    # Get existing item names for quick lookup
    existing_item_names = {item.name for item in world.items}
    existing_item_names_lower = {name.lower() for name in existing_item_names}
    characters_by_name = {character.name: character for character in world.characters}
    
    for puzzle in world.puzzles:
        
        for reward in puzzle.rewards:
            if isinstance(reward, ItemReward):
                item_name = reward.item_name
                
                if item_name.lower() not in existing_item_names_lower:
                    print(f"[WARNING] ItemReward item '{item_name}' does not exist. Creating it...")
                    
                    # Create the missing item
                    new_item = GeneratedItem(
                        name=item_name,
                        descriptions=[f"A {item_name.lower()} obtained as a reward for solving puzzles."],
                        gettable=True,
                        is_objective_target=False,
                        relevance_to_objective=f"Reward item from puzzle '{puzzle.name}'",
                        required_for=[]
                    )
                    
                    world.items.append(new_item)
                    existing_item_names.add(item_name)
                    items_created.append(item_name)
                    
                    # Determine where to place the item
                    # For observation puzzles, the item should be in the location, not on the character
                    if puzzle.puzzle_type == "observation" and puzzle.location:
                        location_found = False
                        for location in world.locations:
                            if location.name == puzzle.location:
                                location.items.append(item_name)
                                print(f"[INFO] Added observation puzzle reward item '{item_name}' to location '{location.name}'")
                                location_found = True
                                break
                        if not location_found:
                             print(f"[WARNING] Puzzle location '{puzzle.location}' not found, adding item to first location")
                             if world.locations:
                                 world.locations[0].items.append(item_name)

                    elif puzzle.proposed_by_character:
                        # For other puzzle types, add to character's inventory
                        char_found = False
                        for character in world.characters:
                            if character.name == puzzle.proposed_by_character:
                                character.inventory.append(item_name)
                                print(f"[INFO] Added item '{item_name}' to character '{character.name}' inventory")
                                char_found = True
                                break
                        
                        if not char_found:
                            print(f"[WARNING] Character '{puzzle.proposed_by_character}' not found, adding item to first location")
                            if world.locations:
                                world.locations[0].items.append(item_name)
                    
                    elif puzzle.location:
                        # Add to puzzle location
                        location_found = False
                        for location in world.locations:
                            if location.name == puzzle.location:
                                location.items.append(item_name)
                                print(f"[INFO] Added item '{item_name}' to location '{location.name}'")
                                location_found = True
                                break
                        
                        if not location_found:
                            print(f"[WARNING] Puzzle location '{puzzle.location}' not found, adding item to first location")
                            if world.locations:
                                world.locations[0].items.append(item_name)
                    
                    else:
                        # Add to first location as fallback
                        if world.locations:
                            world.locations[0].items.append(item_name)
                            print(f"[INFO] Added item '{item_name}' to location '{world.locations[0].name}' (fallback)")

            elif isinstance(reward, RecruitCharacterReward):
                character = characters_by_name.get(reward.character_name)
                if character is None:
                    print(f"[ERROR] RecruitCharacterReward in puzzle '{puzzle.name}' references non-existent character '{reward.character_name}'")
                    all_ok = False
                elif not character.recruitable:
                    print(f"[WARNING] RecruitCharacterReward character '{character.name}' was not marked recruitable. Fixing...")
                    character.recruitable = True
        
    return all_ok, world
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/llm/test_generation_pipeline.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/ivie/llm/generation_pipeline.py tests/llm/test_generation_pipeline.py
git commit -m "feat: validate RecruitCharacterReward in verify_puzzle_rewards_and_fix"
```

---

### Task 5: Recruitment configuration

**Files:**
- Modify: `config.ini`
- Modify: `src/ivie/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `FeelingLevel` (Task 1)
- Produces: `get_recruitment_config(config) -> tuple[bool, FeelingLevel]` in `src/ivie/config.py`; `[Recruitment]` section in `config.ini`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:
```python
import configparser

from src.ivie.config import get_recruitment_config
from src.ivie.llm.structured_data_models import FeelingLevel


def _config_from_string(text):
    config = configparser.ConfigParser()
    config.read_string(text)
    return config


def test_get_recruitment_config_reads_enabled_and_threshold():
    config = _config_from_string("""
[Recruitment]
enabled = true
feeling_threshold = friendly
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is True
    assert threshold == FeelingLevel.FRIENDLY


def test_get_recruitment_config_defaults_when_keys_missing():
    config = _config_from_string("""
[Recruitment]
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is True
    assert threshold == FeelingLevel.FRIENDLY


def test_get_recruitment_config_reads_disabled():
    config = _config_from_string("""
[Recruitment]
enabled = false
feeling_threshold = devoted
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is False
    assert threshold == FeelingLevel.DEVOTED
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_recruitment_config'`.

- [ ] **Step 3: Add the config section and getter**

Modify `config.ini`, add a new section at the end of the file:
```ini
[Recruitment]
enabled = true
feeling_threshold = friendly
```

Modify `src/ivie/config.py` imports (line 9-13) to add the `FeelingLevel` import:
```python
import os
from dotenv import load_dotenv
import configparser
import time
from urllib.parse import quote_plus

from .llm.structured_data_models import FeelingLevel
```

Add a new function after `get_debug` (after line 43):
```python
def get_recruitment_config(config):
    """Get recruitment settings from config."""
    enabled = config["Recruitment"].getboolean("enabled", fallback=True)
    feeling_threshold = FeelingLevel(config["Recruitment"].get("feeling_threshold", fallback="friendly"))
    return enabled, feeling_threshold
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add config.ini src/ivie/config.py tests/test_config.py
git commit -m "feat: add [Recruitment] config section and get_recruitment_config"
```

---

### Task 6: "Ask to recruit" detection in the game loop

**Files:**
- Modify: `src/ivie/core/game_logic.py`
- Test: `tests/core/test_game_logic.py`

**Interfaces:**
- Consumes: `World.can_recruit`, `World.recruit_character` (Task 2); `get_recruitment_config` (Task 5)
- Produces: `check_recruitment_request(world, message, language, config=None) -> Optional[str]` in `src/ivie/core/game_logic.py`, wired into the `game_loop` closure inside `create_game_loop`.

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_game_logic.py`:
```python
import configparser

from src.ivie.core.game_logic import check_recruitment_request
from src.ivie.core.world import World, Character, Location, Puzzle
from src.ivie.llm.structured_data_models import FeelingLevel


def _config_with_threshold(threshold="friendly", enabled="true"):
    config = configparser.ConfigParser()
    config.read_string(f"""
[Recruitment]
enabled = {enabled}
feeling_threshold = {threshold}
""")
    return config


def _world_with_recruitable_npc(feeling, recruitment_puzzle=None):
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(
        name="Elder", descriptions=["desc"], location=town,
        recruitable=True, feeling=feeling, recruitment_puzzle=recruitment_puzzle,
    )
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    return world, npc


def test_recruitment_granted_directly_when_feeling_meets_threshold():
    world, npc = _world_with_recruitable_npc(FeelingLevel.FRIENDLY)
    response = check_recruitment_request(world, "I ask Elder to join my party", "en", config=_config_with_threshold())
    assert response is not None
    assert npc.recruited is True


def test_recruitment_proposes_challenge_when_feeling_below_threshold():
    world, npc = _world_with_recruitable_npc(FeelingLevel.NEUTRAL, recruitment_puzzle="Elder's Trust")
    world.add_puzzle(Puzzle(name="Elder's Trust", descriptions=["desc"], problem="Solve this riddle", answer="a"))
    response = check_recruitment_request(world, "I ask Elder to join my party", "en", config=_config_with_threshold())
    assert response is not None
    assert "Solve this riddle" in response
    assert npc.recruited is False


def test_recruitment_rejected_when_no_path_available():
    world, npc = _world_with_recruitable_npc(FeelingLevel.NEUTRAL)
    response = check_recruitment_request(world, "I ask Elder to join my party", "en", config=_config_with_threshold())
    assert response is not None
    assert npc.recruited is False


def test_recruitment_ignored_when_message_has_no_recruit_intent():
    world, npc = _world_with_recruitable_npc(FeelingLevel.FRIENDLY)
    response = check_recruitment_request(world, "I look around the room", "en", config=_config_with_threshold())
    assert response is None
    assert npc.recruited is False


def test_recruitment_ignored_for_non_recruitable_character():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Bystander", descriptions=["desc"], location=town, recruitable=False)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    response = check_recruitment_request(world, "I ask Bystander to join my party", "en", config=_config_with_threshold())
    assert response is None


def test_recruitment_disabled_by_config_returns_none():
    world, npc = _world_with_recruitable_npc(FeelingLevel.FRIENDLY)
    response = check_recruitment_request(
        world, "I ask Elder to join my party", "en", config=_config_with_threshold(enabled="false"),
    )
    assert response is None
    assert npc.recruited is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_game_logic.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_recruitment_request'`.

- [ ] **Step 3: Implement `check_recruitment_request` and wire it into the game loop**

In `src/ivie/core/game_logic.py`, modify the imports (line 12) to bring in the config helpers:
```python
from ..llm.prompts import prompt_narrate_current_scene, prompt_world_update_structured, prompt_describe_objective
from .world_builder import generate_world_overview, generate_objective_validation_report
from .world_utils import create_world_state_summary
from ..llm.structured_data_models import WorldUpdate
from ..llm.memory_system import create_memory_system
from ..database.mongodb_handler import db_handler
from ..config import load_config, get_recruitment_config
```

Add the new function immediately after `check_character_puzzle_mention` (after line 295, before `def handle_debug_command`):
```python
def check_recruitment_request(world, message, language, config=None):
    if not message:
        return None

    if config is None:
        config = load_config()
    recruitment_enabled, feeling_threshold = get_recruitment_config(config)
    if not recruitment_enabled:
        return None

    message_lower = message.lower()
    recruit_keywords = ['recruit', 'join my party', 'join me', 'come with me',
                         'reclut', 'únete a mi', 'unete a mi', 'ven conmigo']
    if not any(k in message_lower for k in recruit_keywords):
        return None

    for character in world.characters.values():
        if character.location != world.player.location or not character.recruitable:
            continue
        if character.name.lower() not in message_lower:
            continue
        if character.recruited:
            return None

        if world.can_recruit(character.name, feeling_threshold):
            world.recruit_character(character.name)
            if language == 'es':
                return f"🤝 **{character.name}** acepta unirse a tu grupo."
            return f"🤝 **{character.name}** agrees to join your party."

        if character.recruitment_puzzle and character.recruitment_puzzle in world.puzzles:
            puzzle_state = world.puzzle_states.get(character.recruitment_puzzle)
            if puzzle_state == 'not_proposed':
                puzzle = world.puzzles[character.recruitment_puzzle]
                if language == 'es':
                    return (f"🎭 **{character.name}** todavía no confía en ti lo suficiente.\n\n"
                            f"🧩 **Desafío: {puzzle.name}**\n📝 **Problema:** {puzzle.problem}")
                return (f"🎭 **{character.name}** doesn't trust you enough yet.\n\n"
                        f"🧩 **Challenge: {puzzle.name}**\n📝 **Problem:** {puzzle.problem}")
            return None

        if language == 'es':
            return f"🎭 **{character.name}** rechaza unirse a ti por ahora."
        return f"🎭 **{character.name}** declines to join you for now."

    return None
```

Wire it into the `game_loop` closure inside `create_game_loop` (lines 519-527), right after the existing `check_character_puzzle_mention` short-circuit:
```python
    def game_loop(message, history):
        nonlocal last_player_position, number_of_turns, game_log_dictionary
        debug_response = handle_debug_command(message, world, language)
        if debug_response:
            return debug_response

        puzzle_response = check_character_puzzle_mention(world, message, language)
        if puzzle_response:
            return puzzle_response

        recruitment_response = check_recruitment_request(world, message, language)
        if recruitment_response:
            return recruitment_response

        number_of_turns += 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_game_logic.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Run the full test suite to check for regressions**

Run: `pytest tests/ -v`
Expected: PASS (all tests from Tasks 1-6)

- [ ] **Step 6: Commit**

```bash
git add src/ivie/core/game_logic.py tests/core/test_game_logic.py
git commit -m "feat: detect ask-to-recruit intent in the game loop"
```

---

### Task 7: Narration awareness of relationships (render_world + generation prompts)

**Files:**
- Modify: `src/ivie/core/world.py`
- Modify: `src/ivie/llm/prompts.py`
- Test: `tests/core/test_world.py` (append)
- Test: `tests/llm/test_prompts_recruitment.py`

**Interfaces:**
- Consumes: `RelationshipTag` (Task 1), `World.npc_relationships` (Task 2)
- Produces: `World.render_world` includes a "Known relationships" / "Relaciones conocidas" section listing tagged pairs when `npc_relationships` is non-empty; `prompt_world_update_structured`, `PROMPT_STEP_3_DETAILS`, and `PROMPT_STEP_4_PUZZLES` mention the new recruitment fields/reward and instruct the narrator not to invent untagged reactions. No new public symbols.

- [ ] **Step 1: Write the failing tests**

Append to `tests/core/test_world.py`:
```python
def test_render_world_lists_known_relationships_when_present():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc_a = Character(name="Ally A", descriptions=["desc"], location=town)
    npc_b = Character(name="Ally B", descriptions=["desc"], location=town)
    world = World(player)
    world.add_location(town)
    world.add_character(npc_a)
    world.add_character(npc_b)
    world.npc_relationships.append(NPCRelationship(character_a="Ally A", character_b="Ally B", tag=RelationshipTag.RIVAL))

    rendered = world.render_world(language='en')

    assert "Ally A" in rendered and "Ally B" in rendered
    assert "rivals" in rendered


def test_render_world_omits_relationships_section_when_none_defined():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    world = World(player)
    world.add_location(town)

    rendered = world.render_world(language='en')

    assert "Known relationships" not in rendered
```

Create `tests/llm/test_prompts_recruitment.py`:
```python
from src.ivie.llm.prompts import PROMPT_STEP_3_DETAILS, PROMPT_STEP_4_PUZZLES, prompt_world_update_structured


def test_step_3_details_mentions_recruitment_fields_in_both_languages():
    for language in ("es", "en"):
        text = PROMPT_STEP_3_DETAILS(
            skeleton_data="", title="T", backstory="B", player_concept="P", main_objective="M", language=language,
        )
        assert "recruitable" in text
        assert "initial_feeling" in text
        assert "npc_relationships" in text


def test_step_4_puzzles_mentions_recruit_character_reward_in_both_languages():
    for language in ("es", "en"):
        text = PROMPT_STEP_4_PUZZLES(world_data="{}", language=language)
        assert "RecruitCharacterReward" in text


def test_world_update_prompt_instructs_narrator_about_social_reactions():
    system_msg_es, _, _ = prompt_world_update_structured(world_state="state", input="do something", language='es')
    system_msg_en, _, _ = prompt_world_update_structured(world_state="state", input="do something", language='en')
    assert "REACCIONES SOCIALES" in system_msg_es
    assert "NPC SOCIAL REACTIONS" in system_msg_en
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_world.py tests/llm/test_prompts_recruitment.py -v`
Expected: FAIL — `NPCRelationship`/`RelationshipTag` not imported in the test yet triggers `NameError`, and the new assertions fail (text not present).

First, update the import line at the top of `tests/core/test_world.py` (from Task 2) to also bring in `RelationshipTag`:
```python
from src.ivie.core.world import World, Character, Location, Puzzle, NPCRelationship, shift_feeling, FEELING_ORDER
from src.ivie.llm.structured_data_models import FeelingLevel, RelationshipTag
```
(This line already exists from Task 2 — confirm it includes `RelationshipTag`, which it does.)

- [ ] **Step 3: Add the relationships section to `render_world`**

In `src/ivie/core/world.py`, modify `__render_world_english` (the `if detail_components:` block, lines 653-676) to append the new section right before the `return` statement (line 678):
```python
      if len(self.npc_relationships) > 0:
        details += "Known relationships (the player's party composition only affects the feelings of characters listed here toward the player; do not invent reactions for any other character pair):\n"
        for relationship in self.npc_relationships:
          relation_word = "allies" if relationship.tag == RelationshipTag.ALLY else "rivals"
          details += f"- {relationship.character_a} and {relationship.character_b} are {relation_word}.\n"

    return world_description + '\n' + details
```

Modify `__render_world_spanish` (the `if detail_components:` block, lines 590-614) to append the equivalent section right before the `return` statement (line 616):
```python
      if len(self.npc_relationships) > 0:
        details += "Relaciones conocidas (la composición del grupo del jugador SOLO afecta el sentimiento de los personajes listados aquí; no inventes reacciones para ningún otro par de personajes):\n"
        for relationship in self.npc_relationships:
          relation_word = "aliados" if relationship.tag == RelationshipTag.ALLY else "rivales"
          details += f"- {relationship.character_a} y {relationship.character_b} son {relation_word}.\n"

    return world_description + '\n' + details
```

- [ ] **Step 4: Add recruitment instructions to the generation prompts**

In `src/ivie/llm/prompts.py`, modify `PROMPT_STEP_3_DETAILS`: in the Spanish branch, insert a new block right after the `**REGLAS DE PERSONAJES:**` list (after line 838, before `**REGLAS DE OBJETOS:**` on line 840):
```python
**REGLAS DE RECLUTAMIENTO DE PERSONAJES:**
1. **Marca como reclutable SOLO a un subconjunto de personajes**: La mayoría de los personajes deben tener `recruitable: false`. Marca `recruitable: true` únicamente en personajes clave que tenga sentido que se unan al grupo del jugador.
2. **initial_feeling**: Para personajes reclutables, define `initial_feeling` según la relación narrativa que ya tengan con el jugador (por ejemplo, "friendly" o "devoted" si son aliados desde el inicio, "neutral" o "wary" si aún no confían en el jugador). Para personajes no reclutables, deja el valor por defecto "neutral".
3. **npc_relationships**: Añade una entrada en `npc_relationships` SOLO cuando la historia realmente motive una rivalidad ("rival") o alianza ("ally") entre dos personajes concretos. La mayoría de los pares de personajes NO deben tener ninguna entrada - eso es lo esperado, no un error.

```
In the English branch, insert the equivalent block right after the `**CHARACTER RULES:**` list (after line 969, before `**OBJECT RULES:**` on line 971):
```python
**CHARACTER RECRUITMENT RULES:**
1. **Only mark a subset of characters as recruitable**: Most characters should have `recruitable: false`. Only set `recruitable: true` on key characters for whom it makes narrative sense to join the player's party.
2. **initial_feeling**: For recruitable characters, set `initial_feeling` based on their existing narrative relationship with the player (e.g. "friendly" or "devoted" if they are already allies, "neutral" or "wary" if they don't yet trust the player). For non-recruitable characters, leave it at the default "neutral".
3. **npc_relationships**: Only add an entry to `npc_relationships` when the story actually motivates a rivalry ("rival") or alliance ("ally") between two specific characters. Most character pairs should have NO entry at all - that is expected, not an error.

```

Modify `PROMPT_STEP_4_PUZZLES`: in the Spanish branch, insert a new numbered rule right after rule 9 (`**OBSTÁCULO vs. LLAVE**...`, line 1123), before `**REGLAS OBLIGATORIAS PARA SISTEMA DE PISTAS:**` (line 1125):
```python
10. **RECOMPENSA DE RECLUTAMIENTO**: Si un personaje tiene `recruitable: true` y su `initial_feeling` es "hostile", "wary" o "neutral", PUEDES añadir un puzzle propuesto por ese mismo personaje (`proposed_by_character`) cuya única recompensa sea un `RecruitCharacterReward` con `character_name` igual al nombre de ese personaje. Esto representa el desafío que el jugador debe superar para reclutarlo. NO añadas este tipo de puzzle para personajes cuyo `initial_feeling` ya sea "friendly" o "devoted" - esos personajes se reclutan directamente sin desafío.

```
In the English branch, insert the equivalent rule right after `**OBSTACLE vs. KEY**...` (line 1219), before `**MANDATORY RULES FOR HINT SYSTEM:**` (line 1221):
```python
- **RECRUITMENT REWARD**: If a character has `recruitable: true` and their `initial_feeling` is "hostile", "wary", or "neutral", you MAY add a puzzle proposed by that same character (`proposed_by_character`) whose only reward is a `RecruitCharacterReward` with `character_name` equal to that character's name. This represents the challenge the player must complete to recruit them. Do NOT add this kind of puzzle for characters whose `initial_feeling` is already "friendly" or "devoted" - those characters can be recruited directly without a challenge.

```

Modify `prompt_world_update_structured`: in the Spanish `system_msg` (lines 143-175), insert a new bullet right after the `REGLAS GENERALES:` list's last bullet (`- Presta atención a las descripciones...`, line 156), before the blank line at line 157:
```python
- **REACCIONES SOCIALES DE PERSONAJES**: El sentimiento de un personaje hacia el jugador SOLO cambia por las reglas del motor del juego, nunca por tu narración. Si el estado del mundo lista "Relaciones conocidas", puedes reflejar en el diálogo/narración una rivalidad o alianza ya conocida cuando sea relevante. Si un personaje NO aparece listado en "Relaciones conocidas" junto a otro, NO inventes ninguna rivalidad, alianza o reacción entre ellos - trata a ese par como socialmente indiferente a las decisiones de grupo del jugador.
```
In the English `system_msg` (lines 231-261), insert the equivalent bullet right after the `GENERAL RULES:` list's last bullet (`- Pay attention to the descriptions...`, line 245), before the blank line at line 246:
```python
- **NPC SOCIAL REACTIONS**: A character's feeling toward the player only changes due to the game engine's own rules, never from your narration. If the world state lists "Known relationships", you may reflect an already-known rivalry or alliance in dialogue/narration when relevant. If a character is NOT listed in "Known relationships" with another character, do not invent a rivalry, alliance, or any reaction between them - treat that pair as socially indifferent to the player's party choices.
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/core/test_world.py tests/llm/test_prompts_recruitment.py -v`
Expected: PASS (12 passed in test_world.py, 3 passed in test_prompts_recruitment.py)

- [ ] **Step 6: Run the full test suite**

Run: `pytest tests/ -v`
Expected: PASS (all tests from Tasks 1-7)

- [ ] **Step 7: Commit**

```bash
git add src/ivie/core/world.py src/ivie/llm/prompts.py tests/core/test_world.py tests/llm/test_prompts_recruitment.py
git commit -m "feat: render known NPC relationships and instruct narrator to respect them"
```

---

## Manual smoke test (not automated)

After Task 7, there is no automated end-to-end test that exercises the real LLM generation pipeline (Steps 1-4) or a live game session, since that requires API credentials and is non-deterministic. Before considering this feature done, run one real world generation with `python main.py`, pick a theme, and manually verify:
1. The generated world's debug "inspect world" output (via `handle_debug_command`) shows at least one character with `recruitable=True` where narratively appropriate.
2. Asking to recruit a `friendly`/`devoted` NPC succeeds immediately.
3. Asking to recruit a `neutral`/`wary`/`hostile` NPC with a `recruitment_puzzle` presents the challenge; solving it and asking again recruits them.
4. If the generated world includes `npc_relationships`, recruiting one member changes the counterpart's `feeling` (visible via a second "inspect world" check) and the narrator does not fabricate a reaction between untagged NPCs.
