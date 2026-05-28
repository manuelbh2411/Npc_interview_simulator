from app.prompts import build_system_prompt


def test_personality_prompts_have_distinct_interviewer_identities() -> None:
    amable = build_system_prompt("Ingeniería", "Amable")
    agresivo = build_system_prompt("Ingeniería", "Agresivo")
    tecnico = build_system_prompt("Ingeniería", "Técnico")
    rrhh = build_system_prompt("Ingeniería", "RRHH")
    startup = build_system_prompt("Ingeniería", "Startup informal")

    assert "entrevistadora amable" in amable
    assert "entrevistadora de presion" in agresivo
    assert "entrevistadora tecnica" in tecnico
    assert "Recursos Humanos" in rrhh
    assert "entrevistadora de startup" in startup
    assert "Eres Carolina" in amable


def test_personality_prompts_include_style_examples() -> None:
    prompt = build_system_prompt("Marketing", "Startup informal")

    assert "vamos al barro" in prompt
    assert "sin humo" in prompt
    assert "aterrizamelo" in prompt
