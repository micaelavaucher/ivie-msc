from src.ivie.llm.prompts import PROMPT_STEP_3_DETAILS, PROMPT_STEP_4_PUZZLES, prompt_world_update_structured


def test_step_3_details_mentions_recruitment_fields_in_both_languages():
    for language in ("es", "en"):
        text = PROMPT_STEP_3_DETAILS(
            skeleton_data="", title="T", backstory="B", player_concept="P", main_objective="M", language=language,
        )
        assert "recruitable" in text
        assert "initial_feeling" in text
        assert "npc_relationships" in text


def test_step_4_puzzles_mentions_recruit_character_reward_in_both_languages():
    for language in ("es", "en"):
        text = PROMPT_STEP_4_PUZZLES(world_data="{}", language=language)
        assert "RecruitCharacterReward" in text


def test_world_update_prompt_instructs_narrator_about_social_reactions():
    system_msg_es, _, _ = prompt_world_update_structured(world_state="state", input="do something", language='es')
    system_msg_en, _, _ = prompt_world_update_structured(world_state="state", input="do something", language='en')
    assert "REACCIONES SOCIALES" in system_msg_es
    assert "NPC SOCIAL REACTIONS" in system_msg_en
