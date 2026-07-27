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
