"""Tests for the debug-mode reports used to manually inspect recruitment and puzzle state.

These are the views a tester reads to answer "why can't I recruit this NPC yet?", so they must
show the live verdict rather than the raw fields, and must never crash on a legacy world
restored from a trace recorded before recruitment existed.
"""

from src.ivie.core.game_logic import handle_debug_command
from src.ivie.core.world import Character, Item, Location, NPCRelationship, Puzzle, World
from src.ivie.core.world_builder import (
    generate_npc_debug_report,
    generate_puzzle_debug_report,
    generate_world_overview,
)
from src.ivie.llm.structured_data_models import (
    FeelingLevel,
    PuzzleConditionType,
    PuzzleSolutionCondition,
    RelationshipTag,
)


def _bell_world():
    entrance = Location(name="The Entrance", descriptions=["warm grass"])
    shrine = Location(name="The Shrine", descriptions=["cold stone"])
    bell = Item(name="Small Silver Bell", descriptions=["a tiny polished bell"])
    entrance.items.append(bell)

    player = Character(name="Tabby Scout", descriptions=["a nimble tabby"], location=entrance)
    queen = Character(name="The Queen of Cats", descriptions=["a majestic white cat"], location=entrance,
                      recruitable=True, feeling=FeelingLevel.NEUTRAL, recruitment_puzzle="The Queen's Nap")
    mouse = Character(name="Grey Mouse", descriptions=["a wary mouse"], location=shrine,
                      recruitable=False, feeling=FeelingLevel.WARY)

    puzzle = Puzzle(
        name="The Queen's Nap",
        descriptions=["waking the royal authority"],
        problem="The Queen of Cats is asleep and will not speak to you.",
        answer="Ring the Small Silver Bell.",
        proposed_by_character="The Queen of Cats",
        accepted_answers=["the bell"],
        solution_conditions=[
            PuzzleSolutionCondition(
                condition_type=PuzzleConditionType.HAS_ITEM,
                description="The player is carrying the Small Silver Bell.",
                item_name="Small Silver Bell",
            ),
        ],
    )

    world = World(player)
    world.add_location(entrance)
    world.add_location(shrine)
    world.add_item(bell)
    world.add_character(queen)
    world.add_character(mouse)
    world.add_puzzle(puzzle)
    world.npc_relationships = [NPCRelationship("The Queen of Cats", "Grey Mouse", RelationshipTag.RIVAL)]
    return world, player, bell


def test_npc_report_explains_why_a_character_cannot_be_recruited_yet():
    world, _, _ = _bell_world()

    report = generate_npc_debug_report(world, 'en')

    assert "The Queen of Cats" in report
    assert "The Queen's Nap" in report
    assert "not_proposed" in report
    # The verdict, not just the raw flags: the threshold is what she is short of.
    assert "friendly" in report
    assert "CAN BE RECRUITED" not in report


def test_npc_report_flips_to_recruitable_once_the_challenge_is_solved():
    world, _, _ = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'solved'

    report = generate_npc_debug_report(world, 'en')

    assert "CAN BE RECRUITED" in report
    assert "challenge solved" in report


def test_npc_report_shows_party_membership_relationships_and_a_pending_offer():
    world, _, _ = _bell_world()
    world.characters["The Queen of Cats"].recruited = True
    world.pending_recruitment_offer = "Grey Mouse"

    report = generate_npc_debug_report(world, 'en')

    assert "IN PARTY" in report
    assert "rival" in report and "Grey Mouse" in report
    assert "awaiting your yes/no" in report


def test_puzzle_report_marks_which_conditions_currently_hold():
    world, player, bell = _bell_world()

    before = generate_puzzle_debug_report(world, 'en')
    assert "has_item" in before and "Small Silver Bell" in before
    assert "⬜ `has_item`" in before

    player.save_item(bell, player.location)
    after = generate_puzzle_debug_report(world, 'en')
    assert "✅ `has_item`" in after
    # All three verification routes are visible: conditions, accepted text, and the answer.
    assert "the bell" in after
    assert "Ring the Small Silver Bell." in after


def test_debug_commands_route_to_the_reports_in_both_languages():
    world, _, _ = _bell_world()

    assert "NPCs & RECRUITMENT" in handle_debug_command("npc list", world, 'en')
    assert "NPCs & RECRUITMENT" in handle_debug_command("npcs", world, 'en')
    assert "NPCs Y RECLUTAMIENTO" in handle_debug_command("lista npcs", world, 'es')
    assert "PUZZLES" in handle_debug_command("puzzle list", world, 'en')
    assert "PUZZLES" in handle_debug_command("lista puzzles", world, 'es')
    assert handle_debug_command("look around", world, 'en') is None


def test_world_overview_counts_recruitable_npcs_solved_puzzles_and_the_party():
    world, _, _ = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'solved'
    world.characters["The Queen of Cats"].recruited = True

    overview = generate_world_overview(world, 'en')

    assert "1 recruitable" in overview
    assert "1 solved" in overview
    assert "The Queen of Cats" in overview


def test_reports_survive_a_legacy_world_missing_every_recruitment_attribute():
    """jsonpickle restores __dict__ without calling __init__, so a pre-recruitment trace has
    none of these attributes - the debug views must degrade rather than raise."""
    location = Location(name="Old Hall", descriptions=["dusty"])
    player = Character(name="Player", descriptions=["you"], location=location)
    npc = Character(name="Old NPC", descriptions=["from before"], location=location)

    world = World(player)
    world.add_location(location)
    world.add_character(npc)
    for attribute in ('interacted_characters', 'pending_recruitment_offer', 'npc_relationships'):
        delattr(world, attribute)
    for attribute in ('recruitable', 'recruited', 'feeling', 'recruitment_puzzle'):
        delattr(npc, attribute)

    assert "Old NPC" in generate_npc_debug_report(world, 'en')
    assert generate_puzzle_debug_report(world, 'en')
    assert "Nobody" in generate_world_overview(world, 'en')
