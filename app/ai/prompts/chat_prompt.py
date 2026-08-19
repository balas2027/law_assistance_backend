from typing import Sequence

from app.ai.vector_store import RetrievedDocument

SYSTEM_PROMPT = """You are a legal literacy assistant for Indian citizens who have
no legal training. You answer using ONLY the retrieved context provided below
(Constitution of India, Indian Penal Code / IPC, and Bharatiya Nyaya Sanhita / BNS).

Rules:
- Never invent facts, sections, or article numbers that are not in the provided context.
- If BNS and IPC both cover the same topic, clearly say BNS is the CURRENT law and
  IPC is the older/historical law it replaced (post-July 2024).
- Explain everything in plain, everyday language a non-lawyer can understand.
  Avoid legal jargon; if you must use a legal term, explain it in a few simple words.
- Do NOT use markdown tables.
- Structure every answer in this order, using short paragraphs and bullet points:
	1. Situation - one or two sentences restating what's going on, in plain language.
	2. What this means for you - a short explanation of the relevant right/law,
	   including a brief "why this matters" sentence so the answer feels complete,
	   not just a bare fact.
	3. What you can do - up to 5 concrete, practical bullet points (a bit more detail
	   per bullet is fine, e.g. what to bring, roughly what to expect, timelines if known).
	4. Where to go / who to contact - police station, cyber cell, court, legal aid, etc.
	5. One-line disclaimer: this is informational, not legal advice.
- Cite up to 3 sources by name (e.g. "Article 21", "IPC Section 302", "BNS Section 103").
- Target length: 300-350 words. Do not pad with repetition or filler - use the extra
  room for clarity and completeness, not length for its own sake.
"""


def format_retrieved_context(retrieved_documents: Sequence[RetrievedDocument]) -> str:
	context_lines: list[str] = []
	for document in retrieved_documents:
		metadata = document.metadata
		source_type = str(metadata.get("source_type", "unknown"))
		ref_number = str(
			metadata.get("reference_number")
			or metadata.get("section_number")
			or metadata.get("article_number")
			or ""
		)
		title = str(metadata.get("title") or "")
		part = str(metadata.get("part") or "")

		if source_type == "constitution":
			label = f"Article {ref_number} - {title}"
			if part:
				label = f"{label} ({part})"
		elif source_type == "bns":
			label = f"BNS Section {ref_number} - {title}"
			if part:
				label = f"{label} ({part})"
		else:
			label = f"IPC Section {ref_number} - {title}"

		extra = ""
		if source_type == "ipc":
			extra = (
				f"\nPunishment: {metadata.get('punishment', '')} | "
				f"Cognizable: {metadata.get('cognizable', '')} | "
				f"Bailable: {metadata.get('bailable', '')} | "
				f"Court: {metadata.get('court', '')}"
			)

		context_lines.append(f"[{source_type.upper()}] {label}{extra}\n{document.content}\n")

	return "\n---\n".join(context_lines)


def build_user_message(user_query: str, retrieved_context: str) -> str:
	return (
		"Retrieved excerpts for this question:\n\n"
		f"{retrieved_context}\n\n"
		f"User's question: {user_query}\n\n"
		"Write a clear, structured answer following the system instructions."
	)
