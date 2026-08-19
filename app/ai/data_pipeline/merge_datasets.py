"""
Merge Constitution chunks + IPC chunks into one unified collection-ready file.

Both datasets get normalized into a common schema so they can live in the
same ChromaDB collection with consistent, filterable metadata:

  chunk_id, source_type, reference_number, title, text, embedding_text,
  part, offense, punishment, cognizable, bailable, court, is_repealed

source_type lets you filter/distinguish at query time (e.g. "only search
Constitution" or show a different citation format per source).
"""
import json

CONSTITUTION_FILE = "constitution_chunks_enriched.json"
IPC_FILE = "fir_ipc_chunks.json"
BNS_FILE = "bns_chunks.json"
OUTPUT_FILE = "combined_chunks.json"


def normalize_constitution_chunk(c):
    return {
        "chunk_id": c["chunk_id"],
        "source_type": "constitution",
        "reference_number": c["article_number"],
        "title": c["title"],
        "text": c["text"],
        "embedding_text": c["embedding_text"],
        "part": c.get("part", ""),
        "offense": "",
        "punishment": "",
        "cognizable": "",
        "bailable": "",
        "court": "",
        "is_repealed": bool(c.get("is_repealed", False)),
    }


def normalize_ipc_chunk(c):
    return {
        "chunk_id": c["chunk_id"],
        "source_type": "ipc",
        "reference_number": c["section_number"],
        "title": c.get("offense", "") or f"IPC Section {c['section_number']}",
        "text": c["description"],
        "embedding_text": c["embedding_text"],
        "part": "",
        "offense": c.get("offense", ""),
        "punishment": c.get("punishment", ""),
        "cognizable": c.get("cognizable", ""),
        "bailable": c.get("bailable", ""),
        "court": c.get("court", ""),
        "is_repealed": False,
    }


def normalize_bns_chunk(c):
    return {
        "chunk_id": c["chunk_id"],
        "source_type": "bns",
        "reference_number": c["section_number"],
        "title": c["title"],
        "text": c["text"],
        "embedding_text": c["embedding_text"],
        "part": c.get("chapter", ""),
        "offense": "",
        "punishment": "",
        "cognizable": "",
        "bailable": "",
        "court": "",
        "is_repealed": False,
    }


def main():
    with open(CONSTITUTION_FILE, encoding="utf-8") as f:
        constitution_data = json.load(f)
    with open(IPC_FILE, encoding="utf-8") as f:
        ipc_data = json.load(f)
    with open(BNS_FILE, encoding="utf-8") as f:
        bns_data = json.load(f)

    combined = []
    combined.extend(normalize_constitution_chunk(c) for c in constitution_data)
    combined.extend(normalize_ipc_chunk(c) for c in ipc_data)
    combined.extend(normalize_bns_chunk(c) for c in bns_data)

    # validation
    ids = [c["chunk_id"] for c in combined]
    duplicates = len(ids) - len(set(ids))
    if duplicates:
        print(f"WARNING: {duplicates} duplicate chunk_ids found across datasets!")
        seen = set()
        for c in combined:
            if c["chunk_id"] in seen:
                print(f"  duplicate: {c['chunk_id']}")
            seen.add(c["chunk_id"])
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    const_count = sum(1 for c in combined if c["source_type"] == "constitution")
    ipc_count = sum(1 for c in combined if c["source_type"] == "ipc")
    bns_count = sum(1 for c in combined if c["source_type"] == "bns")
    print(f"Merged {const_count} Constitution chunks + {ipc_count} IPC chunks + {bns_count} BNS chunks")
    print(f"Total combined chunks: {len(combined)}")
    print(f"Saved -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()