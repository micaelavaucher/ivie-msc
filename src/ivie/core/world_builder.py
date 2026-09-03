"""World builder helpers for generating and expanding worlds."""

import json
import jsonpickle
from typing import Dict

from .world import World, Location, Item, Character, Puzzle, NPCRelationship
from ..llm.structured_data_models import GeneratedWorld, WorldExpansion, RecruitCharacterReward, FeelingLevel


def _find_recruitment_puzzle_for_character(character_name: str, puzzles_dict: Dict[str, Puzzle]) -> str:
    """Find the puzzle that gates recruiting this character.

    A RecruitCharacterReward naming them wins; otherwise any puzzle they propose serves as
    their challenge, since solving a character's puzzle is what earns their party invitation.
    """
    for puzzle in puzzles_dict.values():
        for reward in puzzle.rewards:
            if isinstance(reward, RecruitCharacterReward) and reward.character_name == character_name:
                return puzzle.name

    for puzzle in puzzles_dict.values():
        if puzzle.proposed_by_character == character_name:
            return puzzle.name
    return None


def create_world_from_trace(trace_data: dict) -> World:
    try:
        if not trace_data:
            raise ValueError("Trace data is empty or None")

        if "turns" not in trace_data or "0" not in trace_data["turns"]:
            raise ValueError("Trace data missing required 'turns' or turn 0")

        turn_0 = trace_data["turns"]["0"]
        if "initial_symbolic_world_state" not in turn_0:
            raise ValueError("Turn 0 missing 'initial_symbolic_world_state'")

        initial_state = turn_0["initial_symbolic_world_state"]
        world = jsonpickle.decode(initial_state)

        if not isinstance(world, World):
            raise ValueError(f"Decoded object is not a World instance, got {type(world)}")

        print(f"World successfully reconstructed from trace")
        print(f"   - Player: {world.player.name}")
        print(f"   - Starting location: {world.player.location.name}")
        print(f"   - Total locations: {len(world.locations)}")
        print(f"   - Total items: {len(world.items)}")
        print(f"   - Total characters: {len(world.characters)}")

        return world
        
    except Exception as e:
        print(f"❌ Error reconstructing world from trace: {e}")
        raise

def create_world_from_llm_response(world_data) -> World:
    try:
        if isinstance(world_data, GeneratedWorld):
            generated_world = world_data
        elif isinstance(world_data, dict):
            generated_world = GeneratedWorld.model_validate(world_data)
        else:
            data = json.loads(world_data)
            generated_world = GeneratedWorld.model_validate(data)

        items_dict: Dict[str, Item] = {}
        for item_data in generated_world.items:
            item = Item(name=item_data.name, descriptions=item_data.descriptions, gettable=item_data.gettable)
            items_dict[item_data.name] = item

        puzzles_dict: Dict[str, Puzzle] = {}
        for puzzle_data in generated_world.puzzles:
            puzzle = Puzzle(
                name=puzzle_data.name,
                descriptions=puzzle_data.descriptions,
                problem=puzzle_data.problem,
                answer=puzzle_data.answer,
                puzzle_type=getattr(puzzle_data, 'puzzle_type', 'riddle'),
                proposed_by_character=getattr(puzzle_data, 'proposed_by_character', None),
                proposed_by_location=getattr(puzzle_data, 'proposed_by_location', None),
                rewards=getattr(puzzle_data, 'rewards', []),
                relevance_to_objective=getattr(puzzle_data, 'relevance_to_objective', None),
                puzzle_hints=getattr(puzzle_data, 'puzzle_hints', []),
                interaction_hint=getattr(puzzle_data, 'interaction_hint', None),
                accepted_answers=getattr(puzzle_data, 'accepted_answers', []),
                solution_conditions=getattr(puzzle_data, 'solution_conditions', []),
            )
            puzzles_dict[puzzle_data.name] = puzzle

        locations_dict: Dict[str, Location] = {}
        for loc_data in generated_world.locations:
            location_items = [items_dict[item_name] for item_name in getattr(loc_data, 'items', []) if item_name in items_dict]
            location = Location(name=loc_data.name, descriptions=loc_data.descriptions, items=location_items)
            locations_dict[loc_data.name] = location

        # Connect locations
        for loc_data in generated_world.locations:
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                for connected_loc_name in getattr(loc_data, 'connecting_locations', []):
                    if connected_loc_name in locations_dict:
                        connected_location = locations_dict[connected_loc_name]
                        if connected_location not in location.connecting_locations:
                            location.connecting_locations.append(connected_location)
                        if location not in connected_location.connecting_locations:
                            connected_location.connecting_locations.append(location)

        # Handle blocked passages
        for loc_data in generated_world.locations:
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                for blocked in getattr(loc_data, 'blocked_passages', []):
                    if blocked.location in locations_dict:
                        blocked_location = locations_dict[blocked.location]
                        if blocked_location not in location.connecting_locations:
                            location.connecting_locations.append(blocked_location)
                            blocked_location.connecting_locations.append(location)

                        blocking_element = None
                        requirement = getattr(blocked, 'required_to_unblock', None)
                        if requirement:
                            req_type = requirement.requirement_type.value if hasattr(requirement.requirement_type, 'value') else str(requirement.requirement_type)
                            if req_type.lower() == 'puzzle':
                                puzzle_name = getattr(requirement, 'puzzle_name', None)
                                if puzzle_name and puzzle_name in puzzles_dict:
                                    blocking_element = puzzles_dict[puzzle_name]
                            elif req_type.lower() == 'item':
                                item_name = getattr(requirement, 'item_name', None)
                                if item_name and item_name in items_dict:
                                    blocking_element = items_dict[item_name]

                        if blocking_element:
                            if blocked_location.name not in location.blocked_locations:
                                location.block_passage(blocked_location, blocking_element)
                            else:
                                print(f"[WARNING] Skipping duplicate blocked passage: {location.name} -> {blocked_location.name}")

        player_data = generated_world.player
        player_inventory = [items_dict[item_name] for item_name in getattr(player_data, 'inventory', []) if item_name in items_dict]
        player_location = locations_dict.get(getattr(player_data, 'location', None))
        if not player_location and locations_dict:
            player_location = next(iter(locations_dict.values()))

        player = Character(name=player_data.name, descriptions=player_data.descriptions, location=player_location, inventory=player_inventory)
        if player_location:
            player_location.visited = True

        characters_list = []
        for char_data in generated_world.characters:
            char_inventory = [items_dict[item_name] for item_name in getattr(char_data, 'inventory', []) if item_name in items_dict]
            char_location = locations_dict.get(getattr(char_data, 'location', None), player_location)
            recruitment_puzzle = _find_recruitment_puzzle_for_character(char_data.name, puzzles_dict)
            # A character who sets the player a challenge is recruitable by definition: passing
            # their test is what earns the invitation, so they don't need the generator to have
            # remembered to flag them.
            recruitable = getattr(char_data, 'recruitable', False) or recruitment_puzzle is not None
            character = Character(
                name=char_data.name, descriptions=char_data.descriptions, location=char_location,
                inventory=char_inventory, interaction=getattr(char_data, 'interaction', None),
                recruitable=recruitable,
                feeling=getattr(char_data, 'initial_feeling', FeelingLevel.NEUTRAL),
                recruitment_puzzle=recruitment_puzzle,
            )
            characters_list.append(character)

        world = World(player)
        for location in locations_dict.values():
            world.add_location(location)
        for item in items_dict.values():
            world.add_item(item)
        for character in characters_list:
            world.add_character(character)
        for puzzle in puzzles_dict.values():
            world.add_puzzle(puzzle)

        for relationship_data in getattr(generated_world, 'npc_relationships', []):
            world.npc_relationships.append(NPCRelationship(
                character_a=relationship_data.character_a,
                character_b=relationship_data.character_b,
                tag=relationship_data.tag,
            ))

        if getattr(generated_world, 'objective', None):
            world.objective_data = generated_world.objective
            world.objective = set_objective_from_generated(generated_world.objective, items_dict, locations_dict, characters_list, player)

        return world
    except Exception as e:
        print(f"Error creating world from LLM response: {e}")
        import traceback
        traceback.print_exc()
        import examples.example_worlds as example_worlds
        return example_worlds.get_world("1")

def set_objective_from_generated(objective_data, items_dict, locations_dict, characters_list, player):
    try:
        obj_type = objective_data.type.value if hasattr(objective_data.type, 'value') else str(objective_data.type)
        components = getattr(objective_data, 'components', [])

        if obj_type.lower() in ["get_item"]:
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.lower() == "item" and component.name in items_dict:
                    return (player, items_dict[component.name])

        if obj_type.lower() in ["reach_location"]:
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.lower() == "location" and component.name in locations_dict:
                    return (player, locations_dict[component.name])

        if obj_type.lower() in ["find_character"]:
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.lower() == "character":
                    character = next((c for c in characters_list if c.name == component.name), None)
                    if character:
                        return (player, character)

        if obj_type.lower() in ["deliver_an_item"]:
            item_component = None
            target_component = None
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.lower() == "item":
                    item_component = component
                elif component_type.lower() in ["location", "character"]:
                    target_component = component

            if item_component and target_component and item_component.name in items_dict:
                target_type = target_component.component_type.value if hasattr(target_component.component_type, 'value') else str(target_component.component_type)
                if target_type.lower() == "location" and target_component.name in locations_dict:
                    return (items_dict[item_component.name], locations_dict[target_component.name])
                elif target_type.lower() == "character":
                    character = next((c for c in characters_list if c.name == target_component.name), None)
                    if character:
                        return (items_dict[item_component.name], character)

        if obj_type.lower() in ["solve_mystery"]:
            from .world import MysteryObjective, MysteryClue
            valid_clues = []
            for clue_data in getattr(objective_data, 'mystery_clues', []) or []:
                if clue_data.associated_item in items_dict:
                    if clue_data.item_location:
                        if clue_data.item_location in locations_dict:
                            location = locations_dict[clue_data.item_location]
                            if clue_data.associated_item in [item.name for item in getattr(location, 'items', [])]:
                                clue = MysteryClue(name=clue_data.name, description=clue_data.description, associated_item=clue_data.associated_item, relevance_to_mystery=clue_data.relevance_to_mystery, discovered=clue_data.discovered, item_location=clue_data.item_location)
                                valid_clues.append(clue)
                    else:
                        clue = MysteryClue(name=clue_data.name, description=clue_data.description, associated_item=clue_data.associated_item, relevance_to_mystery=clue_data.relevance_to_mystery, discovered=clue_data.discovered)
                        valid_clues.append(clue)

            if valid_clues:
                mystery_solution = getattr(objective_data, 'mystery_solution', 'Mystery solution not specified')
                mystery_objective = MysteryObjective(name=f"Mystery: {objective_data.description}", description=objective_data.description, clues=valid_clues, mystery_solution=mystery_solution)
                print(f"   ✅ Created mystery objective with {len(valid_clues)} valid clues")
                return (player, mystery_objective)
            else:
                print(f"   ❌ No valid clues for mystery objective - skipping mystery creation")
                return None

        description = getattr(objective_data, 'description', '').lower()
        for item_name in items_dict:
            if item_name.lower() in description:
                return (player, items_dict[item_name])
        for location_name in locations_dict:
            if location_name.lower() in description:
                return (player, locations_dict[location_name])

        print("   ❌ No se pudo establecer objetivo")
        return None
    except Exception as e:
        print(f"Error setting objective: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_objective_components(world: World) -> tuple:
    missing_components = []
    validation_details = ""

    if not hasattr(world, 'objective') or not world.objective:
        return False, ["Objective not defined"], "No objective is set for this world"

    if hasattr(world, 'objective_data') and world.objective_data:
        objective_data = world.objective_data
        obj_type = objective_data.type.value if hasattr(objective_data.type, 'value') else str(objective_data.type)

        for component in getattr(objective_data, 'components', []):
            component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
            component_name = component.name

            if component_type.upper() == "ITEM":
                if component_name not in world.items:
                    missing_components.append(f"Item '{component_name}' does not exist in world registry")
                else:
                    item_found = False
                    for location in world.locations.values():
                        if any(getattr(item, 'name', None) == component_name for item in getattr(location, 'items', []) if location.items):
                            item_found = True
                            break
                    if not item_found:
                        for character in world.characters.values():
                            if any(getattr(item, 'name', None) == component_name for item in getattr(character, 'inventory', []) if character.inventory):
                                item_found = True
                                break
                    if not item_found:
                        missing_components.append(f"Item '{component_name}' exists in registry but is not accessible (not placed in any location or inventory)")

            elif component_type.upper() == "LOCATION":
                if component_name not in world.locations:
                    missing_components.append(f"Location '{component_name}' (required for objective)")
            elif component_type.upper() == "CHARACTER":
                character_exists = any(c.name == component_name for c in world.characters.values())
                if not character_exists:
                    missing_components.append(f"Character '{component_name}' (required for objective)")

        obj_first = world.objective[0]
        obj_second = world.objective[1]

        if obj_type.upper() == "DELIVER_AN_ITEM":
            item_component = None
            target_component = None
            for component in objective_data.components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "ITEM":
                    item_component = component
                elif component_type.upper() in ["LOCATION", "CHARACTER"]:
                    target_component = component

            if item_component and target_component:
                expected_item = world.items.get(item_component.name)
                if target_component.component_type.value.upper() == "LOCATION":
                    expected_target = world.locations.get(target_component.name)
                else:
                    expected_target = next((c for c in world.characters.values() if c.name == target_component.name), None)
                if obj_first != expected_item or obj_second != expected_target:
                    missing_components.append(f"Objective tuple mismatch: expected ({item_component.name}, {target_component.name}) but got ({getattr(obj_first, 'name', str(obj_first))}, {getattr(obj_second, 'name', str(obj_second))})")

        if obj_type.upper() == "GET_ITEM":
            item_component = None
            for component in objective_data.components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "ITEM":
                    item_component = component
                    break
            if item_component:
                expected_item = world.items.get(item_component.name)
                if obj_first != world.player or obj_second != expected_item:
                    missing_components.append(f"Objective tuple mismatch: expected (player, {item_component.name}) but got ({getattr(obj_first, 'name', str(obj_first))}, {getattr(obj_second, 'name', str(obj_second))})")

        if obj_type.upper() == "REACH_LOCATION":
            location_component = None
            for component in objective_data.components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "LOCATION":
                    location_component = component
                    break
            if location_component:
                expected_location = world.locations.get(location_component.name)
                if obj_first != world.player or obj_second != expected_location:
                    missing_components.append(f"Objective tuple mismatch: expected (player, {location_component.name}) but got ({getattr(obj_first, 'name', str(obj_first))}, {getattr(obj_second, 'name', str(obj_second))})")

        if obj_type.upper() == "FIND_CHARACTER":
            character_component = None
            for component in objective_data.components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "CHARACTER":
                    character_component = component
                    break
            if character_component:
                expected_character = next((c for c in world.characters.values() if c.name == character_component.name), None)
                if obj_first != world.player or obj_second != expected_character:
                    missing_components.append(f"Objective tuple mismatch: expected (player, {character_component.name}) but got ({getattr(obj_first, 'name', str(obj_first))}, {getattr(obj_second, 'name', str(obj_second))})")

        if obj_type.upper() == "SOLVE_MYSTERY" and hasattr(objective_data, 'mystery_clues') and objective_data.mystery_clues:
            for clue in objective_data.mystery_clues:
                if clue.associated_item not in world.items:
                    missing_components.append(f"Clue item '{clue.associated_item}' (required for mystery clue '{clue.name}')")
                if clue.item_location and clue.item_location not in world.locations:
                    missing_components.append(f"Clue location '{clue.item_location}' (required for mystery clue '{clue.name}')")
    else:
        obj_first = world.objective[0]
        obj_second = world.objective[1]
        if hasattr(obj_first, 'name'):
            if obj_first.__class__.__name__ == "Character":
                character_exists = any(c.name == obj_first.name for c in world.characters.values())
                if not character_exists:
                    missing_components.append(f"Character '{obj_first.name}' (objective component)")
            elif obj_first.__class__.__name__ == "Item":
                if obj_first.name not in world.items:
                    missing_components.append(f"Item '{obj_first.name}' (objective component)")

        if hasattr(obj_second, 'name'):
            if obj_second.__class__.__name__ == "Character":
                character_exists = any(c.name == obj_second.name for c in world.characters.values())
                if not character_exists:
                    missing_components.append(f"Character '{obj_second.name}' (objective component)")
            elif obj_second.__class__.__name__ == "Item":
                if obj_second.name not in world.items:
                    missing_components.append(f"Item '{obj_second.name}' (objective component)")
            elif obj_second.__class__.__name__ == "Location":
                if obj_second.name not in world.locations:
                    missing_components.append(f"Location '{obj_second.name}' (objective component)")

    is_valid = len(missing_components) == 0
    validation_details = "All objective components exist and match the expected objective structure" if is_valid else f"Found {len(missing_components)} issue(s) with the objective"
    return is_valid, missing_components, validation_details


def generate_world_overview(world: World, language: str = 'es') -> str:
    puzzles_count = 0
    if hasattr(world, 'puzzles'):
        puzzles_count = len(world.puzzles) if isinstance(world.puzzles, (dict, list)) else 0

    npc_count = len([c for c in world.characters.values() if c != world.player])

    # getattr defaults throughout: a World/Character restored by jsonpickle from a trace
    # recorded before recruitment existed has none of these attributes.
    npcs = [c for c in world.characters.values() if c != world.player]
    recruitable_count = len([c for c in npcs if getattr(c, 'recruitable', False)])
    party = [c.name for c in npcs if getattr(c, 'recruited', False)]
    solved_count = len([state for state in getattr(world, 'puzzle_states', {}).values() if state == 'solved'])

    if language == 'es':
        overview = "📊 **RESUMEN DEL MUNDO** 📊\n\n"
        overview += f"🏠 **Ubicaciones:** {len(world.locations)}\n"
        overview += f"📦 **Objetos:** {len(world.items)}\n"
        overview += f"👤 **Personajes (NPCs):** {npc_count} ({recruitable_count} reclutables)\n"
        overview += f"🧩 **Puzzles:** {puzzles_count} ({solved_count} resueltos)\n"
        overview += f"🤝 **Grupo:** {', '.join(party) if party else 'Nadie'}\n\n"
    else:
        overview = "📊 **WORLD OVERVIEW** 📊\n\n"
        overview += f"🏠 **Locations:** {len(world.locations)}\n"
        overview += f"📦 **Objects:** {len(world.items)}\n"
        overview += f"👤 **Characters (NPCs):** {npc_count} ({recruitable_count} recruitable)\n"
        overview += f"🧩 **Puzzles:** {puzzles_count} ({solved_count} solved)\n"
        overview += f"🤝 **Party:** {', '.join(party) if party else 'Nobody'}\n\n"

    return overview


FEELING_ICONS = {
    'hostile': '💢',
    'wary': '😒',
    'neutral': '😐',
    'friendly': '🙂',
    'devoted': '💖',
}

PUZZLE_STATE_ICONS = {
    'not_proposed': '⚪',
    'proposed': '🟡',
    'solved': '✅',
}


def _enum_value(value) -> str:
    """Enum members and jsonpickle-restored plain strings both reach these reports."""
    return value.value if hasattr(value, 'value') else str(value)


def generate_npc_debug_report(world: World, language: str = 'es') -> str:
    """Debug view of every NPC's recruitment state: feeling, challenge, party membership,
    relationships, and exactly why they can or cannot be recruited right now."""
    from ..config import load_config, get_recruitment_config

    try:
        enabled, threshold = get_recruitment_config(load_config())
    except (KeyError, ValueError):
        enabled, threshold = True, FeelingLevel.FRIENDLY

    npcs = [c for c in world.characters.values() if c is not world.player]
    interacted = {name.strip().lower() for name in getattr(world, 'interacted_characters', set())}
    pending_offer = getattr(world, 'pending_recruitment_offer', None)
    es = language == 'es'

    report = "🤝 **NPCs Y RECLUTAMIENTO** 🤝\n\n" if es else "🤝 **NPCs & RECRUITMENT** 🤝\n\n"
    report += (f"⚙️ {'Reclutamiento' if es else 'Recruitment'}: "
               f"{'✅ on' if enabled else '❌ off'} · "
               f"{'umbral' if es else 'threshold'} `{_enum_value(threshold)}`\n")
    if pending_offer:
        report += f"❓ **{pending_offer}** {'espera tu sí/no' if es else 'is awaiting your yes/no'}\n"
    report += "\n"

    if not npcs:
        report += "_Sin NPCs._\n" if es else "_No NPCs._\n"
        return report

    for character in npcs:
        feeling = _enum_value(getattr(character, 'feeling', FeelingLevel.NEUTRAL))
        recruitable = getattr(character, 'recruitable', False)
        recruited = getattr(character, 'recruited', False)
        puzzle_name = getattr(character, 'recruitment_puzzle', None)
        puzzle_state = world.puzzle_states.get(puzzle_name) if puzzle_name else None
        location_name = character.location.name if character.location else '—'

        badge = ('🎒 EN EL GRUPO' if es else '🎒 IN PARTY') if recruited else ''
        report += f"### {character.name} {badge}\n"
        report += (f"{FEELING_ICONS.get(feeling, '❔')} {'Sentimiento' if es else 'Feeling'}: "
                   f"`{feeling}` · 📍 {location_name}\n")
        report += (f"{'✅' if recruitable else '❌'} {'reclutable' if es else 'recruitable'} · "
                   f"{'✅' if recruited else '⬜'} {'reclutado' if es else 'recruited'} · "
                   f"{'✅' if character.name.strip().lower() in interacted else '⬜'} "
                   f"{'interactuado' if es else 'talked to'}\n")

        if puzzle_name:
            icon = PUZZLE_STATE_ICONS.get(puzzle_state, '❔')
            report += (f"🧩 {'Desafío' if es else 'Challenge'}: **{puzzle_name}** "
                       f"{icon} `{puzzle_state or 'unknown'}`\n")
        else:
            report += f"🧩 {'Sin desafío de reclutamiento' if es else 'No recruitment challenge'}\n"

        proposes = getattr(getattr(character, 'interaction', None), 'proposes_puzzle', None)
        if proposes and proposes != puzzle_name:
            report += f"💬 {'Propone puzzle' if es else 'Proposes puzzle'}: {proposes}\n"

        relationships = [r for r in getattr(world, 'npc_relationships', [])
                         if character.name in (r.character_a, r.character_b)]
        if relationships:
            rendered = []
            for relationship in relationships:
                other = relationship.character_b if relationship.character_a == character.name else relationship.character_a
                tag = _enum_value(relationship.tag)
                rendered.append(f"{'🤜' if tag == 'rival' else '🫱'} {tag} → {other}")
            report += f"🔗 {' · '.join(rendered)}\n"

        # Spell out the can_recruit verdict, since a "no" here is the usual reason a manual
        # recruitment test looks like it silently did nothing.
        if recruited:
            report += f"➡️ ❌ {'ya está en el grupo' if es else 'already in the party'}\n\n"
        elif not recruitable:
            report += f"➡️ ❌ {'no es reclutable' if es else 'not recruitable'}\n\n"
        elif world.can_recruit(character.name, threshold):
            if es:
                reason = 'desafío resuelto' if puzzle_state == 'solved' else 'sentimiento suficiente'
                report += f"➡️ ✅ SE PUEDE RECLUTAR ({reason})\n\n"
            else:
                reason = 'challenge solved' if puzzle_state == 'solved' else 'feeling is high enough'
                report += f"➡️ ✅ CAN BE RECRUITED ({reason})\n\n"
        else:
            report += (f"➡️ ❌ {'necesita' if es else 'needs'} `{_enum_value(threshold)}` "
                       f"{'o resolver su desafío' if es else 'feeling, or a solved challenge'}\n\n")

    return report


def generate_puzzle_debug_report(world: World, language: str = 'es') -> str:
    """Debug view of every puzzle: its state, all three verification routes, and which of its
    solution conditions currently hold in the world."""
    es = language == 'es'
    report = "🧩 **PUZZLES** 🧩\n\n"

    if not world.puzzles:
        report += "_Sin puzzles._\n" if es else "_No puzzles._\n"
        return report

    for puzzle_name, puzzle in world.puzzles.items():
        state = world.puzzle_states.get(puzzle_name, 'unknown')
        report += f"### {PUZZLE_STATE_ICONS.get(state, '❔')} {puzzle_name} — `{state}`\n"
        report += f"📝 {puzzle.problem}\n"
        report += f"🔑 {'Respuesta' if es else 'Answer'}: `{puzzle.answer}`\n"

        accepted = getattr(puzzle, 'accepted_answers', None) or []
        report += (f"🗣️ {'También se acepta' if es else 'Also accepted'}: "
                   f"{', '.join(f'`{a}`' for a in accepted) if accepted else '—'}\n")

        conditions = getattr(puzzle, 'solution_conditions', None) or []
        if conditions:
            report += (f"⚙️ {'Condiciones' if es else 'Conditions'} "
                       f"({'todas deben cumplirse' if es else 'all must hold'}):\n")
            for condition in conditions:
                held = world._condition_satisfied(condition)
                target = (getattr(condition, 'item_name', None) or
                          getattr(condition, 'character_name', None) or
                          getattr(condition, 'location_name', None) or '—')
                condition_type = _enum_value(getattr(condition, 'condition_type', '?'))
                report += f"  - {'✅' if held else '⬜'} `{condition_type}` → {target}\n"
        else:
            report += (f"⚙️ {'Sin condiciones verificables' if es else 'No engine-checkable conditions'}"
                       f" — {'solo texto o juicio del narrador' if es else 'text or narrator judgement only'}\n")

        if puzzle.proposed_by_character:
            report += f"👤 {'Propuesto por' if es else 'Proposed by'}: {puzzle.proposed_by_character}\n"
        if getattr(puzzle, 'proposed_by_location', None):
            report += f"🏠 {'Propuesto en' if es else 'Proposed at'}: {puzzle.proposed_by_location}\n"

        rewards = getattr(puzzle, 'rewards', None) or []
        if rewards:
            rendered = []
            for reward in rewards:
                reward_type = world._normalized_reward_type(reward)
                target = (getattr(reward, 'item_name', None) or
                          getattr(reward, 'character_name', None) or
                          getattr(reward, 'to_location', None) or '')
                rendered.append(f"{reward_type}{f' ({target})' if target else ''}")
            report += f"🎁 {'Recompensas' if es else 'Rewards'}: {', '.join(rendered)}\n"
        report += "\n"

    return report


def generate_objective_validation_report(world: World, language: str = 'es') -> str:
    is_valid, missing_components, validation_details = validate_objective_components(world)

    if language == 'es':
        report = "🎯 **VALIDACIÓN DEL OBJETIVO** 🎯\n\n"
        if is_valid:
            report += "✅ **Estado:** Válido\n"
            report += f"**Detalles:** {validation_details}\n\n"
        else:
            report += "❌ **Estado:** Inválido\n"
            report += f"**Detalles:** {validation_details}\n\n"
            report += "**Problemas encontrados:**\n"
            for missing in missing_components:
                report += f"• {missing}\n"
            report += "\n"

        if hasattr(world, 'objective_data') and world.objective_data:
            obj_type = world.objective_data.type.value if hasattr(world.objective_data.type, 'value') else str(world.objective_data.type)
            report += f"**Tipo de objetivo esperado:** {obj_type}\n"
            report += f"**Descripción del objetivo:** {getattr(world.objective_data, 'description', '')}\n"
            report += "**Componentes esperados y su accesibilidad:**\n"
            for component in getattr(world.objective_data, 'components', []):
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "ITEM":
                    item_locations = []
                    for loc_name, location in world.locations.items():
                        if any(getattr(item, 'name', None) == component.name for item in getattr(location, 'items', []) if location.items):
                            item_locations.append(f"Ubicación: {loc_name}")
                    for char_name, character in world.characters.items():
                        if any(getattr(item, 'name', None) == component.name for item in getattr(character, 'inventory', []) if character.inventory):
                            item_locations.append(f"Personaje: {char_name}")
                    location_text = ", ".join(item_locations) if item_locations else "❌ NO ACCESIBLE"
                    report += f"• {component.name} ({component_type}) - {location_text}\n"
                else:
                    report += f"• {component.name} ({component_type})\n"

        if hasattr(world, 'objective') and world.objective:
            obj_first = world.objective[0]
            obj_second = world.objective[1]
            first_name = obj_first.name if hasattr(obj_first, 'name') else str(obj_first)
            second_name = obj_second.name if hasattr(obj_second, 'name') else str(obj_second)
            first_type = obj_first.__class__.__name__
            second_type = obj_second.__class__.__name__
            report += f"\n**Objetivo actual implementado:** ({first_name}, {second_name})\n"
            report += f"**Tipos:** ({first_type}, {second_type})\n"
    else:
        report = "🎯 **OBJECTIVE VALIDATION** 🎯\n\n"
        if is_valid:
            report += "✅ **Status:** Valid\n"
            report += f"**Details:** {validation_details}\n\n"
        else:
            report += "❌ **Status:** Invalid\n"
            report += f"**Details:** {validation_details}\n\n"
            report += "**Issues found:**\n"
            for missing in missing_components:
                report += f"• {missing}\n"
            report += "\n"

        if hasattr(world, 'objective_data') and world.objective_data:
            obj_type = world.objective_data.type.value if hasattr(world.objective_data.type, 'value') else str(world.objective_data.type)
            report += f"**Expected objective type:** {obj_type}\n"
            report += f"**Objective description:** {getattr(world.objective_data, 'description', '')}\n"
            report += "**Expected components and their accessibility:**\n"
            for component in getattr(world.objective_data, 'components', []):
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type.upper() == "ITEM":
                    item_locations = []
                    for loc_name, location in world.locations.items():
                        if any(getattr(item, 'name', None) == component.name for item in getattr(location, 'items', []) if location.items):
                            item_locations.append(f"Location: {loc_name}")
                    for char_name, character in world.characters.items():
                        if any(getattr(item, 'name', None) == component.name for item in getattr(character, 'inventory', []) if character.inventory):
                            item_locations.append(f"Character: {char_name}")
                    location_text = ", ".join(item_locations) if item_locations else "❌ NOT ACCESSIBLE"
                    report += f"• {component.name} ({component_type}) - {location_text}\n"
                else:
                    report += f"• {component.name} ({component_type})\n"

        if hasattr(world, 'objective') and world.objective:
            obj_first = world.objective[0]
            obj_second = world.objective[1]
            first_name = obj_first.name if hasattr(obj_first, 'name') else str(obj_first)
            second_name = obj_second.name if hasattr(obj_second, 'name') else str(obj_second)
            first_type = obj_first.__class__.__name__
            second_type = obj_second.__class__.__name__
            report += f"\n**Actual implemented objective:** ({first_name}, {second_name})\n"
            report += f"**Types:** ({first_type}, {second_type})\n"

    return report
