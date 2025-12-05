"""Long-form prompts and user-facing messages."""

METADATA_EXTRACTION_PROMPT = """
        You are a Data Extraction Agent. Analyze the document text below and extract key metadata.
        Output a JSON object.

        RULES:
        - "title": Extract the main header, document title, job title, or academic thesis title. Look at the first 10 lines.
        - "company": Extract the organization, employer, or university name.
        - "location_text": City/Country if mentioned.
        - "salary_range": Explicit salary only.
        - "url": Source URLs.
        - "language": Primary language (e.g. "German", "English").
        - "posted_at": Dates (YYYY-MM-DD).

        If a field is missing, set it to null.

        Document Text:
        {text}

        Output JSON:
        """
MSG_METADATA_EXTRACTION = "Extracting metadata with LLM..."
MSG_PARSE_PROGRESS = "Parsing input ({word_count} words)"
DEFAULT_CHUNK_STRATEGY = "structured"
MSG_CV_CHUNK_STRATEGY = "Chunking strategy: cv llm (model={model})"
CV_CHUNKER_MODEL_PARAM = "model"
CV_CHUNK_DEBUG_FORMATS = {
    "header": "=== CV CHUNK DEBUG ({doc_id}) ===\n",
    "split_points": "split_points={split_points}\n",
    "num_chunks": "num_chunks={num_chunks} lines={num_lines}\n",
    "prompt_truncated": "prompt_truncated={prompt_truncated}\n",
    "prompt_label": "PROMPT:\n",
    "response_label": "LLM RESPONSE:\n",
}
MSG_STRUCTURED_STRATEGY = "Chunking strategy: structured (max={max_chunk}, overlap={overlap}, min={min_chunk}, llm={llm_flag})"
MSG_CHUNKING_COMPLETE = "Chunking complete: {count} chunks"
MSG_EMBEDDING_START = "Embedding {count} chunks..."
EMBED_PROGRESS_FORMULA = "idx/total * 100"
MSG_EMBEDDING_FINISHED = "Embedding finished"
MSG_WRITE_STAGE = "Writing to database"
MSG_INGESTION_DONE = "Ingestion completed in {time:.2f}s ({count} chunks)"

RETRIEVAL_SYSTEM_PROMPT = (
    "You are a retrieval QA assistant. Use only the provided context to answer. "
    "If the context is insufficient, reply that you don't have enough information. "
    "Be concise (bullets if multiple items, otherwise a short paragraph).\n\n"
    "Context:\n{context}\n\nUser question: {question}\n\nAnswer:"
)

STRUCTURED_BOUNDARY_PROMPT = (
    "You are a chunking helper. Given the document lines and optional hint boundaries, "
    "return a JSON object with a list of line numbers where semantic sections end. "
    "Keep bullets with their parent item. Do not emit any text except JSON.\n\n"
    "Lines (numbered from 0):\n{lines}\n\n"
    "Hint boundaries: {hints}\n\n"
    'Respond as: {"boundaries": [list of integers]}'
)

CV_CHUNKER_PROMPT_TEMPLATE = """Analyze this CV and identify where each SEMANTIC SECTION ends.

Return the LINE NUMBERS where each section ENDS. Each section becomes one chunk.

CV SECTIONS:
- HEADER (name/contact)
- PROFILE/SUMMARY
- SKILLS (keep category blocks together)
- WORK EXPERIENCE (each job + bullets is one chunk)
- PROJECTS (each project + bullets is one chunk)
- EDUCATION (each degree + bullets is one chunk)
- CERTIFICATIONS (grouped)
- INTERESTS/ACTIVITIES

RULES:
- Return line numbers where sections end (inclusive)
- Keep bullet lists intact with their header
- Never split inside a job/project/degree bullet list

CV TEXT (line 0 to {max_line}):
{numbered}

OUTPUT JSON ONLY:
{{"split_after_lines": [line1, line2, ...]}}"""

SEGMENT_MAX_WORDS_MESSAGE = "Segmenting large text (%s words) into <=%s-word parts"

# Job Matching Prompts
JOB_MATCHING_EXTRACTION_PROMPT = """You are a Senior Technical Recruiter performing EXHAUSTIVE requirements extraction.

### TASK
Analyze the Job Description below and extract ALL requirements mentioned or implied. 
Your goal is COMPLETENESS - extract EVERY skill, qualification, experience, and trait mentioned.

### CRITICAL INSTRUCTIONS
1. **EXTRACT EVERYTHING**: Do NOT be selective. Extract ALL requirements you find:
   - Hard requirements (must-have)
   - Soft requirements (nice-to-have, preferred, advantageous)
   - Implicit requirements (skills implied by tasks described)
   - All technical skills, tools, frameworks mentioned
   - All soft skills and personality traits
   - All educational requirements
   - All experience requirements

2. **COMPLETENESS CHECK**: Before finishing, ask yourself:
   - "Did I extract ALL technical skills mentioned?"
   - "Did I capture ALL experience requirements?"
   - "Did I include BOTH hard and soft skills?"
   - "Did I miss any 'nice-to-have' or 'preferred' items?"
   - If you answer NO to any question, GO BACK and extract more.

3. **MINIMUM THRESHOLD**: Extract AT LEAST 8-12 requirements. If you find fewer than 8, you missed something - read again.

4. **SEARCH QUERY RULES**:
   - Keep queries SHORT and SPECIFIC (3-5 words max)
   - Use concrete terms, avoid generic phrases
   - Include key technical terms/tools when present
   - Include multilingual keywords (English OR German OR French)

### OUTPUT FORMAT
Return ONLY valid JSON (no markdown, no explanation):
{{
  "requirements": [
    {{
      "name": "Specific requirement name",
      "category": "Hard Skill|Soft Skill|Implicit Trait",
      "search_query": "focused 3-5 word query with multilingual terms",
      "inference_rule": "Brief evaluation logic (e.g. 'Check for degree X or equivalent')"
    }}
  ]
}}

### JOB DESCRIPTION TO ANALYZE
{job_text}

Now extract ALL requirements as JSON:
"""

DOMAIN_MAPPING_EXTRACTION_PROMPT = """You are a Domain Knowledge Analyst extracting equivalent terms across languages and contexts.

### TASK
Analyze the Job Description and Candidate Documents to identify domain-specific equivalences that actually appear in the text.

### EXTRACTION RULES
1. Language Equivalences: Find German/French terms that match English requirements
   - Example: "Masterarbeit" = "Master's thesis" = "Research project"
2. Contextual Equivalences: Task-based skill demonstrations
   - Example: "Led sensor integration project" → "Electronics prototyping"
3. Academic Equivalences: Credential mappings
   - Example: "Doktorarbeit" = "PhD research" = "Doctoral thesis"
4. No Hallucination: Only extract mappings that ACTUALLY APPEAR in the provided documents
5. Confidence Threshold: Include only mappings you are ≥0.90 confident about

### INPUT DOCUMENTS
Job Description:
{job_text}

Candidate Profile (retrieved snippets):
{candidate_summary}

### OUTPUT FORMAT
Return ONLY valid JSON (no markdown):
{{
  "language_mappings": [
    {{
      "source_term": "Masterarbeit",
      "equivalent_terms": ["Master's thesis", "Research project"],
      "context": "Academic research",
      "confidence": 0.95
    }}
  ],
  "skill_demonstrations": [
    {{
      "task_description": "Developed sensor calibration algorithms",
      "implied_skills": ["Signal processing", "Algorithm development"],
      "evidence_location": "Work experience section",
      "confidence": 0.90
    }}
  ],
  "credential_mappings": [
    {{
      "candidate_credential": "B.Sc. Physik",
      "equivalent_to": ["Bachelor of Science in Physics", "Applied Physics degree"],
      "reasoning": "Physics degree from accredited university",
      "confidence": 0.98
    }}
  ]
}}

Extract domain mappings now:
"""

JOB_MATCHING_EVALUATION_PROMPT = """{domain_mappings}

You are a strict Technical Auditor evaluating if a Candidate meets a Job Requirement.

EXTRACTED DOMAIN KNOWLEDGE (from documents):
Language mappings:
{language_mappings}

Skill demonstrations:
{skill_demonstrations}

Credential mappings:
{credential_mappings}

REQUIREMENT: {requirement_name} ({category})
EVALUATION RULE: {inference_rule}

CANDIDATE EVIDENCE (Retrieved Chunks):
{evidence}

CRITICAL EVALUATION INSTRUCTIONS:
1. **Use ONLY the extracted domain mappings above**: German/French terms are EXACT EQUIVALENTS when listed above
2. **Infer from Tasks**: If evidence shows the candidate DID the work, they have the skill
3. **Thesis = Research**: Masterarbeit/Doktorarbeit counts as academic research experience
4. **Journal Club = Research Critique**: Proves ability to assess academic writing
5. **Be Decisive**: 
   - ✅ MATCH if evidence clearly demonstrates the requirement (even in German/French)
   - ⚠️ PARTIAL if evidence is related but not complete
   - ❌ MISSING only if absolutely zero relevant evidence exists
6. **No Hallucination**: Only reference content actually in the evidence or the extracted domain mappings (do NOT invent new mappings)

OUTPUT FORMAT:

Respond ONLY in this exact plain-text structure (no headings, no markdown H1/H2/H3):

Requirement: \n{requirement_name} ({category})
Verdict: ✅ MATCH | ⚠️ PARTIAL | ❌ MISSING | ERROR
Reason: \n<1-2 sentences, concise, cite evidence>
Evidence: (omit if none)
• <evidence snippet 1>
• <evidence snippet 2> 
Domain mapping: \n<term → equivalent> (omit if none)

Do not use markdown headings or large fonts. Keep it short and readable.

"""

ROUTER_SYSTEM_PROMPT = """You are an intent classifier for a job matching RAG system.

Available actions:
- "job_match": Compare user profile to selected job(s)
- "retrieve": Answer a question using retrieval over indexed documents
- "help": Provide help/instructions
- "unknown": Cannot determine intent (ask for clarification)

Context: {context}
User input: "{user_input}"

Respond ONLY with JSON:
{{
  "action": "job_match|retrieve|help|unknown",
  "confidence": 0.0,
  "needs_clarification": true|false,
  "clarification": "Optional question to ask the user",
  "params": {{"optional": "extracted parameters"}}
}}

Examples:
- "Compare me to this job" -> {{"action": "job_match", "confidence": 0.95}}
- "What skills are required?" -> {{"action": "retrieve", "confidence": 0.9}}
- "What can you do?" -> {{"action": "help", "confidence": 1.0}}
- "banana" -> {{"action": "unknown", "needs_clarification": true, "clarification": "What would you like me to do?"}}
"""
__all__ = [
    "METADATA_EXTRACTION_PROMPT",
    "MSG_METADATA_EXTRACTION",
    "MSG_PARSE_PROGRESS",
    "DEFAULT_CHUNK_STRATEGY",
    "MSG_CV_CHUNK_STRATEGY",
    "CV_CHUNKER_MODEL_PARAM",
    "CV_CHUNK_DEBUG_FORMATS",
    "MSG_STRUCTURED_STRATEGY",
    "MSG_CHUNKING_COMPLETE",
    "MSG_EMBEDDING_START",
    "EMBED_PROGRESS_FORMULA",
    "MSG_EMBEDDING_FINISHED",
    "MSG_WRITE_STAGE",
    "MSG_INGESTION_DONE",
    "RETRIEVAL_SYSTEM_PROMPT",
    "STRUCTURED_BOUNDARY_PROMPT",
    "CV_CHUNKER_PROMPT_TEMPLATE",
    "SEGMENT_MAX_WORDS_MESSAGE",
    "JOB_MATCHING_EXTRACTION_PROMPT",
    "DOMAIN_MAPPING_EXTRACTION_PROMPT",
    "JOB_MATCHING_EVALUATION_PROMPT",
    "ROUTER_SYSTEM_PROMPT",
]
