# ============================================================
# XAIDA 4.0
# dataset/imputation_rules.py
# ============================================================

DEFAULT_IMPUTATION_RULES = {

    "numeric": {
        "strategy": "median"
    },

    "categorical": {
        "strategy": "mode"
    },

    "datetime": {
        "strategy": "retain"
    },

    "columns": {

        "PaidDate": {
            "strategy": "retain",
            "reason":
                "Business-valid null value",
        },

        "Amount": {
            "strategy": "median",
        },

        "Currency": {
            "strategy": "mode",
        },

        "Terms": {
            "strategy": "mode",
        },
    },
}
