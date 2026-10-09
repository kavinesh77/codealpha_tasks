from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)


# ============================================================
# CHATBOT RESPONSE ENGINE
# ============================================================

def get_response(message):
    message = message.lower().strip()

    # Greetings
    if re.search(
        r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b",
        message
    ):
        return "Hello! 👋 I'm your AI assistant. How can I help you today?"

    # How are you
    if "how are you" in message:
        return "I'm doing great! Thanks for asking. How can I assist you?"

    # About chatbot
    if "who are you" in message or "what are you" in message:
        return (
            "I'm an AI-powered website chatbot designed to answer "
            "common user questions instantly."
        )

    # Services
    if any(word in message for word in [
        "service", "services", "offer", "provide"
    ]):
        return (
            "We provide AI, Data Science, software development, "
            "and digital technology solutions."
        )

    # Artificial Intelligence
    if re.search(r"\b(ai|artificial intelligence)\b", message):
        return (
            "Artificial Intelligence (AI) enables computers to perform "
            "tasks that normally require human intelligence, such as "
            "understanding language and recognizing patterns."
        )

    # Machine Learning
    if "machine learning" in message:
        return (
            "Machine Learning is a branch of AI where computers learn "
            "patterns from data and use them to make predictions or decisions."
        )

    # Data Science
    if "data science" in message or "data scientist" in message:
        return (
            "Data Science combines statistics, programming, and machine "
            "learning to extract useful insights from data."
        )

    # Python
    if "python" in message:
        return (
            "Python is a popular programming language used for web "
            "development, automation, data science, and AI."
        )

    # Working hours
    if any(word in message for word in [
        "hours", "timing", "open", "working time"
    ]):
        return (
            "Our working hours are Monday to Friday, "
            "9:00 AM to 6:00 PM."
        )

    # Contact
    if any(word in message for word in [
        "contact", "email", "phone", "reach"
    ]):
        return (
            "You can contact our support team at "
            "support@example.com."
        )

    # Location
    if any(word in message for word in [
        "location", "where are you", "address"
    ]):
        return (
            "We operate online and provide services to users "
            "through our website."
        )

    # Pricing
    if any(word in message for word in [
        "price", "pricing", "cost", "fee"
    ]):
        return (
            "Our pricing depends on the service required. "
            "Please contact our support team for detailed pricing."
        )

    # Help
    if any(word in message for word in [
        "help", "support"
    ]):
        return (
            "Sure! I can help with services, AI, Machine Learning, "
            "Data Science, Python, pricing, working hours, "
            "and contact information."
        )

    # Thank you
    if any(word in message for word in [
        "thank you", "thanks", "thank"
    ]):
        return "You're welcome! 😊 I'm happy to help."

    # Goodbye
    if re.search(r"\b(bye|goodbye|see you)\b", message):
        return "Goodbye! 👋 Have a great day!"

    # Default response
    return (
        "I'm sorry, I didn't understand that. "
        "Try asking about our services, AI, Machine Learning, "
        "Data Science, Python, pricing, working hours, "
        "or contact information."
    )


# ============================================================
# CHATBOT WEBSITE
# ============================================================

HTML = """
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>AI Website Chatbot</title>

    <style>

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        body {
            min-height: 100vh;
            background: linear-gradient(
                135deg,
                #0f172a,
                #1e293b
            );

            display: flex;
            justify-content: center;
            align-items: center;

            padding: 20px;
        }

        .chat-container {

            width: 100%;
            max-width: 650px;
            height: 720px;

            background: white;

            border-radius: 20px;

            overflow: hidden;

            box-shadow:
                0 20px 50px rgba(0, 0, 0, 0.35);

            display: flex;
            flex-direction: column;
        }

        .header {

            background: #2563eb;

            color: white;

            padding: 24px;

            text-align: center;
        }

        .header h1 {

            font-size: 25px;

            margin-bottom: 7px;
        }

        .header p {

            font-size: 14px;

            opacity: 0.9;
        }

        .status {

            margin-top: 10px;

            font-size: 13px;
        }

        .status span {

            display: inline-block;

            width: 9px;
            height: 9px;

            background: #22c55e;

            border-radius: 50%;

            margin-right: 5px;
        }

        .chat-box {

            flex: 1;

            padding: 20px;

            overflow-y: auto;

            background: #f8fafc;
        }

        .message {

            display: flex;

            margin-bottom: 15px;
        }

        .message.user {

            justify-content: flex-end;
        }

        .bubble {

            max-width: 75%;

            padding: 12px 16px;

            border-radius: 16px;

            line-height: 1.5;

            font-size: 15px;
        }

        .bot .bubble {

            background: #e2e8f0;

            color: #0f172a;

            border-bottom-left-radius: 4px;
        }

        .user .bubble {

            background: #2563eb;

            color: white;

            border-bottom-right-radius: 4px;
        }

        .input-area {

            padding: 15px;

            background: white;

            border-top: 1px solid #e2e8f0;

            display: flex;

            gap: 10px;
        }

        #messageInput {

            flex: 1;

            padding: 14px;

            border: 1px solid #cbd5e1;

            border-radius: 12px;

            outline: none;

            font-size: 15px;
        }

        #messageInput:focus {

            border-color: #2563eb;
        }

        button {

            border: none;

            cursor: pointer;
        }

        #sendButton {

            background: #2563eb;

            color: white;

            padding: 0 22px;

            border-radius: 12px;

            font-weight: bold;
        }

        #sendButton:hover {

            background: #1d4ed8;
        }

        .bottom-buttons {

            display: flex;

            gap: 10px;

            padding: 0 15px 15px;

            background: white;
        }

        .bottom-buttons button {

            flex: 1;

            padding: 10px;

            border-radius: 10px;

            background: #e2e8f0;

            color: #334155;
        }

        .bottom-buttons button:hover {

            background: #cbd5e1;
        }

        @media (max-width: 600px) {

            .chat-container {

                height: 90vh;
            }

            .bubble {

                max-width: 85%;
            }

            .bottom-buttons {

                flex-wrap: wrap;
            }

            .bottom-buttons button {

                min-width: 40%;
            }
        }

    </style>

</head>


<body>


<div class="chat-container">


    <!-- HEADER -->

    <div class="header">

        <h1>🤖 AI Website Chatbot</h1>

        <p>
            Instant assistance for your questions
        </p>

        <div class="status">

            <span></span>

            Online

        </div>

    </div>


    <!-- CHAT AREA -->

    <div class="chat-box" id="chatBox">

        <div class="message bot">

            <div class="bubble">

                Hello! 👋 I'm your AI assistant.

                <br><br>

                Ask me about:

                <br>

                • Services
                <br>
                • Artificial Intelligence
                <br>
                • Machine Learning
                <br>
                • Data Science
                <br>
                • Python
                <br>
                • Pricing
                <br>
                • Working hours
                <br>
                • Contact information

            </div>

        </div>

    </div>


    <!-- INPUT -->

    <div class="input-area">

        <input
            type="text"
            id="messageInput"
            placeholder="Type your message..."
            autocomplete="off"
        >

        <button
            id="sendButton"
            onclick="sendMessage()"
        >
            Send
        </button>

    </div>


    <!-- QUICK BUTTONS -->

    <div class="bottom-buttons">

        <button
            onclick="quickMessage('What services do you provide?')"
        >
            Services
        </button>

        <button
            onclick="quickMessage('What are your working hours?')"
        >
            Working Hours
        </button>

        <button
            onclick="quickMessage('How can I contact you?')"
        >
            Contact
        </button>

        <button
            onclick="clearChat()"
        >
            Clear
        </button>

    </div>


</div>


<script>

    const input =
        document.getElementById("messageInput");

    const chatBox =
        document.getElementById("chatBox");


    // Send message when Enter is pressed

    input.addEventListener(
        "keypress",
        function(event) {

            if (event.key === "Enter") {

                sendMessage();

            }

        }
    );


    // Add message to chat

    function addMessage(text, sender) {

        const message =
            document.createElement("div");

        message.className =
            "message " + sender;


        const bubble =
            document.createElement("div");

        bubble.className = "bubble";


        // Use textContent for safe rendering

        bubble.textContent = text;


        message.appendChild(bubble);

        chatBox.appendChild(message);


        chatBox.scrollTop =
            chatBox.scrollHeight;
    }


    // Send message to Flask

    function sendMessage() {

        const message =
            input.value.trim();


        if (!message) {

            return;

        }


        // Display user message

        addMessage(
            message,
            "user"
        );


        input.value = "";


        // Send request to Flask

        fetch(
            "/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        )

        .then(
            response => response.json()
        )

        .then(
            data => {

                setTimeout(
                    function() {

                        addMessage(
                            data.response,
                            "bot"
                        );

                    },
                    300
                );

            }
        )

        .catch(
            error => {

                addMessage(
                    "Sorry, something went wrong. Please try again.",
                    "bot"
                );

                console.error(error);

            }
        );
    }


    // Quick message buttons

    function quickMessage(message) {

        input.value = message;

        sendMessage();

    }


    // Clear chat

    function clearChat() {

        chatBox.innerHTML = `

            <div class="message bot">

                <div class="bubble">

                    Chat cleared. 👋
                    How can I help you?

                </div>

            </div>

        `;

    }

</script>


</body>

</html>
"""


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    message = data.get("message", "")

    response = get_response(message)

    return jsonify({
        "response": response
    })


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print("CODEALPHA TASK 4 - AI WEBSITE CHATBOT")

    print("=" * 60)

    print("Status: READY")

    print("Open: http://127.0.0.1:5001")

    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )