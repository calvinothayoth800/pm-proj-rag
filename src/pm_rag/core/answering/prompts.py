from typing import List, Dict

def build_prompt(query: str, chunks: List[Dict]) -> str:
    """
    Constructs the prompt for the LLM.
    """
    if not chunks:
        context = "No relevant context found in the fixed Groww corpus."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "").strip()
            context_parts.append(f"--- Chunk {i} ---\n{text}")
        context = "\n".join(context_parts)
    
    prompt = f"""You are a factual Mutual Fund assistant.
Answer using ONLY the provided context. Be extremely concise.

CRITICAL RULES:
1. MAX 2 SENTENCES (aim for 1-2, never 3)
2. Extract SPECIFIC NUMBERS (e.g., "0.73%", "500")
3. Mention ONE FUND NAME only (the most relevant one)
4. NO generic definitions or explanations
5. NO investment advice, comparisons, or predictions
6. If context lacks the answer, say exactly: "Information not found in the fixed Groww corpus."

GOOD EXAMPLE:
Question: "What is the expense ratio?"
Answer: "The HDFC Mid Cap Fund has an expense ratio of 0.73% for the direct plan growth option."

BAD EXAMPLE (TOO LONG):
Answer: "The HDFC Mid Cap Fund has an expense ratio of 0.73%. This is applicable to the direct plan. The fund's expense ratio is very low."

CONTEXT:
{context}

QUESTION:
{query}

ANSWER (max 2 sentences, one fund name, specific number):"""
    return prompt
