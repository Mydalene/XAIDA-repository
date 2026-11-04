def generate_recommendations(
    session,
    vertex_ai_assistant,
):
    return vertex_ai_assistant.generate_finding_recommendations(session)