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
