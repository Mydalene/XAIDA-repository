# ============================================================
# XAIDA 4.0
# findings/observation_manager.py
# ============================================================

def generate_audit_observations(
    flagged_count,
    anomaly_rate,
    high_risk_count,
    risk_level,
    top_drivers,
):
    observations = []

    observations.append(
        f"""
XAIDA identified {flagged_count:,}
anomalous transactions representing
{anomaly_rate:.2f}% of the analysed
population.
"""
    )

    if high_risk_count > 0:
        observations.append(
            f"""
{high_risk_count:,} transactions were
classified as high-risk exceptions and
exceeded the configured anomaly threshold.
"""
        )

    if top_drivers:
        observations.append(
            f"""
The most influential risk drivers were
{', '.join(top_drivers[:3])}.

These attributes consistently contributed
to elevated anomaly scores across the
flagged population.
"""
        )

    if risk_level in [
        "High",
        "Critical",
    ]:
        observations.append(
            """
The overall anomaly profile indicates
heightened audit risk and suggests a need
for enhanced evaluation of related
transactions and controls.
"""
        )

    return observations