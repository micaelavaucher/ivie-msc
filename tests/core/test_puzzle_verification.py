"""Tests for engine-checkable puzzle verification and the party-invitation flow.

The bug these cover: a generated puzzle whose `answer` describes an ACTION ("Ring the Small
Silver Bell.") could only ever be solved by the player typing that sentence verbatim, so it
stayed unsolved no matter what they did. Verification now has three independent paths -
world-state conditions, accepted answer text, and the narrator's semantic judgement.
"""

import configparser

from src.ivie.core.game_logic import check_recruitment_offer_response, check_recruitment_request
from src.ivie.core.world import Character, Item, Location, Puzzle, World
from src.ivie.llm.structured_data_models import (
    FeelingLevel,
    ItemReward,
    PuzzleConditionType,
    PuzzleSolutionCondition,
    RecruitCharacterReward,
    RewardType,
)


def _config_with_threshold(threshold="friendly", enabled="true"):
    config = configparser.ConfigParser()
    config.read_string(f"""
[Recruitment]
enabled = {enabled}
feeling_threshold = {threshold}
""")
    return config


def _bell_world():
    """The exact shape that exposed the bug: an observation puzzle whose answer is an action."""
    entrance = Location(name="The Sun-Drenched Entrance", descriptions=["warm grass"])
    bell = Item(name="Small Silver Bell", descriptions=["a tiny polished bell"])
    ribbon = Item(name="Royal Velvet Ribbon", descriptions=["a crimson ribbon"])
    entrance.items.append(bell)

    player = Character(name="Tabby Scout", descriptions=["a nimble tabby"], location=entrance)
    queen = Character(name="The Queen of Cats", descriptions=["a majestic white cat"],
                      location=entrance, inventory=[ribbon])

    puzzle = Puzzle(
        name="The Queen's Nap",
        descriptions=["waking the royal authority"],
        problem="The Queen of Cats is asleep and will not speak to you.",
        answer="Ring the Small Silver Bell.",
        puzzle_type="observation",
        proposed_by_character="The Queen of Cats",
        rewards=[ItemReward(reward_type=RewardType.ITEM, description="the ribbon", item_name="Royal Velvet Ribbon")],
        solution_conditions=[
            PuzzleSolutionCondition(
                condition_type=PuzzleConditionType.HAS_ITEM,
                description="The player is carrying the Small Silver Bell.",
                item_name="Small Silver Bell",
            ),
            PuzzleSolutionCondition(
                condition_type=PuzzleConditionType.TALKED_TO_CHARACTER,
                description="The player has interacted with the Queen.",
                character_name="The Queen of Cats",
            ),
        ],
    )

    world = World(player)
    world.add_location(entrance)
    world.add_item(bell)
    world.add_item(ribbon)
    world.add_character(queen)
    world.add_puzzle(puzzle)
    return world, player, queen, bell


# --- Path 1: engine-checkable world-state conditions ---------------------------------

def test_conditions_unsatisfied_while_the_player_has_done_nothing():
    world, _, _, _ = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'proposed'

    assert world.check_puzzle_conditions() == []
    assert world.puzzle_states["The Queen's Nap"] == 'proposed'


def test_acting_out_the_solution_solves_the_puzzle_without_stating_the_answer():
    world, player, _, bell = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'proposed'

    # The player takes the bell and engages the Queen - never typing "Ring the Small Silver Bell."
    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    assert world.check_puzzle_conditions() == ["The Queen's Nap"]
    assert world.puzzle_states["The Queen's Nap"] == 'solved'


def test_partial_conditions_do_not_solve_the_puzzle():
    world, player, _, bell = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'proposed'

    # Holding the bell but never engaging the Queen: ALL conditions must hold, not any.
    player.save_item(bell, player.location)

    assert world.check_puzzle_conditions() == []
    assert world.puzzle_states["The Queen's Nap"] == 'proposed'


def test_conditions_only_fire_for_a_puzzle_that_was_actually_proposed():
    world, player, _, bell = _bell_world()
    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    # Still 'not_proposed': the player can't stumble into solving a challenge never set them.
    assert world.check_puzzle_conditions() == []
    assert world.puzzle_states["The Queen's Nap"] == 'not_proposed'


def test_solved_puzzle_hands_over_its_item_reward():
    world, player, queen, bell = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'proposed'
    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    world.check_puzzle_conditions()

    assert [item.name for item in player.inventory].count("Royal Velvet Ribbon") == 1
    assert queen.inventory == []


def test_condition_matching_tolerates_name_drift_from_the_generator():
    world, player, _, bell = _bell_world()
    world.puzzles["The Queen's Nap"].solution_conditions[1].character_name = "the queen"
    world.puzzle_states["The Queen's Nap"] = 'proposed'

    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    assert world.check_puzzle_conditions() == ["The Queen's Nap"]


# --- Path 2 & 3: accepted answers and the narrator's semantic judgement ---------------

def test_accepted_answers_widen_the_text_match():
    world, _, _, _ = _bell_world()
    world.puzzles["The Queen's Nap"].solution_conditions = []
    world.puzzles["The Queen's Nap"].accepted_answers = ["ring the bell", "the silver bell"]

    assert world.solve_puzzle("The Queen's Nap", "Ring the bell") is True
    assert world.puzzle_states["The Queen's Nap"] == 'solved'


def test_narrator_judgement_solves_an_action_puzzle_that_matches_no_text():
    world, _, _, _ = _bell_world()
    world.puzzles["The Queen's Nap"].solution_conditions = []

    # This is the exact player phrasing from the reported session.
    solved = world.solve_puzzle("The Queen's Nap", "take the silver bell and wake her up", llm_verified=True)

    assert solved is True
    assert world.puzzle_states["The Queen's Nap"] == 'solved'


def test_a_wrong_answer_the_narrator_rejected_still_fails():
    world, _, _, _ = _bell_world()
    world.puzzles["The Queen's Nap"].solution_conditions = []

    assert world.solve_puzzle("The Queen's Nap", "I shout at her", llm_verified=False) is False
    assert world.puzzle_states["The Queen's Nap"] != 'solved'


# --- The party invitation --------------------------------------------------------------

def test_solving_an_npc_puzzle_queues_an_invitation_but_never_auto_recruits():
    world, player, queen, bell = _bell_world()
    world.puzzle_states["The Queen's Nap"] = 'proposed'
    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    world.check_puzzle_conditions()

    assert world.pending_recruitment_offer == "The Queen of Cats"
    assert queen.recruited is False
    # An NPC who was never flagged recruitable becomes so by setting the player a challenge.
    assert queen.recruitable is True


def test_yes_recruits_the_character_and_clears_the_offer():
    world, _, queen, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"
    queen.recruitable = True

    response = check_recruitment_offer_response(world, "yes", "en")

    assert response is not None
    assert queen.recruited is True
    assert world.pending_recruitment_offer is None
    assert queen in world.get_party()


def test_no_declines_without_recruiting_and_clears_the_offer():
    world, _, queen, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"
    queen.recruitable = True

    response = check_recruitment_offer_response(world, "no thanks", "en")

    assert response is not None
    assert queen.recruited is False
    assert world.pending_recruitment_offer is None


def test_not_now_is_read_as_a_refusal_not_as_the_yes_inside_it():
    world, _, queen, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"
    queen.recruitable = True

    check_recruitment_offer_response(world, "not now", "en")

    assert queen.recruited is False
    assert world.pending_recruitment_offer is None


def test_an_unrelated_action_leaves_the_offer_open():
    world, _, queen, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"
    queen.recruitable = True

    # Falling through must not be read as a refusal, or a stray move would silently
    # cost the player the companion they just earned.
    assert check_recruitment_offer_response(world, "I look around the entrance", "en") is None
    assert world.pending_recruitment_offer == "The Queen of Cats"
    assert queen.recruited is False


def test_spanish_offer_response_is_understood():
    world, _, queen, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"
    queen.recruitable = True

    response = check_recruitment_offer_response(world, "sí, únete a mí", "es")

    assert response is not None
    assert queen.recruited is True


def test_recruit_reward_offers_the_named_character_rather_than_the_proposer():
    world, player, queen, bell = _bell_world()
    ally = Character(name="Sir Pounce-a-Lot", descriptions=["an elderly tabby"],
                     location=player.location, recruitable=True, feeling=FeelingLevel.NEUTRAL)
    world.add_character(ally)
    world.puzzles["The Queen's Nap"].rewards = [
        RecruitCharacterReward(reward_type=RewardType.RECRUIT_CHARACTER,
                               description="Sir Pounce-a-Lot joins you",
                               character_name="Sir Pounce-a-Lot")
    ]
    world.puzzle_states["The Queen's Nap"] = 'proposed'
    player.save_item(bell, player.location)
    world.record_interaction("The Queen of Cats")

    world.check_puzzle_conditions()

    assert world.pending_recruitment_offer == "Sir Pounce-a-Lot"
    assert ally.recruited is False


def test_asking_to_recruit_after_solving_the_challenge_succeeds():
    """The player can also just ask outright once the challenge is behind them."""
    world, _, queen, _ = _bell_world()
    queen.recruitable = True
    queen.recruitment_puzzle = "The Queen's Nap"
    world.puzzle_states["The Queen's Nap"] = 'solved'

    response = check_recruitment_request(world, "The Queen of Cats, will you join my party?", "en",
                                         config=_config_with_threshold())

    assert response is not None
    assert queen.recruited is True


# --- Party visibility in the chat state block -----------------------------------------

def test_party_line_is_shown_in_the_chat_state_summary():
    world, _, queen, _ = _bell_world()
    queen.recruitable = True

    empty_state = world.format_world_state_for_chat(language='en')
    assert "Characters in your party:" in empty_state
    assert "Nobody" in empty_state

    world.recruit_character("The Queen of Cats")
    joined_state = world.format_world_state_for_chat(language='en')
    assert "Characters in your party:" in joined_state
    assert "The Queen of Cats" in joined_state.split("Characters in your party:")[1]


def test_pending_offer_is_surfaced_in_the_chat_state_summary():
    world, _, _, _ = _bell_world()
    world.pending_recruitment_offer = "The Queen of Cats"

    state = world.format_world_state_for_chat(language='en')
    assert "waiting for your answer" in state


def test_spanish_party_line_is_shown():
    world, _, queen, _ = _bell_world()
    queen.recruitable = True
    world.recruit_character("The Queen of Cats")

    state = world.format_world_state_for_chat(language='es')
    assert "Personajes en tu grupo:" in state
    assert "The Queen of Cats" in state.split("Personajes en tu grupo:")[1]


# --- Legacy traces ---------------------------------------------------------------------

def test_legacy_world_without_the_new_attributes_does_not_raise():
    """A World decoded by jsonpickle from a pre-verification trace has none of these
    attributes, since jsonpickle restores __dict__ without calling __init__."""
    world, _, _, _ = _bell_world()
    del world.interacted_characters
    del world.pending_recruitment_offer

    world.record_interaction("The Queen of Cats")
    assert world.format_world_state_for_chat(language='en')
    assert check_recruitment_offer_response(world, "yes", "en") is None
