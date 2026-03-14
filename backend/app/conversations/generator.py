import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medico-legal documentation assistant for ICU serious illness conversations. You generate two outputs from a transcribed physician-family conversation:

1. **Physician Note** — A structured clinical documentation note recording what was SAID during the conversation (not clinical facts). Sections:
   - participants: Who was present
   - medical_status_explained: What medical information was conveyed to the family
   - prognosis_discussed: What trajectory/prognosis information was shared
   - uncertainty_addressed: How uncertainty was acknowledged
   - family_understanding_noted: Family's expressed understanding and emotional response
   - code_status: Any code status discussion (DNR/DNI/full code)
   - surrogate_decision_maker: Identified surrogate and their role

2. **Family Summary** — A plain-language summary (~150-200 words, 6th-grade reading level) for the family to take home. Must:
   - Validate emotions before providing information
   - Use simple, clear language
   - Avoid medical jargon (or define it inline)
   - Summarize what was discussed without making predictions

3. **Risk Flags** — Medico-legal risk flags for the physician:
   - type: category of risk (e.g., "missing_documentation", "unclear_prognosis", "no_surrogate")
   - severity: "yellow" (caution) or "red" (critical)
   - message: what the issue is
   - suggestion: actionable recommendation

SAFETY RULES:
1. Never predict survival probability or use "X% chance"
2. Always acknowledge uncertainty explicitly
3. Always document who was present
4. Physician note records what was SAID, not what IS clinically
5. Family summary validates emotions before providing information

FAMILY PRESENCE RULES:
6. If family_present is true in the metadata: Write a BRIEF family summary (100-120 words). The family heard the conversation live — this is a take-home reminder. Open with "As we discussed today..."
7. If family_present is false in the metadata: Write a DETAILED family summary (200-250 words). The family was NOT present — this is their primary way of understanding what happened. Open with phrasing like "Your loved one's care team met to discuss..."

LANGUAGE RULES:
8. Check the "language" field in the metadata. The family_summary MUST be written entirely in that language.
9. Supported languages: english, spanish, chinese, vietnamese, arabic, korean
10. If language is "english" or not specified, write in English (default).
11. If language is "spanish", write the ENTIRE family_summary in Spanish.
12. If language is "chinese", write the ENTIRE family_summary in Simplified Chinese.
13. If language is "vietnamese", write the ENTIRE family_summary in Vietnamese.
14. If language is "arabic", write the ENTIRE family_summary in Arabic.
15. If language is "korean", write the ENTIRE family_summary in Korean.
16. The physician_note must ALWAYS remain in English regardless of the language setting.
17. Keep the same 6th-grade reading level and compassionate tone in all languages.

DEDUPLICATION RULES:
18. The METADATA section contains structured tags (clinician_annotations, family_questions, code_status_discussed) provided by the physician as supplemental context.
19. These tags may overlap with what was said in the transcript. If information appears in BOTH the transcript and metadata, use the transcript as the primary source and treat metadata tags as confirmation — do NOT repeat the same point twice in the physician note.
20. Prioritize the transcript's richer detail over the tag's brief label.

READABILITY ASSESSMENT:
21. After writing the family_summary, estimate its readability as a US grade level (e.g. 5.2 means a 5th-grader could understand it). Return this as "readability_grade".
22. For English text, approximate the Flesch-Kincaid grade level.
23. For non-English text, estimate the equivalent grade level for a native reader of that language. The target is always grade 6 or below.

AI COMMUNICATION INSIGHTS:
24. Score the physician's communication on three dimensions (1-10 scale):
    - empathy: Did the physician acknowledge emotions, validate feelings, use compassionate language?
    - clarity: Was the medical information explained in understandable terms? Were jargon terms defined?
    - completeness: Were all key topics covered (prognosis, uncertainty, code status, next steps)?
25. Provide a brief rationale (1 sentence) for each score as empathy_rationale, clarity_rationale, completeness_rationale.
26. Calculate an overall score as the weighted average: empathy*0.4 + clarity*0.35 + completeness*0.25, rounded to nearest integer.
27. Write a "family_takeaway" — one sentence capturing what the family likely took away from this conversation.
28. Write 3 "next_steps" — actionable talking points the physician should prepare for the next family meeting.

You MUST respond with valid JSON matching this exact schema:
{
  "physician_note": {
    "participants": "string",
    "medical_status_explained": "string",
    "prognosis_discussed": "string",
    "uncertainty_addressed": "string",
    "family_understanding_noted": "string",
    "code_status": "string",
    "surrogate_decision_maker": "string"
  },
  "family_summary": "string",
  "readability_grade": 5.2,
  "risk_flags": [
    {"type": "string", "severity": "yellow|red", "message": "string", "suggestion": "string"}
  ],
  "ai_insights": {
    "communication_scores": {
      "empathy": 8,
      "clarity": 7,
      "completeness": 6,
      "overall": 7,
      "empathy_rationale": "string",
      "clarity_rationale": "string",
      "completeness_rationale": "string"
    },
    "family_takeaway": "string",
    "next_steps": ["string", "string", "string"]
  }
}"""

TONE_INSTRUCTIONS = {
    "optimistic": "Frame the trajectory with measured hope. Emphasize improvements and positive steps while remaining truthful.",
    "neutral": "Present information factually without directional framing.",
    "concerned": "Acknowledge the serious nature of the situation. Validate distress explicitly. Use compassionate but honest language.",
}


DEMO_OUTPUT = {
    "physician_note": {
        "participants": "Dr. Sarah Chen (attending), Maria Rodriguez (patient's daughter, healthcare proxy), James Rodriguez (patient's son), ICU Nurse Patricia Williams",
        "medical_status_explained": "Dr. Chen explained that Mr. Rodriguez remains on mechanical ventilation and vasopressor support (norepinephrine). She described the current multi-organ involvement including respiratory failure requiring ventilator support and hemodynamic instability requiring medication to maintain blood pressure. She noted the kidney function has declined, and the team is monitoring whether dialysis support may become necessary.",
        "prognosis_discussed": "Dr. Chen communicated that while the team is providing maximum medical support, Mr. Rodriguez's trajectory over the past 72 hours has shown a declining trend. She emphasized that the situation remains uncertain and that the medical team is taking it day by day, but wanted the family to understand the seriousness of his current condition.",
        "uncertainty_addressed": "Dr. Chen explicitly acknowledged uncertainty, stating 'I wish I could give you a definitive answer about what will happen, but the honest truth is that we don't know. What I can tell you is what we're seeing right now and what we're doing about it.' She also noted that patients can sometimes improve unexpectedly, but wanted the family to be prepared for the possibility that he may not recover.",
        "family_understanding_noted": "Maria expressed understanding of the severity, stating 'We know Dad is very sick.' She asked several questions about whether he is in pain (addressed by Dr. Chen — sedation is being managed). James was visibly emotional but nodded in understanding. Maria asked about what her father would have wanted, indicating she is beginning to think about goals of care. Both family members expressed gratitude for the team's transparency.",
        "code_status": "Dr. Chen introduced the topic of code status. Maria confirmed that Mr. Rodriguez had previously expressed to her that he 'wouldn't want to be kept alive by machines if there was no hope.' The family requested time to discuss among themselves before making any formal changes. Current status remains Full Code. Dr. Chen affirmed there was no rush and the team would support whatever decision they made.",
        "surrogate_decision_maker": "Maria Rodriguez, patient's daughter, confirmed as healthcare proxy with legal documentation on file. She expressed willingness to make decisions in alignment with her father's previously stated wishes."
    },
    "family_summary": "Thank you for meeting with us today to talk about your father's care. We know this is an incredibly difficult and emotional time, and your love for your father is clear.\n\nHere is a summary of what we discussed:\n\nYour father is currently in the ICU receiving support from a breathing machine (ventilator) and medications to help maintain his blood pressure. His kidneys are also not working as well as we would like, and the team is watching them closely.\n\nOver the past few days, his condition has become more serious. While we are doing everything we can, we want to be honest with you that we are concerned about how things are going. At the same time, we cannot predict exactly what will happen — every patient is different.\n\nWe talked about what your father would want for his care. Maria shared that he had told her he would not want to be kept on life support if there was no chance of recovery. There is no rush to make any decisions — take the time you need to talk as a family.\n\nYour care team is here for you. Please reach out anytime with questions.",
    "readability_grade": 5.4,
    "ai_insights": {
        "communication_scores": {
            "empathy": 9,
            "clarity": 8,
            "completeness": 7,
            "overall": 8,
            "empathy_rationale": "Dr. Chen consistently validated the family's emotions, acknowledged the difficulty of the situation, and affirmed their love for their father.",
            "clarity_rationale": "Medical concepts were explained in plain language with parenthetical definitions, though some terms like 'vasopressor' could have been simplified further.",
            "completeness_rationale": "Prognosis, uncertainty, and code status were addressed; however, specific next steps and timeline for follow-up were not explicitly outlined during the conversation."
        },
        "family_takeaway": "Dad is very sick and may not get better, but the doctors are doing everything they can and will support whatever decisions we make about his care.",
        "next_steps": [
            "Revisit goals-of-care discussion within 24-48 hours after the family has had time to process and talk among themselves.",
            "Check in specifically with James (son) who was visibly emotional but did not verbally confirm his understanding of the situation.",
            "Discuss the possibility of palliative care consultation to provide additional support for the family during decision-making."
        ]
    },
    "risk_flags": [
        {
            "type": "pending_code_status",
            "severity": "yellow",
            "message": "Code status discussion initiated but formal decision deferred. Patient remains Full Code.",
            "suggestion": "Schedule follow-up family meeting within 24-48 hours to revisit goals of care discussion. Document family's request for time in the interim."
        },
        {
            "type": "escalating_organ_support",
            "severity": "yellow",
            "message": "Patient on multiple organ supports (ventilator, vasopressors) with possible need for renal replacement therapy.",
            "suggestion": "Consider proactive palliative care consultation to support ongoing goals-of-care discussions given multi-organ involvement."
        },
        {
            "type": "surrogate_alignment",
            "severity": "yellow",
            "message": "Surrogate (Maria) referenced patient's prior wishes but second family member (James) was emotional and did not verbally confirm understanding.",
            "suggestion": "In follow-up meeting, specifically check in with James regarding his understanding and any concerns. Document all family members' expressed understanding."
        }
    ]
}


async def generate_outputs(
    transcript: str,
    tone: str = "neutral",
    metadata: dict | None = None,
) -> dict:
    """Generate physician note, family summary, and risk flags from transcript."""

    # If no API key configured, return demo output
    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key configured — returning DEMO output. Set ANTHROPIC_API_KEY in backend/.env")
        return DEMO_OUTPUT

    logger.info(f"API key found (starts with {settings.anthropic_api_key[:12]}...)")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["neutral"])

        user_message = f"""CONVERSATION TRANSCRIPT:
{transcript}

TONE INSTRUCTION: {tone_instruction}

METADATA:
{json.dumps(metadata or {}, indent=2)}

Generate the structured physician note, family summary, and risk flags based on this conversation transcript. Respond with valid JSON only."""

        logger.info(f"Calling Claude API with model claude-haiku-4-5-20251001")
        logger.info(f"Transcript length: {len(transcript)} chars")
        logger.info(f"Tone: {tone}")

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = message.content[0].text

        # Try to parse JSON from response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                raise

        return result

    except Exception as e:
        logger.error(f"Claude API error: {type(e).__name__}: {e}")
        logger.error(f"API key loaded: {'yes' if settings.anthropic_api_key else 'NO'}")
        logger.error(f"API key prefix: {settings.anthropic_api_key[:20]}..." if settings.anthropic_api_key else "NO KEY")
        logger.error("Falling back to DEMO output")
        return DEMO_OUTPUT


HANDOFF_SYSTEM_PROMPT = """You are a shift-handoff assistant for ICU physicians. Given a collection of serious illness conversation summaries from the outgoing physician, generate a concise handoff document for the incoming physician.

CRITICAL RULE: You MUST include a dedicated section for EVERY patient provided in the data. If 2 patients are provided, write about 2 patients. If 5 patients are provided, write about all 5. Do NOT skip or merge patients. Each patient should get their own bold-header section.

Structure your response as JSON with these keys:
{
  "summary": "A handoff narrative (scale with patient count: ~150 words per patient + 50 words for pending items). Cover EACH patient with: current status, key decisions made, emotional state of families, and pending items. Write in a professional clinical tone suitable for physician-to-physician communication."
}

Format the summary with:
- A header line with the physician name and shift date
- One **bold section per patient** using markdown-style **Patient Name** headers
- A final **Pending Items** section consolidating all follow-ups
- A **Risk Flags** section if any exist

Focus on:
1. What the incoming physician NEEDS to know immediately for EACH patient
2. Pending decisions or follow-ups per patient
3. Family emotional state and dynamics
4. Any risk flags that require attention
"""

def _build_demo_handoff(conversations_data: list[dict]) -> dict:
    """Build a dynamic demo handoff summary from actual conversation data."""
    patient_aliases = list({c.get("patient_alias", "Unknown Patient") for c in conversations_data})
    n = len(patient_aliases)

    sections = [f"Shift Handoff Summary\n\nDuring this shift, {n} patient{'s were' if n != 1 else ' was'} discussed:\n"]

    for alias in patient_aliases:
        # Find conversations for this patient
        patient_convs = [c for c in conversations_data if c.get("patient_alias") == alias]
        conv = patient_convs[0]  # primary conversation

        organs = ", ".join(conv.get("organ_supports", [])) if conv.get("organ_supports") else "standard ICU care"
        code = "Code status was discussed." if conv.get("code_status_discussed") else "Code status not yet addressed."
        status = conv.get("status", "in_progress")
        tone = conv.get("tone", "neutral")

        # Pull risk flags if available
        flags = conv.get("risk_flags", [])
        flag_text = ""
        if flags:
            flag_items = "\n".join(f"  - {f.get('message', '')}" for f in flags[:3])
            flag_text = f"\n- Risk flags:\n{flag_items}"

        sections.append(
            f"**{alias}** — Status: {status}\n"
            f"- Current supports: {organs}\n"
            f"- Tone of conversation: {tone}\n"
            f"- {code}"
            f"{flag_text}\n"
        )

    sections.append(
        "**Pending Items:**\n"
        "- Review and follow up on any open risk flags for each patient above\n"
        "- Continue goals-of-care discussions as clinically indicated\n"
        "- Ensure all family members confirm understanding of current plan"
    )

    return {"summary": "\n".join(sections)}


async def generate_handoff(conversations_data: list[dict]) -> dict:
    """Generate a shift handoff summary from multiple conversations."""
    if not settings.anthropic_api_key:
        logger.warning("No API key — returning DEMO handoff")
        return _build_demo_handoff(conversations_data)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        user_message = f"""Here are the conversation summaries from this shift:

{json.dumps(conversations_data, indent=2)}

Generate a comprehensive shift handoff document. Respond with valid JSON only."""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=HANDOFF_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = message.content[0].text
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                raise

        return result

    except Exception as e:
        logger.error(f"Handoff generation error: {e}")
        return _build_demo_handoff(conversations_data)
