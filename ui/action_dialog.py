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
    if not pending or pending.get("mode") != "confirmation":
        return

    st.subheader(pending["title"])
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


def render_action_dialog(on_confirm):
    if ACTION_DIALOG_KEY in st.session_state:
        _action_dialog(on_confirm)


def render_action_notification(recommendation=None, warning=None):
    pending = st.session_state.get(ACTION_DIALOG_KEY)
    if pending and pending.get("mode") == "message":
        level = pending.get("level", "info")
        icon = {
            "info": ":material/info:",
            "success": ":material/check_circle:",
            "warning": ":material/warning:",
            "error": ":material/error:",
        }.get(level, ":material/info:")
        st.toast(
            f"**{pending['title']}**\n\n{pending['message']}",
            icon=icon,
            duration="long",
        )
        st.session_state.pop(ACTION_DIALOG_KEY, None)

    if warning:
        title = "Recommendation unavailable"
        message = warning
        level = "warning"
    elif recommendation:
        title = "XAIDA Recommendation"
        message = recommendation
        level = "info"
    else:
        return

    styles = {
        "info": ("blue", ":material/lightbulb:"),
        "success": ("green", ":material/check_circle:"),
        "warning": ("orange", ":material/warning:"),
        "error": ("red", ":material/error:"),
    }
    color, icon = styles.get(level, styles["info"])

    with st.container(border=True, key="xaida_notification_box"):
        st.badge(title, icon=icon, color=color)
        st.text(message)
