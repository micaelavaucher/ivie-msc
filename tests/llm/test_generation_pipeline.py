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
