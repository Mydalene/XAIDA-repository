import pytest

from assistant.session_manager import (
    create_audit_session,
)

from assistant.stage_registry import (
    STAGE_REGISTRY,
)

# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def empty_session():

    session = create_audit_session()

    session.metadata[
        "workflow_stage"
    ] = "analysis"

    return session


REQUIRED_KEYS = [
    "aliases",
    "fields",
    "prompt_builder",
    "type",
    "navigation_title",
    "description",
]

def test_all_stages_have_required_keys():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        for key in REQUIRED_KEYS:

            assert key in config, (
                f"{stage} missing {key}"
            )

def test_prompt_builder_exists():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        if config["type"] == "workflow_stage":

            assert callable(
                config["prompt_builder"]
            )

def test_workflow_order_unique():

    orders = []

    for config in (
        STAGE_REGISTRY.values()
    ):

        if (
            config["type"]
            == "workflow_stage"
        ):

            orders.append(
                config["stage_order"]
            )

    assert len(
        orders
    ) == len(
        set(orders)
    )

# ============================================================
# tests/test_stage_registry.py
# ============================================================

import pytest

from assistant.stage_registry import (
    STAGE_REGISTRY,
)

# ============================================================
# REQUIRED REGISTRY FIELDS
# ============================================================

REQUIRED_KEYS = [
    "aliases",
    "fields",
    "type",
    "navigation_title",
    "description",
]

WORKFLOW_STAGE_KEYS = [
    "stage_order",
    "next_stage",
]

# ============================================================
# REGISTRY EXISTS
# ============================================================

def test_registry_exists():

    assert STAGE_REGISTRY

    assert isinstance(
        STAGE_REGISTRY,
        dict,
    )
    assert "initialization" in STAGE_REGISTRY
    assert "audit_completion" in STAGE_REGISTRY
    assert STAGE_REGISTRY["initialization"]["stage_order"] == 1


# ============================================================
# ALL STAGES HAVE REQUIRED FIELDS
# ============================================================

def test_all_stages_have_required_keys():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        for key in REQUIRED_KEYS:

            assert key in config, (
                f"{stage} missing '{key}'"
            )


# ============================================================
# VALID STAGE TYPES
# ============================================================

def test_stage_types_are_valid():

    valid_types = {
        "workflow_stage",
        "workflow_view",
        "evidence_tab",
    }

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        assert (
            config["type"]
            in valid_types
        ), (
            f"{stage} invalid type "
            f"{config['type']}"
        )


# ============================================================
# ALIASES
# ============================================================

def test_aliases_are_lists():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        aliases = config["aliases"]

        assert isinstance(
            aliases,
            list,
        )

        assert len(
            aliases
        ) > 0


def test_aliases_are_strings():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        for alias in (
            config["aliases"]
        ):

            assert isinstance(
                alias,
                str,
            )


# ============================================================
# FIELDS
# ============================================================

def test_fields_are_lists():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        fields = config["fields"]

        assert isinstance(
            fields,
            list,
        )


def test_fields_are_unique():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        fields = (
            config["fields"]
        )

        assert len(fields) == len(
            set(fields)
        ), (
            f"{stage} contains "
            "duplicate fields"
        )


# ============================================================
# WORKFLOW STAGES
# ============================================================

def test_workflow_stages_have_order():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        if (
            config["type"]
            != "workflow_stage"
        ):
            continue

        for key in (
            WORKFLOW_STAGE_KEYS
        ):

            assert key in config, (
                f"{stage} missing "
                f"{key}"
            )


def test_workflow_stage_order_unique():

    orders = []

    for config in (
        STAGE_REGISTRY.values()
    ):

        if (
            config["type"]
            == "workflow_stage"
        ):

            orders.append(
                config["stage_order"]
            )

    assert len(orders) == len(
        set(orders)
    )


# ============================================================
# WORKFLOW CHAIN
# ============================================================

def test_next_stage_exists():

    stage_names = set(
        STAGE_REGISTRY.keys()
    )

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        if (
            config["type"]
            != "workflow_stage"
        ):
            continue

        next_stage = config.get(
            "next_stage"
        )

        if next_stage is None:
            continue

        assert next_stage in (
            stage_names
        ), (
            f"{stage} references "
            f"unknown stage "
            f"{next_stage}"
        )


# ============================================================
# WORKFLOW ORDER
# ============================================================

def test_workflow_sequence():

    workflow_stages = sorted(
        [
            (
                name,
                config,
            )
            for (
                name,
                config,
            )
            in STAGE_REGISTRY.items()
            if (
                config["type"]
                == "workflow_stage"
            )
        ],
        key=lambda item:
            item[1]["stage_order"],
    )

    expected = [
        "initialization",
        "dataset",
        "data_preparation",
        "duplicate_review",
        "analysis",
        "explainability",
        "audit_review",
        "findings",
        "reporting",
        "audit_completion",
    ]

    actual = [
        stage
        for (
            stage,
            _,
        )
        in workflow_stages
    ]

    assert actual == expected


# ============================================================
# NAVIGATION
# ============================================================

def test_navigation_titles_exist():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        title = config[
            "navigation_title"
        ]

        assert isinstance(
            title,
            str,
        )

        assert title.strip()


# ============================================================
# DESCRIPTIONS
# ============================================================

def test_descriptions_exist():

    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        description = config[
            "description"
        ]

        assert isinstance(
            description,
            str,
        )

        assert description.strip()