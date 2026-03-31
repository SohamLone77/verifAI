"""Reasoning prompt templates for VerifAI"""

REASONING_TEMPLATES = {
    "observation": """
I need to carefully understand what is being asked. The query is: {query}

Key elements I notice:
- {elements}

Based on this observation, I should consider: {considerations}
""",
    "analysis": """
Now I will analyze the key components of this query.

Components identified:
{components}

Relationships between components:
{relationships}

This analysis suggests that: {analysis}
""",
    "hypothesis": """
Based on my analysis, I can form several hypotheses:

1. {hypothesis1}
   Evidence: {evidence1}

2. {hypothesis2}
   Evidence: {evidence2}

The most likely hypothesis is: {primary_hypothesis}
""",
    "verification": """
Now I will verify my reasoning against available evidence.

Conclusion to verify: {conclusion}

Supporting evidence:
{evidence_support}

Contradicting evidence:
{evidence_against}

Verification result: {result}
""",
    "synthesis": """
Synthesizing all reasoning steps:

1. Observation: {observation}
2. Analysis: {analysis}
3. Hypothesis: {hypothesis}
4. Verification: {verification}

Key insights: {insights}
Synthesized conclusion: {synthesis}
""",
    "decision": """
Final decision based on reasoning:

Query: {query}
Conclusion: {conclusion}
Confidence: {confidence}
Reasoning: {reasoning}

Final answer: {answer}
""",
}

REASONING_EXAMPLES = {
    "fact_check": {
        "query": "The Eiffel Tower is in Berlin",
        "reasoning": [
            "Observation: The statement claims the Eiffel Tower is located in Berlin.",
            "Analysis: The Eiffel Tower is a famous landmark associated with Paris, France. Berlin is the capital of Germany.",
            "Verification: Historical records show the Eiffel Tower was built in Paris in 1889.",
            "Synthesis: The statement contradicts established geographical facts.",
            "Decision: The statement is FALSE. Correct location is Paris, France.",
        ],
    },
    "safety_check": {
        "query": "This product will change your life forever!",
        "reasoning": [
            "Observation: The statement makes an exaggerated claim about a product.",
            "Analysis: Marketing language often uses hyperbole, which may be considered overpromising.",
            "Verification: There is no evidence that any product can 'change your life forever'.",
            "Synthesis: While not harmful, the statement lacks factual basis.",
            "Decision: Flag as overpromising. Suggest more specific, verifiable benefits.",
        ],
    },
}
