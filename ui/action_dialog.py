import streamlit as st

ACTION_DIALOG_KEY = "xaida_action_dialog"


def queue_action_message(title, message, level="info"):
    st.session_state[ACTION_DIALOG_KEY] = {
        "mode": "message",
        "title": title,
        "message": message,
        "level": level,
    }


def queue_action_confirmation(
    title,
    message,
    confirm_label,
    action,
    success_message,
):
    st.session_state[ACTION_DIALOG_KEY] = {
        "mode": "confirmation",
        "title": title,
        "message": message,
        "confirm_label": confirm_label,
        "action": action,
        "success_message": success_message,
    }


@st.dialog("XAIDA", width="small", dismissible=False)
def _action_dialog(on_confirm):
    pending = st.session_state.get(ACTION_DIALOG_KEY)
    if not pending:
        return

    st.subheader(pending["title"])
    if pending["mode"] == "confirmation":
        st.warning(pending["message"], icon=":material/warning:")
        confirm_column, cancel_column = st.columns(2)
        with confirm_column:
            if st.button(
                pending["confirm_label"],
                type="primary",
                width="stretch",
                key="xaida_action_dialog_confirm",
            ):
                result = on_confirm(pending)
                queue_action_message(
                    result["title"],
                    result["message"],
                    result["level"],
                )
                st.rerun()
        with cancel_column:
            if st.button(
                "Cancel",
                width="stretch",
                key="xaida_action_dialog_cancel",
            ):
                st.session_state.pop(ACTION_DIALOG_KEY, None)
                st.rerun()
        return

    getattr(st, pending["level"])(
        pending["message"],
        icon={
            "success": ":material/check_circle:",
            "warning": ":material/warning:",
            "error": ":material/error:",
        }.get(pending["level"]),
    )
    if st.button(
        "Close",
        type="primary",
        width="content",
        key="xaida_action_dialog_close",
    ):
        st.session_state.pop(ACTION_DIALOG_KEY, None)
        st.rerun()


def render_action_dialog(on_confirm):
    if ACTION_DIALOG_KEY in st.session_state:
        _action_dialog(on_confirm)
