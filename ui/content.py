RAG_SUPPORTED_QUESTIONS = [
    "Routine guidance (walk, feed, hydration, grooming)",
    "Timing questions (before/after walk, spacing meals)",
    "Care basics for dogs, cats, and rabbits",
    "Schedule-aware suggestions when today's plan is included",
]

RAG_NOT_SUPPORTED = [
    "Veterinary diagnosis or urgent medical advice",
    "Real-time external data (weather, store hours)",
    "Personal pet history that is not stored in PawPal+",
    "Deep multi-document research beyond local notes",
]

RAG_GUARDRAILS = [
    "Answers are grounded in retrieved local sources",
    "Citation format is enforced ([S1], [S2], ...)",
    "Fallback mode works without OPENAI_API_KEY",
    "Medical concerns are escalated to a veterinarian",
]

ROADMAP_STATUS = [
    ("Domain model + scheduler", "Done"),
    ("Persistence + Streamlit services", "Done"),
    ("RAG v1 with citation checks", "Done"),
    ("RAG evaluation harness", "Pending"),
    ("Final demo/report polish", "Pending"),
]
