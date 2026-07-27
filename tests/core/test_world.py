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


def test_render_world_lists_party_members_when_recruited():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, recruited=True)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)

    rendered_en = world.render_world(language='en')
    rendered_es = world.render_world(language='es')

    assert "Party members: Elder" in rendered_en
    assert "Miembros del grupo: Elder" in rendered_es


def test_render_world_omits_party_members_line_when_nobody_recruited():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, recruited=False)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)

    rendered_en = world.render_world(language='en')
    rendered_es = world.render_world(language='es')

    assert "Party members" not in rendered_en
    assert "Miembros del grupo" not in rendered_es


def test_render_world_does_not_render_raw_feeling_values():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.DEVOTED)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)

    rendered = world.render_world(language='en')

    # The narrator must never see the raw feeling enum value/name - only party membership.
    assert "devoted" not in rendered.lower()
    assert "DEVOTED" not in rendered


def _make_legacy_decoded_character(**overrides):
    """Build a Character the normal way, then strip it down to what a pre-recruitment
    jsonpickle payload would actually decode to: jsonpickle.decode restores __dict__
    directly without calling __init__, so a Character serialized before this branch's
    changes landed has none of the recruitment attributes in its __dict__ at all."""
    town = Location(name="Town", descriptions=["desc"])
    character = Character(name=overrides.pop("name", "LegacyNPC"), descriptions=["desc"], location=town)
    for attr in ("recruitable", "feeling", "recruited", "recruitment_puzzle"):
        delattr(character, attr)
    return character, town


def test_render_world_does_not_raise_on_legacy_world_missing_npc_relationships():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    legacy_npc, _ = _make_legacy_decoded_character(name="LegacyNPC")
    legacy_npc.location = town

    world = World(player)
    world.add_location(town)
    world.add_character(legacy_npc)
    # Simulate a World decoded from a pre-recruitment trace: no npc_relationships attribute.
    del world.npc_relationships

    rendered_en = world.render_world(language='en')
    rendered_es = world.render_world(language='es')

    assert "Known relationships" not in rendered_en
    assert "Party members" not in rendered_en
    assert "Relaciones conocidas" not in rendered_es
    assert "Miembros del grupo" not in rendered_es


def test_can_recruit_and_recruit_character_do_not_raise_on_legacy_character():
    legacy_npc, town = _make_legacy_decoded_character(name="LegacyNPC")
    player = Character(name="Player", descriptions=["desc"], location=town)
    world = World(player)
    world.add_location(town)
    world.add_character(legacy_npc)
    del world.npc_relationships

    # A legacy character has no `recruitable` at all, so it must be treated as
    # non-recruitable rather than raising AttributeError.
    assert world.can_recruit("LegacyNPC", FeelingLevel.FRIENDLY) is False
    assert world.recruit_character("LegacyNPC") is False
    assert world.get_party() == []


def test_recruit_character_does_not_raise_when_world_missing_npc_relationships():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY)
    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    # Simulate a legacy World decoded before npc_relationships existed.
    del world.npc_relationships

    assert world.recruit_character("Elder") is True
    assert npc.recruited is True


def test_relationship_ripple_does_not_raise_when_counterpart_is_a_legacy_character():
    town = Location(name="Town", descriptions=["desc"])
    player = Character(name="Player", descriptions=["desc"], location=town)
    npc = Character(name="Elder", descriptions=["desc"], location=town, recruitable=True, feeling=FeelingLevel.FRIENDLY)
    legacy_counterpart, _ = _make_legacy_decoded_character(name="LegacyAlly")
    legacy_counterpart.location = town

    world = World(player)
    world.add_location(town)
    world.add_character(npc)
    world.add_character(legacy_counterpart)
    world.npc_relationships.append(NPCRelationship(character_a="Elder", character_b="LegacyAlly", tag=RelationshipTag.ALLY))

    assert world.recruit_character("Elder") is True
    # The legacy counterpart has no `feeling` attribute; the ripple must default it to
    # NEUTRAL rather than raising, then shift it up one step for the ALLY tag.
    assert legacy_counterpart.feeling == FeelingLevel.FRIENDLY
