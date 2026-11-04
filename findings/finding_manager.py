# ============================================================
# XAIDA 4.0
# findings/finding_manager.py
# ============================================================


def generate_executive_summary(
        total_transactions,
        flagged_count,
        anomaly_rate,
        risk_level,
    ):
        """
    Generates the executive summary section.
        """

        return f"""
    XAIDA analysed {total_transactions:,}
    transactions and identified
    {flagged_count:,} anomalous transactions.

    The anomaly rate was
    {anomaly_rate:.2f}%.

    Based on the distribution,
    severity, and frequency of
    identified anomalies, the
    overall population risk level
    was assessed as {risk_level}.
        """

def generate_anomaly_findings(
        flagged_count,
        high_risk_count,
        risk_level,
    ):
        """
    Generates anomaly findings.
        """

        return f"""
    Anomaly detection procedures identified
    {flagged_count:,} transactions exhibiting
    risk characteristics that deviated from
    the expected population behaviour.

    Of these transactions,
    {high_risk_count:,} were assessed as
    high-risk exceptions based on the model's
    risk scoring framework and exceeded the
    configured anomaly threshold.

    The observed anomalies represent potential
    exceptions requiring additional audit
    attention.

    While anomalous behaviour does not
    automatically indicate control failure,
    fraud, or error, the identified records
    demonstrate characteristics sufficiently
    unusual to warrant further investigation.

    Based on the volume, distribution, and
    severity of detected anomalies, the
    population has been assessed as
    {risk_level.upper()} risk.
        """


def generate_explainability_findings(
        top_drivers,
    ):
        """
    Generates explainability findings.
        """

        if not top_drivers:
            return ""

        drivers_text = "\n• ".join(
        top_drivers
        )

        return f"""
    SHAP explainability analysis was performed
    to determine which transaction attributes
    contributed most significantly to anomaly
    classification.

    The analysis identified the following key
    drivers of anomalous behaviour:

    • {drivers_text}

    These attributes consistently exerted the
    greatest influence on anomaly scores and
    therefore represent the primary factors
    distinguishing flagged transactions from
    the normal population.

    The explainability results suggest that
    unusual patterns associated with these
    attributes were the most significant
    contributors to elevated transaction risk.

    Auditors should consider these drivers when
    performing detailed testing, root-cause
    analysis, and evaluation of related control
    activities.
    """