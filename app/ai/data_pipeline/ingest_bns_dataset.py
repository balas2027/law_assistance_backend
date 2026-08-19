"""
Ingestion pipeline for bns_all_section.json (Bharatiya Nyaya Sanhita, 2023).

Issues found and fixed:
- `body` always has a redundant "Section N - " prefix (stripped)
- `title` is USUALLY a truncated (~250 char) duplicate of body's opening -
  in most cases body is the complete, authoritative text
- BUT 15 sections have it backwards: `body` itself got truncated by the
  scraper (e.g. Section 3's body is just "Section 3 - General", 7 chars of
  real content) while `title` happens to hold the fuller text for those
  specific sections
- 11 sections have a `title` that's truncated mid-word with no sentence-
  ending period at all, so a short display title can't be reliably
  extracted from title alone for those

Strategy: for each section, treat whichever of (title, body-after-prefix)
is LONGER as the authoritative full text (since the shorter one is almost
always the truncated duplicate). Derive a clean short title separately.
"""
import json
import re

INPUT_PATH = "bns_all_section.json"
OUTPUT_PATH = "bns_chunks.json"
MAX_CHUNK_CHARS = 1800

SECTION_PREFIX_PATTERN = re.compile(r"^Section\s+\d+[A-Z]?\s*[\u2013\-]\s*")


def strip_section_prefix(text):
    return SECTION_PREFIX_PATTERN.sub("", text).strip()


def extract_short_title(full_text, fallback_chars=70):
    """First sentence if there's a period within a reasonable range,
    otherwise just take a safe character prefix as a fallback label."""
    period_idx = full_text.find(".")
    if 3 <= period_idx <= 150:
        return full_text[:period_idx].strip()
    return full_text[:fallback_chars].strip().rstrip(",;") + ("..." if len(full_text) > fallback_chars else "")


def build_full_text(entry):
    title = entry["title"].strip()
    body_clean = strip_section_prefix(entry["body"])

    # pick whichever is longer as the authoritative content - the shorter
    # one is almost always the truncated duplicate (see docstring)
    primary = body_clean if len(body_clean) >= len(title) else title

    explanations = entry.get("explanations") or []
    illustrations = entry.get("illustrations") or []

    parts = [primary]
    if explanations:
        parts.append("Explanation(s): " + " | ".join(e.strip() for e in explanations if e.strip()))
    if illustrations:
        parts.append("Illustration(s): " + " | ".join(i.strip() for i in illustrations if i.strip()))

    return "\n\n".join(parts)


def split_long_text(text, max_chars=MAX_CHUNK_CHARS):
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    groups, current, current_len = [], [], 0
    for p in paragraphs:
        p_len = len(p) + 2
        if current and current_len + p_len > max_chars:
            groups.append("\n\n".join(current))
            current, current_len = [p], p_len
        else:
            current.append(p)
            current_len += p_len
    if current:
        groups.append("\n\n".join(current))
    return groups if groups else [text]


def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} BNS sections")

    chunks = []
    for entry in data:
        section_no = str(entry["section_no"])
        full_text = build_full_text(entry)
        short_title = extract_short_title(full_text)

        text_parts = split_long_text(full_text)
        for i, part_text in enumerate(text_parts):
            chunk_id = f"bns_{section_no}" if len(text_parts) == 1 else f"bns_{section_no}_part{i+1}"
            chunk = {
                "chunk_id": chunk_id,
                "section_number": section_no,
                "chapter": entry.get("chapter", ""),
                "title": short_title,
                "text": part_text,
                "chunk_index": i,
                "chunk_total": len(text_parts),
            }
            chunk["embedding_text"] = f"BNS Section {section_no} - {short_title}. {part_text}"
            chunks.append(chunk)

    # validation
    errors = []
    ids = [c["chunk_id"] for c in chunks]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate chunk_id found!")
    empty = [c["chunk_id"] for c in chunks if not c["text"].strip() or not c["title"].strip()]
    if empty:
        errors.append(f"Empty text/title in: {empty}")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(" -", e)
        return

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nValidation passed.")
    print(f"Total BNS chunks: {len(chunks)}")
    print(f"Saved -> {OUTPUT_PATH}")
    print()
    print("Sample - Section 3 (the truncated-body edge case):")
    sample = [c for c in chunks if c["section_number"] == "3"]
    for c in sample:
        print(json.dumps(c, indent=2, ensure_ascii=False)[:500])
    print()
    print("Sample - Section 302-equivalent check (murder is BNS Section 103):")
    sample2 = [c for c in chunks if c["section_number"] == "103"]
    for c in sample2:
        print(json.dumps(c, indent=2, ensure_ascii=False)[:500])


if __name__ == "__main__":
    main()
