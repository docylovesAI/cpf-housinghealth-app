"""
Calibration script for the embeddings-based retrieval threshold.

Run this locally (with a real OPENAI_API_KEY set) to see the actual
similarity scores for a mix of on-topic and off-topic test questions.
Use the results to pick a MIN_RELEVANCE_SCORE in retrieval.py that sits
between the lowest on-topic score and the highest off-topic score.

Usage (from the cpf_app root folder, with dependencies installed):
    python scripts/calibrate_retrieval.py

This calls the real OpenAI embeddings API, so it will use a small amount
of API credit (embeddings are inexpensive -- a fraction of a cent per
call, and this script makes roughly a dozen calls total).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.retrieval import retrieve

ON_TOPIC_QUERIES = [
    "Why is there a limit on how much CPF I can use for my flat?",
    "What happens if my flat lease does not cover me to age 95?",
    "What is the difference between MSR and TDSR?",
    "If I use an HDB loan instead of a bank loan, does that change my CPF limit?",
    "What do I need to refund to CPF when I sell my flat?",
    "What is the CPF interest rate?",
    "How much of my CPF refunds can I use to buy my next flat?",
    "What happens to my housing refunds if I have already met my FRS?",
]

OFF_TOPIC_QUERIES = [
    "What is the weather like today?",
    "Can I use CPF to buy a car?",
    "What time does the MRT stop running?",
    "How do I renew my passport?",
    "Is Arsenal winning the EPL next year?",
]


def main():
    print("=" * 70)
    print("ON-TOPIC QUERIES (these SHOULD get a match)")
    print("=" * 70)
    on_topic_scores = []
    for q in ON_TOPIC_QUERIES:
        results = retrieve(q, top_k=1, min_score=0.0)  # no filter, show raw score
        if results:
            score = results[0]["relevance_score"]
            on_topic_scores.append(score)
            print(f"  [{score:.3f}] {q}\n           -> {results[0]['topic']}")
        else:
            print(f"  [no result at all] {q}")
    print()

    print("=" * 70)
    print("OFF-TOPIC QUERIES (these SHOULD NOT get a match)")
    print("=" * 70)
    off_topic_scores = []
    for q in OFF_TOPIC_QUERIES:
        results = retrieve(q, top_k=1, min_score=0.0)
        if results:
            score = results[0]["relevance_score"]
            off_topic_scores.append(score)
            print(f"  [{score:.3f}] {q}\n           -> {results[0]['topic']}")
    print()

    if on_topic_scores and off_topic_scores:
        lowest_on_topic = min(on_topic_scores)
        highest_off_topic = max(off_topic_scores)
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Lowest on-topic score:   {lowest_on_topic:.3f}")
        print(f"Highest off-topic score: {highest_off_topic:.3f}")
        if lowest_on_topic > highest_off_topic:
            suggested = round((lowest_on_topic + highest_off_topic) / 2, 2)
            print(f"\nThere is a clean gap. Suggested threshold: {suggested}")
            print("(the midpoint between the two -- update MIN_RELEVANCE_SCORE in retrieval.py)")
        else:
            print("\nWARNING: the ranges overlap -- no single threshold cleanly separates")
            print("on-topic from off-topic queries. Consider expanding the knowledge base,")
            print("or accept that some edge cases will be misclassified either way.")


if __name__ == "__main__":
    main()
