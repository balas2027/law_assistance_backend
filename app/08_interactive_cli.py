"""
Legacy interactive CLI entrypoint.

AI retrieval and generation business logic now lives in modular backend components:
- app.ai.embeddings
- app.ai.vector_store
- app.ai.retrievers.*
- app.ai.prompts.chat_prompt
- app.ai.llm_client
- app.services.chat_service

Primary external interface: POST /api/v1/chat
"""


def main() -> None:
    raise SystemExit(
        "Interactive CLI has been deprecated in backend runtime. "
        "Use FastAPI endpoint POST /api/v1/chat instead."
    )


if __name__ == "__main__":
    main()
