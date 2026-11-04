# ===================================
# XAIDA PLATFORM PROFILE
# ===================================

def build_platform_context(
):
    return {

        "platform_name":
            "XAIDA",

        "platform_description":
        """
        XAIDA is an AI-first audit analytics assistant, powered by Vertex AI,
        designed to support auditors through:

        • Data Preparation
        • Duplicate Review
        • Analysis
        • Explainability
        • Findings
        • Reporting
        """,

        "platform_purpose":
        """
        XAIDA assists auditors in interpreting
        audit evidence, anomaly detection
        results, explainability outputs and
        audit findings.

        Audit decisions remain the
        responsibility of the auditor.
        """,

        "platform_retention":
        """
        Analysis results remain available
        within the current audit session and
        saved audit artifacts.

        XAIDA does not independently retain
        data outside configured audit storage.
        """,

        "platform_security":
        """
        Security controls depend on the
        deployment environment and system
        configuration.

        Refer to system administration
        documentation for authoritative
        security controls.
        """,

        "platform_sample_data":
        """
        Sample datasets availability depends
        on local XAIDA deployment
        configuration.
        """,
    }