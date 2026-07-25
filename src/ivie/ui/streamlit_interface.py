"""Modern Streamlit interface for IVIE.

This module provides a beautiful and modern chat interface using Streamlit,
replacing the Gradio interface with enhanced UI and functionality.
"""

import streamlit as st
import os
import time
import json
import base64
from ..config import load_config
from ..llm.models import get_llm
from ..core.game_logic import create_game_loop, generate_starting_narration
from ..llm.generation_pipeline import create_world_incrementally_generate
from ..core.world_builder import create_world_from_llm_response
from .ui_components import get_ui_texts, get_progress_messages
import examples.example_worlds as example_worlds

def render_mermaid(mermaid_code: str, height: int = 600):
    """Render a Mermaid diagram using Mermaid.js from CDN with zoom controls.
    
    Args:
        mermaid_code: The Mermaid diagram code
        height: Height of the rendered diagram in pixels
    """
    # Simple test to verify rendering works
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
            
            window.addEventListener('load', async () => {{
                mermaid.initialize({{ 
                    startOnLoad: false,
                    theme: 'default',
                    flowchart: {{
                        useMaxWidth: false,
                        htmlLabels: true,
                        curve: 'basis'
                    }},
                    securityLevel: 'loose'
                }});
                
                try {{
                    const {{svg}} = await mermaid.render('mermaid-svg', document.getElementById('diagram-code').textContent);
                    document.getElementById('diagram-output').innerHTML = svg;
                    console.log('Mermaid rendered successfully');
                }} catch(e) {{
                    console.error('Mermaid error:', e);
                    document.getElementById('diagram-output').innerHTML = '<pre style="color:red;">Error: ' + e.message + '</pre>';
                }}
            }});
        </script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #ffffff;
                font-family: 'Arial', sans-serif;
            }}
            
            #zoom-controls {{
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: flex;
                gap: 5px;
            }}
            
            .zoom-btn {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            
            .zoom-btn:hover {{
                background: #45a049;
            }}
            
            .zoom-btn:active {{
                background: #3d8b40;
            }}
            
            #zoom-reset {{
                background: #2196F3;
            }}
            
            #zoom-reset:hover {{
                background: #0b7dda;
            }}
            
            #zoom-level {{
                background: #f0f0f0;
                color: #333;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 60px;
                text-align: center;
            }}
            
            #diagram-container {{
                width: 100%;
                height: {height}px;
                overflow: auto;
                cursor: grab;
                position: relative;
                background-color: #f9f9f9;
            }}
            
            #diagram-container:active {{
                cursor: grabbing;
            }}
            
            #diagram-wrapper {{
                display: inline-block;
                transform-origin: top left;
                transition: transform 0.2s ease;
                padding: 20px;
            }}
            
            .mermaid {{
                font-family: 'Arial', sans-serif;
                background-color: white;
                padding: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="zoom-controls">
            <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
            <div id="zoom-level">100%</div>
            <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
            <button class="zoom-btn" id="zoom-reset" title="Reset Zoom">⟲</button>
        </div>
        
        <div id="diagram-container">
            <div id="diagram-wrapper">
                <pre id="diagram-code" style="display:none;">{mermaid_code}</pre>
                <div id="diagram-output"></div>
            </div>
        </div>
        
        <script>
            let scale = 1.0;
            const minScale = 0.3;
            const maxScale = 3.0;
            const scaleStep = 0.1;
            
            const wrapper = document.getElementById('diagram-wrapper');
            const container = document.getElementById('diagram-container');
            const zoomLevel = document.getElementById('zoom-level');
            
            function updateZoom() {{
                wrapper.style.transform = `scale(${{scale}})`;
                zoomLevel.textContent = Math.round(scale * 100) + '%';
            }}
            
            document.getElementById('zoom-in').addEventListener('click', () => {{
                if (scale < maxScale) {{
                    scale = Math.min(scale + scaleStep, maxScale);
                    updateZoom();
                }}
            }});
            
            document.getElementById('zoom-out').addEventListener('click', () => {{
                if (scale > minScale) {{
                    scale = Math.max(scale - scaleStep, minScale);
                    updateZoom();
                }}
            }});
            
            document.getElementById('zoom-reset').addEventListener('click', () => {{
                scale = 1.0;
                updateZoom();
                container.scrollTop = 0;
                container.scrollLeft = 0;
            }});
            
            // Mouse wheel zoom
            container.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const delta = e.deltaY > 0 ? -scaleStep : scaleStep;
                const newScale = Math.max(minScale, Math.min(maxScale, scale + delta));
                
                if (newScale !== scale) {{
                    scale = newScale;
                    updateZoom();
                }}
            }});
            
            // Pan functionality
            let isPanning = false;
            let startX, startY, scrollLeft, scrollTop;
            
            container.addEventListener('mousedown', (e) => {{
                isPanning = true;
                startX = e.pageX - container.offsetLeft;
                startY = e.pageY - container.offsetTop;
                scrollLeft = container.scrollLeft;
                scrollTop = container.scrollTop;
            }});
            
            container.addEventListener('mouseleave', () => {{
                isPanning = false;
            }});
            
            container.addEventListener('mouseup', () => {{
                isPanning = false;
            }});
            
            container.addEventListener('mousemove', (e) => {{
                if (!isPanning) return;
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const y = e.pageY - container.offsetTop;
                const walkX = (x - startX) * 2;
                const walkY = (y - startY) * 2;
                container.scrollLeft = scrollLeft - walkX;
                container.scrollTop = scrollTop - walkY;
            }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=height, scrolling=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'  # Default to English
    
    if 'nickname' not in st.session_state:
        st.session_state.nickname = ''
    
    if 'generation_mode' not in st.session_state:
        st.session_state.generation_mode = 'inspiration'  # Default to inspiration mode
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False  # Default debug mode off
    
    if 'world' not in st.session_state:
        st.session_state.world = None
    
    if 'game_loop' not in st.session_state:
        st.session_state.game_loop = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'world_generated' not in st.session_state:
        st.session_state.world_generated = False
    
    if 'current_inspiration' not in st.session_state:
        st.session_state.current_inspiration = ""
    
    if 'visited_locations' not in st.session_state:
        st.session_state.visited_locations = set()

def get_inspiration_suggestions(language: str) -> dict:
    """Get inspiration suggestions based on language."""
    if language == 'es':
        return {
            "🕵️ Detectives": "Una historia de misterio y crimen donde eres un detective resolviendo un caso complejo",
            "🌙 Crepúsculo, la Saga": "El mundo de la Saga Crepúsculo.",
            "🍄 Super Mario": "Una aventura colorida en el Reino Champiñón con plataformas, power-ups y rescates épicos"
        }
    else:
        return {
            "🕵️ Detectives": "A mystery and crime story where you are a detective solving a complex case",
            "🌙 Twilight Saga": "The Twilight Saga world",
            "🍄 Super Mario": "A colorful adventure in the Mushroom Kingdom with platforms, power-ups and epic rescues"
        }

def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Check if game is active (world is loaded)
        game_active = st.session_state.world_generated and st.session_state.world is not None
        
        # Language selector
        language_options = {'English': 'en', 'Español': 'es'}
        current_lang = st.session_state.language
        selected_lang_name = next(k for k, v in language_options.items() if v == current_lang)
        
        new_lang = st.selectbox(
            "🌐 Language",
            options=list(language_options.keys()),
            index=list(language_options.keys()).index(selected_lang_name),
            disabled=game_active
        )
        
        if not game_active and language_options[new_lang] != st.session_state.language:
            st.session_state.language = language_options[new_lang]
            st.rerun()

        nickname = st.text_input(
            label="🎭 Nickname",
            value=st.session_state.get('nickname', ''),
            max_chars=16,
            placeholder="Enter your nickname" if st.session_state.language == 'en' else 'Ingresa tu nickname',
            disabled=game_active
        )

        if not game_active and nickname != st.session_state.get('nickname', ''):
            st.session_state.nickname = nickname
        
        # Mode selector
        mode_options = {
            'Inspiration': 'inspiration',
            'Generate': 'generate', 
            'Preset': 'preset',
            'Tutorial': 'tutorial',
            'Replay': 'replay'
        }
        current_mode = st.session_state.generation_mode
        selected_mode_name = next(k for k, v in mode_options.items() if v == current_mode)
        
        new_mode = st.selectbox(
            "🎮 Generation Mode",
            options=list(mode_options.keys()),
            index=list(mode_options.keys()).index(selected_mode_name),
            disabled=game_active
        )
        
        if not game_active and mode_options[new_mode] != st.session_state.generation_mode:
            st.session_state.generation_mode = mode_options[new_mode]
            # Reset world state when mode changes
            st.session_state.world = None
            st.session_state.game_loop = None
            st.session_state.chat_history = []
            st.session_state.world_generated = False
            st.rerun()
        
        # Debug mode toggle
        new_debug = st.checkbox(
            "🛠️ Debug Mode",
            value=st.session_state.debug_mode,
            disabled=game_active,
            help="Enable debug quick actions for world inspection"
        )
        
        if not game_active and new_debug != st.session_state.debug_mode:
            st.session_state.debug_mode = new_debug
        
        if game_active:
            st.info("🔒 Settings locked during active game")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🏠 Home", type="secondary"):
            st.session_state.world = None
            st.session_state.game_loop = None
            st.session_state.chat_history = []
            st.session_state.world_generated = False
            st.session_state.visited_locations = set()
            st.rerun()

def render_inspiration_mode():
    """Render the inspiration mode interface."""
    texts = get_ui_texts(st.session_state.language)
    
    st.markdown("# 🌱 IVIE: Incremental & Validated Interactive Experiences")
    st.markdown("### *Where generated worlds come to life*")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Inspiración:** Escribe una idea y genera un mundo único")
    else:
        st.markdown("**Inspiration Mode:** Write an idea and generate a unique world")
    
    # Inspiration suggestions
    suggestions = get_inspiration_suggestions(st.session_state.language)
    
    if st.session_state.language == 'es':
        st.markdown("**💡 Sugerencias populares:**")
    else:
        st.markdown("**💡 Popular suggestions:**")
    
    cols = st.columns(3)
    
    for i, (title, description) in enumerate(suggestions.items()):
        with cols[i]:
            if st.button(title, key=f"suggestion_{i}", help=description):
                st.session_state.inspiration_input = description
                st.rerun()
    
    # Text input for inspiration
    inspiration = st.text_area(
        texts['PROMPT_LABEL'],
        value=st.session_state.get('inspiration_input', ''),
        placeholder=texts['TEXTBOX_LABEL'],
        height=100
    )
    
    # Generate button
    if st.button(texts['GENERATE_WORLD'], type="primary", disabled=not inspiration.strip()):
        generate_world_from_inspiration(inspiration.strip())

def generate_world_from_inspiration(inspiration: str):
    """Generate world from inspiration with progress display."""
    progress_container = st.container()
    progress_messages = get_progress_messages(st.session_state.language)
    
    with progress_container:
        st.markdown("### 🔄 Generating World...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            config = load_config()
            reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
            log_filename = f"streamlit_session_{int(time.time())}.json"
            
            reasoning_model = get_llm(reasoning_model_name)
            narrative_model = get_llm(narrative_model_name)
            
            # Step-by-step generation with proper progress tracking
            from ..llm.generation_pipeline import run_step_1_concept, run_step_2_skeleton, run_step_3_details, run_step_4_puzzles
            
            # Step 1: Concept
            status_text.text(progress_messages['STEP_1'])
            progress_bar.progress(0.1)
            time.sleep(0.2)
            print(f"session_state: {st.session_state}")
            concept = run_step_1_concept(inspiration, st.session_state.language)
            status_text.text(progress_messages['STEP_1_COMPLETE'].format(title=concept.title))
            progress_bar.progress(0.2)
            time.sleep(0.3)
            
            # Step 2: Skeleton
            status_text.text(progress_messages['STEP_2'])
            progress_bar.progress(0.3)
            time.sleep(0.2)
            
            skeleton = run_step_2_skeleton(concept, st.session_state.language)
            status_text.text(progress_messages['STEP_2_COMPLETE'].format(
                locations=len(skeleton.key_locations),
                items=len(skeleton.key_items),
                characters=len(skeleton.key_characters)
            ))
            progress_bar.progress(0.5)
            time.sleep(0.3)
            
            # Step 3: Details
            status_text.text(progress_messages['STEP_3'])
            progress_bar.progress(0.6)
            time.sleep(0.2)
            
            world_basic = run_step_3_details(concept, skeleton, st.session_state.language)
            status_text.text(progress_messages['STEP_3_COMPLETE'].format(
                locations=len(world_basic.locations),
                items=len(world_basic.items)
            ))
            progress_bar.progress(0.7)
            time.sleep(0.3)
            
            # Step 4: Puzzles
            status_text.text(progress_messages['STEP_4'])
            progress_bar.progress(0.8)
            time.sleep(0.2)
            
            world_with_puzzles = run_step_4_puzzles(world_basic, st.session_state.language)
            status_text.text(progress_messages['STEP_4_COMPLETE'].format(
                puzzles=len(world_with_puzzles.puzzles)
            ))
            progress_bar.progress(0.9)
            time.sleep(0.3)
            
            # Step 5: Final expansion (optional, simplified)
            generated_world = world_with_puzzles  # Skip expansion for now to be faster
            
            status_text.text(progress_messages['PIPELINE_COMPLETE'])
            progress_bar.progress(0.95)
            time.sleep(0.2)
            
            # Build world objects
            status_text.text(progress_messages['BUILDING_WORLD'])
            world = create_world_from_llm_response(generated_world)
            
            if world is None:
                # Fallback to preset world
                status_text.text("🔄 Using fallback world...")
                world = example_worlds.get_world(2, language=st.session_state.language)
            
            st.session_state.world = world
            st.session_state.world_generated = True
            st.session_state.current_inspiration = inspiration
            
            # Generate starting narration
            starting_narration = generate_starting_narration(
                st.session_state.world,
                st.session_state.language,
                narrative_model
            )
            
            # Initialize chat with starting narration
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            progress_bar.progress(1.0)
            status_text.success("✅ World generated successfully!")
            time.sleep(1)
            st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error generating world: {str(e)}")

def render_generate_mode():
    """Render the generate mode interface."""
    st.markdown("# 🌱 IVIE: Incremental & Validated Interactive Experiences")
    st.markdown("### Where generated worlds come to life")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Generar:** Genera un mundo completamente aleatorio")
    else:
        st.markdown("**Generate Mode:** Generate a completely random world")
    
    if not st.session_state.world_generated:
        if st.button("🎲 Generate Random World", type="primary"):
            generate_random_world()
    else:
        render_chat_interface()

def generate_random_world():
    """Generate a completely random world."""
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Generating Random World...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            config = load_config()
            reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
            
            narrative_model = get_llm(narrative_model_name)
            
            # Step 1: Generate world
            status_text.text("🌍 Creating world concept...")
            progress_bar.progress(0.2)
            
            generated_world = create_world_incrementally_generate(st.session_state.language)
            
            # Step 2: Build world objects
            status_text.text("🏗️ Building world structure...")
            progress_bar.progress(0.6)
            
            world = create_world_from_llm_response(generated_world)
            
            if world is None:
                # Fallback to preset world
                status_text.text("🔄 Using fallback world...")
                progress_bar.progress(0.8)
                world = example_worlds.get_world(2, language=st.session_state.language)
            
            # Step 3: Initialize game
            status_text.text("🎮 Initializing game...")
            progress_bar.progress(0.9)
            
            st.session_state.world = world
            st.session_state.world_generated = True
            st.session_state.current_inspiration = ""
            
            # Generate starting narration
            starting_narration = generate_starting_narration(
                world,
                st.session_state.language,
                narrative_model
            )
            
            # Initialize chat with starting narration
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            progress_bar.progress(1.0)
            status_text.success("✅ Random world generated successfully!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating random world: {str(e)}")

def render_preset_mode():
    """Render the preset mode interface."""
    st.markdown("# 🌱 IVIE: Incremental & Validated Interactive Experiences")
    st.markdown("### Where generated worlds come to life")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Predefinido:** Usa un mundo preconstruido")
    else:
        st.markdown("**Preset Mode:** Use a pre-built world")
    
    if not st.session_state.world_generated:
        # World selector
        world_options = {
            "Mysterious Library": 1,
            "Desert Oasis": 2, 
            "Haunted Mansion": 3
        }
        
        selected_world = st.selectbox(
            "🏰 Select a world:",
            options=list(world_options.keys())
        )
        
        if st.button("🚀 Load World", type="primary"):
            load_preset_world(world_options[selected_world])
    else:
        render_chat_interface()

def load_preset_world(world_id: int):
    """Load a preset world."""
    try:
        world = example_worlds.get_world(world_id, language=st.session_state.language)
        st.session_state.world = world
        st.session_state.world_generated = True
        st.session_state.current_inspiration = ""
        
        config = load_config()
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        narrative_model = get_llm(narrative_model_name)
        
        # Generate starting narration
        starting_narration = generate_starting_narration(
            world,
            st.session_state.language,
            narrative_model
        )
        
        # Initialize chat with starting narration
        st.session_state.chat_history = [
            {"role": "assistant", "content": starting_narration}
        ]
        
        st.success("✅ Preset world loaded successfully!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error loading preset world: {str(e)}")

def render_replay_mode():
    """Render the replay mode interface."""
    st.markdown("# 🌱 IVIE: Incremental & Validated Interactive Experiences")
    st.markdown("### Where generated worlds come to life")
    
    # Initialize inspection state if not exists
    if 'inspecting_world' not in st.session_state:
        st.session_state.inspecting_world = False
    if 'loaded_world_for_inspection' not in st.session_state:
        st.session_state.loaded_world_for_inspection = None
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Replay:** Reproduce un mundo guardado desde MongoDB")
        st.markdown("""
        🔬 **Modo de Desarrollo**
        
        Este modo te permite inspeccionar y jugar mundos previamente generados desde MongoDB.
        
        **Cómo usarlo:**
        1. Ir al cluster de MongoDB Compass
        2. Buscar en la colección de trazas
        3. Copiar el `world_id` del mundo que se desea reproducir
        4. Pegarlo abajo y hacer clic en "Cargar Mundo"
        5. Elegir entre **Inspeccionar** (ver diagrama del mundo) o **Jugar** directamente
        
        ⚠️ El mundo se va a cargar desde el estado inicial (turno 0)
        """)
    else:
        st.markdown("**Replay Mode:** Replay a saved world from MongoDB")
        st.markdown("""
        🔬 **Development Mode**
        
        This mode allows you to inspect and play previously generated worlds from MongoDB.
        
        **How to use:**
        1. Go to the MongoDB Compass cluster
        2. Search in the traces collection
        3. Copy the `world_id` of the world you want to replay
        4. Paste it below and click "Load World"
        5. Choose between **Inspect** (view world diagram) or **Play** directly
        
        ⚠️ The world will be loaded from initial state (turn 0)
        """)

    # If user requested the played conversation viewer, show it full-width
    if st.session_state.get('show_played_conversation'):
        st.markdown("# 📄 Played Conversation")
        # Close button
        if st.button("⤶ Close Viewer"):
            for k in ('show_played_conversation', 'played_conversation_html', 'played_conversation_world_id'):
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        # Render the previously prepared HTML at full width
        html_to_render = st.session_state.get('played_conversation_html')
        if html_to_render:
            st.components.v1.html(html_to_render, height=900, scrolling=True)
        else:
            st.error("❌ No played conversation available to display.")
        return
    
    # If already playing, show the game
    if st.session_state.world_generated and not st.session_state.inspecting_world:
        render_chat_interface()
        return
    
    # If inspecting, show the inspection view
    if st.session_state.inspecting_world and st.session_state.loaded_world_for_inspection:
        render_world_inspection(st.session_state.loaded_world_for_inspection)
        return
    
    # Otherwise, show the world ID input
    world_id = st.text_input(
        "🆔 World ID:",
        placeholder="e.g., generated_1756850394",
        help="Enter the world_id from MongoDB"
    )
    
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔎 Inspect World", type="secondary", disabled=not world_id.strip()):
            load_world_for_inspection(world_id.strip())

    with col2:
        if st.button("🎮 Play World", type="primary", disabled=not world_id.strip()):
            load_replay_world(world_id.strip())

    with col3:
        if st.button("📄 View Played Conversation", type="secondary", disabled=not world_id.strip()):
            render_played_conversation(world_id.strip())

def load_world_for_inspection(world_id: str):
    """Load a world from MongoDB for inspection only (no gameplay)."""
    from ..database.mongodb_handler import db_handler
    from ..core.world_builder import create_world_from_trace
    
    try:
        with st.spinner(f"🔍 Loading world {world_id} for inspection..."):
            if not db_handler or not db_handler.trace_exists(world_id):
                st.error(f"❌ No trace found for world_id: {world_id}")
                st.info("💡 Make sure the world_id is correct and exists in MongoDB")
                return
            
            trace_data = db_handler.get_trace_by_world_id(world_id)
            
            if not trace_data:
                st.error(f"❌ Failed to retrieve trace for world_id: {world_id}")
                return
            
            world = create_world_from_trace(trace_data)
            
            st.session_state.loaded_world_for_inspection = world
            st.session_state.inspecting_world = True
            
            st.success(f"✅ World {world_id} loaded for inspection!")
            time.sleep(0.5)
            st.rerun()
            
    except ValueError as e:
        st.error(f"❌ Invalid trace data: {str(e)}")
        st.info("💡 The trace may be corrupted or incomplete")
    except Exception as e:
        st.error(f"❌ Error loading world for inspection: {str(e)}")
        import traceback
        if st.session_state.debug_mode:
            st.code(traceback.format_exc())

def render_world_inspection(world):
    """Render the world inspection view with diagram and details."""
    from ..core.world_visualizer import generate_world_mermaid_diagram, generate_world_text_summary
    
    st.markdown("# 🔍 World Inspector")
    
    if st.session_state.language == 'es':
        st.markdown("### Visualización del Mundo")
    else:
        st.markdown("### World Visualization")
    
    # Action buttons at the top
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🎮 Play This World", type="primary"):
            # Move from inspection to playing
            st.session_state.world = st.session_state.loaded_world_for_inspection
            st.session_state.world_generated = True
            st.session_state.current_inspiration = ""
            st.session_state.inspecting_world = False
            
            config = load_config()
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gemini-2.5-flash')
            narrative_model = get_llm(narrative_model_name)
            
            starting_narration = generate_starting_narration(
                world,
                st.session_state.language,
                narrative_model
            )
            
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to World Selection", type="secondary"):
            st.session_state.inspecting_world = False
            st.session_state.loaded_world_for_inspection = None
            st.rerun()
    
    with col3:
        pass  # Spacer
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Valid Objective", "📊 Diagram", "📝 Details"])
    
    with tab1:
        # Generate and display world overview
        try:
            from ..core.world_builder import generate_world_overview
            overview = generate_world_overview(world, st.session_state.language)
            st.markdown(overview)
        except Exception as e:
            st.error(f"❌ Error generating overview: {str(e)}")
            if st.session_state.debug_mode:
                import traceback
                st.code(traceback.format_exc())
    
    with tab2:
        # Generate and display objective validation
        try:
            from ..core.world_builder import generate_objective_validation_report
            validation_report = generate_objective_validation_report(world, st.session_state.language)
            st.markdown(validation_report)
        except Exception as e:
            st.error(f"❌ Error generating objective validation: {str(e)}")
            if st.session_state.debug_mode:
                import traceback
                st.code(traceback.format_exc())
    
    with tab3:
        if st.session_state.language == 'es':
            st.markdown("""
            **Leyenda:**
            - 🟢 Ubicación inicial del jugador
            - 🔵 Ubicaciones normales
            - ➖➖ Pasaje bloqueado (con 🔒 y el elemento que bloquea)
            - 📦 Objeto (se puede tomar)
            - 🚫 Objeto decorativo (no se puede tomar)
            - 👤 Personaje
            - 🧩 Puzzle
            """)
        else:
            st.markdown("""
            **Legend:**
            - 🟢 Player starting location
            - 🔵 Normal locations
            - ➖➖ Blocked passage (with 🔒 and blocking element)
            - 📦 Item (can be taken)
            - 🚫 Decorative item (cannot be taken)
            - 👤 Character
            - 🧩 Puzzle
            """)
        
        # Generate and display Mermaid diagram
        try:
            mermaid_code = generate_world_mermaid_diagram(world, st.session_state.language)
            
            # Debug: show the code if in debug mode
            if st.session_state.debug_mode:
                with st.expander("🔍 Ver código Mermaid" if st.session_state.language == 'es' else "🔍 View Mermaid code"):
                    st.code(mermaid_code, language="mermaid")
            
            render_mermaid(mermaid_code, height=800)
        except Exception as e:
            st.error(f"❌ Error generating diagram: {str(e)}")
            if st.session_state.debug_mode:
                import traceback
                st.code(traceback.format_exc())
    
    with tab4:
        # Generate and display text summary
        try:
            text_summary = generate_world_text_summary(world, st.session_state.language)
            st.markdown(text_summary)
        except Exception as e:
            st.error(f"❌ Error generating summary: {str(e)}")
            if st.session_state.debug_mode:
                import traceback
                st.code(traceback.format_exc())

def load_replay_world(world_id: str):
    """Load a world from MongoDB trace."""
    from ..database.mongodb_handler import db_handler
    from ..core.world_builder import create_world_from_trace
    
    try:
        with st.spinner(f"🔍 Searching for world {world_id}..."):
            if not db_handler or not db_handler.trace_exists(world_id):
                st.error(f"❌ No trace found for world_id: {world_id}")
                st.info("💡 Make sure the world_id is correct and exists in MongoDB")
                return
            
            trace_data = db_handler.get_trace_by_world_id(world_id)
            
            if not trace_data:
                st.error(f"❌ Failed to retrieve trace for world_id: {world_id}")
                return
            
            world = create_world_from_trace(trace_data)
            
            st.session_state.world = world
            st.session_state.world_generated = True
            # Get inspiration from trace data if available, otherwise empty
            st.session_state.current_inspiration = trace_data.get('inspiration', "")
            
            config = load_config()
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gemini-2.5-flash')
            narrative_model = get_llm(narrative_model_name)
            
            starting_narration = generate_starting_narration(
                world,
                st.session_state.language,
                narrative_model
            )
            
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            st.success(f"World {world_id} loaded successfully from MongoDB!")
            time.sleep(1)
            st.rerun()
            
    except ValueError as e:
        st.error(f"❌ Invalid trace data: {str(e)}")
        st.info("The trace may be corrupted or incomplete")
    except Exception as e:
        st.error(f"❌ Error loading replay world: {str(e)}")
        import traceback
        if st.session_state.debug_mode:
            st.code(traceback.format_exc())

def render_played_conversation(world_id: str):
    """Render the played conversation using the static HTML viewer and the stored trace JSON.

    The function loads the trace from MongoDB, reads the `ver_mundos.html` template from
    the `static` folder, injects the trace as a base64 string and runs the viewer JS to
    display the played conversation immediately.
    """
    from ..database.mongodb_handler import db_handler

    try:
        with st.spinner(f"🔍 Loading played conversation for {world_id}..."):
            if not db_handler or not db_handler.trace_exists(world_id):
                st.error(f"❌ No trace found for world_id: {world_id}")
                st.info("💡 Make sure the world_id is correct and exists in MongoDB")
                return

            trace_data = db_handler.get_trace_by_world_id(world_id)

            if not trace_data:
                st.error(f"❌ Failed to retrieve trace for world_id: {world_id}")
                return

            # Read HTML template
            template_path = os.path.join(os.path.dirname(__file__), 'static', 'ver_mundos.html')
            if not os.path.exists(template_path):
                st.error("❌ Viewer template not found: ver_mundos.html")
                return

            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()

            # Convert Mongo-specific types to JSON-serializable primitives
            def _make_serializable(obj):
                # Local imports to avoid heavy top-level deps when not needed
                try:
                    from bson import ObjectId
                except Exception:
                    ObjectId = None
                import datetime

                if ObjectId is not None and isinstance(obj, ObjectId):
                    return str(obj)
                if isinstance(obj, dict):
                    return {k: _make_serializable(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple, set)):
                    return [_make_serializable(v) for v in obj]
                if isinstance(obj, datetime.datetime):
                    # Convert to ISO string
                    return obj.isoformat()
                # Fallback: return as-is (json.dumps may still error if unsupported)
                return obj

            serializable_trace = _make_serializable(trace_data)
            # Encode JSON to base64 to safely inject into the template
            trace_json = json.dumps(serializable_trace)
            trace_b64 = base64.b64encode(trace_json.encode('utf-8')).decode('ascii')

            injection_script = (
                "<script>\n"
                f"const __traceJsonB64 = '{trace_b64}';\n"
                "try {\n"
                "  const traceData = JSON.parse(atob(__traceJsonB64));\n"
                "  document.getElementById('jsonInput').value = JSON.stringify(traceData);\n"
                "  parseAndDisplay();\n"
                "} catch(e) { console.error('Error injecting trace:', e); }\n"
                "</script>"
            )

            # Insert script before closing </body>
            if '</body>' in html_template:
                final_html = html_template.replace('</body>', injection_script + '\n</body>')
            else:
                final_html = html_template + injection_script

            # Save the final HTML to session state and request a rerun so it can be
            # rendered full-width at the top of the replay view (outside columns).
            st.session_state['played_conversation_html'] = final_html
            st.session_state['played_conversation_world_id'] = world_id
            st.session_state['show_played_conversation'] = True
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error rendering played conversation: {str(e)}")
        import traceback
        if st.session_state.debug_mode:
            st.code(traceback.format_exc())

def render_tutorial_mode():
    """Render the tutorial mode interface."""
    st.markdown("# 🌱 IVIE: Incremental & Validated Interactive Experiences")
    st.markdown("### Where generated worlds come to life")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Tutorial:** Aprende a jugar con un mundo simple")
        st.markdown("""
        **¡Bienvenido al Tutorial de IVIE!** 🎮
        
        Este es un mundo simple diseñado para enseñarte cómo jugar:
        
        🏠 **2 ubicaciones:** Habitación Inicial → Jardín  
        🐢 **1 objetivo:** Encuentra y toma la tortuga  
        🎯 **Meta:** Recoger la tortuga del jardín
        
        ### 🤖 Estilo de Juego Chatbot
        IVIE funciona como una conversación entre tú y un narrador IA. Cada mensaje que escribas representa **una acción en el juego**.
        
        **📝 Mecánicas por Turnos:**
        - Un mensaje = Un turno de juego
        - Escribe comandos en lenguaje natural o descripciones de acciones
        - El narrador responderá describiendo lo que sucede
        - El mundo reacciona a tus decisiones dinámicamente
        
        **Ejemplos de cosas que puedes intentar:**
        - `mirar alrededor` - observar tu entorno
        - `ir al jardín` - moverte a otra ubicación  
        - `tomar tortuga` - recoger objetos
        - `inventario` - ver qué llevas contigo
        - `objetivo` - recordar tu misión
        (¡También puedes probar con otras acciones!)
        
        **📊 Aviso de Investigación:** Tu gameplay puede ser registrado de forma anónima para investigación sobre generación de narrativas con IA.
        """)
    else:
        st.markdown("**Tutorial Mode:** Learn to play with a simple world")
        st.markdown("""
        **Welcome to the IVIE Tutorial!** 🎮
        
        This is a simple world designed to teach you how to play:
        
        🏠 **2 locations:** Starting Room → Garden  
        🐢 **1 objective:** Find and take the turtle  
        🎯 **Goal:** Collect the turtle from the garden
        
        ### 🤖 Chatbot-Style Gameplay
        IVIE works like a conversation between you and an AI narrator. Each message you write represents **one action in the game**.
        
        **📝 Turn-Based Mechanics:**
        - One message = One game turn
        - Write commands in natural language or action descriptions
        - The narrator will respond describing what happens
        - The world reacts to your decisions dynamically
        
        **Examples of things you can try:**
        - `look around` - observe your surroundings
        - `go to garden` - move to another location  
        - `take turtle` - pick up objects
        - `inventory` - see what you're carrying
        - `objective` - remember your mission
        (You can experiment with other actions too!)
        
        **📊 Research Notice:** Your gameplay may be recorded anonymously for research on AI narrative generation.
        """)
    
    if not st.session_state.world_generated:
        if st.button("🎓 Start Tutorial", type="primary"):
            load_tutorial_world()
    else:
        render_chat_interface()

def load_tutorial_world():
    """Load the tutorial world."""
    try:
        world = example_worlds.get_world('tutorial', language=st.session_state.language)
        st.session_state.world = world
        st.session_state.world_generated = True
        st.session_state.current_inspiration = ""
        
        config = load_config()
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        narrative_model = get_llm(narrative_model_name)
        
        # Generate starting narration
        starting_narration = generate_starting_narration(
            world,
            st.session_state.language,
            narrative_model
        )
        
        # Initialize chat with starting narration
        st.session_state.chat_history = [
            {"role": "assistant", "content": starting_narration}
        ]
        
        st.success("✅ Tutorial world loaded successfully!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error loading tutorial world: {str(e)}")

def render_chat_interface():
    """Render the main chat interface."""
    st.markdown("### 💬 Adventure Chat")
    
    # Initialize game loop if not exists
    if st.session_state.game_loop is None and st.session_state.world:
        config = load_config()
        reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        enable_rag = config.getboolean('Options', 'EnableRAG', fallback=True)
        
        reasoning_model = get_llm(reasoning_model_name)
        narrative_model = get_llm(narrative_model_name)
        api_key = os.getenv("GEMINI_API_KEY")
        log_filename = f"streamlit_session_{int(time.time())}.json"
        
        st.session_state.game_loop = create_game_loop(
            st.session_state.world, 
            reasoning_model, 
            narrative_model,
            st.session_state.language, 
            st.session_state.visited_locations, 
            api_key, 
            enable_rag,
            st.session_state.current_inspiration
        )
    
    # Handle pending command if exists (process before displaying anything)
    if hasattr(st.session_state, 'pending_command') and st.session_state.pending_command:
        prompt = st.session_state.pending_command
        st.session_state.pending_command = None  # Clear the pending command
        
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Generate response
        if st.session_state.game_loop:
            response = st.session_state.game_loop(prompt, st.session_state.chat_history)
            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": "Game loop not initialized. Please reload the world."})
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Define quick actions based on language and debug mode
    if st.session_state.debug_mode:
        # Debug mode: show all actions
        if st.session_state.language == 'es':
            quick_actions = [
                ("🎯 Objetivo", "objetivo"),
                ("💡 Ayuda", "ayuda"),
                ("📋 Inventario", "inventario"),
                ("🔍 Inspeccionar", "inspeccionar mundo"),
                ("🗺️ Resumen", "resumen mundo"),
                ("📍 Ubicación", "¿dónde estoy?")
            ]
        else:
            quick_actions = [
                ("🎯 Objective", "objective"),
                ("💡 Help", "help"),
                ("📋 Inventory", "inventory"),
                ("🔍 Inspect World", "inspect world"),
                ("🗺️ Overview", "world overview"),
                ("📍 Location", "where am I?")
            ]
    else:
        # Normal mode: only basic actions
        if st.session_state.language == 'es':
            quick_actions = [
                ("🎯 Objetivo", "objetivo"),
                ("💡 Ayuda", "ayuda")
            ]
        else:
            quick_actions = [
                ("🎯 Objective", "objective"),
                ("💡 Help", "help")
            ]
    
    # Quick action buttons - positioned right before chat input
    if st.session_state.debug_mode:
        st.markdown("<div style='text-align: left; margin-left: 4%; padding: 15px;'>🛠️ Debug Quick Actions:</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: left; margin-left: 4%; padding: 15px;'>🎯 Quick Actions:</div>", unsafe_allow_html=True)
    
    # Create buttons for quick actions with better spacing
    if st.session_state.debug_mode:
        # Debug mode: use 2 centered rows of 3 columns each with left margin
        # First row
        col_margin1, col1, col2, col3 = st.columns([0.20, 0.32, 0.32, 0.32])
        # Second row  
        col_margin2, col4, col5, col6 = st.columns([0.20, 0.32, 0.32, 0.32])
        
        cols = [col1, col2, col3, col4, col5, col6]
        
        for i, (button_text, command_text) in enumerate(quick_actions):
            with cols[i]:
                if st.button(button_text, key=f"quick_action_{i}", help=f"Send: {command_text}"):
                    # Simulate sending the command
                    st.session_state.pending_command = command_text
                    st.rerun()
    else:
        # Normal mode: center the 2 buttons with left margin
        col1, col2, col3 = st.columns([0.32, 0.32, 0.32])
        
        # Place buttons in the middle columns
        with col2:
            if st.button(quick_actions[0][0], key="quick_action_0", help=f"Send: {quick_actions[0][1]}"):
                st.session_state.pending_command = quick_actions[0][1]
                st.rerun()
        
        with col3:
            if st.button(quick_actions[1][0], key="quick_action_1", help=f"Send: {quick_actions[1][1]}"):
                st.session_state.pending_command = quick_actions[1][1]
                st.rerun()
    
    # Chat input
    if prompt := st.chat_input("What do you want to do?"):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Generate response
        if st.session_state.game_loop:
            response = st.session_state.game_loop(prompt, st.session_state.chat_history)
            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": "Game loop not initialized. Please reload the world."})
        
        st.rerun()

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="IVIE - Text Adventure Generator",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stButton > button {
            width: 100%;
            margin-top: 1rem;
        }
        
        /* Quick action buttons styling */
        div[data-testid="column"] .stButton > button {
            font-size: 0.8rem;
            padding: 0.25rem 0.5rem;
            margin: 0.1rem;
            height: 2.5rem;
            width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            min-width: 0;
        }
        
        /* Selectbox styling for light mode */
        .stSelectbox > div > div {
            background-color: #f0f2f6;
            color: #262730;
        }
        
        /* Selectbox styling for dark mode */
        [data-theme="dark"] .stSelectbox > div > div,
        .stApp[data-theme="dark"] .stSelectbox > div > div,
        [data-baseweb="select"] > div {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #464646 !important;
        }
        
        /* Selectbox dropdown options for dark mode */
        [data-theme="dark"] .stSelectbox [role="listbox"],
        .stApp[data-theme="dark"] .stSelectbox [role="listbox"] {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Selectbox dropdown option items for dark mode */
        [data-theme="dark"] .stSelectbox [role="option"],
        .stApp[data-theme="dark"] .stSelectbox [role="option"] {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Selectbox dropdown option items hover for dark mode */
        [data-theme="dark"] .stSelectbox [role="option"]:hover,
        .stApp[data-theme="dark"] .stSelectbox [role="option"]:hover {
            background-color: #464646 !important;
            color: #fafafa !important;
        }
        
        /* Force text color for selectbox in dark mode */
        [data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div,
        .stApp[data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div {
            color: #fafafa !important;
        }
        
        /* Fix for the actual selected value display */
        [data-theme="dark"] .stSelectbox div[data-baseweb="select"] span,
        .stApp[data-theme="dark"] .stSelectbox div[data-baseweb="select"] span {
            color: #fafafa !important;
        }
        
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 2rem;
        }
        .assistant-message {
            background-color: #f5f5f5;
            margin-right: 2rem;
        }
        
        /* Chat message styling for dark mode */
        [data-theme="dark"] .user-message,
        .stApp[data-theme="dark"] .user-message {
            background-color: #1e3a8a;
            color: #fafafa;
        }
        [data-theme="dark"] .assistant-message,
        .stApp[data-theme="dark"] .assistant-message {
            background-color: #374151;
            color: #fafafa;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if st.session_state.generation_mode == 'inspiration':
        if not st.session_state.world_generated:
            render_inspiration_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'generate':
        if not st.session_state.world_generated:
            render_generate_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'preset':
        if not st.session_state.world_generated:
            render_preset_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'tutorial':
        if not st.session_state.world_generated:
            render_tutorial_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'replay':
        render_replay_mode()

if __name__ == "__main__":
    main()
