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


# --- Verifiability repair: no puzzle may be solvable only by exact free-text match ---

def test_verifiability_fix_derives_conditions_for_an_action_puzzle():
    """The reported failure case: an answer that describes an action, not a word to say."""
    from src.ivie.llm.generation_pipeline import verify_puzzle_verifiability_and_fix
    from src.ivie.llm.structured_data_models import GeneratedItem, ItemActionType, PuzzleConditionType

    character = GeneratedCharacter(name="The Queen of Cats", descriptions=["desc"], location="Town Square")
    puzzle = GeneratedPuzzle(
        name="The Queen's Nap", puzzle_type=PuzzleType.OBSERVATION, descriptions=["desc"],
        problem="The Queen is asleep.", answer="Ring the Small Silver Bell.",
        proposed_by_character="The Queen of Cats", rewards=[],
        relevance_to_objective="unlocks the path", hint="talk to the Queen",
    )
    world = _minimal_generated_world(characters=[character], puzzles=[puzzle])
    world.items.append(GeneratedItem(name="Small Silver Bell", action_type=ItemActionType.SOLVE_PUZZLE,
                                     descriptions=["a tiny bell"]))

    _, fixed_world = verify_puzzle_verifiability_and_fix(world)

    conditions = fixed_world.puzzles[0].solution_conditions
    assert conditions, "an action puzzle left with no checkable condition is unsolvable"
    assert any(c.condition_type == PuzzleConditionType.HAS_ITEM and c.item_name == "Small Silver Bell"
               for c in conditions)
    assert any(c.condition_type == PuzzleConditionType.TALKED_TO_CHARACTER
               and c.character_name == "The Queen of Cats" for c in conditions)


def test_verifiability_fix_leaves_hand_authored_conditions_alone():
    from src.ivie.llm.generation_pipeline import verify_puzzle_verifiability_and_fix
    from src.ivie.llm.structured_data_models import PuzzleConditionType, PuzzleSolutionCondition

    existing = PuzzleSolutionCondition(condition_type=PuzzleConditionType.PLAYER_AT_LOCATION,
                                       description="be at the square", location_name="Town Square")
    puzzle = GeneratedPuzzle(
        name="Arrival", puzzle_type=PuzzleType.OBSERVATION, descriptions=["desc"], problem="p",
        answer="Walk to the square", rewards=[], relevance_to_objective="x", hint="x",
        solution_conditions=[existing],
    )
    world = _minimal_generated_world(characters=[], puzzles=[puzzle])

    _, fixed_world = verify_puzzle_verifiability_and_fix(world)

    assert fixed_world.puzzles[0].solution_conditions == [existing]


def test_verifiability_fix_widens_answers_when_no_condition_can_be_derived():
    """A riddle names no world object, so it stays a text puzzle - but a bare exact match on
    the full sentence is too strict, so the answer minus its leading verb is also accepted."""
    from src.ivie.llm.generation_pipeline import verify_puzzle_verifiability_and_fix

    puzzle = GeneratedPuzzle(
        name="Echo Riddle", puzzle_type=PuzzleType.RIDDLE, descriptions=["desc"],
        problem="I speak without a mouth.", answer="An echo", rewards=[],
        relevance_to_objective="x", hint="x",
    )
    world = _minimal_generated_world(characters=[], puzzles=[puzzle])

    _, fixed_world = verify_puzzle_verifiability_and_fix(world)

    assert "echo" in fixed_world.puzzles[0].accepted_answers


def test_no_generated_puzzle_is_left_wholly_unverifiable():
    from src.ivie.llm.generation_pipeline import verify_puzzle_verifiability_and_fix
    from src.ivie.llm.structured_data_models import GeneratedItem, ItemActionType

    puzzles = [
        GeneratedPuzzle(name="Action", puzzle_type=PuzzleType.OBSERVATION, descriptions=["d"], problem="p",
                        answer="Ring the Small Silver Bell", proposed_by_character="Queen", rewards=[],
                        relevance_to_objective="x", hint="x"),
        GeneratedPuzzle(name="Riddle", puzzle_type=PuzzleType.RIDDLE, descriptions=["d"], problem="p",
                        answer="An echo", rewards=[], relevance_to_objective="x", hint="x"),
    ]
    character = GeneratedCharacter(name="Queen", descriptions=["desc"], location="Town Square")
    world = _minimal_generated_world(characters=[character], puzzles=puzzles)
    world.items.append(GeneratedItem(name="Small Silver Bell", action_type=ItemActionType.SOLVE_PUZZLE,
                                     descriptions=["a tiny bell"]))

    _, fixed_world = verify_puzzle_verifiability_and_fix(world)

    for puzzle in fixed_world.puzzles:
        assert puzzle.solution_conditions or puzzle.accepted_answers, \
            f"puzzle '{puzzle.name}' has no verification path and can never be solved"
