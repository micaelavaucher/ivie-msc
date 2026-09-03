"""Structured data models for the IVIE world system with semantic connections."""

#---- Imports -----------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

#---- Hint Models -------------------------------------------------------------
class Hint(BaseModel):
    """A hint that can be given to the player."""
    text: str = Field(description="The hint text to show to the player")
    given: bool = Field(default=False, description="Whether this hint has been given to the player")

#---- Enums and Types ---------------------------------------------------------
class PuzzleType(str, Enum):
    RIDDLE = "riddle"           # Adivinanza
    LOGIC = "logic"             # Problema lógico
    WORDPLAY = "wordplay"       # Juego de palabras
    OBSERVATION = "observation" # Observar detalles del entorno
    SEQUENCE = "sequence"       # Ordenar cosas en secuencia
    CODE = "code"               # Descifrar códigos
    MEMORY = "memory"           # Recordar información previa

class ObjectiveType(str, Enum):
    REACH_LOCATION = "reach_location"   # Llegar a un lugar
    GET_ITEM = "get_item"               # Conseguir un objeto
    DELIVER_AN_ITEM = "deliver_an_item" # Entregar un objeto a alguien/algún lugar
    FIND_CHARACTER = "find_character"   # Encontrar a un personaje
    SOLVE_MYSTERY = "solve_mystery"     # Resolver un misterio general

class RewardType(str, Enum):
    PASSAGE = "passage"                 # Desbloquea un pasaje
    ITEM = "item"                       # Otorga un objeto
    OBJECTIVE_COMPLETION = "objective_completion"  # Completa directamente el objetivo
    RECRUIT_CHARACTER = "recruit_character"  # Recluta un personaje al grupo del jugador

class RequirementType(str, Enum):
    ITEM = "item"                       # Necesita un objeto específico
    PUZZLE = "puzzle"                   # Necesita resolver un puzzle
    LOCATION = "location"               # Necesita estar en un lugar específico
    CHARACTER = "character"             # Necesita interactuar con un personaje

class ComponentType(str, Enum):
    ITEM = "item"                       # Componente es un objeto
    CHARACTER = "character"             # Componente es un personaje
    LOCATION = "location"               # Componente es una ubicación

class ItemActionType(str, Enum):
    """Defines the specific, engine-supported actions an item can perform."""
    UNLOCK_PASSAGE = "unlock_passage"   # The item is a key for a blocked passage
    SOLVE_PUZZLE = "solve_puzzle"       # The item is a key or clue for a puzzle
    GIVE_TO_CHARACTER = "give_to_character" # The item is meant to be given to an NPC
    LORE = "lore"                       # The item provides story/information but has no mechanical use

class FeelingLevel(str, Enum):
    """A recruitable NPC's feeling toward the player, ordered low to high."""
    HOSTILE = "hostile"
    WARY = "wary"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    DEVOTED = "devoted"

class RelationshipTag(str, Enum):
    """A symmetric social tag between two characters, used for the party ripple effect."""
    RIVAL = "rival"
    ALLY = "ally"

class PuzzleConditionType(str, Enum):
    """A world-state predicate the engine can check on its own to decide a puzzle is solved.

    These exist so that puzzles whose solution is an ACTION (ring the bell, hand over the
    ribbon, reach the shrine) are verifiable at all: their `answer` is prose the player will
    never type verbatim, so string matching alone leaves them permanently unsolved.
    """
    HAS_ITEM = "has_item"                                   # item is in the player's inventory
    ITEM_GIVEN_TO_CHARACTER = "item_given_to_character"     # item is in that character's inventory
    ITEM_IN_LOCATION = "item_in_location"                   # item has been placed in that location
    PLAYER_AT_LOCATION = "player_at_location"               # player is standing in that location
    TALKED_TO_CHARACTER = "talked_to_character"             # player has interacted with that character

class PuzzleSolutionCondition(BaseModel):
    """One engine-checkable condition. A puzzle is solved when ALL of its conditions hold."""
    condition_type: PuzzleConditionType = Field(description="Which world-state fact the engine must check")
    description: str = Field(description="Plain-language statement of what the player must do to satisfy this condition")
    item_name: Optional[str] = Field(default=None, description="Item involved. Required for has_item, item_given_to_character and item_in_location. Note: this item must exist in the world")
    character_name: Optional[str] = Field(default=None, description="Character involved. Required for item_given_to_character and talked_to_character. Note: this character must exist in the world")
    location_name: Optional[str] = Field(default=None, description="Location involved. Required for item_in_location and player_at_location. Note: this location must exist in the world")

#---- Reward Models (lo que se obtiene al resolver puzzles) ------------------
class PuzzleReward(BaseModel):
    """Base model for what you get when solving a puzzle."""
    reward_type: RewardType = Field(description="Type of reward obtained")
    description: str = Field(description="What exactly is gained")

class PassageReward(PuzzleReward):
    """Unlocks a blocked passage."""
    reward_type: RewardType = Field(default=RewardType.PASSAGE)
    from_location: str = Field(description="Location where passage starts. Note: this location must exist in the world")
    to_location: str = Field(description="Location that becomes accessible. Note: this location must exist in the world")
    
class ItemReward(PuzzleReward):
    """Provides an item."""
    reward_type: RewardType = Field(default=RewardType.ITEM)
    item_name: str = Field(description="Name of the item obtained. Note: this item must exist in the world and be in someone's inventory or a location")

class ObjectiveReward(PuzzleReward):
    """Directly completes the objective."""
    reward_type: RewardType = Field(default=RewardType.OBJECTIVE_COMPLETION)

class RecruitCharacterReward(PuzzleReward):
    """Recruits a character into the player's party."""
    reward_type: RewardType = Field(default=RewardType.RECRUIT_CHARACTER)
    character_name: str = Field(description="Name of the recruitable character this puzzle recruits. Note: this character must exist in the world and have recruitable=True")

#---- Requirement Models (lo que se necesita para activar algo) --------------
class Requirement(BaseModel):
    """Base model for requirements to unlock connections."""
    requirement_type: RequirementType = Field(description="Type of requirement")
    description: str = Field(description="What needs to be done to fulfill this requirement")

class ItemRequirement(Requirement):
    """Requirement to bring a specific item."""
    requirement_type: RequirementType = Field(default=RequirementType.ITEM)
    item_name: str = Field(description="Name of the required item. Note: this item must exist in the world and be gettable=True")
    
class PuzzleRequirement(Requirement):
    """Requirement to solve a puzzle."""
    requirement_type: RequirementType = Field(default=RequirementType.PUZZLE)
    puzzle_name: str = Field(description="Name of the puzzle that must be solved. Note: this puzzle must exist in the world")

class LocationRequirement(Requirement):
    """Requirement to be in a specific location."""
    requirement_type: RequirementType = Field(default=RequirementType.LOCATION)
    location_name: str = Field(description="Name of the required location. Note: this location must exist in the world")

class CharacterRequirement(Requirement):
    """Requirement to interact with a specific character."""
    requirement_type: RequirementType = Field(default=RequirementType.CHARACTER)
    character_name: str = Field(description="Name of the character to interact with. Note: this character must exist in the world")

#---- Enhanced Models --------------------------------------------------------
class GeneratedPuzzle(BaseModel):
    name: str = Field(description="Unique name of the puzzle")
    puzzle_type: PuzzleType = Field(description="Type of puzzle")
    descriptions: List[str] = Field(description="List of descriptive texts explaining the puzzle")
    problem: str = Field(description="Clear statement of the puzzle problem")
    answer: str = Field(description="The solution to the puzzle")
    accepted_answers: List[str] = Field(
        default=[],
        description="Alternative phrasings of the answer that must also be accepted (synonyms, with/without articles, the bare keyword). Always include at least the shortest keyword form of the answer. Only meaningful for puzzles the player solves by SAYING something."
    )
    solution_conditions: List[PuzzleSolutionCondition] = Field(
        default=[],
        description="Engine-checkable world-state conditions that mean this puzzle is solved. REQUIRED for any puzzle whose solution is an ACTION rather than a spoken answer (e.g. answer 'Ring the silver bell' -> conditions: has_item 'Silver Bell' + talked_to_character 'The Queen'). Every puzzle must be solvable via either accepted_answers or solution_conditions - never leave both empty."
    )
    location: Optional[str] = Field(default=None, description="Location where puzzle is found, or None if given by character. Note: if specified, this location must exist in the world")
    proposed_by_character: Optional[str] = Field(default=None, description="Character who proposes this puzzle, or None if environmental, NONE IF REWARD IS A PASSAGE. Note: if specified, this character must exist in the world")
    proposed_by_location: Optional[str] = Field(default=None, description="Location that when investigated/examined should propose this puzzle, or None if it's given by a character.")
    rewards: List[Union[PassageReward, ItemReward, ObjectiveReward, RecruitCharacterReward]] = Field(
        description="What you get when you solve this puzzle. Note: all reward items and locations must exist in the world"
    )
    relevance_to_objective: str = Field(description="How solving this puzzle helps achieve the main objective")
    hint: str = Field(description="How the character or the narration hints to the puzzle")
    puzzle_hints: List[Hint] = Field(default=[], description="Progressive hints for solving this puzzle (from general to specific)")
    interaction_hint: Optional[Hint] = Field(default=None, description="Hint about how to interact with this puzzle if player hasn't started yet")

class GeneratedItem(BaseModel):
    name: str = Field(description="Unique name of the item")
    action_type: ItemActionType = Field(description="The single, specific mechanical action this item can be used for. This defines its purpose in the game engine.")
    descriptions: List[str] = Field(description="List of descriptive texts for the item")
    gettable: bool = Field(default=True, description="Whether the item can be picked up. Note: items required for objectives must always be gettable=True")
    is_objective_target: bool = Field(
        default=False, 
        description="Whether this item is required to complete the main objective. Note: objective targets must always be gettable=True"
    )
    relevance_to_objective: Optional[str] = Field(default=None, description="How this item helps with the main objective, or None if decorative")
    required_for: List[str] = Field(default=[], description="Names of puzzles, characters, or locations this item is required for")

class CharacterInteraction(BaseModel):
    """Defines how a character interacts with the player."""
    gives_information: Optional[str] = Field(default=None, description="Important information the character provides")
    gives_item: Optional[str] = Field(default=None, description="Item the character gives. Note: this item must exist in the character's inventory")
    proposes_puzzle: Optional[str] = Field(default=None, description="Name of puzzle this character proposes when interacted with. Note: this puzzle must exist in the world and have proposed_by_character set to this character's name")
    requires: List[Union[ItemRequirement, PuzzleRequirement, LocationRequirement, CharacterRequirement]] = Field(
        default=[], description="What the character needs before helping. Note: all referenced items, puzzles, locations, and characters must exist in the world"
    )
    interaction_text: Optional[str] = Field(default=None, description="What the character says when first interacted with. Note: this is required if the character proposes a puzzle or gives items")
    relevance_to_objective: str = Field(description="How this character helps achieve the main objective")

class GeneratedCharacter(BaseModel):
    name: str = Field(description="Unique name of the character")
    descriptions: List[str] = Field(description="List of character descriptions")
    location: str = Field(description="Location where this character is placed. CRITICAL LOGIC RULE: If this character holds an item or puzzle solution required to unlock a passage, they CANNOT be placed in the location behind that very passage or any location only accessible through it.")
    inventory: List[str] = Field(default=[], description="Items this character starts with. Note: all items must exist in the world")
    interaction: Optional[CharacterInteraction] = Field(default=None, description="How this character can help the player, or None if just decorative")
    recruitable: bool = Field(default=False, description="Whether the player can recruit this character into their party. Only a subset of characters should be recruitable.")
    initial_feeling: FeelingLevel = Field(default=FeelingLevel.NEUTRAL, description="This character's starting feeling toward the player. Only meaningful when recruitable=True.")

class GeneratedRelationship(BaseModel):
    """A symmetric rivalry or alliance tag between two characters."""
    character_a: str = Field(description="Name of the first character in this relationship. Note: this character must exist in the world")
    character_b: str = Field(description="Name of the second character in this relationship. Note: this character must exist in the world")
    tag: RelationshipTag = Field(description="Whether these two characters are rivals or allies")

class BlockedPassage(BaseModel):
    location: str = Field(description="Destination location that is blocked. Note: this location must exist in the world and be in the connecting_locations list")
    obstacle_name: str = Field(description="Name of the physical object that blocks the passage (e.g., 'Candado', 'Puerta cerrada'). Note: this should be a separate item from what's needed to unblock it")
    obstacle_description: str = Field(description="Description of the physical obstacle")
    required_to_unblock: Union[ItemRequirement, PuzzleRequirement, LocationRequirement, CharacterRequirement] = Field(
        description="What's needed to unblock this passage. Note: this must be different from obstacle_name - the obstacle blocks, the requirement removes the obstacle"
    )
    relevance_to_objective: str = Field(description="Why accessing this location is important for the objective")

class GeneratedLocation(BaseModel):
    name: str = Field(description="Unique name of the location")
    descriptions: List[str] = Field(description="List of atmospheric descriptions")
    items: List[str] = Field(default=[], description="Names of items initially present. CRITICAL LOGIC RULE: An item required to unlock a passage CANNOT be placed in the location behind that very passage or any location only accessible through it.")
    connecting_locations: List[str] = Field(default=[], description="Directly accessible locations. Note: connections must be bidirectional - if A connects to B, then B must connect to A")
    blocked_passages: List[BlockedPassage] = Field(default=[], description="Blocked passages with their requirements")
    relevance_to_objective: Optional[str] = Field(default=None, description="How this location relates to the main objective")

class ObjectiveComponent(BaseModel):
    """Represents a component involved in the objective."""
    name: str = Field(description="Name of the component (item, character, or location). Note: this component must exist in the world")
    component_type: ComponentType = Field(description="Type of component")
    role_in_objective: str = Field(description="What role this component plays in completing the objective")

#---- Mystery Models ---------------------------------------------------------
class MysteryClue(BaseModel):
    name: str = Field(description="Name of the mystery clue")
    description: str = Field(description="Description of what the clue reveals")
    associated_item: str = Field(description="Item that this clue is associated with. Note: this item must exist in the world")
    item_location: Optional[str] = Field(default=None, description="Location where the associated item can be found. Note: this location must exist in the world")
    relevance_to_mystery: str = Field(description="How this clue helps solve the mystery")
    discovered: bool = Field(default=False, description="Whether this clue has been discovered by the player")

class GeneratedObjective(BaseModel):
    type: ObjectiveType = Field(description="Type of the main objective")
    components: List[ObjectiveComponent] = Field(description="All components involved in this objective. Note: all referenced components must exist in the world")
    description: str = Field(description="Clear description of what the player needs to accomplish")
    success_conditions: List[str] = Field(description="Specific conditions that must be met to complete the objective. Note: ensure these conditions are actually achievable given the world setup")
    mystery_clues: Optional[List[MysteryClue]] = Field(default=None, description="List of clues for mystery objectives. Only used when type is SOLVE_MYSTERY")
    mystery_solution: Optional[str] = Field(default=None, description="The solution to the mystery. Only used when type is SOLVE_MYSTERY")
    completion_narration: Optional[str] = Field(default=None, description="Narrative description of what happens after the player successfully completes the objective. This should provide a satisfying conclusion to the adventure. Not used for SOLVE_MYSTERY objectives (which use mystery_solution instead)")
    objective_hints: List[Hint] = Field(default=[], description="Progressive hints for advancing toward the objective (from general to specific). Only used for non-mystery objectives")
    hints: List[Hint] = Field(default=[], description="List of hints that can be given to the player")

class DependencyChain(BaseModel):
    """Represents a chain of dependencies leading to the objective."""
    chain_description: str = Field(description="Description of this dependency chain")
    steps: List[str] = Field(description="Ordered list of steps in this chain")
    elements_involved: List[str] = Field(description="Names of all world elements involved in this chain. Note: all elements must exist in the world")

class GeneratedWorld(BaseModel):
    locations: List[GeneratedLocation] = Field(description="All locations in the world. Note: all location connections must be bidirectional")
    items: List[GeneratedItem] = Field(description="All items in the world. Note: objective target items must be gettable=True")
    characters: List[GeneratedCharacter] = Field(description="All non-player characters. Note: all character locations must exist, and all character inventories must contain existing items")
    puzzles: List[GeneratedPuzzle] = Field(description="All puzzles in the world. Note: puzzle rewards must reference existing world elements")
    player: GeneratedCharacter = Field(description="The player character. Note: player location must exist in the world")
    objective: GeneratedObjective = Field(description="The main objective. Note: all objective components must exist and be accessible in the world")
    dependency_chains: List[DependencyChain] = Field(description="Possible paths to complete the objective. Note: all chains must be actually completable with the given world elements")
    world_theme: str = Field(description="Overall theme or setting of the world")
    narrative_context: str = Field(description="Background story that explains why everything is connected")
    npc_relationships: List[GeneratedRelationship] = Field(default=[], description="Rivalries or alliances between characters. Only include a pair here if the narrative actually motivates a rivalry or alliance - most character pairs should have no entry.")

#---- World Update Models (existing, keeping for compatibility) --------------
class MovedObject(BaseModel):
    object_name: str = Field(description="Name of the object that was moved")
    new_location: str = Field(description="Name of the location where the object is now placed. Use 'Inventory' when the player now has the object, whether they picked it up themselves OR a character handed/gave it to them.")

class BlockedPassageAvailable(BaseModel):
    location_name: str = Field(description="Name of the location where the blocked passage status changed")
    is_available: bool = Field(default=True, description="Whether the passage is now available")

class LocationChange(BaseModel):
    new_location: Optional[str] = Field(default=None, description="Name of the new location where the player moved")

class PuzzleSolved(BaseModel):
    """Represents a puzzle that was solved by the player."""
    puzzle_name: str = Field(description="Name of the puzzle that was solved")
    answer: str = Field(description="What the player said or did as their attempt at this puzzle")
    success: bool = Field(description="Whether the player's attempt actually satisfies the puzzle. Judge by MEANING, not by string equality: set true if what the player said or did accomplishes what the puzzle's expected answer describes (e.g. answer 'Ring the Small Silver Bell' and the player rings the bell). Set false if they said something different, or only asked about the puzzle without attempting it.")

class WorldUpdate(BaseModel):
    moved_objects: List[MovedObject] = Field(default=[], description="List of objects that were moved")
    blocked_passages_available: List[BlockedPassageAvailable] = Field(default=[], description="List of blocked passages that changed status")
    location_changed: LocationChange = Field(default=LocationChange(), description="Player location change information")
    puzzles_solved: List[PuzzleSolved] = Field(default=[], description="List of puzzles that were solved this turn")
    narration: str = Field(description="Narrative text describing what happened")

#---- Pipeline Models (for incremental world generation) --------------------
class WorldConcept(BaseModel):
    """Concept and high-level description of the world."""
    title: str = Field(description="Title or name of the world/adventure")
    backstory: str = Field(description="Background story that sets the context")
    player_concept: str = Field(description="Description of the player character and their role")
    main_objective: str = Field(description="High-level description of what the player must accomplish")

class KeyEntity(BaseModel):
    """Base model for key entities in the world skeleton."""
    name: str = Field(description="Name of the entity")
    purpose: str = Field(description="Role or purpose of this entity in the world")

class WorldSkeleton(BaseModel):
    """Skeleton structure with key entities before detailed generation."""
    key_locations: List[KeyEntity] = Field(description="Key locations that will form the world structure")
    key_items: List[KeyEntity] = Field(description="Key items that will be important for the objective")
    key_characters: List[KeyEntity] = Field(description="Key characters that will interact with the player")

#---- Expansion Models -------------------------------------------------------
class WorldExpansion(BaseModel):
    """Model for expanding existing worlds with new connected areas."""
    new_locations: List[GeneratedLocation] = Field(default=[], description="New locations to add")
    new_items: List[GeneratedItem] = Field(default=[], description="New items to add")
    new_characters: List[GeneratedCharacter] = Field(default=[], description="New characters to add")
    new_puzzles: List[GeneratedPuzzle] = Field(default=[], description="New puzzles to add")
    connections_to_existing: List[str] = Field(description="How the new content connects to existing world")
    expansion_narrative: str = Field(description="Story reason for why these new areas are now accessible")