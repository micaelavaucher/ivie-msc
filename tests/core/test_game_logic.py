import configparser
import inspect

import streamlit as st

from src.ivie.core.game_logic import check_recruitment_request, create_game_loop
from src.ivie.core.world import World, Character, Location, Puzzle
from src.ivie.llm.structured_data_models import FeelingLevel, CharacterInteraction


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


def test_recruitment_challenge_marks_puzzle_proposed_and_is_not_repeated():
    world, npc = _world_with_recruitable_npc(FeelingLevel.NEUTRAL, recruitment_puzzle="Elder's Trust")
    world.add_puzzle(Puzzle(name="Elder's Trust", descriptions=["desc"], problem="Solve this riddle", answer="a"))

    first_response = check_recruitment_request(world, "I ask Elder to join my party", "en", config=_config_with_threshold())
    assert first_response is not None
    assert world.puzzle_states["Elder's Trust"] == 'proposed'

    second_response = check_recruitment_request(world, "I ask Elder to join my party", "en", config=_config_with_threshold())
    assert second_response is None


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


# --- Finding 4: cheap keyword filter must run before any config read ---

def test_recruitment_returns_none_for_non_recruit_message_without_touching_config():
    """A message with no recruit-intent keywords must short-circuit before load_config()/
    get_recruitment_config() ever run, so it can't crash on a missing [Recruitment]
    section. Passing a ConfigParser with no sections at all proves the reordering: if the
    function reached get_recruitment_config() it would raise KeyError('Recruitment')."""
    world, npc = _world_with_recruitable_npc(FeelingLevel.FRIENDLY)
    broken_config = configparser.ConfigParser()  # no [Recruitment] section

    response = check_recruitment_request(world, "I look around the room", "en", config=broken_config)

    assert response is None
    assert npc.recruited is False


def test_recruitment_with_no_recruit_keywords_does_not_call_load_config(monkeypatch):
    """Directly proves the ordering: load_config (a disk read) must not be invoked at all
    for a message without recruit-intent keywords."""
    import src.ivie.core.game_logic as game_logic_module

    def _fail_if_called():
        raise AssertionError("load_config() should not be called for a non-recruit-intent message")

    monkeypatch.setattr(game_logic_module, "load_config", _fail_if_called)

    world, npc = _world_with_recruitable_npc(FeelingLevel.FRIENDLY)
    response = check_recruitment_request(world, "I look around the room", "en")

    assert response is None


# --- Finding 1: legacy jsonpickle-decoded Character must not crash check_recruitment_request ---

def test_check_recruitment_request_does_not_raise_for_legacy_character():
    """A Character decoded via jsonpickle from a pre-recruitment trace has none of the
    recruitment attributes in its __dict__ at all (jsonpickle restores __dict__ directly,
    without calling __init__). check_recruitment_request must treat it as non-recruitable
    rather than raising AttributeError."""
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    legacy_npc = Character(name="LegacyNPC", descriptions=["desc"], location=town)
    for attr in ("recruitable", "feeling", "recruited", "recruitment_puzzle"):
        delattr(legacy_npc, attr)

    world = World(player)
    world.add_location(town)
    world.add_character(legacy_npc)

    response = check_recruitment_request(
        world, "I ask LegacyNPC to join my party", "en", config=_config_with_threshold(),
    )

    assert response is None


# --- Finding 2: check_recruitment_request must run before check_character_puzzle_mention ---

def test_game_loop_source_calls_recruitment_check_before_puzzle_mention():
    """Cheap, direct proof of the ordering fix: check the source text of the game_loop
    closure inside create_game_loop and confirm the recruitment check call appears before
    the puzzle-mention check call."""
    source = inspect.getsource(create_game_loop)
    recruitment_call_index = source.index("check_recruitment_request(world, message, language)")
    puzzle_mention_call_index = source.index("check_character_puzzle_mention(world, message, language)")
    assert recruitment_call_index < puzzle_mention_call_index


class _DummyModel:
    """A stand-in narrative/reasoning model. If the game loop's short-circuits work as
    expected, neither prompt_model nor prompt_model_structured should ever be reached for
    the messages exercised below."""
    model_name = "dummy-test-model"

    def prompt_model(self, **kwargs):
        raise AssertionError("prompt_model should not be called: message should have been short-circuited")

    def prompt_model_structured(self, **kwargs):
        raise AssertionError("prompt_model_structured should not be called: message should have been short-circuited")


def test_game_loop_recruitment_check_fires_before_puzzle_mention_and_puzzle_still_flows_after():
    """End-to-end (closure-level) proof for the scenario the final review flagged: a
    recruitable NPC whose interaction.proposes_puzzle points at their own
    recruitment_puzzle (the natural narrative shape the Task 7 prompts steer the LLM
    toward). Before the fix, check_character_puzzle_mention ran first and intercepted
    every mention of the NPC, so the player never saw check_recruitment_request's
    challenge narration, and the puzzle presentation repeated forever because
    check_character_puzzle_mention never marks a puzzle 'proposed'.

    After the fix, check_recruitment_request runs first: it proposes the challenge and
    marks the puzzle 'proposed'. A later message naming the same NPC then falls through
    check_recruitment_request (puzzle already proposed, not solved -> returns None) and
    reaches check_character_puzzle_mention's normal, still-functioning puzzle flow.
    """
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    interaction = CharacterInteraction(proposes_puzzle="Elder's Trust", relevance_to_objective="companionship")
    npc = Character(
        name="Elder", descriptions=["desc"], location=town, interaction=interaction,
        recruitable=True, feeling=FeelingLevel.NEUTRAL, recruitment_puzzle="Elder's Trust",
    )
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    world.add_puzzle(Puzzle(name="Elder's Trust", descriptions=["desc"], problem="Solve this riddle", answer="a"))

    st.session_state["nickname"] = "tester"
    game_loop = create_game_loop(
        world, _DummyModel(), _DummyModel(), "en", set(), enable_rag=False,
    )

    # First mention: recruit-intent message naming the recruitable NPC. Must be handled
    # by check_recruitment_request (the challenge), not check_character_puzzle_mention.
    first_response = game_loop("I ask Elder to join my party", [])
    assert first_response is not None
    assert "doesn't trust you enough" in first_response
    assert "Solve this riddle" in first_response
    assert world.puzzle_states["Elder's Trust"] == 'proposed'
    assert npc.recruited is False

    # Second mention of the same message: check_recruitment_request now falls through
    # (puzzle already 'proposed', not 'solved' -> returns None per its own logic), and
    # control reaches check_character_puzzle_mention, proving the puzzle interaction is
    # not swallowed or blocked by the recruitment stage.
    second_response = game_loop("I ask Elder to join my party", [])
    assert second_response is not None
    assert "Elder" in second_response
    assert npc.recruited is False
