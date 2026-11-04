# ============================================================
# XAIDA 4.0
# assistant/conversation_manager.py
# ============================================================

MAX_CONVERSATION_MESSAGES = 20


class ConversationManager:

    def add_user_message(
        self,
        session,
        message,
    ):

        session.conversation.append(
            {
                "role": "user",
                "content": message,
            }
            
        )

        self.trim_history(
        session
        )

    def add_assistant_message(
        self,
        session,
        message,
    ):

        session.conversation.append(
            {
                "role": "assistant",
                "content": message,
            }
        )

        self.trim_history(
        session
        )

    def get_history(
        self,
        session,
    ):
        return session.conversation

    def get_recent_history(
        self,
        session,
        max_messages=MAX_CONVERSATION_MESSAGES,
    ):

        return [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in session.conversation[-max_messages:]
        ]

    def clear_history(
        self,
        session,
    ):

        session.conversation = []

    def count_messages(
        self,
        session,
    ):

        return len(
            session.conversation
        )

    def trim_history(
        self,
        session,
        max_messages=MAX_CONVERSATION_MESSAGES,
    ):

        if len(session.conversation) > max_messages:

            session.conversation = (
                session.conversation[
                    -max_messages:
                ]
            )

    def add_message(
        self,
        session,
        role,
        content,
    ):

        session.conversation.append(
            {
                "role": role,
                "content": content,
            }
        )

        self.trim_history(
        session
        )

conversation_manager = (
    ConversationManager()
)

def add_user_message(
    session,
    message,
):

    conversation_manager.add_user_message(
        session,
        message,
    )

def add_assistant_message(
    session,
    message,
):

    conversation_manager.add_assistant_message(
        session,
        message,
    )

def get_history(
    session,
):
    return (
        conversation_manager
        .get_history(session)
    )

def get_recent_history(
    session,
):

    return (
        conversation_manager
        .get_recent_history(session)
    )

def get_feedback_exchange(session, interaction_id):
    for index, message in enumerate(session.conversation):
        if (
            message.get("role") == "assistant"
            and message.get("interaction_id") == interaction_id
        ):
            user_message = next(
                (
                    previous
                    for previous in reversed(session.conversation[:index])
                    if previous.get("role") == "user"
                ),
                None,
            )
            if user_message is None:
                return None
            return {
                "user_message": user_message.get("content"),
                "assistant_response": message.get("content"),
            }
    return None

def clear_conversation(
    session,
):
    conversation_manager.clear_history(
        session
    )

def count_messages(
    session,
):
    return (
        conversation_manager
        .count_messages(session)
    )