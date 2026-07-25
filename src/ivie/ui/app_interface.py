"""Application interface management for IVIE.

This module handles the different UI modes and interfaces,
including inspiration mode, generate mode, and preset mode.
"""

import gradio as gr
import re
import os
from .ui_components import get_ui_texts
from ..core.world_generation import create_world_with_progress
from ..core.game_logic import create_game_loop
from ..llm.prompts import prompt_narrate_current_scene, prompt_describe_objective

def create_inspiration_interface(
        language,
        narrative_model,
        reasoning_model,
        reasoning_model_name,
        narrative_model_name,
        log_filename,
        visited_locations,
        enable_rag=True):
    """Create the inspiration mode interface."""
    texts = get_ui_texts(language)
    
    # Get API key for memory system
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Store world reference for game loop
    world_ref = {'world': None}
    game_loop_ref = {'game_loop': None}  # Store game loop to avoid recreating
    
    with gr.Blocks() as interfaz:
        with gr.Column(visible=True) as pre_game:
            gr.Markdown(texts['TITLE'])
            gr.Markdown(texts['PROMPT_LABEL'])
            inspo_input = gr.Textbox(label=texts['TEXTBOX_LABEL'])
            generar_btn = gr.Button(texts['GENERATE_WORLD'], elem_id="generar-btn")
            error_output = gr.Textbox(visible=False, label=texts['ERROR_LABEL'])
            progress_output = gr.Textbox(visible=False, label=texts['PROGRESS_LABEL'], lines=10, interactive=False)

        with gr.Column(visible=False) as main_game:
            chat = gr.Chatbot(
                height="85vh",
                bubble_full_width=False, 
                show_copy_button=False,
                type='messages'
            )
            textbox = gr.Textbox(placeholder=texts['TEXTBOX_PLACEHOLDER'], container=False, scale=5)

        def build_world_and_start(inspo):
            """Build world and start game with progress reporting."""
            try:
                print(f"[INFO] Generando mundo desde inspiración: '{inspo}'")
                
                # Use the world generation function with progress
                for result in create_world_with_progress(inspo, language, narrative_model, reasoning_model_name, narrative_model_name, log_filename, world_ref, game_loop_ref):
                    yield result
                    
            except Exception as e:
                print(f"[ERROR] {e}")
                yield (
                    gr.update(visible=True),         # pre_game visible (show error)
                    gr.update(visible=False),        # main_game hidden
                    [],                              # chat empty
                    gr.update(value=f"❌ Error generando el mundo: {str(e)}", visible=True),  # error visible
                    gr.update(value=texts['GENERATE_WORLD'], interactive=True),               # button enabled
                    gr.update(value="", visible=False)                                        # progress hidden
                )

        # Connect button to world generation
        generar_btn.click(
            fn=build_world_and_start,
            inputs=inspo_input,
            outputs=[pre_game, main_game, chat, error_output, generar_btn, progress_output]
        )

        def game_loop_wrapper(message, history):
            """Wrapper for game loop to handle chat interface."""
            if world_ref['world'] is None:
                return history + [{"role": "assistant", "content": "❌ Error: No world loaded"}], ""
                
            history.append({"role": "user", "content": message})
            
            # Create game loop only once, then reuse it
            if game_loop_ref['game_loop'] is None:
                game_loop_ref['game_loop'] = create_game_loop(
                    world_ref['world'], reasoning_model, narrative_model,
                    language, visited_locations, api_key, enable_rag, ""
                )
            
            respuesta = game_loop_ref['game_loop'](message, history)

            history.append({"role": "assistant", "content": respuesta})
            return history, ""

        textbox.submit(
            fn=game_loop_wrapper,
            inputs=[textbox, chat],
            outputs=[chat, textbox]
        )

    return interfaz

def create_standard_interface(world, starting_narration, language, reasoning_model, narrative_model, log_filename, visited_locations, enable_rag=True):
    """Create the standard game interface for preset/generate modes."""
    api_key = os.getenv("GEMINI_API_KEY")
    game_loop = create_game_loop(world, reasoning_model, narrative_model, language, visited_locations, api_key, enable_rag, "")
    
    return gr.ChatInterface(
        fn=game_loop,
        chatbot=gr.Chatbot(
            height="85vh",
            value=[{"role": "assistant", "content": starting_narration.replace("<", r"\<").replace(">", r"\>")}],
            bubble_full_width=False, 
            show_copy_button=False,
            type='messages',
        ),
        textbox=gr.Textbox(placeholder="What do you want to do?", container=False, scale=5),
        title="IVIE",
        theme="Soft",
        type='messages',
        autoscroll=True,
    )

def generate_starting_narration(world, language, narrative_model):
    """Generate the starting narration for a world."""
    system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
        world.render_world(language=language),
        previous_narrations=world.player.visited_locations[world.player.location.name],
        language=language, 
        starting_scene=True
    )
    starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
    world.player.visited_locations[world.player.location.name] += [starting_narration]
    
    # Add objective description
    if hasattr(world, 'objective') and world.objective:
        system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
        narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
        import re
        try:
            objective_texts = re.findall(r'#(.*?)#', narrated_objective, re.DOTALL)
            if objective_texts:
                objective_text = " ".join([t.strip() for t in objective_texts])
                # Clean up the objective text: remove extra periods and # symbols
                objective_text = objective_text.strip()
                if objective_text.endswith('#.'):
                    objective_text = objective_text[:-2]
                elif objective_text.endswith('.#'):
                    objective_text = objective_text[:-2]
                elif objective_text.endswith('#'):
                    objective_text = objective_text[:-1]
                
                # Ensure proper ending punctuation
                if not objective_text.endswith(('.', '!', '?')):
                    objective_text += '.'
                
                starting_narration += f"\n\n🎯 {objective_text}"
            else:
                raise IndexError
        except (IndexError, TypeError):
            print("⚠️ No se pudo extraer el objetivo narrado con el formato #...#, usando la respuesta completa.")
            # Clean up the raw objective response
            clean_objective = narrated_objective.strip()
            # Remove # symbols at the beginning and end
            clean_objective = re.sub(r'^#\s*', '', clean_objective)
            clean_objective = re.sub(r'\s*#\.?$', '', clean_objective)
            clean_objective = re.sub(r'\s*#$', '', clean_objective)
            
            if not clean_objective.strip().endswith(('.', '!', '?')):
                clean_objective += '.'
            starting_narration += f"\n\n🎯 {clean_objective}"
    else:
        print("ℹ️ No se encontró un objetivo principal en el mundo generado/cargado.")
    
    # Add formatted world state to starting narration
    world_state_formatted = world.format_world_state_for_chat(language=language)
    starting_narration += f"\n\n---\n{world_state_formatted}"
    
    return starting_narration
