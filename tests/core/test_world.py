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


def test_recruit_character_returns_false_and_does_not_recruit_non_recruitable_character():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    bystander = Character(name="Bystander", descriptions=["desc"], location=town, recruitable=False)
    world = World(player)
    world.add_location(town)
    world.add_character(bystander)
    assert world.recruit_character("Bystander") is False
    assert bystander.recruited is False
