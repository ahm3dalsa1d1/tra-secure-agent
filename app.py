import gradio as gr

from graph import graph
from nodes import classify_request


# =========================================================
# CHAT LOGIC
# =========================================================

def handle_message(message, history):
    """
    Handles a normal message from the user.

    General question:
        -> Run normally.

    Sensitive question:
        -> Save the question.
        -> Open authentication popup.
        -> Do NOT access company data yet.
    """

    history = history or []

    # Ignore empty messages
    if not message or not message.strip():
        return (
            history,
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            None,
        )

    message = message.strip()

    # Add user's message to chat
    history = history + [
        {
            "role": "user",
            "content": message,
        }
    ]

    # -----------------------------------------------------
    # Check whether the request is sensitive
    # -----------------------------------------------------

    classification = classify_request(
        {
            "question": message
        }
    )

    is_sensitive = classification["sensitive"]

    # -----------------------------------------------------
    # Sensitive request
    # -----------------------------------------------------

    if is_sensitive:
        return (
            history,
            "",                         # clear message box
            gr.update(visible=True),    # show backdrop
            gr.update(visible=True),    # show login popup
            message,                    # save pending question
        )

    # -----------------------------------------------------
    # General request
    # -----------------------------------------------------

    result = graph.invoke(
        {
            "question": message
        }
    )

    history = history + [
        {
            "role": "assistant",
            "content": result["answer"],
        }
    ]

    return (
        history,
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        None,
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def authenticate_and_continue(
    username,
    password,
    pending_question,
    history,
):
    """
    Called when the user submits credentials.

    The original sensitive question is passed into LangGraph
    together with the username and password.
    """

    history = history or []

    if not pending_question:
        return (
            history,
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "",
            None,
        )

    # Run the real LangGraph flow
    result = graph.invoke(
        {
            "question": pending_question,
            "username": username,
            "password": password,
        }
    )

    # Add result to chat
    history = history + [
        {
            "role": "assistant",
            "content": result["answer"],
        }
    ]

    # Close popup and clear credentials
    return (
        history,
        gr.update(visible=False),
        gr.update(visible=False),
        "",
        "",
        None,
    )


# =========================================================
# CANCEL AUTHENTICATION
# =========================================================

def cancel_login(history):
    history = history or []

    history = history + [
        {
            "role": "assistant",
            "content": "Authentication cancelled.",
        }
    ]

    return (
        history,
        gr.update(visible=False),
        gr.update(visible=False),
        "",
        "",
        None,
    )


# =========================================================
# CSS
# =========================================================

css = """

/* -------------------------------------------------------
   Main application
------------------------------------------------------- */

.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
}


/* -------------------------------------------------------
   Dark background behind authentication popup
------------------------------------------------------- */

.modal-backdrop-inner {
    position: fixed;

    top: 0;
    left: 0;

    width: 100vw;
    height: 100vh;

    background: rgba(0, 0, 0, 0.60);

    backdrop-filter: blur(3px);

    z-index: 9998;
}


/* -------------------------------------------------------
   Authentication modal
------------------------------------------------------- */

#auth-modal {

    position: fixed !important;

    top: 50% !important;
    left: 50% !important;

    transform: translate(
        -50%,
        -50%
    ) !important;

    width: 450px !important;

    max-width:
        calc(100vw - 40px) !important;

    z-index: 9999 !important;

    padding: 28px !important;

    border-radius: 18px !important;

    border:
        1px solid
        rgba(255, 255, 255, 0.15) !important;

    background:
        rgba(30, 30, 34, 0.98) !important;

    box-shadow:
        0 20px 70px
        rgba(0, 0, 0, 0.65) !important;

    gap: 18px !important;
}


/* -------------------------------------------------------
   Popup heading
------------------------------------------------------- */

#auth-modal h2 {

    margin-top: 0 !important;

    margin-bottom: 8px !important;

}


/* -------------------------------------------------------
   Inputs
------------------------------------------------------- */

#auth-modal input {

    width: 100% !important;

    min-height: 45px !important;

}


/* -------------------------------------------------------
   Login button row
------------------------------------------------------- */

#auth-buttons {

    gap: 12px !important;

    margin-top: 10px !important;

}


/* -------------------------------------------------------
   Chat box
------------------------------------------------------- */

#main-chat {

    border-radius: 12px !important;

}
"""


# =========================================================
# GRADIO UI
# =========================================================

with gr.Blocks(
    title="TRA Secure Bot"
) as demo:

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    # Stores the sensitive question while waiting
    # for authentication.
    pending_question = gr.State(None)

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    gr.Markdown(
        """
# TRA Secure Bot

Ask general questions normally.

Protected company information requires authentication.
"""
    )

    # -----------------------------------------------------
    # Chat
    # -----------------------------------------------------

    chatbot = gr.Chatbot(
    height=520,
    elem_id="main-chat",
    placeholder="Ask me something...",
    )
    # -----------------------------------------------------
    # Message input
    # -----------------------------------------------------

    with gr.Row():

        message_box = gr.Textbox(
            placeholder="Type your message...",
            show_label=False,
            lines=1,
            scale=8,
        )

        send_button = gr.Button(
            "Send",
            variant="primary",
            scale=1,
        )

    # =====================================================
    # MODAL BACKDROP
    # =====================================================

    backdrop = gr.HTML(
        """
        <div class="modal-backdrop-inner"></div>
        """,
        visible=False,
    )

    # =====================================================
    # AUTHENTICATION POPUP
    # =====================================================

    with gr.Column(
        visible=False,
        elem_id="auth-modal",
    ) as auth_popup:

        gr.Markdown(
            """
## 🔐 Authentication Required

This request requires access to protected company information.

Please enter your credentials to continue.
"""
        )

        username = gr.Textbox(
            label="Username",
            placeholder="Enter your username",
            lines=1,
        )

        password = gr.Textbox(
            label="Password",
            placeholder="Enter your password",
            type="password",
            lines=1,
        )

        with gr.Row(
            elem_id="auth-buttons"
        ):

            login_button = gr.Button(
                "Login",
                variant="primary",
            )

            cancel_button = gr.Button(
                "Cancel",
                variant="secondary",
            )

    # =====================================================
    # EVENTS
    # =====================================================

    # -----------------------------------------------------
    # Send button
    # -----------------------------------------------------

    send_button.click(
        fn=handle_message,
        inputs=[
            message_box,
            chatbot,
        ],
        outputs=[
            chatbot,
            message_box,
            backdrop,
            auth_popup,
            pending_question,
        ],
    )

    # -----------------------------------------------------
    # Press Enter in message box
    # -----------------------------------------------------

    message_box.submit(
        fn=handle_message,
        inputs=[
            message_box,
            chatbot,
        ],
        outputs=[
            chatbot,
            message_box,
            backdrop,
            auth_popup,
            pending_question,
        ],
    )

    # -----------------------------------------------------
    # Login button
    # -----------------------------------------------------

    login_button.click(
        fn=authenticate_and_continue,
        inputs=[
            username,
            password,
            pending_question,
            chatbot,
        ],
        outputs=[
            chatbot,
            backdrop,
            auth_popup,
            username,
            password,
            pending_question,
        ],
    )

    # -----------------------------------------------------
    # Press Enter while inside password box
    # -----------------------------------------------------

    password.submit(
        fn=authenticate_and_continue,
        inputs=[
            username,
            password,
            pending_question,
            chatbot,
        ],
        outputs=[
            chatbot,
            backdrop,
            auth_popup,
            username,
            password,
            pending_question,
        ],
    )

    # -----------------------------------------------------
    # Cancel button
    # -----------------------------------------------------

    cancel_button.click(
        fn=cancel_login,
        inputs=[
            chatbot,
        ],
        outputs=[
            chatbot,
            backdrop,
            auth_popup,
            username,
            password,
            pending_question,
        ],
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    demo.queue().launch(
        css=css
    )