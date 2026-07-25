"""UI components and text constants for IVIE.

This module contains all UI-related constants, messages, and component
definitions for different languages and modes.
"""

def get_ui_texts(language):
    """Get UI text constants based on language."""
    if language == "es":
        return {
            'TITLE': "# 🌱 IVIE: Modo inspiración",
            'PROMPT_LABEL': "Escribí una frase o temática para inspirar la creación del mundo:",
            'TEXTBOX_LABEL': "Frase o temática",
            'CREATE_BUTTON_TEXT': "Crear mundo",
            'ERROR_LABEL': "Error",
            'SPINNER_TEXT': "Generando mundo...",
            'GENERATE_WORLD': "Crear mundo",
            'TEXTBOX_PLACEHOLDER': "¿Qué quieres hacer?",
            'PROGRESS_LABEL': "Progreso"
        }
    else:
        return {
            'TITLE': "# 🌱 IVIE: Inspiration Mode",
            'PROMPT_LABEL': "Write a theme or idea to inspire the world:",
            'TEXTBOX_LABEL': "Theme or idea",
            'CREATE_BUTTON_TEXT': "Create world",
            'ERROR_LABEL': "Error",
            'SPINNER_TEXT': "Generating world...",
            'GENERATE_WORLD': "Create world",
            'TEXTBOX_PLACEHOLDER': "What do you want to do next?",
            'PROGRESS_LABEL': "Progress"
        }

def get_progress_messages(language):
    """Get progress message templates based on language."""
    if language == "es":
        return {
            'INIT': "⚙️ Iniciando generación del mundo...",
            'RETRY': "🔄 Intento {attempt}/{max_attempts}: Regenerando mundo porque falta el objetivo...",
            'STEP_1': "📝 Paso 1: Generando concepto del mundo...",
            'STEP_1_COMPLETE': "✅ Concepto creado: '{title}'",
            'STEP_2': "🦴 Paso 2: Creando esqueleto del mundo...",
            'STEP_2_COMPLETE': "✅ Esqueleto creado con {locations} ubicaciones, {items} objetos y {characters} personajes",
            'STEP_3': "🌍 Paso 3: Desarrollando detalles y conexiones...",
            'STEP_3_COMPLETE': "✅ Mundo base creado con {locations} ubicaciones y {items} objetos",
            'STEP_4': "🧩 Paso 4: Añadiendo puzzles y obstáculos...",
            'STEP_4_COMPLETE': "✅ Puzzles añadidos: {puzzles} puzzles en total",
            'STEP_5': "🎨 Paso 5: Expandiendo con contenido adicional...",
            'STEP_5_COMPLETE': "✅ Expansión completada: mundo final con {locations} ubicaciones",
            'PIPELINE_COMPLETE': "🌱 ¡Generación incremental completada exitosamente!",
            'BUILDING_WORLD': "🔧 Construyendo mundo desde respuesta del LLM...",
            'NO_OBJECTIVE_WARNING': "⚠️ El mundo generado no tiene un objetivo definido. Intentando de nuevo...",
            'NO_OBJECTIVE_ERROR': "❌ No se pudo generar un mundo con objetivo después de varios intentos.",
            'SUCCESS': "✅ ¡Nuevo mundo creado exitosamente con objetivo definido!",
            'NARRATION': "📖 Generando narración inicial...",
            'OBJECTIVE': "🎯 Generando descripción del objetivo...",
            'SAVING': "💾 Guardando estado inicial del mundo...",
            'COMPLETE': "🎉 ¡Mundo generado exitosamente! Iniciando juego..."
        }
    else:
        return {
            'INIT': "⚙️ Starting world generation...",
            'RETRY': "🔄 Attempt {attempt}/{max_attempts}: Regenerating world because objective is missing...",
            'STEP_1': "📝 Step 1: Generating world concept...",
            'STEP_1_COMPLETE': "✅ Concept created: '{title}'",
            'STEP_2': "🦴 Step 2: Creating world skeleton...",
            'STEP_2_COMPLETE': "✅ Skeleton created with {locations} locations, {items} items and {characters} characters",
            'STEP_3': "🌍 Step 3: Developing details and connections...",
            'STEP_3_COMPLETE': "✅ Base world created with {locations} locations and {items} items",
            'STEP_4': "🧩 Step 4: Adding puzzles and obstacles...",
            'STEP_4_COMPLETE': "✅ Puzzles added: {puzzles} puzzles in total",
            'STEP_5': "🎨 Step 5: Expanding with additional content...",
            'STEP_5_COMPLETE': "✅ Expansion completed: final world with {locations} locations",
            'PIPELINE_COMPLETE': "🌱 Incremental generation completed successfully!",
            'BUILDING_WORLD': "🔧 Building world from LLM response...",
            'NO_OBJECTIVE_WARNING': "⚠️ Generated world has no defined objective. Trying again...",
            'NO_OBJECTIVE_ERROR': "❌ Failed to generate a world with objective after several attempts.",
            'SUCCESS': "✅ New world created successfully with defined objective!",
            'NARRATION': "📖 Generating initial narration...",
            'OBJECTIVE': "🎯 Generating objective description...",
            'SAVING': "💾 Saving initial world state...",
            'COMPLETE': "🎉 World generated successfully! Starting game..."
        }
