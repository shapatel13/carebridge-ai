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
  "risk_flags": [
    {"type": "string", "severity": "yellow|red", "message": "string", "suggestion": "string"}
  ]
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
        logger.info("No Anthropic API key configured, returning demo output")
        return DEMO_OUTPUT

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

        message = client.messages.create(
            model="claude-sonnet-4-6",
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
        logger.error(f"Claude API error: {e}, returning demo output")
        return DEMO_OUTPUT
