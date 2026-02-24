Career Assistant AI Agent
An autonomous AI agent that monitors incoming employer messages and automatically drafts, evaluates, and logs professional email responses — powered by OpenAI GPT-4o-mini, orchestrated with FastAPI, and connected to Telegram for real-time notifications.

What It Does
When a recruiter or employer sends a message, the agent:

Detects whether the message requires human involvement (salary negotiation, legal terms, out-of-domain questions)
Generates a professional, context-aware email reply using your CV profile
Evaluates the reply across 5 quality dimensions and rewrites it if the score is below the threshold
Notifies you in real time via Telegram at every stage
Logs every interaction to a local JSON file for audit and review
