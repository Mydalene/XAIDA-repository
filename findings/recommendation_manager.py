def generate_recommendations(
    session,
    copilot,
):
    return copilot.generate_finding_recommendations(session)