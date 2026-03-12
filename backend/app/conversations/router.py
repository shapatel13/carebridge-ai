from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.conversations.generator import generate_outputs
from app.conversations.models import (
    Conversation,
    ConversationSegment,
    ConversationStatus,
    GeneratedOutput,
)
from app.conversations.schemas import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdate,
    GenerateRequest,
    GeneratedOutputResponse,
    SegmentCreate,
    SegmentResponse,
)
from app.core.database import get_db

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = Conversation(
        patient_alias=body.patient_alias,
        physician_id=user.id,
        hospital_id=user.hospital_id,
        tone_setting=body.tone_setting,
        risk_calibration=body.risk_calibration,
        participants=body.participants,
        organ_supports=body.organ_supports,
        code_status_discussed=body.code_status_discussed,
        code_status_change=body.code_status_change,
        surrogate_name=body.surrogate_name,
        surrogate_relationship=body.surrogate_relationship,
        family_questions=body.family_questions,
        clinician_annotations=body.clinician_annotations,
        is_demo=user.is_demo,
    )
    db.add(conversation)
    await db.flush()

    return ConversationResponse(
        id=conversation.id,
        patient_alias=conversation.patient_alias,
        physician_id=conversation.physician_id,
        hospital_id=conversation.hospital_id,
        status=conversation.status.value,
        tone_setting=conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
        risk_calibration=conversation.risk_calibration,
        participants=conversation.participants,
        organ_supports=conversation.organ_supports,
        code_status_discussed=conversation.code_status_discussed,
        code_status_change=conversation.code_status_change,
        surrogate_name=conversation.surrogate_name,
        surrogate_relationship=conversation.surrogate_relationship,
        family_questions=conversation.family_questions,
        clinician_annotations=conversation.clinician_annotations,
        created_at=str(conversation.created_at),
        finalized_at=None,
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.physician_id == user.id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()
    return [
        ConversationResponse(
            id=c.id,
            patient_alias=c.patient_alias,
            physician_id=c.physician_id,
            hospital_id=c.hospital_id,
            status=c.status.value,
            tone_setting=c.tone_setting.value if hasattr(c.tone_setting, 'value') else c.tone_setting,
            risk_calibration=c.risk_calibration,
            participants=c.participants,
            organ_supports=c.organ_supports,
            code_status_discussed=c.code_status_discussed,
            code_status_change=c.code_status_change,
            surrogate_name=c.surrogate_name,
            surrogate_relationship=c.surrogate_relationship,
            family_questions=c.family_questions,
            clinician_annotations=c.clinician_annotations,
            created_at=str(c.created_at),
            finalized_at=str(c.finalized_at) if c.finalized_at else None,
        )
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.segments), selectinload(Conversation.output))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.physician_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ConversationDetailResponse(
        conversation=ConversationResponse(
            id=conversation.id,
            patient_alias=conversation.patient_alias,
            physician_id=conversation.physician_id,
            hospital_id=conversation.hospital_id,
            status=conversation.status.value,
            tone_setting=conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
            risk_calibration=conversation.risk_calibration,
            participants=conversation.participants,
            organ_supports=conversation.organ_supports,
            code_status_discussed=conversation.code_status_discussed,
            code_status_change=conversation.code_status_change,
            surrogate_name=conversation.surrogate_name,
            surrogate_relationship=conversation.surrogate_relationship,
            family_questions=conversation.family_questions,
            clinician_annotations=conversation.clinician_annotations,
            created_at=str(conversation.created_at),
            finalized_at=str(conversation.finalized_at) if conversation.finalized_at else None,
        ),
        segments=[
            SegmentResponse(
                id=s.id,
                text=s.text,
                confidence=s.confidence,
                segment_order=s.segment_order,
            )
            for s in conversation.segments
        ],
        output=GeneratedOutputResponse(
            id=conversation.output.id,
            conversation_id=conversation.output.conversation_id,
            physician_note=conversation.output.physician_note,
            family_summary=conversation.output.family_summary,
            risk_flags=conversation.output.risk_flags,
            created_at=str(conversation.output.created_at),
        ) if conversation.output else None,
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.physician_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if conversation.status == ConversationStatus.FINALIZED:
        raise HTTPException(status_code=400, detail="Cannot edit finalized conversation")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conversation, key, value)

    await db.flush()

    return ConversationResponse(
        id=conversation.id,
        patient_alias=conversation.patient_alias,
        physician_id=conversation.physician_id,
        hospital_id=conversation.hospital_id,
        status=conversation.status.value,
        tone_setting=conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
        risk_calibration=conversation.risk_calibration,
        participants=conversation.participants,
        organ_supports=conversation.organ_supports,
        code_status_discussed=conversation.code_status_discussed,
        code_status_change=conversation.code_status_change,
        surrogate_name=conversation.surrogate_name,
        surrogate_relationship=conversation.surrogate_relationship,
        family_questions=conversation.family_questions,
        clinician_annotations=conversation.clinician_annotations,
        created_at=str(conversation.created_at),
        finalized_at=str(conversation.finalized_at) if conversation.finalized_at else None,
    )


@router.post("/{conversation_id}/segments", response_model=SegmentResponse, status_code=201)
async def add_segment(
    conversation_id: str,
    body: SegmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.physician_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get next segment order
    seg_result = await db.execute(
        select(ConversationSegment)
        .where(ConversationSegment.conversation_id == conversation_id)
        .order_by(ConversationSegment.segment_order.desc())
        .limit(1)
    )
    last_segment = seg_result.scalar_one_or_none()
    next_order = (last_segment.segment_order + 1) if last_segment else 0

    segment = ConversationSegment(
        conversation_id=conversation_id,
        text=body.text,
        confidence=body.confidence,
        segment_order=next_order,
    )
    db.add(segment)
    await db.flush()

    return SegmentResponse(
        id=segment.id,
        text=segment.text,
        confidence=segment.confidence,
        segment_order=segment.segment_order,
    )


@router.post("/{conversation_id}/generate", response_model=GeneratedOutputResponse)
async def generate_output(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.segments))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.physician_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build transcript from segments
    transcript = "\n".join(s.text for s in conversation.segments)

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="No transcript segments found. Add conversation text first.")

    metadata = {
        "patient_alias": conversation.patient_alias,
        "tone_setting": conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
        "participants": conversation.participants,
        "organ_supports": conversation.organ_supports,
        "code_status_discussed": conversation.code_status_discussed,
        "code_status_change": conversation.code_status_change,
        "surrogate_name": conversation.surrogate_name,
        "surrogate_relationship": conversation.surrogate_relationship,
        "family_questions": conversation.family_questions,
        "clinician_annotations": conversation.clinician_annotations,
    }

    output_data = await generate_outputs(
        transcript=transcript,
        tone=conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
        metadata=metadata,
    )

    # Delete existing output if regenerating
    existing = await db.execute(
        select(GeneratedOutput).where(GeneratedOutput.conversation_id == conversation_id)
    )
    existing_output = existing.scalar_one_or_none()
    if existing_output:
        await db.delete(existing_output)
        await db.flush()

    generated = GeneratedOutput(
        conversation_id=conversation_id,
        physician_note=output_data.get("physician_note", {}),
        family_summary=output_data.get("family_summary", ""),
        risk_flags=output_data.get("risk_flags", []),
    )
    db.add(generated)
    await db.flush()

    return GeneratedOutputResponse(
        id=generated.id,
        conversation_id=generated.conversation_id,
        physician_note=generated.physician_note,
        family_summary=generated.family_summary,
        risk_flags=generated.risk_flags,
        created_at=str(generated.created_at),
    )


@router.post("/{conversation_id}/finalize", response_model=ConversationResponse)
async def finalize_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.output))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.physician_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if conversation.status == ConversationStatus.FINALIZED:
        raise HTTPException(status_code=400, detail="Already finalized")
    if conversation.output is None:
        raise HTTPException(status_code=400, detail="Must generate output before finalizing")

    conversation.status = ConversationStatus.FINALIZED
    conversation.finalized_at = datetime.now(timezone.utc)
    await db.flush()

    return ConversationResponse(
        id=conversation.id,
        patient_alias=conversation.patient_alias,
        physician_id=conversation.physician_id,
        hospital_id=conversation.hospital_id,
        status=conversation.status.value,
        tone_setting=conversation.tone_setting.value if hasattr(conversation.tone_setting, 'value') else conversation.tone_setting,
        risk_calibration=conversation.risk_calibration,
        participants=conversation.participants,
        organ_supports=conversation.organ_supports,
        code_status_discussed=conversation.code_status_discussed,
        code_status_change=conversation.code_status_change,
        surrogate_name=conversation.surrogate_name,
        surrogate_relationship=conversation.surrogate_relationship,
        family_questions=conversation.family_questions,
        clinician_annotations=conversation.clinician_annotations,
        created_at=str(conversation.created_at),
        finalized_at=str(conversation.finalized_at),
    )
