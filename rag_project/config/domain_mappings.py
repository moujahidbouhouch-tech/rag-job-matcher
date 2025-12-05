"""Domain mapping rules for multilingual/semantic equivalence in job matching."""

# Placeholder: replace with the full mappings from your QA reference when available.
DOMAIN_MAPPINGS = """
CRITICAL: German/French CVs use different terminology than English job postings.
You MUST treat these as EXACT EQUIVALENTS when evaluating evidence.

Examples:
- "Masterarbeit" / "Mémoire" / "Thèse de Master" => Master thesis / research project
- "Dipl.-Ing." / "Ingénieur" => Engineering degree
- "Zeitreihenanalyse" => Time series analysis
- "Feature Engineering" => Feature engineering
- "Praktikum" / "Stage" => Internship
- "Werkstudent" => Working student / part-time engineer
- "Forschung" / "Recherche" => Research
- "Mikrosystemtechnik" => Microsystems engineering
- "Statistik" / "Statistiques" => Statistics
- "Signalverarbeitung" => Signal processing
Extend this list with the full mapping text from your QA source for best coverage.
"""

INFERENCE_RULES = {
    "Hard Skill": "Check explicit evidence of the skill/tool/tech or clear applied work.",
    "Soft Skill": "Look for behaviors or outcomes that demonstrate the trait.",
    "Implicit Trait": "Infer from tasks/responsibilities; research/thesis counts as research experience.",
}

__all__ = ["DOMAIN_MAPPINGS", "INFERENCE_RULES"]
