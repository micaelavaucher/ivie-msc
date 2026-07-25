"""World visualization utilities for debugging and inspection."""

from .world import World
from .world_builder import generate_world_overview, generate_objective_validation_report

def generate_world_mermaid_diagram(world: World, language: str = 'en') -> str:
    """Generate a Mermaid diagram representing the world structure.
    
    Args:
        world: The World object to visualize
        language: Language for labels ('en' or 'es')
        
    Returns:
        str: Mermaid diagram syntax
    """
    lines = ["graph TD"]
    
    # Define styling classes
    lines.append("    classDef playerLoc fill:#4ade80,stroke:#22c55e,stroke-width:3px,color:#000")
    lines.append("    classDef normalLoc fill:#60a5fa,stroke:#3b82f6,stroke-width:2px,color:#000")
    lines.append("    classDef blockedPath stroke:#ef4444,stroke-width:2px,stroke-dasharray:5")
    lines.append("    classDef item fill:#fbbf24,stroke:#f59e0b,stroke-width:1px,color:#000")
    lines.append("    classDef character fill:#c084fc,stroke:#a855f7,stroke-width:2px,color:#000")
    lines.append("    classDef puzzle fill:#fb923c,stroke:#f97316,stroke-width:2px,color:#000")
    lines.append("")
    
    # Track which locations have been added
    location_ids = {}
    player_location_name = world.player.location.name
    
    # Add locations as nodes
    for loc_name, location in world.locations.items():
        loc_id = f"loc_{len(location_ids)}"
        location_ids[loc_name] = loc_id
        
        # Escape special characters in location names
        safe_name = loc_name.replace('"', '\\"').replace('[', '(').replace(']', ')')
        
        if loc_name == player_location_name:
            lines.append(f'    {loc_id}["{safe_name}<br/>⭐ PLAYER START"]')
            lines.append(f'    class {loc_id} playerLoc')
        else:
            lines.append(f'    {loc_id}["{safe_name}"]')
            lines.append(f'    class {loc_id} normalLoc')
    
    lines.append("")
    
    # Add connections between locations
    processed_connections = set()
    for loc_name, location in world.locations.items():
        loc_id = location_ids[loc_name]
        
        for connected_loc in location.connecting_locations:
            connected_id = location_ids.get(connected_loc.name)
            if not connected_id:
                continue
            
            # Avoid duplicate bidirectional connections
            connection_pair = tuple(sorted([loc_id, connected_id]))
            if connection_pair in processed_connections:
                continue
            processed_connections.add(connection_pair)
            
            # Check if this connection is blocked
            is_blocked = False
            blocking_element = None
            
            # blocked_locations keys are location names (strings), not Location objects
            if hasattr(location, 'blocked_locations') and connected_loc.name in location.blocked_locations:
                is_blocked = True
                blocking_info = location.blocked_locations[connected_loc.name]
                blocking_element = blocking_info[1] if len(blocking_info) > 1 else None
            
            # Create connection line
            if is_blocked:
                if blocking_element:
                    safe_blocker = str(blocking_element.name).replace('"', '\\"')
                    if language == 'es':
                        lines.append(f'    {loc_id} -.->|"🔒 {safe_blocker}"| {connected_id}')
                    else:
                        lines.append(f'    {loc_id} -.->|"🔒 {safe_blocker}"| {connected_id}')
                else:
                    if language == 'es':
                        lines.append(f'    {loc_id} -.->|"🔒 Bloqueado"| {connected_id}')
                    else:
                        lines.append(f'    {loc_id} -.->|"🔒 Blocked"| {connected_id}')
                lines.append(f'    class {loc_id} blockedPath')
            else:
                lines.append(f'    {loc_id} <--> {connected_id}')
    
    lines.append("")
    
    # Add items to locations
    item_counter = 0
    for loc_name, location in world.locations.items():
        loc_id = location_ids[loc_name]
        
        if hasattr(location, 'items') and location.items:
            for item in location.items:
                item_id = f"item_{item_counter}"
                item_counter += 1
                safe_item_name = item.name.replace('"', '\\"').replace('[', '(').replace(']', ')')
                
                gettable_icon = "📦" if item.gettable else "🚫"
                lines.append(f'    {item_id}("{gettable_icon} {safe_item_name}")')
                lines.append(f'    class {item_id} item')
                lines.append(f'    {loc_id} --> {item_id}')
    
    lines.append("")
    
    # Add characters (NPCs) to locations
    char_counter = 0
    for char_name, character in world.characters.items():
        if character == world.player:
            continue
        
        char_id = f"char_{char_counter}"
        char_counter += 1
        safe_char_name = character.name.replace('"', '\\"').replace('[', '(').replace(']', ')')
        
        # Add inventory info if character has items
        inventory_info = ""
        if hasattr(character, 'inventory') and character.inventory:
            item_count = len(character.inventory)
            if language == 'es':
                inventory_info = f"<br/>🎒 {item_count} objetos"
            else:
                inventory_info = f"<br/>🎒 {item_count} items"
        
        lines.append(f'    {char_id}["👤 {safe_char_name}{inventory_info}"]')
        lines.append(f'    class {char_id} character')
        
        # Link to location
        if hasattr(character, 'location') and character.location:
            char_loc_id = location_ids.get(character.location.name)
            if char_loc_id:
                lines.append(f'    {char_loc_id} --> {char_id}')
    
    lines.append("")
    
    # Add puzzles
    puzzle_counter = 0
    for puzzle_name, puzzle in world.puzzles.items():
        puzzle_id = f"puzzle_{puzzle_counter}"
        puzzle_counter += 1
        safe_puzzle_name = puzzle.name.replace('"', '\\"').replace('[', '(').replace(']', ')')
        
        lines.append(f'    {puzzle_id}{{"🧩 {safe_puzzle_name}"}}')
        lines.append(f'    class {puzzle_id} puzzle')
        
        # Link puzzle to location if it has one
        if hasattr(puzzle, 'proposed_by_location') and puzzle.proposed_by_location:
            puzzle_loc_id = location_ids.get(puzzle.proposed_by_location)
            if puzzle_loc_id:
                lines.append(f'    {puzzle_loc_id} -.-> {puzzle_id}')
        # Or link to character if proposed by one
        elif hasattr(puzzle, 'proposed_by_character') and puzzle.proposed_by_character:
            for char_name, character in world.characters.items():
                if character.name == puzzle.proposed_by_character:
                    char_id = f"char_{list(world.characters.keys()).index(char_name)}"
                    lines.append(f'    {char_id} -.-> {puzzle_id}')
                    break
    
    return "\n".join(lines)


def generate_world_text_summary(world: World, language: str = 'en') -> str:
    """Generate a detailed text summary of the world structure.
    
    Args:
        world: The World object to summarize
        language: Language for labels ('en' or 'es')
        
    Returns:
        str: Formatted text summary
    """
    lines = []
    
    if language == 'es':
        lines.append("## 📊 Resumen del Mundo")
        lines.append(f"**Jugador:** {world.player.name}")
        lines.append(f"**Ubicación inicial:** {world.player.location.name}")
        lines.append(f"**Total de ubicaciones:** {len(world.locations)}")
        lines.append(f"**Total de objetos:** {len(world.items)}")
        lines.append(f"**Total de personajes:** {len(world.characters) - 1}")  # -1 for player
        lines.append(f"**Total de puzzles:** {len(world.puzzles)}")
    else:
        lines.append("## 📊 World Summary")
        lines.append(f"**Player:** {world.player.name}")
        lines.append(f"**Starting location:** {world.player.location.name}")
        lines.append(f"**Total locations:** {len(world.locations)}")
        lines.append(f"**Total items:** {len(world.items)}")
        lines.append(f"**Total characters:** {len(world.characters) - 1}")  # -1 for player
        lines.append(f"**Total puzzles:** {len(world.puzzles)}")
    
    lines.append("")
    
    # Objective info
    if hasattr(world, 'objective') and world.objective:
        if language == 'es':
            lines.append("### 🎯 Objetivo")
        else:
            lines.append("### 🎯 Objective")
        
        if hasattr(world, 'objective_data') and world.objective_data:
            obj_data = world.objective_data
            lines.append(f"**Tipo:** {obj_data.type.value if hasattr(obj_data.type, 'value') else str(obj_data.type)}")
            lines.append(f"**Descripción:** {obj_data.description}")
        else:
            lines.append("*Objetivo definido (formato legacy)*")
    
    lines.append("")
    
    # Location details
    if language == 'es':
        lines.append("### 🗺️ Ubicaciones Detalladas")
    else:
        lines.append("### 🗺️ Detailed Locations")
    
    for loc_name, location in world.locations.items():
        is_start = (loc_name == world.player.location.name)
        start_marker = " ⭐" if is_start else ""
        lines.append(f"\n**{loc_name}{start_marker}**")
        
        # Connections
        if hasattr(location, 'connecting_locations') and location.connecting_locations:
            conn_names = [loc.name for loc in location.connecting_locations]
            if language == 'es':
                lines.append(f"- Conecta con: {', '.join(conn_names)}")
            else:
                lines.append(f"- Connects to: {', '.join(conn_names)}")
        
        # Blocked passages
        if hasattr(location, 'blocked_locations') and location.blocked_locations:
            if language == 'es':
                lines.append(f"- Pasajes bloqueados:")
            else:
                lines.append(f"- Blocked passages:")
            for blocked_loc_name, blocking_info in location.blocked_locations.items():
                # blocking_info is a tuple: (location, obstacle, symmetric)
                blocker = blocking_info[1] if len(blocking_info) > 1 else None
                blocker_name = blocker.name if blocker and hasattr(blocker, 'name') else "Unknown"
                lines.append(f"  - {blocked_loc_name} (bloqueado por: {blocker_name})")
        
        # Items
        if hasattr(location, 'items') and location.items:
            item_names = [f"{item.name} {'📦' if item.gettable else '🚫'}" for item in location.items]
            if language == 'es':
                lines.append(f"- Objetos: {', '.join(item_names)}")
            else:
                lines.append(f"- Items: {', '.join(item_names)}")
        
        # Characters
        chars_here = [char for char in world.characters.values() 
                     if hasattr(char, 'location') and char.location == location and char != world.player]
        if chars_here:
            char_names = [char.name for char in chars_here]
            if language == 'es':
                lines.append(f"- Personajes: {', '.join(char_names)}")
            else:
                lines.append(f"- Characters: {', '.join(char_names)}")
    
    return "\n".join(lines)
