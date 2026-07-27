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
