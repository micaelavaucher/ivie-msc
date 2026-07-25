def create_world_state_summary(world, player_action, language='en'):
    """Create a rich contextual summary of the world state for memory embedding."""
    try:
        player_location = world.player.location.name
        
        location_description = ""
        if hasattr(world.player.location, 'descriptions') and world.player.location.descriptions:
            # Take the first description or join multiple descriptions
            if isinstance(world.player.location.descriptions, list):
                location_description = " ".join(world.player.location.descriptions)
            else:
                location_description = str(world.player.location.descriptions)
        elif hasattr(world.player.location, 'description'):
            location_description = world.player.location.description
        elif hasattr(world.player.location, 'desc'):
            location_description = world.player.location.desc
        
        # Safely get visible items in current location
        visible_items = []
        if hasattr(world.player.location, 'items') and world.player.location.items:
            visible_items = [item.name for item in world.player.location.items]
        
        # Get characters in current location (they are stored in world.characters, not location.characters)
        present_characters = []
        if hasattr(world, 'characters') and world.characters:
            for character in world.characters.values():
                if hasattr(character, 'location') and character.location is world.player.location:
                    # Don't include the player character in the list
                    if character is not world.player:
                        present_characters.append(character.name)
        
        # Safely get player inventory
        player_items = []
        if hasattr(world.player, 'inventory') and world.player.inventory:
            player_items = [item.name for item in world.player.inventory]
        
        # Extract key object from player action if possible
        key_object = ""
        action_words = player_action.lower().split()
        if hasattr(world, 'items') and world.items:
            for item_name, item in world.items.items():
                if any(word in item_name.lower() for word in action_words):
                    key_object = item_name
                    break
        
        # Build rich contextual summary
        if language == 'es':
            summary = f"Ubicación: {player_location}. "
            
            if location_description:
                summary += f"Descripción: {location_description[:100]}{'...' if len(location_description) > 100 else ''}. "
            
            if visible_items:
                summary += f"Objetos visibles: {', '.join(visible_items)}. "
            
            if present_characters:
                summary += f"Personajes presentes: {', '.join(present_characters)}. "
                
            if player_items:
                summary += f"Inventario del jugador: {', '.join(player_items)}. "
                
            if key_object:
                summary += f"Objeto clave de la acción: {key_object}. "
                
            summary += f"Acción realizada: {player_action}"
            
        else:
            summary = f"Location: {player_location}. "
            
            if location_description:
                summary += f"Description: {location_description[:100]}{'...' if len(location_description) > 100 else ''}. "
            
            if visible_items:
                summary += f"Visible items: {', '.join(visible_items)}. "
            
            if present_characters:
                summary += f"Present characters: {', '.join(present_characters)}. "
                
            if player_items:
                summary += f"Player inventory: {', '.join(player_items)}. "
                
            if key_object:
                summary += f"Key object in action: {key_object}. "
                
            summary += f"Action performed: {player_action}"
        
        return summary
        
    except Exception as e:
        print(f"⚠️ Error creating world state summary: {e}")
        # Fallback to basic summary
        if language == 'es':
            return f"Ubicación: {world.player.location.name}. Acción: {player_action}"
        else:
            return f"Location: {world.player.location.name}. Action: {player_action}"