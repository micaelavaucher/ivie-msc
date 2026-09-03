from .structured_data_models import WorldUpdate
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

def prompt_describe_objective (objective, language:str = 'en'):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_describe_objective_spanish(objective)
    else:
        system_msg, user_msg = prompt_describe_objective_english(objective)
    
    return system_msg, user_msg 

def prompt_describe_objective_english (objective):

    system_msg = """You have to provide an alternative way to narrate the objective given to you. You should always use simple language. 
    
    Provide your narration in a clear, direct format. For example: You have to get the key or You have to reach the castle"""

    # Handle new GeneratedObjective structure - check if it's a tuple with new structure
    if len(objective) == 2 and hasattr(objective[1], 'description') and hasattr(objective[1], 'type'):
        user_msg = f'The objective to narrate in an alternative way is: "{objective[1].description}"'
    else:
        # Legacy fallback for old objective structure
        first_component_class = objective[0].__class__.__name__
        second_component_class = objective[1].__class__.__name__
        user_msg = ""

        if first_component_class == "Character" and second_component_class == "Location":
            user_msg =  f'The objective to narrate in an alterative way is "You have to go to {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "Item":
            user_msg = f'The objective to narrate in an alterative way is "{objective[0].name} has to get the item {objective[1].name}."'
        elif first_component_class == "Item" and second_component_class == "Location":
            user_msg = f'The objective to narrate in an alterative way is "You have to leave item {objective[0].name} in place {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "Character":
            user_msg = f'The objective to narrate in an alterative way is "{objective[0].name} has to find {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "MysteryObjective":
            user_msg = f'The objective to narrate in an alterative way is "{objective[0].name} has to solve the mystery: {objective[1].description}."'

    return system_msg, user_msg 

def prompt_describe_objective_spanish (objective):

    system_msg = """Tienes que dar una forma alternativa de narrar el objetivo que se te dará. Siempre usa lenguaje simple. 
    
    Proporciona tu narración en un formato claro y directo. Por ejemplo: Tienes que conseguir la llave o Tienes que llegar al castillo"""

    # Handle new GeneratedObjective structure - check if it's a tuple with new structure
    if len(objective) == 2 and hasattr(objective[1], 'description') and hasattr(objective[1], 'type'):
        user_msg = f'El objetivo a decir de forma alternativa es: "{objective[1].description}"'
    else:
        # Legacy fallback for old objective structure
        first_component_class = objective[0].__class__.__name__
        second_component_class = objective[1].__class__.__name__
        user_msg = ""

        if first_component_class == "Character" and second_component_class == "Location":
            user_msg = f'El objetivo a decir de forma alternativa es "Tienes que ir a {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "Item":
            user_msg = f'El objetivo a decir de forma alternativa es "{objective[0].name} tiene que conseguir el objeto {objective[1].name}."'
        elif first_component_class == "Item" and second_component_class == "Location":
            user_msg = f'El objetivo a decir de forma alternativa es "Tienes que dejar el objeto {objective[0].name} en el lugar {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "Character":
            user_msg = f'El objetivo a decir de forma alternativa es "{objective[0].name} tiene que encontrar a {objective[1].name}."'
        elif first_component_class == "Character" and second_component_class == "MysteryObjective":
            user_msg = f'El objetivo a decir de forma alternativa es "{objective[0].name} tiene que resolver el misterio: {objective[1].description}."'

    return system_msg, user_msg

def prompt_narrate_current_scene (world_state: str, previous_narrations: 'list[str]', language: str = 'en', starting_scene: bool = False, first_visit: bool = None):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_narrate_current_scene_spanish(world_state, previous_narrations, starting_scene, first_visit)
    else:
        system_msg, user_msg = prompt_narrate_current_scene_english(world_state, previous_narrations, starting_scene, first_visit)


    return system_msg, user_msg

def prompt_narrate_current_scene_english (world_state: str, previous_narrations: 'list[str]', starting_scene: bool = False, first_visit: bool = None):
    system_msg = "You are a storyteller. Take the state of the world given to you and narrate it in vivid, evocative sentences. Use the detailed descriptions of locations, objects, and characters provided in the world state to create rich, immersive narrations with sensory details. Incorporate textures, colors, sounds, smells, and visual elements based on the available descriptions. Be careful not to include details that contradict the current state of the world, that move the story forward, or invent new puzzles that aren't in the world."
    
    if starting_scene:
        system_msg += "\nTake into account that this is the first scene in the story: introduce the main character using their descriptions, creating a small background story and why that character is in that specific location. Use the location descriptions to paint a vivid scene. It is important that you mention all components in this location using their descriptions to bring them to life. It is very important that you name the places the player can access from this position in an engaging way.\n"
    elif first_visit or (first_visit is None and len(previous_narrations)==0):
        system_msg += "Take into account that the player already knows what the main character looks like, so do not mention anything about that. However, it is the first time the player visits this place, so describe it exhaustively using the location descriptions. Mention all components in this location using their descriptions. It is very important that you name the places the player can access from this position."
    else:
        system_msg += "Take into account that the player already knows what the main character looks like, so just describe changes or anything absolutely necessary, keep the narration short. Next I’ll give you some previous narrations of this same location (from oldest to newest) so you can be sure to not repeat the same details again:\n"
        for narration in previous_narrations:
            system_msg+=f'- {narration}\n'

    system_msg+= "\nRemember: you are talking to the player, describing what his or her character has and what he or she can see, hear, smell, or feel. Use the component descriptions to make everything come alive with vivid details."

    user_msg =f"""This is the state of the world at the moment:
    {world_state}
    """

    return system_msg, user_msg

def prompt_narrate_current_scene_spanish (world_state: str, previous_narrations: 'list[str]', starting_scene: bool = False, first_visit: bool = None):
    
    system_msg = f"""Eres un narrador. Toma el estado del mundo que se te de y nárralo con oraciones vívidas y evocativas. Usa las descripciones detalladas de ubicaciones, objetos y personajes proporcionadas en el estado del mundo para crear narraciones ricas e inmersivas con detalles sensoriales. Incorpora texturas, colores, sonidos, olores y elementos visuales basándote en las descripciones disponibles. Ten cuidado de no incluir detalles que contradigan el estado del mundo actual, o que hagan avanzar la historia, o inventar puzzles o acertijos que no estén ya en el mundo. Además, si el jugador está en la misma ubicación en la que existe un puzzle, debes darle una pista que le haga saber que allí hay un puzzle, o que un personaje tiene un puzzle para él."""
    
    if starting_scene:
        system_msg += "\nTen en cuenta que esta es la primera escena en la historia narrada: presenta al personaje del jugador usando sus descripciones, creando un pequeño trasfondo y por qué este personaje está en ese lugar específicamente. Usa las descripciones de la ubicación para pintar una escena vívida. Es importante que menciones todos los componentes que hay en este lugar usando sus descripciones para darles vida. Es muy importante que nombres los lugares a los que puede acceder el jugador desde esta posición de manera atractiva.\n"
    elif first_visit or (first_visit is None and len(previous_narrations)==0):
        system_msg += "Ten en cuenta que el jugador ya conoce a su personaje, y cómo se ve, así que no menciones nada sobre esto. Sin embargo, es la primera vez que el jugador visita este lugar, así que descríbelo exhaustivamente usando las descripciones de la ubicación. Menciona todos los componentes que hay en este lugar usando sus descripciones. Es muy importante que nombres los lugares a los que puede acceder el jugador desde esta posición.\n"
    else:
        system_msg += "Ten en cuenta que el jugador ya conoce a su personaje, y cómo se ve, así que no menciones nada sobre esto. Además, no es la primera vez que el jugador visita este lugar, así solo describe cualquier cambio o aspecto sumamente relevante, manten la narracion corta. A continuación te daré algunas narraciones previas de este mismo lugar (de la más antigua a la más nueva), así te puedes asegurar de no repetir los mismos detalles de nuevo:\n"
        for narration in previous_narrations:
            system_msg+=f'- {narration}\n'

    system_msg+= "\nRecuerda: le estás hablando al jugador, describiendo lo que su personaje tiene y lo que puede sentir, ver, oír u oler. Usa las descripciones de los componentes para hacer que todo cobre vida con detalles vívidos. MANTÉN EL ESPAÑOL durante toda la narración - nunca cambies al inglés."

    user_msg = f"""Este es el estado del mundo en este momento:
    {world_state}
    """

    return system_msg, user_msg

def prompt_world_update (world_state: str, input: str, language: str = 'en'):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_world_update_spanish(world_state, input)
    else:
        system_msg, user_msg = prompt_world_update_english(world_state, input)


    return system_msg, user_msg

def prompt_world_update_structured(world_state: str, input: str, language: str = 'en', relevant_memories: str = ""):
    """Create a world update prompt that will return structured data based on Pydantic models."""
    if language == 'es':
        system_msg = """Eres un narrador experto manejando un mundo ficticio interactivo. Tu tarea es analizar las acciones del jugador y determinar los cambios exactos en el estado del mundo.

REGLAS CRÍTICAS PARA PUZZLES:
1. **PROPOSICIÓN DE PUZZLES**: Si un personaje tiene la propiedad "proposes_puzzle", el personaje DEBE proponer el puzzle cuando el jugador interactúe con él, ANTES de dar cualquier recompensa.
1b. **PROPOSICIÓN DE PUZZLES POR OBJETOS**: Si un puzzle tiene la propiedad "proposed_by_location", el puzzle DEBE ser propuesto cuando el jugador interactúe con ese objeto específico o intente desbloquear el pasaje (investigate, examine, look at, etc.).
2. **RESOLUCIÓN DE PUZZLES - SE REQUIERE UN INTENTO REAL**: Solo completa el campo "puzzles_solved" cuando el jugador hace un intento real. Un intento es (a) decir una respuesta ("la respuesta es FUTURO"), o (b) REALIZAR la acción que describe la respuesta del puzzle ("toco la campana", "le entrego la cinta"). Ambos cuentan, y (b) cuenta aunque el jugador nunca escriba el texto de la respuesta. Órdenes genéricas como "resolver [puzzle]" SIN decir ni hacer nada NO son intentos. Cuando haya un intento real, juzga si satisface el puzzle por SIGNIFICADO (ver VALIDACIÓN DE PUZZLES abajo).
3. **FLEXIBILIDAD EN OBSERVACIÓN**: Para puzzles de observación (`puzzle_type`: "observation"), si la acción del jugador es un intento razonable de encontrar el objeto (p. ej., 'buscar en el escritorio', 'mirar en los libros'), considera el puzzle resuelto aunque no nombre el escondite exacto ('el cajón con fondo falso'). El objetivo es recompensar la exploración lógica.
4. **REQUISITOS**: Verifica que se cumplan todos los requisitos antes de permitir acciones (objetos necesarios, puzzles resueltos, etc.).

REGLAS GENERALES:
- Objetos solo cambian de lugar si el jugador realiza acciones específicas (tomar, dar, dejar), o si un personaje le entrega/da un objeto al jugador (ver regla de OBJETOS RECIBIDOS DE PERSONAJES más abajo)
- Pasajes bloqueados solo se desbloquean si se cumplen los requisitos específicos
- **REGLA DE MOVIMIENTO**: El jugador se mueve si intenta explícitamente ir a otra ubicación Y esa ubicación está listada en "From [ubicación actual] the player can access:" en el estado del mundo. Si una ubicación está listada como accesible, el movimiento ES posible, SIN EXCEPCIÓN, incluso si en algún "Recuerdo Relevante del Pasado" un intento anterior fue rechazado o un pasaje aparecía como bloqueado. El estado del mundo (accesible/bloqueado) es SIEMPRE el hecho actual y más reciente; una entrada en "Recuerdos Relevantes del Pasado" que contradiga el estado del mundo actual describe una situación PASADA que ya cambió (p. ej., un obstáculo que ya fue resuelto), NUNCA la situación actual. Si la ubicación NO aparece en "Blocked passages", el pasaje NO está bloqueado, sin importar lo que un recuerdo pasado sugiera.
- Presta atención a las descripciones, capacidades y requisitos de cada componente
- **REACCIONES SOCIALES DE PERSONAJES**: El sentimiento de un personaje hacia el jugador SOLO cambia por las reglas del motor del juego, nunca por tu narración. Si el estado del mundo lista "Relaciones conocidas", puedes reflejar en el diálogo/narración una rivalidad o alianza ya conocida cuando sea relevante. Si un personaje NO aparece listado en "Relaciones conocidas" junto a otro, NO inventes ninguna rivalidad, alianza o reacción entre ellos - trata a ese par como socialmente indiferente a las decisiones de grupo del jugador.

CRÍTICO - OBJETOS RECIBIDOS DE PERSONAJES:
Si el jugador le pide un objeto a un personaje (p. ej. "dile a X que me dé el objeto Y", "pídele el objeto a X") y el personaje accede a entregarlo (no tiene requisitos pendientes que lo impidan), DEBES incluir ese objeto en "moved_objects" con "new_location": "Inventory", exactamente igual que si el jugador lo hubiera tomado directamente. No es suficiente con narrar que el personaje entrega el objeto: el campo "moved_objects" DEBE reflejar ese cambio, o el objeto NO pasará al inventario del jugador aunque la narración diga lo contrario.

REGLAS PARA NARRACIÓN RICA:
- **USA LAS DESCRIPCIONES**: El estado del mundo incluye descripciones detalladas de ubicaciones, objetos y personajes. Úsalas para crear narraciones vívidas y evocativas.
- **DETALLES SENSORIALES**: Incorpora sonidos, olores, texturas, y sensaciones visuales basándote en las descripciones disponibles.
- **DESCRIBE LOS OBJETOS**: Cuando el jugador interactúa con objetos, usa sus descripciones para darles vida (materiales, aspecto, peso, etc.).
- **ATMOSFERA DE UBICACIONES**: Usa las descripciones de las ubicaciones para crear ambiente y inmersión.
- **PERSONALIDAD DE PERSONAJES**: Refleja las descripciones de los personajes en su comportamiento y diálogo.
- **CONEXIONES NARRATIVAS**: Menciona ubicaciones accesibles y objetos visibles de manera natural en la narración.

INSTRUCCIÓN ESPECIAL SOBRE MEMORIA:
Presta especial atención a la sección 'Recuerdos Relevantes del Pasado' si está presente. Úsala SOLO para continuidad narrativa (p. ej., cómo reaccionaría un personaje basándose en interacciones pasadas, o para recordar detalles de la historia). NUNCA uses los recuerdos pasados para decidir hechos MECÁNICOS del juego actuales, como si un pasaje está bloqueado, si un objeto es accesible, o si el jugador puede moverse a un lugar. Esos hechos SIEMPRE se determinan exclusivamente por el "Estado actual del mundo" de este prompt, que es la única fuente de verdad presente. Un recuerdo pasado puede describir un obstáculo que YA FUE RESUELTO (p. ej., "el paso estaba bloqueado" cuando ahora ya no lo está) — en ese caso, ignora el recuerdo para esa decisión y confía en el estado actual. No repitas ni justifiques un rechazo anterior si el estado actual del mundo ya no lo respalda.

CRÍTICO - CONSISTENCIA DE IDIOMA:
Tu respuesta DEBE estar completamente en español. Todos los diálogos de personajes, descripciones y narraciones deben ser en español. Si encuentras texto en inglés en las descripciones del mundo, tradúcelo mentalmente y responde en español.

Tu respuesta debe ser un JSON válido que siga exactamente el modelo WorldUpdate."""
        
        user_msg_base = f"""Estado actual del mundo:
{world_state}

{relevant_memories}El jugador ahora realiza la siguiente acción:
<accion>
{input}
</accion>

Devuelve un objeto JSON con la siguiente estructura:
{{
    "moved_objects": [
        {{"object_name": "nombre", "new_location": "ubicación"}}
    ],
    "blocked_passages_available": [
        {{"location_name": "ubicación", "is_available": true}}
    ],
    "location_changed": {{
        "new_location": "nombre_ubicación_o_null"
    }},
    "puzzles_solved": [
        {{"puzzle_name": "nombre_exacto_del_puzzle", "answer": "respuesta_del_jugador", "success": true}}
    ],
    "narration": "Descripción narrativa rica de lo que ocurrió"
}}

CRÍTICO - VALIDACIÓN DE PUZZLES:
Cuando el jugador intenta resolver un puzzle, DEBES juzgar si su intento realmente lo satisface:
1. Busca el puzzle en el estado del mundo por su nombre exacto
2. Lee el campo "answer" del puzzle y determina qué exige realmente
3. Juzga por SIGNIFICADO, no por igualdad de cadenas. Existen dos tipos de respuesta:
   - Una respuesta DICHA (la solución de una adivinanza, un nombre, un código). El jugador la
     satisface diciéndola. Acepta sinónimos, artículos de más o de menos, y diferencias de
     mayúsculas. Rechaza una palabra genuinamente distinta.
   - Una ACCIÓN que el jugador debe realizar ("Tocar la campana de plata", "Darle la cinta",
     "Abrir la puerta del este"). El jugador la satisface HACIENDO esa cosa en su acción, sin
     importar cómo la exprese. Nunca le exijas escribir la frase literal.
4. Si el intento satisface el puzzle: success = true. Si no lo satisface: success = false
5. Si el jugador solo preguntó SOBRE el puzzle sin intentarlo: no incluyas ninguna entrada

Ejemplos de validación:
- Puzzle answer: "Un mapa", Player: "un mapa" → success: true ✅ (lo mismo)
- Puzzle answer: "Un mapa", Player: "mapa" → success: true ✅ (el artículo no importa)
- Puzzle answer: "Un mapa", Player: "carta náutica" → success: false ❌ (palabra diferente)
- Puzzle answer: "Tocar la campana de plata", Player: "tomo la campana y la hago sonar para despertarla"
  → success: true ✅ (el jugador realizó la acción requerida)
- Puzzle answer: "Tocar la campana de plata", Player: "le grito para que despierte"
  → success: false ❌ (hizo otra cosa)
- Puzzle answer: "Caracola, Vieira", Player: "Vieira, Caracola" → success: true ✅ (mismo conjunto)
- Puzzle answer: "Tocar la campana", Player: "¿cuál es la respuesta del puzzle?" → sin entrada ❌ (no es un intento)

CRÍTICO - PASAJES BLOQUEADOS:
NO manipules manualmente "blocked_passages_available" para desbloquear pasajes de puzzles. Los pasajes se desbloquean AUTOMÁTICAMENTE cuando:
1. Un puzzle con recompensa de PASAJE es resuelto (success=true)
2. El jugador toma un objeto que estaba bloqueando un pasaje
3. La lógica del juego determina que el requisito se cumplió

Solo debes establecer blocked_passages_available cuando detectes que el jugador ha tomado un objeto que estaba bloqueando físicamente un pasaje.

CRÍTICO - NOMBRES EXACTOS DE OBJETOS:
El campo "object_name" en moved_objects DEBE ser el nombre EXACTO de un objeto listado en el estado del mundo. NO uses aproximaciones, nombres parciales, o variaciones del nombre. Por ejemplo, si el estado del mundo contiene "El Recipiente Mágico", debes usar exactamente "El Recipiente Mágico", NO "el recipiente", "recipiente", o "recipiente mágico". Revisa cuidadosamente el estado del mundo y copia el nombre exacto tal como aparece listado.

IMPORTANTE: Siempre incluye el campo narration con una descripción detallada y evocativa de lo que ocurrió en el mundo. Usa las descripciones específicas de objetos, ubicaciones y personajes del estado del mundo para crear una narración rica en detalles sensoriales. Menciona texturas, colores, sonidos, olores y sensaciones cuando sea apropiado."""
    else:
        system_msg = """You are an expert narrator managing an interactive fictional world. Your task is to analyze the player's actions and determine the exact changes in the world state.

CRITICAL RULES FOR PUZZLES:
1. **PUZZLE PROPOSITION**: If a character has the "proposes_puzzle" property, the character MUST propose the puzzle when the player interacts with them, BEFORE giving any reward. CRITICAL: You MUST include the exact puzzle problem text from the world state in your narration. Check the character's "proposes_puzzle" field, find that puzzle in the world state, and copy its "problem" field verbatim into your narration. Do NOT paraphrase or mention puzzles vaguely - state the actual puzzle problem clearly so the player knows what to solve.
1b. **PUZZLE PROPOSITION BY ITEMS**: If a puzzle has the "proposed_by_location" property, the puzzle MUST be proposed when the player interacts with that specific item or if they try to unblock the passage it blocks (investigate, examine, look at, etc.). Include the exact puzzle problem text in your narration.
2. **PUZZLE RESOLUTION - AN ACTUAL ATTEMPT IS REQUIRED**: Only populate the "puzzles_solved" field when the player makes a real attempt at the puzzle. An attempt is either (a) stating an answer ("the answer is FUTURE", "I answer: echo"), or (b) PERFORMING the action the puzzle's answer describes ("I ring the bell", "I hand her the ribbon"). Both count, and (b) counts even though the player never typed the answer text. Generic commands like "solve [puzzle name]" or "answer the riddle" WITHOUT stating an answer or doing anything are NOT attempts: narrate asking the player what they want to answer or do, and do not mark the puzzle solved. Once there is a real attempt, judge whether it satisfies the puzzle by MEANING (see PUZZLE VALIDATION below).
2b. **EXACT PUZZLE NAMES - CRITICAL**: When filling the "puzzles_solved" field, you MUST use the EXACT puzzle name as it appears in the world state. Do NOT modify, add to, or paraphrase the puzzle name. Do NOT add character names or location names to the puzzle name. Example: If the world state shows a puzzle named "Captain's Riddle", use EXACTLY "Captain's Riddle" in puzzles_solved, NOT "Captain Thorne's Riddle" or "The Captain's Riddle". Copy the name character-for-character from the world state.
3. **FLEXIBILITY IN OBSERVATION**: For observation puzzles (`puzzle_type`: "observation"), if the player's action is a reasonable attempt to find the item (e.g., 'search the desk', 'look through the books'), consider the puzzle solved even if they don't name the exact hiding spot ('the false-bottomed drawer'). The goal is to reward logical exploration.
4. **REQUIREMENTS**: Verify that all requirements are met before allowing actions (necessary objects, solved puzzles, etc.).

GENERAL RULES:
- Objects only change location if the player performs specific actions (take, give, drop), OR if a character hands/gives an object to the player (see the ITEMS RECEIVED FROM CHARACTERS rule below)
- Blocked passages only unlock if specific requirements are met
- **MOVEMENT RULE**: The player moves if they explicitly attempt to go to another location AND that location is listed in "From [current location] the player can access:" in the world state. If a location is listed as accessible, movement IS possible, WITH NO EXCEPTIONS, even if a 'Relevant Past Memory' shows an earlier attempt being refused or the passage once being blocked. The world state (accessible/blocked) is ALWAYS the current, most up-to-date fact; a 'Relevant Past Memories' entry that contradicts the current world state describes a PAST situation that has since changed (e.g., an obstacle that has since been resolved), NEVER the current situation. If the location does NOT appear under "Blocked passages", it is NOT blocked, regardless of what any past memory suggests.
- Pay attention to the descriptions, capabilities, and requirements of each component
- **NPC SOCIAL REACTIONS**: A character's feeling toward the player only changes due to the game engine's own rules, never from your narration. If the world state lists "Known relationships", you may reflect an already-known rivalry or alliance in dialogue/narration when relevant. If a character is NOT listed in "Known relationships" with another character, do not invent a rivalry, alliance, or any reaction between them - treat that pair as socially indifferent to the player's party choices.

CRITICAL - ITEMS RECEIVED FROM CHARACTERS:
If the player asks a character for an item (e.g. "tell X I need item Y, to give it to me", "ask X for the item") and the character agrees to hand it over (no pending unmet requirements block it), you MUST include that item in "moved_objects" with "new_location": "Inventory", exactly as if the player had taken it directly. Narrating that the character hands over the item is NOT enough by itself: the "moved_objects" field MUST reflect the change, otherwise the item will NOT actually enter the player's inventory even though the narration says it did.

RULES FOR RICH NARRATION:
- **USE THE DESCRIPTIONS**: The world state includes detailed descriptions of locations, objects, and characters. Use them to create vivid and evocative narrations.
- **SENSORY DETAILS**: Incorporate sounds, smells, textures, and visual sensations based on available descriptions.
- **DESCRIBE OBJECTS**: When the player interacts with objects, use their descriptions to bring them to life (materials, appearance, weight, etc.).
- **LOCATION ATMOSPHERE**: Use location descriptions to create ambiance and immersion.
- **CHARACTER PERSONALITY**: Reflect character descriptions in their behavior and dialogue.
- **NARRATIVE CONNECTIONS**: Naturally mention accessible locations and visible objects in the narration.

SPECIAL INSTRUCTION ABOUT MEMORY:
Pay special attention to the 'Relevant Past Memories' section if present. Use it ONLY for narrative continuity (e.g., how a character would react based on past interactions, or recalling story details). NEVER use past memories to decide current game-MECHANICAL facts, such as whether a passage is blocked, whether an item is accessible, or whether the player can move to a place. Those facts are ALWAYS determined exclusively by the "Current world state" in this prompt, which is the sole source of truth present. A past memory may describe an obstacle that has SINCE BEEN RESOLVED (e.g., "the passage was blocked" when it no longer is) — in that case, ignore the memory for that decision and trust the current state. Do not repeat or justify an earlier refusal if the current world state no longer supports it.

Your response must be valid JSON that follows exactly the WorldUpdate model."""
    
        user_msg_base = f"""Current world state:
{world_state}

{relevant_memories}The player now performs the following action:
<action>
{input}
</action>

Return a JSON object with the following structure:
{{
    "moved_objects": [
        {{"object_name": "name", "new_location": "location"}}
    ],
    "blocked_passages_available": [
        {{"location_name": "location", "is_available": true}}
    ],
    "location_changed": {{
        "new_location": "location_name_or_null"
    }},
    "puzzles_solved": [
        {{"puzzle_name": "exact_puzzle_name", "answer": "player_answer", "success": true}}
    ],
    "narration": "Rich narrative description of what happened"
}}

CRITICAL - PUZZLE VALIDATION:
When the player attempts a puzzle, you MUST judge whether their attempt actually satisfies it:
1. Find the puzzle in the world state by its exact name
2. Read the puzzle's "answer" field and decide what it actually requires
3. Judge by MEANING, not by string equality. Two kinds of answer exist:
   - A SPOKEN answer (a riddle's solution, a name, a code). The player satisfies it by saying
     it. Accept synonyms, missing or extra articles, and different capitalisation. Reject a
     genuinely different word.
   - An ACTION the player must perform ("Ring the silver bell", "Give her the ribbon", "Open
     the eastern gate"). The player satisfies it by DOING that thing in their action, however
     they phrase it. Never require them to type the sentence out.
4. If the attempt satisfies the puzzle: success = true. If it doesn't: success = false
5. If the player only asked ABOUT the puzzle without attempting it: emit no entry at all

Validation examples:
- Puzzle answer: "A map", Player: "a map" → success: true ✅ (same thing)
- Puzzle answer: "A map", Player: "map" → success: true ✅ (article doesn't matter)
- Puzzle answer: "A map", Player: "chart" → success: false ❌ (different word)
- Puzzle answer: "Ring the Small Silver Bell", Player: "take the bell and ring it to wake her"
  → success: true ✅ (the player performed the required action)
- Puzzle answer: "Ring the Small Silver Bell", Player: "I shout at her to wake up"
  → success: false ❌ (did something else)
- Puzzle answer: "Conch, Scallop", Player: "Scallop, Conch" → success: true ✅ (same set)
- Puzzle answer: "Ring the bell", Player: "what is the answer to the puzzle?" → no entry ❌ (not an attempt)

CRITICAL - BLOCKED PASSAGES:
DO NOT manually manipulate "blocked_passages_available" to unblock puzzle passages. Passages are unblocked AUTOMATICALLY when:
1. A puzzle with a PASSAGE reward is solved (success=true)
2. The player takes an item that was physically blocking a passage
3. The game logic determines the requirement is met

You should ONLY set blocked_passages_available when you detect the player has taken an item that was physically blocking a passage.

CRITICAL - EXACT OBJECT NAMES:
The "object_name" field in moved_objects MUST be the EXACT name of an object listed in the world state. Do NOT use approximations, partial names, or variations of the name. For example, if the world state contains "The Ancient Key", you must use exactly "The Ancient Key", NOT "ancient key", "key", or "the key". Carefully review the world state and copy the exact name as it appears listed.

IMPORTANT: Always include the narration field with a detailed, evocative description of what occurred in the world. Use the specific descriptions of objects, locations, and characters from the world state to create rich narrations with sensory details. Mention textures, colors, sounds, smells, and sensations when appropriate."""
    
    return system_msg, user_msg_base, WorldUpdate

def prompt_world_update_spanish (world_state: str, input: str):
    system_msg = f"""Eres un narrador experto manejando un mundo ficticio interactivo. Siguiendo un formato específico, tu tarea es encontrar los cambios en el mundo a raíz de las acciones del jugador. En específico, tendrás que encontrar qué objetos cambiaron de lugar, qué pasajes entre lugares se desbloquearon, si el jugador se movió de lugar, y si resolvió puzzles.
    
    **REGLAS CRÍTICAS PARA PUZZLES:**
    (P1) **PROPOSICIÓN DE PUZZLES**: Si un personaje tiene la propiedad "proposes_puzzle", el personaje DEBE proponer el puzzle cuando el jugador interactúe con él, ANTES de dar cualquier recompensa. CRÍTICO: DEBES incluir el texto exacto del problema del puzzle del estado del mundo en tu narración. Revisa el campo "proposes_puzzle" del personaje, encuentra ese puzzle en el estado del mundo, y copia su campo "problem" textualmente en tu narración. NO parafrasees ni menciones puzzles vagamente - declara el problema del puzzle claramente para que el jugador sepa qué resolver.
    (P1b) **PROPOSICIÓN DE PUZZLES POR OBJETOS**: Si un puzzle tiene la propiedad "proposed_by_location", el puzzle DEBE ser propuesto cuando el jugador interactúe con ese objeto específico o el pasaje que bloquea (investigate, examine, look at, etc.). Incluye el texto exacto del problema del puzzle en tu narración.
    (P2) **RESOLUCIÓN DE PUZZLES - RESPUESTA REQUERIDA**: Solo debes llenar el campo "puzzles_solved" si el jugador proporciona explícitamente una respuesta al puzzle en su acción. Comandos genéricos como "resolver [nombre del puzzle]" o "responder el acertijo" SIN proporcionar la respuesta real deben resultar en una narración pidiendo al jugador que proporcione su respuesta, NO marcar el puzzle como resuelto. El jugador DEBE declarar su respuesta explícitamente (ej: "la respuesta es FUTURO" o "respondo: eco"). Una vez que se proporciona una respuesta, analiza si es correcta comparándola con la respuesta esperada del puzzle.
    (P2b) **NOMBRES EXACTOS DE PUZZLES - CRÍTICO**: Al llenar el campo "puzzles_solved", DEBES usar el nombre EXACTO del puzzle tal como aparece en el estado del mundo. NO modifiques, agregues, ni parafrasees el nombre del puzzle. NO agregues nombres de personajes o ubicaciones al nombre del puzzle. Ejemplo: Si el estado del mundo muestra un puzzle llamado "Captain's Riddle", usa EXACTAMENTE "Captain's Riddle" en puzzles_solved, NO "Captain Thorne's Riddle" ni "The Captain's Riddle". Copia el nombre carácter por carácter del estado del mundo.
    (P3) **REQUISITOS DE PUZZLES**: Verifica que se cumplan todos los requisitos antes de permitir que un puzzle sea resuelto.
    (P4) **RECOMPENSAS CONDICIONADAS**: Las recompensas (objetos, pasajes, información) solo se otorgan DESPUÉS de resolver exitosamente el puzzle.

    **REGLAS CRÍTICAS PARA INTERACCIONES CON PERSONAJES:**
    (I1) **SER DIRECTO Y ÚTIL**: Cuando el jugador interactúa con un personaje, el personaje debe ser DIRECTO sobre lo que necesita o quiere. No debe dar vueltas o ser evasivo innecesariamente.
    (I2) **COMUNICAR REQUISITOS CLARAMENTE**: Si un personaje tiene requisitos específicos (objetos, puzzles resueltos, etc.), debe comunicárselos al jugador de forma CLARA en la primera o segunda interacción. No debe seguir siendo misterioso después de que el jugador muestre interés.
    (I3) **EVITAR REPETICIÓN INÚTIL**: Si el jugador ya interactuó con un personaje y el personaje ya le dijo que necesita algo, no debe repetir la misma información vaga. En su lugar, debe ser más específico o sugerir dónde conseguir lo que necesita.
    (I4) **INFORMACIÓN PROGRESIVA**: En cada interacción, el personaje debe proporcionar información MÁS ESPECÍFICA que en la anterior, hasta que el jugador tenga toda la información necesaria para cumplir con los requisitos.

    Aquí hay otras aclaraciones importantes:
    (A) Presta atención a la descripción de los componentes y sus capacidades.
    (B) Si un pasaje está bloqueado, significa que el jugador debe desbloquearlo antes de poder acceder al lugar. Aunque el jugador te diga que va a acceder al lugar bloqueado, tienes que estar seguro de que está cumpliendo con lo pedido para permitirle desbloquear el acceso, por ejemplo usando una llave o resolviendo un puzzle.
    (C) **PERSONAJES CON REQUISITOS**: Si un personaje tiene requisitos específicos (como resolver un puzzle o tener ciertos objetos), NO debe dar objetos o ayudar hasta que esos requisitos se cumplan. Revisa cuidadosamente la sección de "interaction" de cada personaje y sus "requires".
    (D) No asumas que lo que dice el jugador siempre tiene sentido; quizás esas acciones intentan hacer algo que el mundo no lo permite.
    (D2) **REGLA DE MOVIMIENTO**: El jugador se mueve si intenta explícitamente ir a otra ubicación Y esa ubicación está listada en "From [ubicación actual] the player can access:" en el estado del mundo. Si una ubicación está listada como accesible, el movimiento ES posible.
    (E) **PUZZLES PROPUESTOS POR PERSONAJES**: Si un personaje propone un puzzle ("proposes_puzzle"), debe mencionarlo ANTES de dar cualquier recompensa. El jugador debe resolver el puzzle primero.
    (E2) **PUZZLES PROPUESTOS POR OBJETOS**: Si un puzzle tiene "proposed_by_location", debe ser propuesto cuando el jugador interactúe con ese objeto específico o el pasaje que bloquea (investigate, examine, etc.).
    (F) Sigue siempre el siguiente formato con las tres categorías, usando "None" en cada caso si no hay cambios y repite la categoría por cada caso:
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    - Puzzle solved: <puzzle_name> with answer <answer> (solo si el jugador resolvió un puzzle)
    (G) Por último, puedes agregar una narración de los cambios detecados en el estado del mundo (¡sin hacer avanzar la historia y sin crear detalles no incluidos en el estado del mundo!) usando el formato: #tu mensaje final#
    (H) Dentro de la sección de narración que agregues al final, entre símbolos #, también puedes responder preguntas que haga el jugador en su entrada, sobre los objetos o personajes que puede ver, o el lugar en el que se encuentra.
    (I) Tu narración debe ser rica en detalles y evocadora, utilizando detalles sensoriales cuando sea apropiado. Haz que el mundo cobre vida a través de tus descripciones, sin dejar de adherirte a los hechos del estado del mundo.
    (J) CRÍTICO: MANTÉN EL ESPAÑOL durante toda tu respuesta. Todos los diálogos de personajes y narraciones deben estar en español. Si encuentras texto en inglés en las descripciones del mundo, tradúcelo mentalmente y responde en español.

    Aquí hay algunos ejemplos (con la aclaración entre paréntesis sobre qué podría haber intentado hacer el jugador) sobre el formato, descritos en los puntos (F) y (G):
    
    Ejemplo 1 (El jugador guarda el hacha en su inventario)
    - Moved object: <hacha> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Tomas el mango de madera desgastada del hacha, sintiendo su peso reconfortante mientras la levantas. La cabeza metálica brilla tenuemente bajo la luz mientras la aseguras cuidadosamente en tu mochila. El peso familiar contra tu espalda te recuerda el consejo de tu padre sobre siempre mantener una buena herramienta a mano. #

    Ejemplo 2 (El jugador desbloquea el pasaje al Sótano)
    - Moved object: None
    - Blocked passages now available: <Sótano>
    - Your location changed: None
    - Puzzle solved: None
    # Con un giro final de la oxidada llave, el viejo candado se abre con un satisfactorio clic. Lo quitas del pestillo y empujas a un lado la pesada barra de madera que aseguraba la puerta del sótano. Una bocanada de aire frío y húmedo surge desde abajo, trayendo consigo el olor a piedra húmeda y recuerdos olvidados. El sótano, previamente prohibido, ahora es accesible, sus secretos esperando ser descubiertos en la oscuridad de abajo. #

    Ejemplo 3 (El jugador ahora está en el Jardín)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Jardín>
    - Puzzle solved: None
    # Atraviesas la chirriante verja del jardín y entras en un mundo de colores vibrantes y fragancias. La luz del sol se filtra a través de las hojas de un roble antiguo, proyectando sombras moteadas sobre el sendero cubierto de vegetación. Mariposas danzan entre flores de todos los tonos, y en algún lugar cercano, el agua fluye musicalmente. El jardín te abraza con su belleza salvaje, tan diferente de los confines estériles que acabas de dejar atrás. #

    Ejemplo 4 (El jugador guarda objetos en la bolsa y deja el hacha en el suelo)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Colocas cuidadosamente el plátano maduro y la botella de vidrio en tu bolsa, organizándolos para que nada se aplaste. El aroma dulce del plátano se mezcla con el olor a humedad de tu mochila bien viajada. Con deliberado cuidado, dejas el hacha pesada sobre el suelo pulido del Salón Principal. Reposa allí con cierta finalidad, su hoja reflejando la danzante luz de la araña de cristal que cuelga arriba. Quizás alguien más encuentre mejor uso para ella que tú. #

    Ejemplo 5 (El jugador guarda objetos en la bolsa, deja el hacha en el suelo y desbloquea el pasaje a la Habitación Pequeña)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: <Habitación Pequeña>
    - Your location changed: None
    - Puzzle solved: None
    # Tus dedos trabajan rápidamente mientras guardas el plátano y la botella en tu mochila. El vidrio tintinea suavemente contra tus otras posesiones mientras aseguras la solapa. El hacha la colocas cuidadosamente sobre el suelo de mármol del Salón Principal, su mango gastado apuntando hacia la gran escalera. Después de insertar la ornamentada llave en la pequeña cerradura de latón, escuchas una serie de clics y zumbidos mientras los mecanismos ocultos se desenganchan. La puerta previamente sellada hacia la Habitación Pequeña se estremece y luego se abre ligeramente, liberando una bocanada de aire viciado. Un nuevo camino está ahora disponible para ti, llamándote con la promesa del descubrimiento. #

    Ejemplo 6 (El jugador guarda objetos en la bolsa, deja el hacha en el suelo, desbloquea el pasaje y va a la Habitación Pequeña)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: <Habitación Pequeña>
    - Your location changed: <Habitación Pequeña>
    - Puzzle solved: None
    # Con eficiencia practicada, guardas tanto el plátano como la botella en tu bolsa, sintiendo cómo aumenta el peso cómodo contra tu cadera. El hacha la dejas deliberadamente sobre el suelo reluciente del Salón Principal, donde su cabeza metálica atrapa la luz del candelabro de cristal que cuelga arriba. Después de girar la antigua llave en la cerradura, la puerta oculta hacia la Habitación Pequeña se abre con un crujido, revelando un espacio intacto durante lo que deben ser décadas. Motas de polvo bailan en el rayo de luz que ahora se introduce en este santuario olvidado. Llevado por la curiosidad, cruzas el umbral, las tablas del suelo gimiendo bajo tu peso al entrar en la Habitación Pequeña. El aire aquí está cargado de secretos y el dulce olor a humedad de libros antiguos y recuerdos olvidados. #

    Ejemplo 7 (El jugador guarda el lápiz en la bolsa y le da el libro a Juan)
    - Moved object: <libro> now is in <Juan>, <lápiz> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Deslizas el gastado lápiz de cedro en tu bolsa, su forma familiar anidándose entre tus otras posesiones. El pesado libro encuadernado en cuero lo extiendes hacia Juan con ambas manos, respetando su aparente edad y valor. Sus ojos se ensanchan ligeramente al reconocer el tomo. "Esto es... He estado buscando esto durante años", susurra, su voz espesa de emoción. Sus manos curtidas aceptan el libro con reverencia, acunándolo como quien sostiene una reliquia preciosa. Juan abre cuidadosamente la cubierta, y por un momento, su comportamiento estoico se suaviza mientras contempla las páginas amarillentas en su interior. #

    Ejemplo 8 (El jugador da la computadora a Susana)
    - Moved object: <computadora> now is in <Susana>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Le entregas la elegante laptop a Susana, cuyos ojos se iluminan con interés profesional. "Por fin", murmura, sus dedos ya bailando sobre el teclado mientras la pantalla ilumina su rostro concentrado. El resplandor azul resalta la determinación en su expresión mientras accede rápidamente a archivos que tú no podrías esperar entender. Guarda la computadora de manera segura en su bolso de mensajero, el movimiento practicado y eficiente. "Esto podría cambiarlo todo", añade críticamente, asintiendo en agradecimiento mientras su mente claramente corre con nuevas posibilidades. #

    Ejemplo 9 (El jugador hace algo que no tiene el resultado esperado)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Intentas girar la ornamentada manija de latón, pero la puerta permanece obstinadamente cerrada. El mecanismo hace un sonido de clic sordo, pero nada más sucede. Quizás hay otra forma de abrirla, o algo que te estás perdiendo. Las marcas descoloridas sobre el marco de la puerta parecen burlarse de tus esfuerzos, manteniendo sus secretos bien guardados. #

    Ejemplo 10 (El jugador hace una pregunta)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Al examinar el extraño símbolo grabado en la pared, lo reconoces como un antiguo sigilo que representa protección y conocimiento oculto. La artesanía es notable, con intrincados patrones en espiral que parecen cambiar ligeramente cuando se ven desde diferentes ángulos. Las leyendas hablan de tales marcas utilizadas por los antiguos practicantes para alejar a los espíritus malignos mientras realizaban sus investigaciones arcanas. El hecho de que permanezca intacto después de todos estos siglos habla del poder que se creía que tenía. #"""
    
    
    user_msg = f"""Expresa los cambios en el mundo siguiendo el formato pedido, teniendo en cuenta que el jugador ingresó esta entrada "{input}" a partir de este estado del mundo:
    
    {world_state}"""

    return system_msg, user_msg

def prompt_world_update_english (world_state: str, input: str):
    system_msg = f"""You are an expert storyteller managing an interactive fictional world. Following a specific format, your task is to find the changes in the world after the actions in the player input. Specifically, you will have to find what objects were moved, which previously blocked passages are now unblocked, if the player moved to a new place, and if any puzzles were solved.

    **CRITICAL RULES FOR PUZZLES:**
    (P1) **PUZZLE PROPOSITION**: If a character has the "proposes_puzzle" property, the character MUST propose the puzzle when the player interacts with them, BEFORE giving any reward.
    (P1b) **PUZZLE PROPOSITION BY LOCATION**: If a puzzle has the "proposed_by_location" property, the puzzle MUST be proposed when the player explores the location.
    (P2) **PUZZLE RESOLUTION**: If the player attempts to solve a puzzle, carefully analyze if their answer is correct by comparing it with the expected answer.
    (P3) **PUZZLE REQUIREMENTS**: Verify that all requirements are met before allowing a puzzle to be solved.
    (P4) **CONDITIONAL REWARDS**: Rewards (objects, passages, information) are only granted AFTER successfully solving the puzzle.
       
    Here are other important clarifications:
    (A) Pay attention to the description of the components and their capabilities.
    (B) If a passage is blocked, then the player must unblock it before being able to reach the place. Even if the player tells you that he is going to access the locked location, you have to be sure that he is complying with what you asked to allow him to unlock the access, for example by using a key or solving a puzzle.
    (C) **CHARACTERS WITH REQUIREMENTS**: If a character has specific requirements (like solving a puzzle or having certain objects), they should NOT give objects or help until those requirements are met. Carefully review the "interaction" section of each character and their "requires".
    (D) Do not assume that the player input always makes sense; maybe those actions try to do something that the world does not allow.
    (D2) **MOVEMENT RULE**: The player moves if they explicitly attempt to go to another location AND that location is listed in "From [current location] the player can access:" in the world state. If a location is listed as accessible, movement IS possible.
    (E) Follow always the following format with the four categories, using "None" in each case if there are no changes and repeat the category for each case:
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    - Puzzle solved: <puzzle_name> with answer <answer> (only if the player solved a puzzle)
    (F) Finally, you can narrate the changes you've detected in the world state (without moving the story forward and without making up details not included in the world state!) using the format: #your final message#
    (G) In the narration section that you add at the end, between # symbols, you can also answer questions that the player asks in their input, about the objects or characters they can see, or the place they are in.
    (H) Your narration should be richly detailed and evocative, using sensory details when appropriate. Make the world come alive through your descriptions, while still adhering to the facts of the world state.

    Here I give you some examples (in parentheses, a clarification about what the player might have tried to do) for the asked format, as described in items (E) and (F):

    Example 1 (The player took the axe and put it in the inventory)
    - Moved object: <axe> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You grasp the weathered wooden handle of the axe, feeling its reassuring weight as you lift it. The metal head gleams dully in the light as you carefully secure it in your pack. The familiar weight against your back reminds you of your father's advice about always keeping a good tool handy.#

    Example 2 (The player unblocks the passage to the basement)
    - Moved object: None
    - Blocked passages now available: <Basement>
    - Your location changed: None
    - Puzzle solved: None
    #With a final turn of the rusty key, the old padlock releases with a satisfying click. You remove it from the latch and push aside the heavy wooden bar that secured the basement door. A waft of cool, musty air rises from below, carrying the scent of damp stone and forgotten memories. The previously forbidden basement is now accessible, its secrets waiting to be discovered in the darkness below.#

    Example 3 (The player now is in the garden)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Garden>
    - Puzzle solved: None
    #You step through the creaking garden gate and into a world of vibrant color and fragrance. Sunlight filters through the leaves of an ancient oak, casting dappled shadows across the overgrown path. Butterflies dance between blooms of every hue, and somewhere nearby, water trickles musically. The garden embraces you with its wild beauty, so different from the sterile confines you just left behind.#

    Example 4 (The player puts objects in the bag and leaves the axe on the floor)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You carefully place the ripe banana and glass bottle into your bag, arranging them so nothing gets crushed. The banana's sweet aroma mingles with the musty scent of your well-traveled pack. With deliberate care, you set the heavy axe down on the polished floor of the Main Hall. It rests there with a certain finality, its blade reflecting the dancing light from the chandelier above. Perhaps someone else might find better use for it than you.#

    Example 5 (The player puts objects in the bag and leaves the axe on the floor and unblocks the passage to the Small room)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: None
    - Puzzle solved: None
    #Your fingers work quickly as you tuck the banana and bottle safely into your pack. The glass clinks softly against your other possessions as you secure the flap. The axe you place carefully on the marble floor of the Main Hall, its worn handle pointing toward the grand staircase. After inserting the ornate key into the small brass lock, you hear a series of clicks and whirrs as hidden mechanisms disengage. The previously sealed doorway to the Small Room shudders and then swings open slightly, releasing a puff of stale air. A new path is now available to you, beckoning with the promise of discovery.#

    Example 6 (The player puts objects in the bag and leaves the axe on the floor, unblocks the passage and goes to the Small room)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: <Small room>
    - Puzzle solved: None
    #With practiced efficiency, you stow both the banana and bottle in your bag, feeling the comfortable weight increase against your hip. The axe you deliberately place on the gleaming floor of the Main Hall, where its metal head catches the light from the crystal chandelier above. After turning the ancient key in the lock, the hidden door to the Small Room creaks open, revealing a space untouched for what must be decades. Dust motes dance in the beam of light that now intrudes upon this forgotten sanctuary. Drawn by curiosity, you step across the threshold, the floorboards groaning beneath your weight as you enter the Small Room. The air here is thick with secrets and the sweet musty scent of old books and forgotten memories.#

    Example 7 (The player solves a riddle correctly)
    - Moved object: None
    - Blocked passages now available: <Secret Chamber>
    - Your location changed: None
    - Puzzle solved: <Ancient Riddle> with answer <echo>
    #Your voice echoes in the chamber as you speak the answer with confidence: "Echo." The ancient statue's eyes suddenly blaze with inner light, and a rumbling sound fills the air. Stone grinds against stone as a hidden mechanism activates, revealing a secret passage behind the wall. The Ancient Riddle has been solved, and the way to the Secret Chamber now lies open before you, promising mysteries yet to be discovered.#

    Example 8 (The player puts the pencil in the bag and gives the book to John)
    - Moved object: <book> now is in <John>, <pencil> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You slip the worn cedar pencil into your bag, its familiar shape nestling among your other possessions. The heavy leather-bound book you extend toward John with both hands, respecting its apparent age and value. His eyes widen slightly as he recognizes the tome. "This is... I've been searching for this for years," he whispers, his voice thick with emotion. His weathered hands accept the book with reverence, cradling it as one might hold a precious relic. John carefully opens the cover, and for a moment, his stoic demeanor softens as he gazes at the yellowed pages within.#

    Example 9 (The player gives the computer to Susan)
    - Moved object: <computer> now is in <Susan>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    - Your location changed: None
    #You hand the sleek laptop to Susan, whose eyes light up with professional interest. "Finally," she murmurs, her fingers already dancing across the keyboard as the screen illuminates her focused face. The blue glow highlights the determination in her expression as she quickly accesses files you couldn't hope to understand. She tucks the computer securely into her messenger bag, the movement practiced and efficient. "This could change everything," she adds cryptically, nodding her thanks while her mind clearly races with new possibilities.#

    Example 10 (The player does something that has not the expected outcome)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You try turning the ornate brass handle, but the door remains stubbornly shut. The mechanism makes a dull clicking sound, but nothing else happens. Perhaps there's another way to open it, or something you're missing. The faded markings above the doorframe seem to mock your efforts, holding their secrets close.#

    Example 11 (The player asks a question)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #As you examine the strange symbol etched into the wall, you recognize it as an ancient sigil representing protection and hidden knowledge. The craftsmanship is remarkable, with intricate swirling patterns that seem to shift slightly when viewed from different angles. Legends speak of such markings being used by the old practitioners to ward off evil spirits while conducting their arcane research. The fact that it remains intact after all these centuries speaks to the power it was believed to hold.#

    Example 12 (The player moves from a tavern to a house with detailed transition narration)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Maria's House>
    - Puzzle solved: None
    #You push through the heavy wooden door of the tavern, leaving behind the warm glow of the fireplace and the murmur of evening conversations. The brass hinges creak in protest as you step out into the night. A sharp gust of cold air immediately greets you, carrying the scent of rain and woodsmoke from distant chimneys. Your breath forms small clouds in the frigid air as you pull your cloak tighter around your shoulders. The cobblestone street gleams wetly under the flickering light of oil lamps, their flames dancing in the wind. You navigate carefully across the uneven stones, your footsteps echoing between the narrow houses that line the street. The warm yellow light spilling from Maria's House windows grows larger as you approach, a welcoming beacon against the harsh night. You reach for the iron door knocker, shaped like a sleeping cat, and rap it twice against the weathered oak door. After a moment, you hear footsteps approaching from within, and the door swings open to reveal Maria's cozy home, filled with the comforting aroma of fresh bread and herbs drying from the ceiling beams.#"""
    
    
    user_msg = f"""Give the changes in the world following the specified format, after this player input "{input}" on this world state:
    
    {world_state}"""

    return system_msg, user_msg

#---- Incremental Generation Prompts -----------------------------------------
def PROMPT_STEP_1_CONCEPT(language: str = 'es') -> str:
    """Generate the first step prompt for creating a world concept."""
    if language == 'es':
        return """Eres un diseñador experto de mundos de ficción interactiva. Tu tarea es crear el concepto general de un mundo de aventura.

**LIBERTAD CREATIVA TOTAL:**
- Inventa cualquier historia, tema, o ambientación (medieval, sci-fi, moderno, fantástico, etc.)
- Crea personajes únicos con personalidades interesantes
- Diseña un objetivo principal desafiante y atractivo
- Decide el tono (aventura, misterio, drama, comedia, etc.)

**INSPIRACIÓN TEMÁTICA (elige uno o combina):**
- **Misterio**: Resolver un crimen, encontrar un tesoro perdido, descubrir un secreto
- **Aventura**: Rescatar a alguien, explorar ruinas, completar una misión
- **Supervivencia**: Escapar de un lugar, conseguir recursos, encontrar la salida
- **Social**: Convencer personajes, reunir información, mediar conflictos
- **Exploración**: Descubrir nuevas áreas, mapear territorio, encontrar artefactos

**ELEMENTOS OBLIGATORIOS A DEFINIR:**
- Un título atractivo para la aventura
- Una historia de fondo que establezca el contexto y la atmósfera (coherente con el tema)
- Una descripción del personaje jugador y su rol en la historia
- Un objetivo principal claro, motivador y ESPECÍFICO que el jugador debe lograr

**REQUISITOS DEL OBJETIVO:**
- Debe ser CLARO y ESPECÍFICO (no vago como "explorar el mundo")
- Debe ser MOTIVADOR para el jugador
- Debe ser COMPLETABLE con elementos físicos del mundo
- Debe tener una razón narrativa sólida
- Debe enfocarse en UNA meta principal, no múltiples objetivos

**EJEMPLOS DE BUENOS OBJETIVOS:**
- "Encontrar la Espada Legendaria para derrotar al dragón"
- "Rescatar a la princesa del castillo encantado"
- "Descubrir el tesoro del pirata perdido"
- "Reunir los tres cristales para abrir el portal"

**EJEMPLOS DE MALOS OBJETIVOS:**
- "Explorar el mundo" (muy vago)
- "Ser feliz" (no específico)
- "Caminar por ahí" (no motivador)

El concepto debe ser cohesivo, interesante y proporcionar una base sólida para construir un mundo de aventura completo.

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON (como 'title', 'backstory', 'name') deben permanecer en inglés para coincidir con el esquema solicitado.**
"""
    else:
        return """You are an expert designer of interactive fiction worlds. Your task is to create the overall concept of an adventure world.

**TOTAL CREATIVE FREEDOM:**
- Invent any story, theme, or setting (medieval, sci-fi, modern, fantasy, etc.)
- Create unique characters with interesting personalities
- Design a main objective that is challenging and engaging
- Decide the tone (adventure, mystery, drama, comedy, etc.)

**THEMATIC INSPIRATION (choose one or combine):**
- **Mystery**: Solve a crime, find a lost treasure, uncover a secret
- **Adventure**: Rescue someone, explore ruins, complete a mission
- **Survival**: Escape from a place, gather resources, find the way out
- **Social**: Persuade characters, gather information, mediate conflicts
- **Exploration**: Discover new areas, map territory, find artifacts

**MANDATORY ELEMENTS TO DEFINE:**
- An attractive title for the adventure
- A backstory that sets the context and atmosphere (consistent with the theme)
- A description of the player character and their role in the story
- A clear, motivating, and SPECIFIC main objective the player must achieve

**OBJECTIVE REQUIREMENTS:**
- Must be CLEAR and SPECIFIC (not vague like "explore the world")
- Must be MOTIVATING for the player
- Must be COMPLETABLE using physical elements from the world
- Must have a solid narrative reason
- Must focus on ONE primary goal, not multiple objectives

**EXAMPLES OF GOOD OBJECTIVES:**
- "Find the Legendary Sword to defeat the dragon"
- "Rescue the princess from the enchanted castle"
- "Discover the treasure of the lost pirate"
- "Gather the three crystals to open the portal"

**EXAMPLES OF BAD OBJECTIVES:**
- "Explore the world" (too vague)
- "Be happy" (not specific)
- "Just walk around" (not motivating)

The concept must be cohesive, interesting, and provide a solid foundation to build a complete adventure world.

**CRITICAL LANGUAGE INSTRUCTION: The response MUST be entirely in English. All text values (names, descriptions, etc.) must be generated in English. The JSON keys (such as 'title', 'backstory', 'name') must remain in English to match the required schema.**
"""


def PROMPT_STEP_1_CONCEPT_BY_THEME(theme: str, language: str = 'es') -> str:
    """Generate the first step prompt for creating a world concept."""
    if language == 'es':
        return f"""Eres un diseñador experto de mundos de ficción interactiva. Tu tarea es crear el concepto general de un mundo de aventura COMPLETAMENTE BASADO en el tema proporcionado. Es CRÍTICO que TODOS los elementos del mundo (ubicaciones, objetos, personajes y objetivo) estén directamente relacionados con el tema central.

**TEMA CENTRAL OBLIGATORIO:** {theme}

**INSTRUCCIONES CRÍTICAS:**
- El tema proporcionado DEBE ser la base fundamental de TODO el concepto del mundo
- TODOS los elementos deben estar temáticamente vinculados al tema central
- NO inventes elementos desconectados del tema proporcionado
- Cada ubicación, personaje, objeto y el objetivo principal DEBEN ser manifestaciones del tema

**DISEÑO DEL MUNDO:**
- Desarrolla una historia que explore directamente el tema proporcionado
- Crea una ambientación que refleje naturalmente aspectos del tema
- Usa o inventa personajes que encarnen diferentes facetas del tema
- El tono (aventura, misterio, drama, comedia) debe complementar el tema central

**ELEMENTOS OBLIGATORIOS A DEFINIR (TODOS RELACIONADOS AL TEMA):**
- Un título atractivo para la aventura que refleje claramente el tema
- Una historia de fondo que establezca el contexto y la atmósfera, basada directamente en el tema
- Una descripción del personaje jugador y su rol en la historia, relacionado con el tema
- Un objetivo principal claro, motivador y ESPECÍFICO, derivado directamente del tema central

**REQUISITOS DEL OBJETIVO:**
- Debe ser CLARO y ESPECÍFICO (no vago como "explorar el mundo")
- Debe ser MOTIVADOR para el jugador
- Debe ser COMPLETABLE con elementos físicos del mundo
- Debe estar DIRECTAMENTE RELACIONADO con el tema proporcionado
- Debe tener una razón narrativa sólida dentro del contexto temático
- Debe enfocarse en UNA meta principal, no múltiples objetivos

**EJEMPLOS DE BUENOS OBJETIVOS:**
- Si el tema es "piratas": "Encontrar el mapa del tesoro del Capitán Barbanegra en la Isla Calavera"
- Si el tema es "medieval": "Recuperar la corona real robada de las mazmorras del Castillo Oscuro"
- Si el tema es "espacio": "Reparar la nave espacial recolectando piezas dispersas por la estación abandonada"

**EJEMPLOS DE MALOS OBJETIVOS:**
- Objetivos vagos o genéricos no relacionados claramente con el tema
- Objetivos que podrían aplicarse a cualquier tema sin cambios
- Objetivos sin conexión narrativa al contexto temático

El concepto debe ser cohesivo, interesante y proporcionar una base sólida para construir un mundo de aventura completo, donde CADA ELEMENTO refleje y refuerce el tema central: {theme}

**VERIFICACIÓN FINAL:** Antes de finalizar, confirma que cada elemento propuesto (título, historia, personajes, objetivo) está claramente relacionado con el tema proporcionado y no podría existir sin modificaciones en un mundo con un tema diferente.

Tema: {theme}

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON (como 'title', 'backstory', 'name') deben permanecer en inglés para coincidir con el esquema solicitado.**
"""
    else:
        return f"""You are an expert designer of interactive fiction worlds. Your task is to create the overall concept of an adventure world COMPLETELY BASED on the provided theme. It is CRITICAL that ALL world elements (locations, objects, characters, and objective) are directly related to the central theme.

**MANDATORY CENTRAL THEME:** {theme}

**CRITICAL INSTRUCTIONS:**
- The provided theme MUST be the fundamental base for ALL of the world concept
- ALL elements must be thematically linked to the central theme
- DO NOT invent elements disconnected from the provided theme
- Each location, character, object, and the main objective MUST be manifestations of the theme

**WORLD DESIGN:**
- Develop a story that directly explores the provided theme
- Create a setting that naturally reflects aspects of the theme
- Use or invent characters that embody different facets of the theme
- The tone (adventure, mystery, drama, comedy) should complement the central theme

**MANDATORY ELEMENTS TO DEFINE (ALL RELATED TO THE THEME):**
- An attractive title for the adventure that clearly reflects the theme
- A backstory that establishes context and atmosphere, directly based on the theme
- A description of the player character and their role in the story, related to the theme
- A clear, motivating, and SPECIFIC main objective, directly derived from the central theme

**OBJECTIVE REQUIREMENTS:**
- Must be CLEAR and SPECIFIC (not vague like "explore the world")
- Must be MOTIVATING for the player
- Must be COMPLETABLE using physical elements from the world
- Must be DIRECTLY RELATED to the provided theme
- Must have a solid narrative reason within the thematic context
- Must focus on ONE primary goal, not multiple objectives

**EXAMPLES OF GOOD OBJECTIVES:**
- If the theme is "pirates": "Find Captain Blackbeard's treasure map on Skull Island"
- If the theme is "medieval": "Recover the stolen royal crown from the dungeons of Dark Castle"
- If the theme is "space": "Repair the spaceship by collecting scattered parts around the abandoned station"

**EXAMPLES OF BAD OBJECTIVES:**
- Vague or generic objectives not clearly related to the theme
- Objectives that could apply to any theme without changes
- Objectives without narrative connection to the thematic context

The concept must be cohesive, interesting, and provide a solid foundation to build a complete adventure world where EVERY ELEMENT reflects and reinforces the central theme: {theme}

**FINAL VERIFICATION:** Before finalizing, confirm that each proposed element (title, story, characters, objective) is clearly related to the provided theme and could not exist without modifications in a world with a different theme.

Theme: {theme}

**CRITICAL LANGUAGE INSTRUCTION: The response MUST be entirely in English. All text values (names, descriptions, etc.) must be generated in English. The JSON keys (such as 'title', 'backstory', 'name') must remain in English to match the required schema.**
"""


def PROMPT_STEP_2_SKELETON(title: str, backstory: str,player_concept: str, main_objective: str, language: str = 'es') -> str:
    locations = config['Size_World']['Locations']
    objects = config['Size_World']['Objects']
    npcs = config['Size_World']['NPCs']
    """Generate the first step prompt for creating a world concept."""
    if language == 'es':
        return f"""Eres un arquitecto de mundos de ficción interactiva. Basándote en el concepto de mundo proporcionado, tu tarea es definir las entidades clave que formarán la estructura del mundo.

Concepto del mundo:
- Título: {title}
- Historia de fondo: {backstory}
- Concepto del jugador: {player_concept}
- Objetivo principal: {main_objective}

**ESTRUCTURA REQUERIDA:**
- {locations} ubicaciones: Los lugares más importantes para la historia y el objetivo
- {objects} objetos: Los elementos físicos esenciales para completar el objetivo
- {npcs} personajes no jugadores: Los NPCs importantes que ayudarán o desafiarán al jugador

**REGLAS PARA EL ESQUELETO:**
1. **Enfoque en objetivo**: Cada entidad debe tener una conexión clara con el objetivo principal
2. **Ruta lógica**: Debe existir una secuencia lógica de ubicaciones y elementos para alcanzar el objetivo
3. **Dependencias claras**: Los objetos y personajes deben formar una cadena de dependencias hacia el objetivo

Para cada entidad, especifica su nombre y su propósito/rol en el mundo. Piensa en términos de la ruta principal hacia el objetivo y cómo cada elemento contribuye a esa ruta.

**EJEMPLO DE BUENA ESTRUCTURA:**
- Ubicación inicial → Ubicación con personaje clave → Ubicación con objeto importante → Ubicación objetivo
- Objeto inicial → Objeto para intercambio → Objeto final requerido
- Personaje informativo → Personaje que otorga objeto/acceso → Personaje objetivo (si aplica)

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""
    else:
        return f"""You are an architect of interactive fiction worlds. Based on the provided world concept, your task is to define the key entities that will form the structure of the world.

World concept:
- Title: {title}
- Backstory: {backstory}
- Player concept: {player_concept}
- Main objective: {main_objective}

**REQUIRED STRUCTURE:**
- {locations} locations: The most important places for the story and the objective
- {objects} objects: The essential physical elements to complete the objective
- {npcs} non-player characters: Key NPCs who will help or challenge the player

**RULES FOR THE SKELETON:**
1. **Objective focus**: Each entity must have a clear connection to the main objective  
2. **Logical path**: There must be a logical sequence of locations and items to reach the objective  
3. **Clear dependencies**: Objects and characters must form a chain of dependencies toward the objective

For each entity, specify its name and its purpose/role in the world. Think in terms of the main path toward the objective and how each element contributes to that path.

**EXAMPLE OF A GOOD STRUCTURE:**
- Initial location → Location with key character → Location with important object → Goal location  
- Initial object → Object for trade → Final required object  
- Informative character → Character that grants item/access → Target character (if applicable)

**CRITICAL LANGUAGE INSTRUCTION: The response MUST be entirely in English. All text values (names, descriptions, etc.) must be generated in English. The JSON keys must also remain in English to match the required schema.**
"""

def PROMPT_STEP_3_DETAILS(skeleton_data: str, title: str, backstory: str, player_concept: str, main_objective: str, language: str = 'es') -> str:
    """Generate the third step prompt for fleshing out the world details."""
    if language == 'es':
        return f"""Eres un constructor de mundos de ficción interactiva. Tu tarea es tomar las entidades clave del esqueleto y desarrollarlas en un mundo detallado y jugable, enfocándote en la ruta principal hacia el objetivo.

Concepto del mundo:
- Título: {title}
- Historia de fondo: {backstory}
- Concepto del jugador: {player_concept}
- Objetivo principal: {main_objective}

Entidades clave a desarrollar:
{skeleton_data}

**RESTRICCIONES TÉCNICAS OBLIGATORIAS:**

**RESTRICCIÓN DE TAMAÑO CRÍTICA:**
- SOLO puedes usar las ubicaciones listadas arriba - PROHIBIDO crear nuevas ubicaciones
- NO agregues ubicaciones adicionales más allá del esqueleto proporcionado

**REGLAS DE CONEXIÓN OBLIGATORIAS:**
1. **Conexiones bidireccionales**: Si A conecta con B, entonces B DEBE conectar con A
2. **Conectividad global**: TODAS las ubicaciones deben ser accesibles desde cualquier punto del mundo - NO puede haber ubicaciones aisladas o grupos separados
3. **Objetivo alcanzable**: El objetivo DEBE ser completable con los elementos que crees
4. **Cadena de dependencias**: Debe existir al menos una ruta lógica desde el estado inicial hasta completar el objetivo

**REGLAS DE PERSONAJES:**
1. **Interacciones funcionales**: Si un personaje tiene `interaction`, DEBE tener `interaction_text`
2. **Inventarios válidos**: Todo objeto en inventarios de personajes DEBE existir en la lista de objetos del mundo
3. **Ubicaciones válidas**: Todos los personajes DEBEN estar ubicados en lugares que existen

**REGLAS DE RECLUTAMIENTO DE PERSONAJES:**
1. **Marca como reclutable SOLO a un subconjunto de personajes**: La mayoría de los personajes deben tener `recruitable: false`. Marca `recruitable: true` únicamente en personajes clave que tenga sentido que se unan al grupo del jugador.
2. **initial_feeling**: Para personajes reclutables, define `initial_feeling` según la relación narrativa que ya tengan con el jugador (por ejemplo, "friendly" o "devoted" si son aliados desde el inicio, "neutral" o "wary" si aún no confían en el jugador). Para personajes no reclutables, deja el valor por defecto "neutral".
3. **npc_relationships**: Añade una entrada en `npc_relationships` SOLO cuando la historia realmente motive una rivalidad ("rival") o alianza ("ally") entre dos personajes concretos. La mayoría de los pares de personajes NO deben tener ninguna entrada - eso es lo esperado, no un error.

**REGLAS DE OBJETOS:**
1. **Objetivos completables**: Si un objeto es requerido para el objetivo (`is_objective_target: true`), DEBE ser `gettable: true`
2. **Consistencia funcional**: Objetos decorativos pueden ser `gettable: false`, objetos funcionales DEBEN ser `gettable: true`
3. **Relevancia clara**: Cada objeto debe tener una razón de existir (funcional o atmosférica)

**INSTRUCCIONES ESPECIALES PARA OBJETIVOS DE MISTERIO:**
Si el objetivo principal es resolver un misterio (type: "solve_mystery"), DEBES incluir:
1. **mystery_clues**: Lista detallada de pistas que el jugador puede descubrir
2. **mystery_solution**: Solución completa del misterio
3. **CRÍTICO**: Cada pista debe estar asociada ÚNICAMENTE con un OBJETO/ITEM físico que existe en el mundo - NUNCA con personajes o ubicaciones
4. **CRÍTICO**: El "associated_item" debe ser exactamente el nombre de un objeto que aparece en la lista de items del mundo

**INSTRUCCIONES CRÍTICAS PARA COMPONENTES DEL OBJETIVO:**
- El objetivo DEBE tener SOLO UN COMPONENTE PRINCIPAL que representa la meta final
- Para objetivos tipo "reach_location": UN solo componente de tipo "location" (la ubicación de destino)
- Para objetivos tipo "get_item": UN solo componente de tipo "item" (el objeto que obtener)
- Para objetivos tipo "find_character": UN solo componente de tipo "character" (el personaje que encontrar)
- Para objetivos tipo "deliver_an_item": UN item y UN destino (character o location)
- NO incluyas elementos auxiliares o herramientas como componentes principales
- Los componentes principales son SOLO el objetivo final, no los medios para alcanzarlo

**INSTRUCCIONES ESPECIALES PARA OBJETIVOS NO-MISTERIO:**
Para todos los demás tipos de objetivos (que NO sean "solve_mystery"), DEBES incluir:
1. **completion_narration**: Una descripción narrativa de lo que sucede después de que el jugador complete exitosamente el objetivo. Esto debe proporcionar una conclusión satisfactoria a la aventura y explicar las consecuencias de lograr el objetivo.
2. **objective_hints**: Lista de EXACTAMENTE 3 pistas progresivas para el objetivo principal (de general a específica). Estas pistas se usarán cuando el jugador esté en una ubicación sin puzzles y pida ayuda.

Ejemplos de completion_narration:
- "Con la espada legendaria en tus manos, finalmente derrotas al dragón. El reino está a salvo y eres aclamado como un héroe."
- "Al entregar todos los documentos requeridos, el oficial te otorga el permiso. Ahora puedes continuar tu viaje hacia tierras lejanas."
- "Al encontrar todos los ingredientes y preparar la poción, la aldea queda liberada de la maldición que la aquejaba durante décadas."

**FORMATO OBLIGATORIO PARA OBJECTIVE_HINTS:**
```json
"objective_hints": [
  {{"text": "Pista general sobre qué hacer para avanzar hacia el objetivo", "used": false}},
  {{"text": "Pista más específica sobre dónde buscar o con quién hablar", "used": false}},
  {{"text": "Pista muy específica que casi revela el siguiente paso", "used": false}}
]
```
5. **CRÍTICO**: El "item_location" debe ser exactamente el nombre de una ubicación que existe en el mundo
6. Las pistas deben proporcionar información que conduzca lógicamente a la solución
7. Debe haber al menos 3-5 pistas para hacer el misterio interesante

**REGLAS OBLIGATORIAS PARA MYSTERY_CLUES:**
- "associated_item": DEBE ser el nombre exacto de un OBJETO que existe en la lista de items
- "item_location": DEBE ser el nombre exacto de una UBICACIÓN que existe en la lista de locations
- NUNCA uses nombres de personajes como "associated_item"
- NUNCA uses nombres de ubicaciones como "associated_item"
- Los jugadores descubren pistas al interactuar con objetos físicos, no con personajes

**EJEMPLO DE PISTAS DE MISTERIO CORRECTAS:**
```json
"mystery_clues": [
  {{
    "name": "Huellas fangosas",
    "description": "Hay huellas fangosas que conducen desde la ventana hasta la caja fuerte",
    "associated_item": "Botas de jardín",
    "item_location": "Cobertizo del jardín",
    "relevance_to_mystery": "Las huellas coinciden con las botas del jardinero, lo que sugiere que él tenía acceso",
    "discovered": false
  }},
  {{
    "name": "Documento comprometedor",
    "description": "Una nota manuscrita que revela información sobre el plan",
    "associated_item": "Carta misteriosa",
    "item_location": "Oficina del director",
    "relevance_to_mystery": "Demuestra que había un plan premeditado",
    "discovered": false
  }}
]
```

**VALIDACIÓN DE COMPLETABILIDAD:**
Antes de finalizar, verifica mentalmente:
1. **¿HAS DEFINIDO UN OBJETIVO PRINCIPAL CLARO?** (OBLIGATORIO)
2. **¿TODAS las ubicaciones son accesibles desde la ubicación inicial?** (OBLIGATORIO - no debe haber ubicaciones aisladas)
3. ¿Puede el jugador completar el objetivo con los elementos disponibles?
4. ¿Existe al menos una ruta de solución desde el estado inicial?
5. ¿Todos los elementos referenciados existen realmente en el mundo?
6. ¿Las interacciones de personajes están completas?
7. **Si es un misterio: ¿Tienes pistas suficientes y una solución clara?** (OBLIGATORIO para solve_mystery)
8. **Si es un misterio: ¿Cada pista está asociada con un OBJETO físico que existe en el mundo?** (OBLIGATORIO - no personajes ni ubicaciones)

**EJEMPLO DE CADENA DE DEPENDENCIAS VÁLIDA:**
1. Jugador quiere [objetivo principal]
2. Para [objetivo] necesita [objeto/ubicación X]
3. Para conseguir X necesita [interactuar con personaje Y]
4. Personaje Y requiere [completar tarea/tener objeto Z]
5. El jugador puede conseguir Z directamente o mediante otro paso

Debes crear:
- Ubicaciones completas con descripciones atmosféricas y conexiones lógicas bidireccionales
- Objetos detallados con descripciones y propiedades apropiadas
- Personajes con personalidades, ubicaciones e interacciones básicas completas
- Un objetivo claro y específico con UN COMPONENTE PRINCIPAL definido y alcanzable
- El personaje jugador en una ubicación inicial apropiada
- Cadenas de dependencias que muestren cómo completar el objetivo

IMPORTANTE: Enfócate solo en la ruta principal. No añadas puzzles complejos todavía - eso vendrá en el siguiente paso. Las interacciones de personajes deben ser directas y simples pero COMPLETAS.

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""
    else:
        return f"""You are a builder of interactive fiction worlds. Your task is to take the key skeleton entities and develop them into a detailed and playable world, focusing on the main path to the objective.

World concept:
- Title: {title}
- Backstory: {backstory}
- Player concept: {player_concept}
- Main objective: {main_objective}

Key entities to develop:
{skeleton_data}

**MANDATORY TECHNICAL RESTRICTIONS:**

**CRITICAL SIZE RESTRICTION:**
- You may ONLY use the locations listed above - FORBIDDEN to create new locations
- DO NOT add additional locations beyond the provided skeleton

**MANDATORY CONNECTION RULES:**
1. **Bidirectional connections**: If A connects to B, then B MUST connect to A
2. **Global connectivity**: ALL locations must be accessible from any point in the world – there can be NO isolated locations or separate groups
3. **Reachable objective**: The objective MUST be completable using the elements you create
4. **Dependency chain**: There must be at least one logical path from the initial state to completing the objective

**CHARACTER RULES:**
1. **Functional interactions**: If a character has `interaction`, it MUST have `interaction_text`
2. **Valid inventories**: Every object in characters' inventories MUST exist in the world’s object list
3. **Valid locations**: All characters MUST be located in places that exist

**CHARACTER RECRUITMENT RULES:**
1. **Only mark a subset of characters as recruitable**: Most characters should have `recruitable: false`. Only set `recruitable: true` on key characters for whom it makes narrative sense to join the player's party.
2. **initial_feeling**: For recruitable characters, set `initial_feeling` based on their existing narrative relationship with the player (e.g. "friendly" or "devoted" if they are already allies, "neutral" or "wary" if they don't yet trust the player). For non-recruitable characters, leave it at the default "neutral".
3. **npc_relationships**: Only add an entry to `npc_relationships` when the story actually motivates a rivalry ("rival") or alliance ("ally") between two specific characters. Most character pairs should have NO entry at all - that is expected, not an error.

**OBJECT RULES:**
1. **Completable objectives**: If an object is required for the objective (`is_objective_target: true`), it MUST be `gettable: true`
2. **Functional consistency**: Decorative objects can be `gettable: false`, functional objects MUST be `gettable: true`
3. **Clear relevance**: Every object must have a reason to exist (functional or atmospheric)

**SPECIAL INSTRUCTIONS FOR MYSTERY OBJECTIVES:**
If the main objective is to solve a mystery (type: "solve_mystery"), you MUST include:
1. **mystery_clues**: Detailed list of clues that the player can discover
2. **mystery_solution**: Complete solution to the mystery
3. **CRITICAL**: Each clue must be associated ONLY with a physical OBJECT/ITEM that exists in the world - NEVER with characters or locations
4. **CRITICAL**: The "associated_item" must be exactly the name of an object that appears in the world's items list

**CRITICAL INSTRUCTIONS FOR OBJECTIVE COMPONENTS:**
- The objective MUST have ONLY ONE PRIMARY COMPONENT that represents the final goal
- For "reach_location" objectives: ONE single component of type "location" (the destination)
- For "get_item" objectives: ONE single component of type "item" (the target item)
- For "find_character" objectives: ONE single component of type "character" (the target character)
- For "deliver_an_item" objectives: ONE item and ONE destination (character or location)
- DO NOT include auxiliary elements or tools as primary components
- Primary components are ONLY the final objective, not the means to achieve it

**SPECIAL INSTRUCTIONS FOR NON-MYSTERY OBJECTIVES:**
For all other objective types (that are NOT "solve_mystery"), you MUST include:
1. **completion_narration**: A narrative description of what happens after the player successfully completes the objective. This should provide a satisfying conclusion to the adventure and explain the consequences of achieving the goal.
2. **objective_hints**: List of EXACTLY 3 progressive hints for the main objective (from general to specific). These hints will be used when the player is in a location with no puzzles and asks for help.

Examples of completion_narration:
- "With the legendary sword in your hands, you finally defeat the dragon. The kingdom is safe and you are hailed as a hero."
- "By delivering all the required documents, the official grants you the permit. You can now continue your journey to distant lands."
- "By finding all the ingredients and preparing the potion, the village is freed from the curse that plagued it for decades."

**MANDATORY FORMAT FOR OBJECTIVE_HINTS:**
```json
"objective_hints": [
  {{"text": "General hint about what to do to progress toward the objective", "used": false}},
  {{"text": "More specific hint about where to look or who to talk to", "used": false}},
  {{"text": "Very specific hint that almost reveals the next step", "used": false}}
]
```
5. **CRITICAL**: The "item_location" must be exactly the name of a location that exists in the world
6. Clues must provide information that logically leads to the solution
7. There should be at least 3-5 clues to make the mystery interesting

**MANDATORY RULES FOR MYSTERY_CLUES:**
- "associated_item": MUST be the exact name of an OBJECT that exists in the items list
- "item_location": MUST be the exact name of a LOCATION that exists in the locations list
- NEVER use character names as "associated_item"
- NEVER use location names as "associated_item"
- Players discover clues by interacting with physical objects, not characters

**EXAMPLE OF CORRECT MYSTERY CLUES:**
```json
"mystery_clues": [
  {{
    "name": "Muddy footprints",
    "description": "There are muddy footprints leading from the window to the safe",
    "associated_item": "Garden boots",
    "item_location": "Garden shed",
    "relevance_to_mystery": "The prints match the gardener's boots, suggesting he had access",
    "discovered": false
  }},
  {{
    "name": "Incriminating document",
    "description": "A handwritten note revealing information about the plan",
    "associated_item": "Mysterious letter",
    "item_location": "Director's office",
    "relevance_to_mystery": "Shows there was a premeditated plan",
    "discovered": false
  }}
]
```

**COMPLETION VALIDATION:**
Before finishing, mentally verify:
1. **HAVE YOU DEFINED A CLEAR MAIN OBJECTIVE?** (MANDATORY)
2. **Are ALL locations accessible from the initial location?** (MANDATORY – there must be no isolated locations)
3. Can the player complete the objective using the available elements?
4. Is there at least one solution path from the starting state?
5. Do all referenced elements actually exist in the world?
6. Are all character interactions complete?
7. **If it's a mystery: Do you have sufficient clues and a clear solution?** (MANDATORY for solve_mystery)
8. **If it's a mystery: Is each clue associated with a physical OBJECT that exists in the world?** (MANDATORY - not characters or locations)

**EXAMPLE OF A VALID DEPENDENCY CHAIN:**
1. Player wants [main objective]
2. To [achieve objective] they need [object/location X]
3. To get X they need to [interact with character Y]
4. Character Y requires [completing task/having object Z]
5. The player can get Z directly or through another step

You must create:
- Fully described locations with atmospheric detail and logical bidirectional connections
- Detailed objects with appropriate descriptions and properties
- Characters with personalities, locations, and complete basic interactions
- A clear and specific objective with ONE PRIMARY COMPONENT defined and achievable
- The player character in a suitable starting location
- Dependency chains showing how to complete the objective

IMPORTANT: Focus only on the main path. Do not add complex puzzles yet – that will come in the next step. Character interactions should be straightforward and simple, but COMPLETE.

**CRITICAL LANGUAGE INSTRUCTION: The response MUST be entirely in English. All text values (names, descriptions, etc.) must be generated in English. The JSON keys must remain in English to match the required schema.**
"""

def PROMPT_STEP_4_PUZZLES(world_data: str, language: str = 'es') -> str:
    if language == 'es':
        return f"""Eres un diseñador de puzzles para ficción interactiva. Tu tarea es añadir puzzles y obstáculos al mundo existente para hacer la aventura más desafiante e interesante.

Mundo actual:
{world_data}

**OBJETIVO CRÍTICO:** En lugar de simplemente añadir puzzles aislados, debes crear CADENAS DE DEPENDENCIAS que hagan la progresión hacia el objetivo mucho más interesante y desafiante.

**EJEMPLO DE CADENA DE DEPENDENCIAS COMPLEJA:**
Objetivo: Conseguir el Amuleto Mágico
1. El Amuleto está en la Habitación Secreta, pero la puerta está bloqueada por un Candado Mágico
2. Para abrir el Candado Mágico necesitas la Palabra Clave que solo conoce el Mago
3. El Mago te dará la Palabra Clave, pero primero quiere que le traigas su Bastón Perdido
4. El Bastón está en poder del Comerciante, quien lo intercambiará por 3 Gemas
5. Para conseguir las 3 Gemas debes resolver el Acertijo del Guardián en la Cueva
6. Pero para entrar a la Cueva necesitas la Llave de Hierro que tiene la Anciana
7. La Anciana te dará la Llave si le traes una Poción Curativa del Herbolario
8. El Herbolario te dará la Poción a cambio de encontrar su Libro de Recetas...

**ESTRUCTURA DE CADENAS OBLIGATORIA:**
1. **Cadena principal**: La ruta principal hacia el objetivo debe tener AL MENOS de 3 a 6 pasos interdependientes
2. **Subcadenas**: Cada paso principal puede tener sus propias subcadenas de 1-3 pasos
3. **Múltiples rutas opcionales**: Donde sea posible, proporciona rutas alternativas para algunos pasos
4. **Puzzles integrados**: Los puzzles deben estar integrados orgánicamente en las cadenas

**REGLAS DE CADENAS DE DEPENDENCIAS:**
1. **Progresión lógica**: Cada paso debe ser una consecuencia lógica del anterior
2. **Motivación clara**: Cada personaje debe tener una razón convincente para sus peticiones
3. **Diversidad de tareas**: Combina diferentes tipos de desafíos (puzzles, intercambios, exploración, interacciones sociales)
4. **Escalado de dificultad**: Los desafíos deben volverse progresivamente más complejos
5. **Conectividad temática**: Todas las tareas deben estar conectadas con la historia principal

**TIPOS DE DEPENDENCIAS A CREAR:**
1. **Intercambios en cadena**: A quiere B de C, quien quiere D de E, etc.
2. **Información en cascada**: Para conseguir X necesitas saber Y, que se obtiene resolviendo Z
3. **Acceso progresivo**: Para llegar a A necesitas la llave B, que obtienes en C, accesible con objeto D
4. **Puzzles conectados**: Resolver puzzle A revela la pista para puzzle B, que desbloquea acceso a C
5. **Relaciones sociales**: Personaje A confía en ti solo si ayudas a personaje B primero

**REGLAS TÉCNICAS OBLIGATORIAS:**
1. **NO NUEVAS UBICACIONES**: PROHIBIDO crear nuevas ubicaciones - solo usa las existentes
2. **Conectividad global**: TODAS las ubicaciones deben seguir siendo accesibles - NO crear grupos aislados
3. **Elementos existentes**: Todas las referencias DEBEN apuntar a objetos/personajes/ubicaciones que existen
4. **Soluciones descubribles**: Cada puzzle DEBE tener pistas que el jugador pueda encontrar explorando
5. **Interacciones completas**: Todo personaje con interacción DEBE tener `interaction_text`
6. **Obstáculos lógicos**: Los obstáculos deben estar separados de sus soluciones
7. **Si el puzzle es dado por un personaje, el reward debe ser un item, y el item DEBE EXISTIR Y ESTAR EN EL INVENTARIO DEL PERSONAJE QUE LO PROPONE**
8. **NO CRAFTING**: El motor del juego no soporta la creación o transformación de objetos. No crees puzzles que requieran que el jugador combine o altere objetos (p. ej., usar una receta para hacer una poción). Las recompensas deben ser objetos que se puedan usar directamente.
9. **OBSTÁCULO vs. LLAVE**: Sé preciso. Un 'obstáculo' es lo que bloquea el camino (p. ej., 'una puerta cerrada'). El 'requisito' es la llave que lo quita (p. ej., 'una llave de hierro'). La llave nunca es el obstáculo.
10. **RECOMPENSA DE RECLUTAMIENTO**: Si un personaje tiene `recruitable: true` y su `initial_feeling` es "hostile", "wary" o "neutral", PUEDES añadir un puzzle propuesto por ese mismo personaje (`proposed_by_character`) cuya única recompensa sea un `RecruitCharacterReward` con `character_name` igual al nombre de ese personaje. Esto representa el desafío que el jugador debe superar para reclutarlo. NO añadas este tipo de puzzle para personajes cuyo `initial_feeling` ya sea "friendly" o "devoted" - esos personajes se reclutan directamente sin desafío.

**REGLA OBLIGATORIA - TODO PUZZLE DEBE SER VERIFICABLE:**
El motor comprueba mecánicamente si un puzzle fue resuelto. Un puzzle cuya única forma de
resolverse sea que el jugador escriba literalmente el texto de `answer` es INJUGABLE cuando esa
respuesta describe una acción. Por eso, para CADA puzzle DEBES rellenar al menos uno de estos
dos campos:

1. **accepted_answers**: si el puzzle se resuelve DICIENDO algo (adivinanza, código, nombre).
   Incluye variantes válidas: la palabra clave sola, con y sin artículo, sinónimos evidentes.
   Ejemplo → answer: "Una llave de hierro", accepted_answers: ["llave de hierro", "la llave", "llave"]

2. **solution_conditions**: si el puzzle se resuelve HACIENDO algo. Son condiciones sobre el
   estado del mundo que el motor verifica solo. TODAS deben cumplirse para dar el puzzle por
   resuelto. Tipos disponibles:
   - `has_item` (item_name): el jugador lleva ese objeto
   - `item_given_to_character` (item_name, character_name): ese personaje tiene el objeto
   - `item_in_location` (item_name, location_name): el objeto está en ese lugar
   - `player_at_location` (location_name): el jugador está en ese lugar
   - `talked_to_character` (character_name): el jugador interactuó con ese personaje

   Ejemplo → answer: "Tocar la Campana de Plata para despertar a la Reina"
   ```json
   "solution_conditions": [
     {{"condition_type": "has_item", "item_name": "Campana de Plata", "description": "El jugador lleva la Campana de Plata"}},
     {{"condition_type": "talked_to_character", "character_name": "La Reina de los Gatos", "description": "El jugador interactuó con la Reina"}}
   ]
   ```

**NUNCA** dejes `accepted_answers` y `solution_conditions` ambos vacíos. Si dudas de qué tipo es
el puzzle, rellena los dos. Todo nombre de objeto, personaje o ubicación citado en una condición
DEBE existir en el mundo y escribirse EXACTAMENTE igual que en el mundo.

**REGLAS OBLIGATORIAS PARA SISTEMA DE PISTAS:**
Para CADA puzzle que añadas, DEBES incluir:
1. **puzzle_hints**: Lista de 3-5 pistas progresivas (de general a específica) para resolver el puzzle
2. **interaction_hint**: Pista sobre cómo interactuar con el puzzle si el jugador no ha empezado aún
   - Para puzzles de personajes: "Intenta hablar con [personaje]"
   - Para puzzles de objetos: "Intenta examinar [objeto]"
   - Para puzzles de ubicación: "Busca pistas en esta ubicación"

**FORMATO OBLIGATORIO DE PISTAS:**
```json
"puzzle_hints": [
  {{"text": "Pista general que orienta hacia la solución", "used": false}},
  {{"text": "Pista más específica que da más detalles", "used": false}},
  {{"text": "Pista muy específica que casi revela la respuesta", "used": false}}
],
"interaction_hint": {{"text": "Pista de interacción apropiada", "used": false}}
```

**ESTRATEGIAS PARA CREAR COMPLEJIDAD:**
1. **Bloquear acceso directo**: El objetivo no debe ser directamente accesible - añade obstáculos
2. **Requerir múltiples elementos**: Para el paso final se necesitan varios objetos/información
3. **Crear cuellos de botella**: Ciertos personajes clave que controlan múltiples recursos
4. **Esconder elementos críticos**: Objetos importantes en ubicaciones que requieren esfuerzo alcanzar
5. **Información fragmentada**: Dividir pistas importantes entre múltiples personajes/ubicaciones

**MODIFICACIONES REQUERIDAS AL MUNDO:**
1. **Expandir interacciones de personajes**: Añade peticiones, intercambios, información
2. **Añadir puzzles estratégicos**: Que bloqueen puntos críticos de la progresión
3. **Crear pasajes bloqueados**: Con obstáculos que requieren elementos de las cadenas
4. **Redistribuir objetos**: Mueve objetos importantes a ubicaciones menos accesibles
5. **Añadir nuevos objetos/personajes**: SOLO si es absolutamente necesario (NO ubicaciones)

**VALIDACIÓN DE CADENAS:**
Antes de finalizar, verifica mentalmente:
1. **¿El camino al objetivo tiene AL MENOS 3-6 pasos principales?** (OBLIGATORIO)
2. **¿Cada paso tiene una motivación lógica y clara?**
3. **¿Hay variedad en los tipos de desafíos?**
4. **¿Todas las ubicaciones siguen siendo accesibles?**
5. **¿Todos los elementos referenciados existen?**
6. **¿Las cadenas son interesantes pero no frustrantes?**
7. **Las cadenas tienen relacion a la tematica del mundo?**

Tu misión es convertir un mundo simple y directo en una aventura rica en la que cada logro se sienta ganado a través de exploración, ingenio e interacción social. ¡Haz que el jugador trabaje por su victoria!

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""
    else:
        return  f"""You are a puzzle designer for interactive fiction. Your task is to add puzzles and obstacles to the existing world to make the adventure more challenging and interesting.

Current world:
{world_data}

**CRITICAL OBJECTIVE:** Instead of simply adding isolated puzzles, you must create DEPENDENCY CHAINS that make progression toward the objective much more interesting and challenging.

**EXAMPLE OF A COMPLEX DEPENDENCY CHAIN:**
Objective: Obtain the Magic Amulet
- The Amulet is in the Secret Room, but the door is locked by a Magic Lock
- To open the Magic Lock you need the Password that only the Wizard knows
- The Wizard will give you the Password, but first he wants you to bring him his Lost Staff
- The Staff is in the Merchant's possession, who will trade it for 3 Gems
- To get the 3 Gems you must solve the Guardian's Riddle in the Cave
- But to enter the Cave you need the Iron Key that the Old Woman has
- The Old Woman will give you the Key if you bring her a Healing Potion from the Herbalist
- The Herbalist will give you the Potion in exchange for finding his Recipe Book...

**REQUIRED CHAIN STRUCTURE:**
- **Main chain**: The main route to the objective must have AT LEAST 3 to 6 interdependent main steps
- **Subchains**: Each main step may have its own subchains of 1–3 steps
- **Multiple optional routes**: Where possible, provide alternative routes for some steps
- **Integrated puzzles**: Puzzles must be organically integrated into the chains

**DEPENDENCY CHAIN RULES:**
- **Logical progression**: Each step must be a logical consequence of the previous one
- **Clear motivation**: Each character must have a convincing reason for their requests
- **Task diversity**: Combine different types of challenges (puzzles, trades, exploration, social interactions)
- **Difficulty scaling**: Challenges should become progressively more complex
- **Thematic connectivity**: All tasks must be connected to the main story

**TYPES OF DEPENDENCIES TO CREATE:**
- **Chained trades**: A wants B from C, who wants D from E, etc.
- **Cascading information**: To obtain X you need to know Y, which is obtained by solving Z
- **Progressive access**: To reach A you need key B, which you get in C, accessible with item D
- **Connected puzzles**: Solving puzzle A reveals the clue for puzzle B, which unlocks access to C
- **Social relationships**: Character A trusts you only if you help character B first

**MANDATORY TECHNICAL RULES:**
- **NO NEW LOCATIONS**: FORBIDDEN to create new locations - only use existing ones
- **Global connectivity**: ALL locations must remain accessible - DO NOT create isolated groups
- **Existing elements**: All references MUST point to objects/characters/locations that exist
- **Discoverable solutions**: Each puzzle MUST have hints the player can find by exploring
- **Complete interactions**: Every interactive character MUST have `interaction_text`
- **Logical separation of obstacles and solutions**: Obstacles must be separate from their solutions
- **If a puzzle is proposed by a character, the reward must be an item, AND THAT ITEM SHOULD EXIST AND BE IN THE INVENTORY OF THE CHARACTER THAT PROPOSES THE PUZZLE**
- **NO CRAFTING**: The game engine does not support crafting or transforming items. Do not create puzzles that require the player to combine or alter items (e.g., using a recipe to make a potion). Rewards must be items that can be used directly.
- **OBSTACLE vs. KEY**: Be precise. An 'obstacle' is the thing blocking the way (e.g., 'a locked door'). The 'requirement' is the key that removes it (e.g., 'an iron key'). The key is never the obstacle.
- **RECRUITMENT REWARD**: If a character has `recruitable: true` and their `initial_feeling` is "hostile", "wary", or "neutral", you MAY add a puzzle proposed by that same character (`proposed_by_character`) whose only reward is a `RecruitCharacterReward` with `character_name` equal to that character's name. This represents the challenge the player must complete to recruit them. Do NOT add this kind of puzzle for characters whose `initial_feeling` is already "friendly" or "devoted" - those characters can be recruited directly without a challenge.

**MANDATORY RULE - EVERY PUZZLE MUST BE VERIFIABLE:**
The engine mechanically checks whether a puzzle was solved. A puzzle whose only route to being
solved is the player typing the text of `answer` verbatim is UNPLAYABLE whenever that answer
describes an action. So for EACH puzzle you MUST fill in at least one of these two fields:

1. **accepted_answers**: for puzzles solved by SAYING something (riddle, code, name). Include
   the valid variants: the bare keyword, with and without an article, obvious synonyms.
   Example → answer: "An iron key", accepted_answers: ["iron key", "the key", "key"]

2. **solution_conditions**: for puzzles solved by DOING something. These are world-state
   conditions the engine verifies by itself. ALL of them must hold for the puzzle to count as
   solved. Available types:
   - `has_item` (item_name): the player is carrying that item
   - `item_given_to_character` (item_name, character_name): that character holds the item
   - `item_in_location` (item_name, location_name): the item sits in that location
   - `player_at_location` (location_name): the player is standing in that location
   - `talked_to_character` (character_name): the player has interacted with that character

   Example → answer: "Ring the Small Silver Bell to wake the Queen"
   ```json
   "solution_conditions": [
     {{"condition_type": "has_item", "item_name": "Small Silver Bell", "description": "The player is carrying the Small Silver Bell"}},
     {{"condition_type": "talked_to_character", "character_name": "The Queen of Cats", "description": "The player has interacted with the Queen"}}
   ]
   ```

**NEVER** leave both `accepted_answers` and `solution_conditions` empty. If you are unsure which
kind of puzzle it is, fill in both. Every item, character, or location named in a condition MUST
exist in the world and be spelled EXACTLY as it appears there.

**MANDATORY RULES FOR HINT SYSTEM:**
For EACH puzzle you add, YOU MUST include:
- **puzzle_hints**: A list of 3–5 progressive hints (from general to specific) to solve the puzzle
- **interaction_hint**: A hint about how to interact with the puzzle if the player has not started yet
  - For character puzzles: "Try talking to [character]"
  - For object puzzles: "Try examining [object]"
  - For location puzzles: "Search for clues in this location"

**MANDATORY HINT FORMAT:**
```json
"puzzle_hints": [
  {{"text": "General hint that guides toward the solution", "given": false}},
  {{"text": "More specific hint that gives additional details", "given": false}},
  {{"text": "Very specific hint that almost reveals the answer", "given": false}}
],
"interaction_hint": {{"text": "Appropriate interaction hint", "given": false}}
```

**STRATEGIES TO CREATE COMPLEXITY:**
1. **Block direct access**: The objective must not be directly accessible - add obstacles
2. **Require multiple elements**: The final step requires several items/information
3. **Create bottlenecks**: Certain key characters control multiple resources
4. **Hide critical elements**: Important objects in locations that require effort to reach
5. **Fragmented information**: Split important clues among multiple characters/locations

**REQUIRED MODIFICATIONS TO THE WORLD:**
1. **Expand character interactions**: Add requests, trades, pieces of information
2. **Add strategic puzzles**: That block critical progression points
3. **Create blocked passages**: With obstacles that require chain items to bypass
4. **Redistribute objects**: Move important items to less accessible locations
5. **Add new objects/characters**: ONLY if absolutely necessary (NO locations)

**CHAIN VALIDATION:**
Before finalizing, verify mentally:
1. **Does the path to the objective have AT LEAST 3–6 main steps?** (MANDATORY)
2. **Does each step have a logical and clear motivation?**
3. **Is there variety in the types of challenges?**
4. **Are all locations still accessible?**
5. **Do all referenced elements exist?**
6. **Are the chains interesting but not frustrating?**
7. **Do the chains relate to the world's theme?**

Your mission is to turn a simple, straightforward world into a richly layered adventure where every achievement feels earned through exploration, ingenuity, and social interaction. Make the player work for their victory!

**CRITICAL LANGUAGE INSTRUCTION: The response MUST be entirely in English. All text values (names, descriptions, etc.) must be generated in English. The JSON keys must remain in English to match the required schema.**
"""
