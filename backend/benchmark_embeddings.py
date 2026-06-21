"""
Benchmark: LaBSE vs BanglaBERT for Bangla customer support RAG.

Tests:
  1. Cosine similarity on query-document pairs (relevant vs irrelevant)
  2. Retrieval ranking accuracy (MRR, Hit@1, Hit@3)
  3. Inference speed (ms/query)

Run: venv\Scripts\python benchmark_embeddings.py
"""

import time
import sys
import io
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---------------------------------------------------------------------------
# Test data: (query, relevant_doc_index, docs)
# ---------------------------------------------------------------------------
DOCS = [
    "অর্ডার ডেলিভারি সাধারণত ৩-৫ কার্যদিবসের মধ্যে হয়। ঢাকার ভেতরে ১-২ দিন এবং ঢাকার বাইরে ৩-৫ দিন লাগে।",
    "রিটার্ন পলিসি: পণ্য পাওয়ার ৭ দিনের মধ্যে রিটার্ন করা যাবে। পণ্য অবশ্যই অক্ষত এবং অরিজিনাল প্যাকেজিংয়ে থাকতে হবে।",
    "পেমেন্ট পদ্ধতি: বিকাশ, নগদ, রকেট, ক্রেডিট কার্ড এবং ডেবিট কার্ড গ্রহণযোগ্য। ক্যাশ অন ডেলিভারিও পাওয়া যায়।",
    "অর্ডার বাতিল করতে চাইলে ডেলিভারির আগে আমাদের সাথে যোগাযোগ করুন। শিপমেন্টের পরে বাতিল সম্ভব নয়।",
    "ওয়ারেন্টি পলিসি: ইলেকট্রনিক পণ্যে ১ বছরের ওয়ারেন্টি দেওয়া হয়। ওয়ারেন্টি কার্ড অবশ্যই সংরক্ষণ করুন।",
    "আমাদের কাস্টমার সার্ভিস সকাল ৯টা থেকে রাত ১০টা পর্যন্ত চালু থাকে। ফোন: 01700-000000।",
    "ডিসকাউন্ট কুপন ব্যবহার করতে চেকআউটের সময় কুপন কোড বক্সে কোড দিন। একটি অর্ডারে একটিমাত্র কুপন ব্যবহার করা যাবে।",
]

# (query, correct_doc_index)
QUERIES = [
    ("আমার অর্ডার কতদিনে আসবে?", 0),
    ("ডেলিভারি কতদিন লাগে ঢাকার বাইরে?", 0),
    ("পণ্য ফেরত দিতে চাই", 1),
    ("রিটার্ন করার নিয়ম কী?", 1),
    ("বিকাশে পেমেন্ট করা যাবে?", 2),
    ("কীভাবে পেমেন্ট করব?", 2),
    ("অর্ডার বাতিল করব কীভাবে?", 3),
    ("ওয়ারেন্টি কত বছরের?", 4),
    ("কাস্টমার সার্ভিসে কখন ফোন করব?", 5),
    ("কুপন কোড কোথায় দেব?", 6),
    # English queries (LaBSE handles these; BanglaBERT may struggle)
    ("When will my order arrive?", 0),
    ("How to return a product?", 1),
    ("What payment methods are accepted?", 2),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-9)

def rank_docs(query_vec, doc_vecs):
    scores = [(cosine(query_vec, dv), i) for i, dv in enumerate(doc_vecs)]
    scores.sort(reverse=True)
    return [i for _, i in scores]

def evaluate(model_fn, label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    # Embed docs
    t0 = time.perf_counter()
    doc_vecs = [model_fn(d) for d in DOCS]
    doc_time = time.perf_counter() - t0

    # Embed queries and rank
    hit1 = hit3 = mrr = 0
    query_times = []
    results = []

    for query, correct_idx in QUERIES:
        t0 = time.perf_counter()
        qvec = model_fn(query)
        query_times.append(time.perf_counter() - t0)

        ranked = rank_docs(qvec, doc_vecs)
        rank = ranked.index(correct_idx) + 1  # 1-based

        hit1 += int(rank == 1)
        hit3 += int(rank <= 3)
        mrr += 1.0 / rank
        results.append((query, rank, cosine(qvec, doc_vecs[correct_idx])))

    n = len(QUERIES)
    mrr /= n

    print(f"\n  Results per query:")
    for q, rank, sim in results:
        status = "✓" if rank == 1 else ("~" if rank <= 3 else "✗")
        print(f"  {status} Rank {rank}  sim={sim:.3f}  \"{q[:45]}\"")

    print(f"\n  --- Metrics ---")
    print(f"  Hit@1  : {hit1}/{n}  ({100*hit1/n:.0f}%)")
    print(f"  Hit@3  : {hit3}/{n}  ({100*hit3/n:.0f}%)")
    print(f"  MRR    : {mrr:.3f}")
    print(f"  Doc embed time   : {doc_time*1000:.0f} ms total  ({doc_time/len(DOCS)*1000:.1f} ms/doc)")
    print(f"  Query embed time : {sum(query_times)*1000:.0f} ms total  ({sum(query_times)/n*1000:.1f} ms/query)")

    return {"hit1": hit1/n, "hit3": hit3/n, "mrr": mrr, "ms_per_query": sum(query_times)/n*1000}

# ---------------------------------------------------------------------------
# Model loaders
# ---------------------------------------------------------------------------
def load_labse():
    from sentence_transformers import SentenceTransformer
    print("  Loading LaBSE...")
    model = SentenceTransformer("sentence-transformers/LaBSE")
    def embed(text):
        return model.encode([text])[0].tolist()
    return embed

def load_banglabert():
    from transformers import AutoTokenizer, AutoModel
    import torch
    print("  Loading BanglaBERT...")
    tokenizer = AutoTokenizer.from_pretrained("csebuetnlp/banglabert")
    model = AutoModel.from_pretrained("csebuetnlp/banglabert")
    model.eval()

    def embed(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True,
                           max_length=512, padding=True)
        with torch.no_grad():
            out = model(**inputs)
        # Mean pooling over token embeddings
        token_embs = out.last_hidden_state
        mask = inputs["attention_mask"].unsqueeze(-1).float()
        pooled = (token_embs * mask).sum(dim=1) / mask.sum(dim=1)
        return pooled[0].tolist()
    return embed

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\nBenchmark: LaBSE vs BanglaBERT")
    print("Test set: Bangla customer support queries + 3 English queries")
    print(f"Docs: {len(DOCS)}  |  Queries: {len(QUERIES)}")

    scores = {}

    try:
        embed_fn = load_labse()
        scores["LaBSE"] = evaluate(embed_fn, "LaBSE (sentence-transformers/LaBSE)")
    except Exception as e:
        print(f"\n[ERROR] LaBSE failed: {e}")

    try:
        embed_fn = load_banglabert()
        scores["BanglaBERT"] = evaluate(embed_fn, "BanglaBERT (csebuetnlp/banglabert)")
    except Exception as e:
        print(f"\n[ERROR] BanglaBERT failed: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Model':<15} {'Hit@1':>7} {'Hit@3':>7} {'MRR':>7} {'ms/query':>10}")
    print(f"  {'-'*48}")
    for name, s in scores.items():
        print(f"  {name:<15} {s['hit1']:>6.0%} {s['hit3']:>6.0%} {s['mrr']:>7.3f} {s['ms_per_query']:>9.1f}")

    if len(scores) == 2:
        winner = max(scores, key=lambda k: scores[k]["mrr"])
        print(f"\n  WINNER by MRR: {winner}")
        labse = scores.get("LaBSE", {})
        bb = scores.get("BanglaBERT", {})
        if labse and bb:
            if labse["mrr"] > bb["mrr"]:
                print("  -> LaBSE wins. Keep current config (sentence-transformers/LaBSE).")
            elif bb["mrr"] > labse["mrr"]:
                print("  -> BanglaBERT wins. Switch EMBEDDING_MODEL_NAME in config.py.")
                print("     Note: BanglaBERT needs custom mean-pooling embedder (not sentence-transformers).")
            else:
                print("  -> Tie. LaBSE preferred — faster and handles English queries too.")
    print()
