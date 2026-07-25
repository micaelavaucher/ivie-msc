"""This module implements the classes needed to represent the fictional world of the game.

The world class includes references to the several components (Items, Locations, Character),
and methods to update according to the detected changes by a language model.
"""

import re
from typing import Type

from ..llm.structured_data_models import FeelingLevel, RelationshipTag


FEELING_ORDER = [FeelingLevel.HOSTILE, FeelingLevel.WARY, FeelingLevel.NEUTRAL, FeelingLevel.FRIENDLY, FeelingLevel.DEVOTED]


def shift_feeling(level: FeelingLevel, steps: int) -> FeelingLevel:
  """Move a FeelingLevel up or down the ladder, clamped at both ends."""
  index = FEELING_ORDER.index(level)
  new_index = max(0, min(len(FEELING_ORDER) - 1, index + steps))
  return FEELING_ORDER[new_index]


class Component:
  """A class to represent a component of the world.

  The components considered in the IVIE approach are Items, Locations and Characters.
  """
  def __init__ (self, name:str, descriptions: 'list[str]'):

    self.name = name
    """the name of the component"""

    self.descriptions = descriptions
    """a set of natural language descriptions for the component"""
  
class MysteryClue:
    """A clue in a mystery objective."""
    def __init__(self, name: str, description: str, associated_item: str, 
                 relevance_to_mystery: str, discovered: bool = False, item_location: str = None):
        self.name = name
        self.description = description
        self.associated_item = associated_item
        self.relevance_to_mystery = relevance_to_mystery
        self.discovered = discovered
        self.item_location = item_location

class MysteryObjective:
    """A mystery objective that requires discovering clues."""
    def __init__(self, name: str, description: str, clues: 'list[MysteryClue]', 
                 mystery_solution: str):
        self.name = name
        self.description = description
        self.clues = clues
        self.mystery_solution = mystery_solution
    
    def discover_clue_for_item(self, item_name: str):
        """Mark a clue as discovered when the associated item is interacted with."""
        for clue in self.clues:
            if clue.associated_item == item_name and not clue.discovered:
                clue.discovered = True
                return clue
        return None
    
    def get_completion_progress(self):
        """Get the number of discovered clues vs total clues."""
        discovered = len([clue for clue in self.clues if clue.discovered])
        total = len(self.clues)
        return discovered, total
    
    def is_completed(self):
        """Check if all clues have been discovered."""
        return all(clue.discovered for clue in self.clues)
    
    def get_discovered_clues(self):
        """Get list of discovered clues."""
        return [clue for clue in self.clues if clue.discovered]


class Puzzle (Component):
  """A class to represent a Puzzle"""

  def __init__(self, name: str, descriptions: 'list[str]', problem: str, answer: str, 
               puzzle_type: str = "riddle", proposed_by_character: str = None, 
               proposed_by_location: str = None, rewards: list = None, 
               relevance_to_objective: str = None, puzzle_hints: 'list[dict]' = None, interaction_hint: str = None):
    
    super().__init__(name, descriptions)
    """inherited from Component"""

    self.problem = problem
    """the main problem to be solved"""

    self.answer = answer
    """a possible answer to the riddle or puzzle"""
    
    self.puzzle_type = puzzle_type
    """type of puzzle (riddle, logic, sequence, etc.)"""
    
    self.proposed_by_character = proposed_by_character
    """character who proposes this puzzle, or None if environmental"""
    
    self.proposed_by_location = proposed_by_location
    """location that when investigated proposes this puzzle, or None if proposed by character"""
    
    self.rewards = rewards or []
    """list of rewards obtained when solving this puzzle"""
    
    self.relevance_to_objective = relevance_to_objective
    """how solving this puzzle helps achieve the main objective"""

    self.puzzle_hints = puzzle_hints or []

    self.interaction_hint = interaction_hint


class Item (Component):
  """A class to represent an Item."""
  def __init__ (self, name:str, descriptions: 'list[str]', gettable: bool = True):

    super().__init__(name, descriptions)
    """inherited from Component"""

    self.gettable = gettable
    """indicates if the Item can be taken by the player"""

class Location (Component):
  """A class to represent a Location in the world."""
  def __init__ (self, name:str, descriptions: 'list[str]', items: 'list[Item]' = None, connecting_locations: 'list[Location]' = None):

    super().__init__(name, descriptions)
    """inherited from Component"""

    self.items = items or []
    """a list of the items available in that location"""

    self.connecting_locations = connecting_locations or []
    """a list of the reachable locations from itself."""

    self.visited = False
    """indicates if the location has been visited by the player before"""

    self.blocked_locations = {}
    """a dictionary with the name of a location as key and <location,obstacle,symmetric> as value.
    A blocked passage between self and a location means that it
    will be reachable from [self] after overcoming the [obstacle].
    The symmetric variable is a boolean that indicates if, when unblocked,
    [self] will also be reachable from [location].
    """

  def block_passage(self, location: 'Location', obstacle, symmetric: bool = True):
    """Block a passage between self and location using an obstacle."""
    if location in self.connecting_locations:
      if location.name not in self.blocked_locations:
        self.blocked_locations[location.name] = (location, obstacle, symmetric)
        self.connecting_locations = [x for x in self.connecting_locations if x is not location]
      else:
        raise Exception(f"Error: A blocked passage to {location.name} already exists")
    else:
        raise Exception(f"Error: Two non-conected locations cannot be blocked")

  def unblock_passage(self, location: 'Location'):
    """Unblock a passage between self and location by adding it to the connecting locations of self.

    In case that the block was symmetric, self will be added to the connecting locations of location.
    """
    if location.name in self.blocked_locations and self.blocked_locations[location.name]:
      self.connecting_locations += [location]
      if self.blocked_locations[location.name][2] and self not in location.connecting_locations:
        location.connecting_locations += [self]
      del self.blocked_locations[location.name]
      print(f"✅ Passage unblocked: {self.name} → {location.name}")
    else:
      raise Exception("Error: That is not a blocked passage")

class Character (Component):
  """A class to represent a character."""
  def __init__ (self, name:str, descriptions: 'list[str]', location:Location, inventory: 'list[Item]' = None, interaction=None,
                recruitable: bool = False, feeling: 'FeelingLevel' = FeelingLevel.NEUTRAL, recruited: bool = False,
                recruitment_puzzle: str = None):

    super().__init__(name, descriptions)
    """inherited from Component"""

    self.inventory = inventory or []
    """a set of Items the carachter has"""

    self.location = location
    """the location of the character"""

    self.visited_locations = {self.location.name: []}
    """a dictionary that contains the successive descriptions of the visited places"""

    self.interaction = interaction
    """interaction data from GeneratedCharacter, contains proposes_puzzle and other interaction info"""

    self.recruitable = recruitable
    """whether the player can recruit this character into their party, set at generation time"""

    self.feeling = feeling
    """this character's FeelingLevel toward the player; mutated only by the party relationship ripple"""

    self.recruited = recruited
    """whether this character has joined the player's party"""

    self.recruitment_puzzle = recruitment_puzzle
    """name of the Puzzle that, when solved, recruits this character regardless of feeling; or None"""

  def move(self, new_location: Location):
    """Move the character to a new location."""
    if new_location in self.location.connecting_locations:
      self.location = new_location
      if self.location.name not in self.visited_locations:
        self.visited_locations[self.location.name] = []
    else:
      raise Exception(f"Error: {new_location.name} is not reachable")

  def save_item(self,item: Item, item_location_or_owner):
    """Add an item to the character inventory."""
    if item.gettable:
      if item not in self.inventory:
        self.inventory += [item]
        if item_location_or_owner.__class__.__name__ == 'Character':
          item_location_or_owner.inventory = [i for i in item_location_or_owner.inventory if i is not item]
        elif item_location_or_owner.__class__.__name__ == 'Location':
          item_location_or_owner.items = [i for i in item_location_or_owner.items if i is not item]
      else:
        raise Exception(f"Error: {item.name} is already in your inventory")
    else:
      raise Exception(f"Error: {item.name} cannot be taken")

  def drop_item (self, item: Item):
    """Leave an item in the current location."""
    self.inventory = [i for i in self.inventory if i is not item]
    self.location.items += [item]

  def give_item (self, character: 'Character', item: Item):
    """Give an item to another character."""
    try:
      character.save_item(item, self)
    except Exception as e:
      print(e)


class NPCRelationship:
  """A symmetric rivalry or alliance tag between two characters, used for the party social ripple effect."""
  def __init__(self, character_a: str, character_b: str, tag: RelationshipTag):
    self.character_a = character_a
    self.character_b = character_b
    self.tag = tag


class World:
  """A class to represent the fictional world, with references to every component."""
  def __init__ (self, player: Character) -> None:

    self.items = {}
    """a dictionary of all the Items in the world, with their names as values"""

    self.characters = {}
    """a dictionary of all the Characters in the world, with their names as values"""

    self.locations =  {}
    """a dictionary of all the Locations in the world, with their names as values"""
    
    self.puzzles = {}
    """a dictionary of all the Puzzles in the world, with their names as values"""

    self.player = player
    """a character for the player"""

    self.objective = None
    """the current objective for the player in this world"""
    
    self.objective_data = None
    """the structured GeneratedObjective that contains hints and metadata"""
    
    # Hints system
    self.current_hints = []
    """currently active hints that can be given to the player"""
    
    # Default exploration hints
    self.default_explore_hints = [
        {"text": "explore the world", "given": False},
        {"text": "try interacting with characters and objects", "given": False},
        {"text": "try investigating objects and asking things to characters", "given": False}
    ]
    
    # Puzzle state tracking
    self.puzzle_states = {}
    """track the state of puzzles: 'not_proposed', 'proposed', 'solved'"""

    self.npc_relationships = []
    """list of NPCRelationship: sparse, symmetric rival/ally tags between characters"""

  ## Deprecated ##
  def set_objective (self, first_component: Type[Component], second_component: Type[Component]):
    
    first_component_class = first_component.__class__.__name__
    second_component_class = second_component.__class__.__name__
    
    if first_component_class == "Character" and second_component_class == "Character":
      self.objective = (first_component, second_component)
    elif (first_component_class == "Character" and second_component_class in ["Location", "Item"]) or (second_component_class == "Character" and first_component_class in ["Location", "Item"]):
      self.objective = (first_component, second_component)
    elif (first_component_class  == "Item" and second_component_class == "Location") or (second_component_class  == "Item" and first_component_class == "Location"):
      self.objective = (first_component, second_component)
    else:
      raise Exception(f"Error: Cannot set objective with classes {first_component_class} and {second_component_class}")

  def check_objective(self) -> bool:

    done = False
    first_component_class = self.objective[0].__class__.__name__
    second_component_class = self.objective[1].__class__.__name__

    if first_component_class == "Character" and second_component_class == "Character":
      if self.objective[0].location == self.objective[1].location: done = True
    elif first_component_class == "Character" and second_component_class == "Location":
      if self.objective[0].location == self.objective[1]: done = True
    elif first_component_class == "Character" and second_component_class == "Item":
      if self.objective[1] in self.objective[0].inventory: done = True
    elif first_component_class == "Item" and second_component_class == "Location":
      if self.objective[0] in self.objective[1].items: done = True
    elif second_component_class == "MysteryObjective":
      # Check if mystery objective is completed
      mystery_obj = self.objective[1]
      done = mystery_obj.is_completed()
    elif hasattr(self.objective[1], 'name') and 'Mystery:' in str(self.objective[1].name):
      # Legacy mystery objectives require manual completion through narrative
      # For now, they are never automatically completed
      done = False

    return done

  def set_objective_from_generated(self, objective_data, items_dict, locations_dict, characters_list, player):
      try:
          # Store the structured objective data for access to completion_narration and other metadata
          self.objective_data = objective_data
          
          # Handle enum values properly
          obj_type = objective_data.type.value if hasattr(objective_data.type, 'value') else str(objective_data.type)
          components = objective_data.components
          
          # Handle different objective types with new component system
          if obj_type in ["GET_ITEM", "get_item"]:
              # Find the item component
              for component in components:
                  component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                  if component_type in ["ITEM", "item"]:
                      if component.name in items_dict:
                          self.objective = (player, items_dict[component.name])
                          return
          
          elif obj_type in ["REACH_LOCATION", "reach_location"]:
              # Find the location component
              for component in components:
                  component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                  if component_type in ["LOCATION", "location"]:
                      if component.name in locations_dict:
                          self.objective = (player, locations_dict[component.name])
                          return
          
          elif obj_type in ["FIND_CHARACTER", "find_character"]:
              # Find the character component
              for component in components:
                  component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                  if component_type in ["CHARACTER", "character"]:
                      character = next((c for c in characters_list if c.name == component.name), None)
                      if character:
                          self.objective = (player, character)
                          return
          
          elif obj_type in ["DELIVER_AN_ITEM", "deliver_an_item"]:
              # Need both item and location/character components
              item_component = None
              target_component = None
              
              for component in components:
                  component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                  if component_type in ["ITEM", "item"]:
                      item_component = component
                  elif component_type in ["LOCATION", "location", "CHARACTER", "character"]:
                      target_component = component
              
              if item_component and target_component:
                  if item_component.name in items_dict:
                      target_type = target_component.component_type.value if hasattr(target_component.component_type, 'value') else str(target_component.component_type)
                      if target_type in ["LOCATION", "location"] and target_component.name in locations_dict:
                          self.objective = (items_dict[item_component.name], locations_dict[target_component.name])
                          return
                      elif target_type in ["CHARACTER", "character"]:
                          character = next((c for c in characters_list if c.name == target_component.name), None)
                          if character:
                              self.objective = (items_dict[item_component.name], character)
                              return
          
          elif obj_type in ["SOLVE_MYSTERY", "solve_mystery"]:
              # Create a proper MysteryObjective with clue validation
              from .world import MysteryObjective, MysteryClue
              
              # Validate and create clues
              valid_clues = []
              if hasattr(objective_data, 'mystery_clues') and objective_data.mystery_clues:
                  for clue_data in objective_data.mystery_clues:
                      # Validate that the associated item exists
                      if clue_data.associated_item in items_dict:
                          clue = MysteryClue(
                              name=clue_data.name,
                              description=clue_data.description,
                              associated_item=clue_data.associated_item,
                              relevance_to_mystery=clue_data.relevance_to_mystery,
                              discovered=clue_data.discovered,
                              item_location=getattr(clue_data, 'item_location', None)
                          )
                          valid_clues.append(clue)
              
              # Only create mystery objective if there are valid clues
              if valid_clues:
                  mystery_solution = getattr(objective_data, 'mystery_solution', 'Mystery solution not specified')
                  mystery_objective = MysteryObjective(
                      name=f"Mystery: {objective_data.description}",
                      description=objective_data.description,
                      clues=valid_clues,
                      mystery_solution=mystery_solution
                  )
                  self.objective = (player, mystery_objective)
                  return
          
          # Fallback for legacy objective types or unknown formats
          elif obj_type == "item_to_location":
              item_name, location_name = objective_data.components
              if item_name in items_dict and location_name in locations_dict:
                  self.objective = (items_dict[item_name], locations_dict[location_name])
                  return
          
          print(f"❌ Could not set objective from type: {obj_type}")
          self.objective = None
                  
      except Exception as e:
          print(f"Error setting objective: {e}")
          import traceback
          traceback.print_exc()
          self.objective = None

  def add_puzzle(self, puzzle: Puzzle) -> None:
      if puzzle.name in self.puzzles:
          raise Exception(f"Error: Already exists a puzzle called '{puzzle.name}'")
      else:
          self.puzzles[puzzle.name] = puzzle
          # Initialize puzzle state as not proposed
          self.puzzle_states[puzzle.name] = 'not_proposed'
  
  def add_puzzles(self, puzzles: 'list[Puzzle]') -> None:
      for puzzle in puzzles:
          self.add_puzzle(puzzle)

  def add_location (self,location: Location) -> None:
    if location.name in self.locations:
      raise Exception(f"Error: Already exists a location called '{location.name}'")
    else:
       self.locations[location.name] = location

  def add_item (self, item: Item) -> None:
    if item.name in self.items:
      raise Exception(f"Error: Already exists an item called '{item.name}'")
    else:
      self.items[item.name] = item

  def add_character (self, character: Character) -> None:
    if character.name in self.characters:
      raise Exception(f"Error: Already exists a character called '{character.name}'")
    else:
      self.characters[character.name] = character

  def add_locations (self,locations: 'list[Location]') -> None:
    for location in locations:
      self.add_location(location)

  def add_items (self, items: 'list[Item]') -> None:
    for item in items:
      self.add_item(item)

  def add_characters (self, characters: 'list[Character]') -> None:
    for character in characters:
      self.add_character(character)

  def get_party(self) -> 'list[Character]':
    """Return the characters currently recruited into the player's party."""
    return [character for character in self.characters.values() if character.recruited]

  def can_recruit(self, character_name: str, feeling_threshold: 'FeelingLevel') -> bool:
    """Check whether character_name can be recruited: their feeling already meets feeling_threshold,
    or their recruitment challenge puzzle has been solved. These are independent conditions."""
    character = self.characters.get(character_name)
    if character is None or not character.recruitable or character.recruited:
      return False

    feeling_ok = FEELING_ORDER.index(character.feeling) >= FEELING_ORDER.index(feeling_threshold)
    puzzle_ok = (character.recruitment_puzzle is not None and
                 self.puzzle_states.get(character.recruitment_puzzle) == 'solved')
    return feeling_ok or puzzle_ok

  def recruit_character(self, character_name: str) -> bool:
    """Mark character_name as recruited and apply the social ripple to related NPCs. Returns False if
    the character doesn't exist, isn't recruitable, or is already recruited."""
    character = self.characters.get(character_name)
    if character is None or not character.recruitable or character.recruited:
      return False

    character.recruited = True
    self._apply_relationship_ripple(character_name)
    return True

  def _apply_relationship_ripple(self, recruited_character_name: str) -> None:
    for relationship in self.npc_relationships:
      if relationship.character_a == recruited_character_name:
        other_name = relationship.character_b
      elif relationship.character_b == recruited_character_name:
        other_name = relationship.character_a
      else:
        continue

      other = self.characters.get(other_name)
      if other is None:
        continue

      step = 1 if relationship.tag == RelationshipTag.ALLY else -1
      other.feeling = shift_feeling(other.feeling, step)

  def render_world(self, *, language:str = 'en', detail_components:bool = True) -> str:
    rendered_world = ''

    if language == 'es':
      rendered_world = self.__render_world_spanish(detail_components = detail_components)
    else:
      rendered_world = self.__render_world_english(detail_components = detail_components)

    return rendered_world

  def format_world_state_for_chat(self, *, language:str = 'en') -> str:
    player_location = self.player.location
    reachable_locations = [f"**{p.name}**" for p in player_location.connecting_locations]
    blocked_passages = [f"**{p}**" for p in player_location.blocked_locations.keys()]
    characters_in_the_scene = [character for character in self.characters.values() if character.location is player_location]

    # Categorize items by their current holder/location
    location_items = list(player_location.items)  # Items free in the location
    blocking_items = []  # Items blocking passages
    
    # Get items blocking passages
    for blocked_values in player_location.blocked_locations.values():
        if isinstance(blocked_values[1], Item):
            blocking_items.append(blocked_values[1])

    if language == 'es':
      formatted_state = f"📍 **Ubicación actual:** {player_location.name}\n"
      
      if reachable_locations:
        formatted_state += f"🚪 **Lugares accesibles:** {', '.join(reachable_locations)}\n"
      else:
        formatted_state += f"🚪 **Lugares accesibles:** Ninguno\n"

      if blocked_passages:
        formatted_state += f"🔒 **Pasajes bloqueados:** {', '.join(blocked_passages)}\n"

      # Player inventory
      if self.player.inventory:
        formatted_state += f"🎒 **Tu inventario:** {', '.join([f'**{i.name}**' for i in self.player.inventory])}\n"
      else:
        formatted_state += f"🎒 **Tu inventario:** Vacío\n"

      # Items free in the location
      if location_items:
        formatted_state += f"📦 **Objetos en este lugar:** {', '.join([f'**{i.name}**' for i in location_items])}\n"

      # Items in character inventories
      for character in characters_in_the_scene:
        if character.inventory:
          formatted_state += f"👤 **{character.name} tiene:** {', '.join([f'**{i.name}**' for i in character.inventory])}\n"

      # Items blocking passages
      if blocking_items:
        formatted_state += f"🚧 **Objetos bloqueando:** {', '.join([f'**{i.name}**' for i in blocking_items])}\n"

      # Characters present
      if characters_in_the_scene:
        formatted_state += f"👥 **Personajes presentes:** {', '.join([f'**{c.name}**' for c in characters_in_the_scene])}\n"
    else:
      formatted_state = f"📍 **Current location:** {player_location.name}\n"
      
      if reachable_locations:
        formatted_state += f"🚪 **Accessible places:** {', '.join(reachable_locations)}\n"
      else:
        formatted_state += f"🚪 **Accessible places:** None\n"

      if blocked_passages:
        formatted_state += f"🔒 **Blocked passages:** {', '.join(blocked_passages)}\n"

      # Player inventory
      if self.player.inventory:
        formatted_state += f"🎒 **Your inventory:** {', '.join([f'**{i.name}**' for i in self.player.inventory])}\n"
      else:
        formatted_state += f"🎒 **Your inventory:** Empty\n"

      # Items free in the location
      if location_items:
        formatted_state += f"📦 **Items in this place:** {', '.join([f'**{i.name}**' for i in location_items])}\n"

      # Items in character inventories
      for character in characters_in_the_scene:
        if character.inventory:
          formatted_state += f"👤 **{character.name} has:** {', '.join([f'**{i.name}**' for i in character.inventory])}\n"

      # Items blocking passages
      if blocking_items:
        formatted_state += f"🚧 **Items blocking passages:** {', '.join([f'**{i.name}**' for i in blocking_items])}\n"

      # Characters present
      if characters_in_the_scene:
        formatted_state += f"👥 **Characters present:** {', '.join([f'**{c.name}**' for c in characters_in_the_scene])}\n"

    return formatted_state
  
  def __render_world_spanish(self, *,  detail_components:bool = True) -> str:
    player_location = self.player.location
    reachable_locations = [f"{p.name}" for p in player_location.connecting_locations]
    blocked_passages = [f"{p} bloqueado por {player_location.blocked_locations[p][1].name}" for p in player_location.blocked_locations.keys()]
    characters_in_the_scene = [character for character in self.characters.values() if character.location is player_location]
    
    # Add puzzles proposed by characters in the scene
    puzzles_available = []
    for character in characters_in_the_scene:
        for puzzle_name, puzzle in self.puzzles.items():
            if puzzle.proposed_by_character == character.name:
                puzzles_available.append(puzzle)

    world_description = f'El jugador está en {player_location.name}\n'
    
    if reachable_locations:
      world_description += f'Desde {player_location.name} el jugador puede ir a: {(", ").join(reachable_locations)}\n'
    else:
      world_description += f'Desde {player_location.name} el jugador puede ir a: None\n'

    if blocked_passages:
      world_description += f'Desde {player_location.name} hay pasajes bloqueados hacia: {(", ").join(blocked_passages)}\n'
    else:
      world_description += f'Desde {player_location.name} hay pasajes bloqueados hacia: None\n'

    if self.player.inventory:
      world_description += f'El jugador tiene los siguientes objetos en su inventario: {(", ").join([f"{i.name}" for i in self.player.inventory])}\n'
    else:
      world_description += f'El jugador tiene los siguientes objetos en su inventario: None\n'

    if player_location.items:
      world_description += f'El jugador puede ver los siguientes objetos: {(", ").join([f"{i.name}" for i in player_location.items])}\n'
    else:
      world_description += f'El jugador puede ver los siguientes objetos: None\n'
      
    if characters_in_the_scene:
      world_description += f'El jugador puede ver a los siguientes personajes: {(", ").join([f"{c.name}" for c in characters_in_the_scene])}\n'
    else:
      world_description += f'El jugador puede ver a los siguientes personajes: None\n'
    
    if puzzles_available:
      world_description += f'Hay puzzles disponibles propuestos por personajes: {(", ").join([f"{p.name}" for p in puzzles_available])}'
    else:
      world_description += f'Hay puzzles disponibles propuestos por personajes: None'

    details = ""
    if detail_components:
      items_in_the_scene = player_location.items + self.player.inventory + [blocked_values[1] for blocked_values in player_location.blocked_locations.values() if isinstance(blocked_values[1], Item)]
      puzzles_in_the_scene = [blocked_values[1] for blocked_values in player_location.blocked_locations.values() if isinstance(blocked_values[1], Puzzle)]
      puzzles_in_the_scene += puzzles_available  # Add character-proposed puzzles

      details += "\nAquí hay una descripción de cada componente.\n"
      details += f"{player_location.name}: Este es el lugar en el que está el jugador. {('. ').join(player_location.descriptions)}.\n"
      details += "Personajes:\n"
      details += f"- Jugador: El jugador está actuando como {self.player.name}. {('. ').join(self.player.descriptions)}.\n"
      if len(characters_in_the_scene)>0:
        for character in characters_in_the_scene:
          details += f"- {character.name}: {('. ').join(character.descriptions)}."
          if len(character.inventory)>0:
            details += f"Este personaje tiene los siguientes objetos en su inventario: {(', ').join([f'{i.name}' for i in character.inventory])}\n"
            items_in_the_scene += [i for i in character.inventory if i not in items_in_the_scene]
          else:
            details += "\n"
      if len(items_in_the_scene)>0:
        details+="Objetos:\n"
        for item in items_in_the_scene:
          details += f"- {item.name}: {('. ').join(item.descriptions)}\n"
      if len(puzzles_in_the_scene)>0:
        details+="Puzzles:\n"
        for puzzle in puzzles_in_the_scene:
          details+= f'- {puzzle.name}: {(". ").join(puzzle.descriptions)}. El acertijo a resolver es: "{puzzle.problem}". La respuesta esperada, que NO PUEDES decirle al jugador (JAMÁS) es: "{puzzle.answer}".\n'

    return world_description + '\n' + details

  def __render_world_english(self, *,  detail_components:bool = True) -> str:
    player_location = self.player.location
    reachable_locations = [f"{p.name}" for p in player_location.connecting_locations]
    blocked_passages = [f"{p} blocked by {player_location.blocked_locations[p][1].name}" for p in player_location.blocked_locations.keys()]
    characters_in_the_scene = [character for character in self.characters.values() if character.location is player_location]

    
    world_description = f'The player is in {player_location.name}\n'
    
    if reachable_locations:
      world_description += f'From {player_location.name} the player can access: {(", ").join(reachable_locations)}\n'
    else:
      world_description += f'From {player_location.name} the player can access: None\n'

    if blocked_passages:
      world_description += f'From {player_location.name} there are blocked passages to: {(", ").join(blocked_passages)}\n'
    else:
      world_description += f'From {player_location.name} there are blocked passages to: None\n'

    if self.player.inventory:
      world_description += f'The player has the following objects in the inventory: {(", ").join([f"{i.name}" for i in self.player.inventory])}\n'
    else:
      world_description += f'The player has the following objects in the inventory: None\n'

    if player_location.items:
      world_description += f'The player can see the following objects: {(", ").join([f"{i.name}" for i in player_location.items])}\n'
    else:
      world_description += f'The player can see the following objects: None\n'
      
    if characters_in_the_scene:
      world_description += f'The player can see the following characters: {(", ").join([f"{c.name}" for c in characters_in_the_scene])}'
    else:
      world_description += f'The player can see the following characters: None'

    details = ""
    if detail_components:
      items_in_the_scene = player_location.items + self.player.inventory + [blocked_values[1] for blocked_values in player_location.blocked_locations.values() if isinstance(blocked_values[1], Item)]
      puzzles_in_the_scene = [blocked_values[1] for blocked_values in player_location.blocked_locations.values() if isinstance(blocked_values[1], Puzzle)]

      details += "\nHere is a description of each component.\n"
      details += f"{player_location.name}: This is the player's location. {('. ').join(player_location.descriptions)}.\n"
      details += "Characters:\n"
      details += f"- Player: The player is acting as {self.player.name}. {('. ').join(self.player.descriptions)}.\n"
      if len(characters_in_the_scene)>0:
        for character in characters_in_the_scene:
          details += f"- {character.name}: {('. ').join(character.descriptions)}."
          if len(character.inventory)>0:
            details += f" This character has the following items: {(', ').join([f'{i.name}' for i in character.inventory])}\n"
            items_in_the_scene += [i for i in character.inventory if i not in items_in_the_scene]
          else:
            details += "\n"
      if len(items_in_the_scene)>0:
        details+="Objects:\n"
        for item in items_in_the_scene:
          details += f"- <{item.name}>: {('. ').join(item.descriptions)}\n"
      if len(puzzles_in_the_scene)>0:
        details+="Puzzles:\n"
        for puzzle in puzzles_in_the_scene:
          details+= f'- <{puzzle.name}>: {(". ").join(puzzle.descriptions)}. The riddle to solve is: "{puzzle.problem}". The expected answer, that you CANNOT tell the player (EVER) is: "{puzzle.answer}".\n'

    return world_description + '\n' + details

  def _check_mystery_clue_discovery(self, item_name: str, language: str = 'en') -> str:
    discovery_message = ""
    
    # Check if we have a mystery objective
    if (hasattr(self, 'objective') and self.objective and 
        len(self.objective) >= 2 and 
        hasattr(self.objective[1], '__class__') and 
        self.objective[1].__class__.__name__ == 'MysteryObjective'):
        
        mystery_obj = self.objective[1]
        discovered_clue = mystery_obj.discover_clue_for_item(item_name)
        
        if discovered_clue:
            # Create discovery message based on language
            if language == 'es':
                discovery_message = f"\n\n🔍 **¡Pista del Misterio Descubierta!**\n"
                discovery_message += f"**{discovered_clue.name}:** {discovered_clue.description}\n"
                discovery_message += f"*Relevancia:* {discovered_clue.relevance_to_mystery}\n"
                
                # Show progress
                discovered, total = mystery_obj.get_completion_progress()
                discovery_message += f"*Progreso:* {discovered}/{total} pistas descubiertas"
                
                print(f"🔍 Pista del misterio descubierta: {discovered_clue.name}")
            else:
                discovery_message = f"\n\n🔍 **Mystery Clue Discovered!**\n"
                discovery_message += f"**{discovered_clue.name}:** {discovered_clue.description}\n"
                discovery_message += f"*Relevance:* {discovered_clue.relevance_to_mystery}\n"
                
                # Show progress
                discovered, total = mystery_obj.get_completion_progress()
                discovery_message += f"*Progress:* {discovered}/{total} clues discovered"
                
                print(f"🔍 Mystery clue discovered: {discovered_clue.name}")
    
    return discovery_message

  def _has_puzzles_in_location(self, location: 'Location' = None) -> bool:
    if location is None:
        location = self.player.location
    
    # Check for puzzles proposed by characters in this location
    for character in self.characters.values():
        if character.location is location:
            for puzzle in self.puzzles.values():
                if hasattr(puzzle, 'proposed_by_character') and puzzle.proposed_by_character == character.name:
                    return True
    
    # Check for puzzles proposed by items in this location
    for item in location.items:
        for puzzle in self.puzzles.values():
            if hasattr(puzzle, 'proposed_by_location') and puzzle.proposed_by_location == item.name:
                return True
    
    # Check for puzzles that block passages from this location
    for blocked_location_name, (_, obstacle, _) in location.blocked_locations.items():
        if obstacle.__class__.__name__ == 'Puzzle':
            return True
    
    return False    
  def _get_objective_hints(self) -> list:
        # First, check if we have the structured objective data with hints
        if (hasattr(self, 'objective_data') and self.objective_data and 
            hasattr(self.objective_data, 'objective_hints') and self.objective_data.objective_hints):
            hints = []
            for hint in self.objective_data.objective_hints:
                # Handle both Pydantic Hint objects and dict/simple objects
                if hasattr(hint, 'text') and hasattr(hint, 'given'):
                    hints.append({"text": hint.text, "given": hint.given})
                elif isinstance(hint, dict):
                    hints.append(hint)
                else:
                    # Fallback for unexpected hint format
                    hints.append({"text": str(hint), "given": False})
            return hints
        
        # Fallback: check the objective tuple structure (legacy support)
        if (hasattr(self, 'objective') and self.objective and 
            isinstance(self.objective, tuple) and len(self.objective) >= 2):
            obj_component = self.objective[1]
            
            # Check if it's a structured objective with hints
            if hasattr(obj_component, 'objective_hints') and obj_component.objective_hints:
                hints = []
                for hint in obj_component.objective_hints:
                    # Handle both Pydantic Hint objects and dict/simple objects
                    if hasattr(hint, 'text') and hasattr(hint, 'given'):
                        hints.append({"text": hint.text, "given": hint.given})
                    elif isinstance(hint, dict):
                        hints.append(hint)
                    else:
                        # Fallback for unexpected hint format
                        hints.append({"text": str(hint), "given": False})
                return hints
            
            # Check if it's a mystery objective (no hints for mysteries)
            elif (hasattr(obj_component, '__class__') and 
                  obj_component.__class__.__name__ == 'MysteryObjective'):
                return []  # No hints for mystery objectives
        
        return []

  def _get_puzzle_hints_for_location(self, location: 'Location' = None) -> list:
    if location is None:
        location = self.player.location
    
    puzzle_hints = []
    
    # Get hints from puzzles proposed by characters in this location
    for character in self.characters.values():
        if character.location is location:
            for puzzle in self.puzzles.values():
                if (hasattr(puzzle, 'proposed_by_character') and 
                    puzzle.proposed_by_character == character.name):
                    if hasattr(puzzle, 'puzzle_hints') and puzzle.puzzle_hints:
                        for hint in puzzle.puzzle_hints:
                            if hasattr(hint, 'text') and hasattr(hint, 'given'):
                                puzzle_hints.append({"text": hint.text, "given": hint.given})
                            elif isinstance(hint, dict):
                                puzzle_hints.append(hint)
                    if hasattr(puzzle, 'interaction_hint') and puzzle.interaction_hint:
                        hint = puzzle.interaction_hint
                        if hasattr(hint, 'text') and hasattr(hint, 'given'):
                            puzzle_hints.append({"text": hint.text, "given": hint.given})
                        elif isinstance(hint, dict):
                            puzzle_hints.append(hint)
    
    # Get hints from puzzles proposed by items in this location
    for item in location.items:
        for puzzle in self.puzzles.values():
            if (hasattr(puzzle, 'proposed_by_location') and 
                puzzle.proposed_by_location == item.name):
                if hasattr(puzzle, 'puzzle_hints') and puzzle.puzzle_hints:
                    for hint in puzzle.puzzle_hints:
                        if hasattr(hint, 'text') and hasattr(hint, 'given'):
                            puzzle_hints.append({"text": hint.text, "given": hint.given})
                        elif isinstance(hint, dict):
                            puzzle_hints.append(hint)
                if hasattr(puzzle, 'interaction_hint') and puzzle.interaction_hint:
                    hint = puzzle.interaction_hint
                    if hasattr(hint, 'text') and hasattr(hint, 'given'):
                        puzzle_hints.append({"text": hint.text, "given": hint.given})
                    elif isinstance(hint, dict):
                        puzzle_hints.append(hint)
    
    # Get hints from puzzles that block passages from this location
    for blocked_location_name, (_, obstacle, _) in location.blocked_locations.items():
        if obstacle.__class__.__name__ == 'Puzzle':
            puzzle = obstacle
            if hasattr(puzzle, 'puzzle_hints') and puzzle.puzzle_hints:
                for hint in puzzle.puzzle_hints:
                    if hasattr(hint, 'text') and hasattr(hint, 'given'):
                        puzzle_hints.append({"text": hint.text, "given": hint.given})
                    elif isinstance(hint, dict):
                        puzzle_hints.append(hint)
            if hasattr(puzzle, 'interaction_hint') and puzzle.interaction_hint:
                hint = puzzle.interaction_hint
                if hasattr(hint, 'text') and hasattr(hint, 'given'):
                    puzzle_hints.append({"text": hint.text, "given": hint.given})
                elif isinstance(hint, dict):
                    puzzle_hints.append(hint)
    
    return puzzle_hints

  def update_hints(self):
    current_location = self.player.location
    
    if self._has_puzzles_in_location(current_location):
        # Location has puzzles: use puzzle-specific hints
        puzzle_hints = self._get_puzzle_hints_for_location(current_location)
        if puzzle_hints:
            self.current_hints = puzzle_hints
        else:
            # Fallback to explore hints if no puzzle hints available
            self.current_hints = self.default_explore_hints.copy()
    else:
        # Location has no puzzles: use objective hints
        objective_hints = self._get_objective_hints()
        if objective_hints:
            self.current_hints = objective_hints
        else:
            # Fallback to explore hints if no objective hints available
            self.current_hints = self.default_explore_hints.copy()

  def update_hints_for_puzzle_activity(self, puzzle_name: str):
    # Find the puzzle and switch to its specific hints
    if puzzle_name in self.puzzles:
        puzzle = self.puzzles[puzzle_name]
        puzzle_hints = []
                
        if hasattr(puzzle, 'puzzle_hints') and puzzle.puzzle_hints:
            for i, hint in enumerate(puzzle.puzzle_hints):
                if hasattr(hint, 'text') and hasattr(hint, 'given'):
                    hint_dict = {"text": hint.text, "given": hint.given}
                    puzzle_hints.append(hint_dict)
                elif isinstance(hint, dict):
                    puzzle_hints.append(hint)
        if puzzle_hints:
            self.current_hints = puzzle_hints

  def get_next_hint(self) -> str:
    for hint in self.current_hints:
        if not hint["given"]:
            hint["given"] = True
            return hint["text"]
    
    # If all hints have been given, return a generic message
    return "Keep exploring and trying different actions. You're on the right track!"

  def reset_hints(self):
    for hint in self.current_hints:
        if isinstance(hint, dict):
            hint["given"] = False

  def update_from_structured(self, world_update, language: str = 'en') -> None:
    
    # Handle moved objects
    for moved_obj in world_update.moved_objects:
      try:
        # Use flexible object matching instead of strict dictionary lookup
        world_item = self._find_object_flexible(moved_obj.object_name)
        
        if world_item is None:
          print(f"❌ Object '{moved_obj.object_name}' not found in world")
          continue
        
        # Check if item should go to player inventory (case-insensitive)
        new_location_lower = moved_obj.new_location.lower()
        player_name_lower = self.player.name.lower()
        
        if new_location_lower in ['inventory', 'inventario', 'player', 'jugador', player_name_lower]:
          # Player takes item
          item_source = next((char for char in self.characters.values() if world_item in char.inventory), None)
          if not item_source:
              item_source = next((loc for loc in self.locations.values() if world_item in loc.items), None)

          if item_source:
              # This is a standard item in a location or inventory
              try:
                  self.player.save_item(world_item, item_source)
                  # Check for mystery clue discovery when taking items
                  clue_discovery = self._check_mystery_clue_discovery(world_item.name, language)
                  if clue_discovery:
                      world_update.narration += clue_discovery
              except Exception as e:
                  # Item cannot be taken - override the narration to reflect reality
                  if "cannot be taken" in str(e):
                      if language == 'es':
                          world_update.narration = f"Intentas tomar {world_item.name}, pero es demasiado grande, está fijado en su lugar, o simplemente no puedes llevarlo contigo. Tendrás que dejarlo aquí."
                      else:
                          world_update.narration = f"You try to take {world_item.name}, but it's too large, fixed in place, or you simply can't carry it with you. You'll have to leave it here."
                      print(f"⚠️ Item '{world_item.name}' is not gettable - narration corrected")
                  else:
                      raise  # Re-raise if it's a different error
          else:
              # If not found, check if it's a blocking item
              obstacle_found = False
              for location in self.locations.values():
                  for _, (blocked_loc, obstacle, _) in location.blocked_locations.items():
                      if obstacle is world_item:
                          if world_item.gettable:
                              # Add blocking item to player inventory
                              if world_item not in self.player.inventory:
                                  self.player.inventory.append(world_item)

                              # Unblock the passage since the obstacle is taken
                              location.unblock_passage(blocked_loc)
                              print(f"✅ Player took blocking item '{world_item.name}', unblocking passage from '{location.name}' to '{blocked_loc.name}'.")

                              # Check for clue discovery
                              clue_discovery = self._check_mystery_clue_discovery(world_item.name, language)
                              if clue_discovery:
                                  world_update.narration += clue_discovery
                          else:
                              # Blocking item is not gettable - override narration
                              if language == 'es':
                                  world_update.narration = f"Intentas tomar {world_item.name}, pero está bloqueando el paso y no puedes moverlo. Necesitas encontrar otra forma de lidiar con esto."
                              else:
                                  world_update.narration = f"You try to take {world_item.name}, but it's blocking the passage and you can't move it. You need to find another way to deal with this."
                              print(f"⚠️ Blocking item '{world_item.name}' is not gettable - narration corrected")

                          obstacle_found = True
                          break
                  if obstacle_found:
                      break
              if obstacle_found:
                  break
            
        elif moved_obj.new_location in self.characters:
          # Player gives item to character
          self.player.give_item(self.characters[moved_obj.new_location], world_item)
          
        else:
          # Item moves to a location — remove from player and all character inventories
          self.player.inventory = [i for i in self.player.inventory if i is not world_item]
          for char in self.characters.values():
            char.inventory = [i for i in char.inventory if i is not world_item]

          if moved_obj.new_location in self.locations:
            target_loc = self.locations[moved_obj.new_location]
            if world_item not in target_loc.items:
              target_loc.items.append(world_item)
          else:
            if world_item not in self.player.location.items:
              self.player.location.items.append(world_item)
          
      except Exception as e:
        print(f"Error moving object {moved_obj.object_name}: {e}")

    # Handle blocked passages
    for passage in world_update.blocked_passages_available:
      try:
        if passage.is_available and passage.location_name in self.locations:
          self.locations[self.player.location.name].unblock_passage(self.locations[passage.location_name])
      except Exception as e:
        print(f"Error unblocking passage to {passage.location_name}: {e}")

    # Handle location change
    if world_update.location_changed.new_location:
      try:
        new_location_name = world_update.location_changed.new_location
        target_location = None
        
        # First try exact match
        if new_location_name in self.locations:
          target_location = self.locations[new_location_name]
        else:
          target_location = self._find_location_case_insensitive(new_location_name)
          
          # If still not found, try partial matching for location names that contain the search term
          if target_location is None:
            for name, location in self.locations.items():
              if new_location_name.lower() in name.lower() or name.lower().startswith(new_location_name.lower()):
                target_location = location
                print(f"🔍 Location found via partial match: '{new_location_name}' -> '{name}'")
                break
        
        if target_location:
          self.player.move(target_location)
          print(f"✅ Player successfully moved to {target_location.name}")
          # Update hints when player changes location
          self.update_hints()
        else:
          print(f"❌ Location '{new_location_name}' not found in world")
          print(f"Available locations: {list(self.locations.keys())}")
      except Exception as e:
        print(f"Error moving player to {world_update.location_changed.new_location}: {e}")

    # Handle puzzle solutions
    for puzzle_solution in world_update.puzzles_solved:
      try:
        if puzzle_solution.success:
          success = self.solve_puzzle(puzzle_solution.puzzle_name, puzzle_solution.answer)
          if success:
            print(f"✅ Puzzle {puzzle_solution.puzzle_name} solved successfully!")
            # Update hints after solving a puzzle - player may now need different hints
            self.update_hints()
          else:
            print(f"❌ Incorrect answer for puzzle {puzzle_solution.puzzle_name}")
        else:
          print(f"❌ Player attempted puzzle {puzzle_solution.puzzle_name} but failed")
      except Exception as e:
        print(f"Error processing puzzle solution {puzzle_solution.puzzle_name}: {e}")

    # Check for puzzle proposition when investigating items
    # This handles cases where investigating items should propose puzzles
    if hasattr(world_update, 'narration') and world_update.narration:
      # Look for item investigation keywords in the narration
      investigation_keywords = ['investigate', 'examine', 'look at', 'inspect', 'observe', 'check', 'study']
      narration_lower = world_update.narration.lower()
      
      # Check if any item in the current location has been investigated
      for item_name, item in self.items.items():
        if item in self.player.location.items:
          # Check if the item is mentioned with investigation keywords
          item_mentioned = any(keyword in narration_lower and item_name.lower() in narration_lower 
                             for keyword in investigation_keywords)
          
          # Also check if item was mentioned without being moved (indicating investigation)
          item_investigated_not_moved = (item_name.lower() in narration_lower and 
                                       not any(moved_obj.object_name == item_name for moved_obj in world_update.moved_objects))
          
          if item_mentioned or item_investigated_not_moved:
            # Check if this item should propose a puzzle
            puzzle = self.find_puzzle_proposed_by_location(item_name)
            if puzzle:
              print(f"🧩 Item {item_name} investigation triggered puzzle: {puzzle.name}")
              # Update hints to focus on this specific puzzle
              self.update_hints_for_puzzle_activity(puzzle.name)
              # Add puzzle proposition to narration if not already present
              if puzzle.name.lower() not in world_update.narration.lower():
                puzzle_description = puzzle.descriptions[0] if puzzle.descriptions else puzzle.problem
                world_update.narration += f"\n\n🧩 {puzzle_description}\n\n{puzzle.problem}"

    # Check for mystery clue discovery when interacting with items
    # This handles cases where items can't be picked up (gettable=False) but players interact with them
    if hasattr(world_update, 'narration') and world_update.narration:
      for item_name, item in self.items.items():
        # Check if the item is mentioned in the narration and is in the current location
        if (item_name.lower() in world_update.narration.lower() and 
            item in self.player.location.items and
            not any(moved_obj.object_name == item_name for moved_obj in world_update.moved_objects)):
          # Player interacted with item but didn't move it - check for clue discovery
          clue_discovery = self._check_mystery_clue_discovery(item_name, language)
          if clue_discovery:
            # Add discovery message to narration
            world_update.narration += clue_discovery

    # Check if any puzzle problem is mentioned in the narration (indicates puzzle was presented)
    if hasattr(world_update, 'narration') and world_update.narration:
      narration_lower = world_update.narration.lower()
      for puzzle_name, puzzle in self.puzzles.items():
        if hasattr(puzzle, 'problem') and puzzle.problem:
          # Check if the puzzle problem text appears in the narration
          puzzle_problem_lower = puzzle.problem.lower()
          # Look for significant portions of the puzzle problem (at least 10 characters)
          if len(puzzle_problem_lower) >= 10 and puzzle_problem_lower in narration_lower:
            print(f"🧩 Puzzle problem detected in narration: {puzzle_name}")
            # Update hints to focus on this specific puzzle
            self.update_hints_for_puzzle_activity(puzzle_name)
            break  # Only update for the first puzzle found to avoid conflicts

  def update (self, updates: str) -> None:
    self.parse_moved_objects(updates)
    self.parse_blocked_passages(updates)
    self.parse_location_change(updates)
    self.parse_puzzle_solution(updates)
    
    # Check for mystery clue discovery when interacting with items (legacy method)
    # This handles cases where items can't be picked up but players interact with them
    for item_name, item in self.items.items():
      # Check if the item is mentioned in the updates and is in the current location
      if (item_name.lower() in updates.lower() and 
          item in self.player.location.items):
        # Check if the item was NOT moved (no "Moved object: <item_name>" in updates)
        moved_pattern = f"Moved object:.*<{re.escape(item_name)}>"
        if not re.search(moved_pattern, updates, re.IGNORECASE):
          # Player interacted with item but didn't move it - check for clue discovery
          clue_discovery = self._check_mystery_clue_discovery(item_name, 'en')  # Default to English for legacy
          if clue_discovery:
            print(clue_discovery)

  def parse_moved_objects (self, updates: str) -> None:
    parsed_objects = re.findall(r".*Moved object:\s*(.+)",updates)
    if 'None' not in parsed_objects and parsed_objects:
      parsed_objects_split = re.findall(r"<[^<>]*?>.*?<[^<>]*?>",parsed_objects[0])
      for parsed_object in parsed_objects_split:
        pair = re.findall(r"<([^<>]*?)>.*?<([^<>]*?)>",parsed_object)
        try:
          world_item = self.items[pair[0][0]]
          
          if pair[0][1] in ['Inventory', 'Inventario', 'Player',  'Jugador', self.player.name]: # (save_item case)
            item_location = next((char for char in self.characters.values() if world_item in char.inventory), None)
            if not item_location:
                item_location = next((loc for loc in self.locations.values() if world_item in loc.items), None)

            if item_location:
                self.player.save_item(world_item, item_location)
                # Check for mystery clue discovery when taking items
                clue_discovery = self._check_mystery_clue_discovery(world_item.name)
                if clue_discovery:
                    print(clue_discovery)
            else:
                # Check if it's a blocking item
                obstacle_found = False
                for location in self.locations.values():
                    for _, (blocked_loc, obstacle, _) in list(location.blocked_locations.items()):
                        if obstacle is world_item:
                            if world_item.gettable:
                                if world_item not in self.player.inventory:
                                    self.player.inventory.append(world_item)
                                location.unblock_passage(blocked_loc)
                                print(f"INFO: Player took blocking item '{world_item.name}', unblocking passage from '{location.name}' to '{blocked_loc.name}'.")

                                clue_discovery = self._check_mystery_clue_discovery(world_item.name)
                                if clue_discovery:
                                    print(clue_discovery)

                            obstacle_found = True
                            break
                    if obstacle_found:
                        break
                if obstacle_found:
                    break

          elif pair[0][1] in self.characters: #(give_item case)
            self.player.give_item(self.characters[pair[0][1]], world_item)
          
          else: #(drop_item case)
            self.player.drop_item(world_item)
        except Exception as e:
          print(e)

  def parse_blocked_passages (self, updates: str) -> None:
    parsed_blocked_passages = re.findall(r".*Blocked passages now available:\s*(.+)",updates)
    if 'None' not in parsed_blocked_passages and parsed_blocked_passages:
      parsed_blocked_passages_split = re.findall(r"<([^<>]*?)>",parsed_blocked_passages[0])
      for parsed_passage in parsed_blocked_passages_split:
        try:
          self.locations[self.player.location.name].unblock_passage(self.locations[parsed_passage])
        except Exception as e:
          print (e)

  def parse_location_change (self, updates: str) -> None:
    parsed_location_change = re.findall(r".*Your location changed: (.+)",updates)
    if "None" not in parsed_location_change and parsed_location_change:
      parsed_location_change_split = re.findall(r"<([^<>]*?)>",parsed_location_change[0])
      try:
        self.player.move(self.locations[parsed_location_change_split[0]])
      except Exception as e:
        print(e)

  def parse_puzzle_solution(self, updates: str) -> None:
    parsed_puzzle_solutions = re.findall(r".*Puzzle solved:\s*(.+)", updates)
    if 'None' not in parsed_puzzle_solutions and parsed_puzzle_solutions:
        # Formato esperado: "Puzzle solved: <puzzle_name> with answer <answer>"
        puzzle_info = parsed_puzzle_solutions[0]
        
        # Extraer nombre del puzzle y respuesta - REGEX CORREGIDO
        puzzle_match = re.findall(r"<([^<>]*?)>.*?with\s+answer\s+<([^<>]*?)>", puzzle_info)
        if puzzle_match:
            puzzle_name = puzzle_match[0][0]
            user_answer = puzzle_match[0][1].strip()
            
            try:
                if self.solve_puzzle(puzzle_name, user_answer):
                    print(f"✅ Puzzle {puzzle_name} resuelto correctamente!")
                else:
                    print(f"❌ Respuesta incorrecta para puzzle {puzzle_name}")
            except Exception as e:
                print(f"Error processing puzzle solution: {e}")
        else:
            # Fallback para formato sin brackets en la respuesta
            puzzle_match_fallback = re.findall(r"<([^<>]*?)>.*?with\s+answer\s+(.+)", puzzle_info)
            if puzzle_match_fallback:
                puzzle_name = puzzle_match_fallback[0][0]
                user_answer = puzzle_match_fallback[0][1].strip()
                
                try:
                    if self.solve_puzzle(puzzle_name, user_answer):
                        print(f"✅ Puzzle {puzzle_name} resuelto correctamente!")
                    else:
                        print(f"❌ Respuesta incorrecta para puzzle {puzzle_name}")
                except Exception as e:
                    print(f"Error processing puzzle solution: {e}")

  def normalize_answer(self, answer: str) -> str:
      import re
      answer = answer.lower().strip()
      # Remove leading articles (a, an, the) - case insensitive
      answer = re.sub(r'^(a |an |the )', '', answer, flags=re.IGNORECASE)
      # Remove punctuation at the end and beginning of the answer
      answer = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', answer)
      # Remove all punctuation except spaces between words
      answer = re.sub(r'[^\w\s]', '', answer)
      # Normalize whitespace (multiple spaces to single space)
      answer = ' '.join(answer.split())
      return answer

  def solve_puzzle(self, puzzle_name: str, answer: str) -> bool:
      # Try exact match first
      puzzle = None
      actual_puzzle_name = None
      
      if puzzle_name in self.puzzles:
          puzzle = self.puzzles[puzzle_name]
          actual_puzzle_name = puzzle_name
      else:
          # Fuzzy matching for puzzle names (case-insensitive, partial match)
          puzzle_name_lower = puzzle_name.lower()
          for actual_name, p in self.puzzles.items():
              actual_name_lower = actual_name.lower()
              # Check if names match with flexible comparison
              if (puzzle_name_lower == actual_name_lower or
                  puzzle_name_lower in actual_name_lower or
                  actual_name_lower in puzzle_name_lower):
                  puzzle = p
                  actual_puzzle_name = actual_name
                  print(f"🔍 Fuzzy matched puzzle: '{puzzle_name}' → '{actual_name}'")
                  break
      
      if not puzzle:
          print(f"❌ Puzzle not found: '{puzzle_name}'. Available puzzles: {list(self.puzzles.keys())}")
          return False
      
      # Normalize both answers for flexible comparison
      correct_answer_norm = self.normalize_answer(puzzle.answer)
      user_answer_norm = self.normalize_answer(answer)
      
      print(f"🔍 Puzzle validation: '{puzzle_name}'")
      print(f"   Expected (normalized): '{correct_answer_norm}'")
      print(f"   Player (normalized): '{user_answer_norm}'")
      
      if correct_answer_norm == user_answer_norm:
          # Apply rewards
          self._apply_puzzle_rewards(puzzle)
          # Mark puzzle as solved (use actual puzzle name from world)
          self.puzzle_states[actual_puzzle_name] = 'solved'
          print(f"✅ Puzzle state updated: puzzle_states['{actual_puzzle_name}'] = 'solved'")
          
          # Automatically unblock passages that are blocked by this puzzle
          self._unblock_passages_for_solved_puzzle(actual_puzzle_name, puzzle)
          
          return True
      
      print(f"❌ Answer mismatch: '{user_answer_norm}' != '{correct_answer_norm}'")
      return False

  def _apply_puzzle_rewards(self, puzzle: 'Puzzle'):
      for reward in puzzle.rewards:
          try:
              if hasattr(reward, 'reward_type'):
                  # Special handling for observation puzzles where the reward is finding the item
                  if puzzle.puzzle_type == "observation" and reward.reward_type == "ITEM":
                      item = self._find_item_case_insensitive(reward.item_name)
                      if item and item in self.player.location.items:
                          self.player.save_item(item, self.player.location)
                          print(f"[INFO] Player found observation reward item '{item.name}' in location.")
                          continue # Move to next reward

                  if reward.reward_type == "ITEM" and hasattr(reward, 'item_name'):
                      # Give item to player - case insensitive search
                      item = self._find_item_case_insensitive(reward.item_name)
                      if item:
                          # Find who has the item and transfer it
                          owner_found = False
                          # First, check all character inventories
                          for char in self.characters.values():
                              if item in char.inventory:
                                  char.give_item(self.player, item)
                                  owner_found = True
                                  break  # Exit character loop once found and transferred

                          # If not found in any character's inventory, check locations
                          if not owner_found:
                              for location in self.locations.values():
                                  if item in location.items:
                                      self.player.save_item(item, location)
                                      # No need to set owner_found=True, as we break immediately
                                      break # Exit location loop once found and transferred
                  
                  elif reward.reward_type == "PASSAGE" and hasattr(reward, 'from_location') and hasattr(reward, 'to_location'):
                      # Unblock passage - case insensitive search
                      from_loc = self._find_location_case_insensitive(reward.from_location)
                      to_loc = self._find_location_case_insensitive(reward.to_location)
                      if from_loc and to_loc and to_loc.name in from_loc.blocked_locations:
                          from_loc.unblock_passage(to_loc)
          except Exception as e:
              print(f"Error applying puzzle reward: {e}")

  def _find_item_case_insensitive(self, item_name: str) -> 'Item':
      for name, item in self.items.items():
          if name.lower() == item_name.lower():
              return item
      return None

  def find_puzzle_proposed_by_location(self, item_name: str):
      for puzzle_name, puzzle in self.puzzles.items():
          if hasattr(puzzle, 'proposed_by_location') and puzzle.proposed_by_location:
              if puzzle.proposed_by_location.lower() == item_name.lower():
                  return puzzle
      return None

  def _find_location_case_insensitive(self, location_name: str) -> 'Location':
      for name, location in self.locations.items():
          if name.lower() == location_name.lower():
              return location
      return None

  def _find_object_flexible(self, object_name: str):
      # Strategy 1: Exact match (preserves existing behavior)
      if object_name in self.items:
          return self.items[object_name]
      
      # Strategy 2: Case-insensitive exact match
      for name, item in self.items.items():
          if name.lower() == object_name.lower():
              return item
      
      # Strategy 3: Partial matching - object_name contained in item name or item name starts with object_name
      for name, item in self.items.items():
          # Remove common articles and prepositions for better matching
          clean_object_name = object_name.lower().strip()
          clean_item_name = name.lower().strip()
          
          # Remove leading articles in both Spanish and English
          for article in ['el ', 'la ', 'los ', 'las ', 'un ', 'una ', 'the ', 'a ', 'an ']:
              if clean_object_name.startswith(article):
                  clean_object_name = clean_object_name[len(article):]
              if clean_item_name.startswith(article):
                  clean_item_name = clean_item_name[len(article):]
          
          # Check if the cleaned object name is contained in the item name or vice versa
          if (clean_object_name in clean_item_name or 
              clean_item_name.startswith(clean_object_name) or
              clean_object_name.startswith(clean_item_name)):
              return item
      
      # No match found
      return None

  def _unblock_passages_for_solved_puzzle(self, puzzle_name: str, puzzle: 'Puzzle'):
      passages_unblocked = []
      
      # Check all locations for blocked passages blocked by this puzzle
      for location in self.locations.values():
          if hasattr(location, 'blocked_locations') and location.blocked_locations:
              # Create a list of items to remove (to avoid modifying dict during iteration)
              passages_to_unblock = []
              
              for _, (blocked_loc, obstacle, _) in location.blocked_locations.items():
                  # Check if the obstacle is the puzzle we just solved
                  if (isinstance(obstacle, type(puzzle)) and 
                      hasattr(obstacle, 'name') and 
                      obstacle.name == puzzle_name):
                      passages_to_unblock.append(blocked_loc)
                      
              # Unblock the passages
              for blocked_loc in passages_to_unblock:
                  try:
                      location.unblock_passage(blocked_loc)
                      passages_unblocked.append(f"{location.name} → {blocked_loc.name}")
                  except Exception as e:
                      print(f"⚠️ Error unblocking passage {location.name} → {blocked_loc.name}: {e}")
      
      if passages_unblocked:
          print(f"🔓 Passages automatically unblocked: {', '.join(passages_unblocked)}")
      else:
          print(f"🔍 No passages found blocked by puzzle '{puzzle_name}'")
