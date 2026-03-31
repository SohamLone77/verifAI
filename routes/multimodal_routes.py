# MULTIMODAL
from __future__ import annotations

from typing import Annotated, Union

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from app.environment import PromptReviewEnv
from app.models import Action, ActionType, StepResponse
from app.session import session_store
from verifai.environment.multimodal_review import MultiModalReviewer
from verifai.models.multimodal import (
    AudioReviewResult,
    ImageReviewResult,
    ReviewAudioAction,
    ReviewConfig,
    ReviewImageAction,
    ReviewVideoAction,
    VideoReviewResult,
)

router = APIRouter()
_env = PromptReviewEnv()


MultiModalAction = Annotated[
    Union[ReviewImageAction, ReviewAudioAction, ReviewVideoAction],
    Field(discriminator="action_type"),
]


class MultiModalSessionRequest(BaseModel):
    session_id: str
    action: MultiModalAction


@router.post("/multimodal/image", response_model=ImageReviewResult)
async def review_image(
    action: ReviewImageAction = Body(
        ..., 
        examples={
            "basic": {
                "summary": "Safety + brand scan",
                "value": {
                    "action_type": "review_image",
                    "image_base64": "<base64>",
                    "review_type": "all",
                    "threshold": 0.7,
                    "detect_objects": True,
                    "extract_text": True,
                },
            }
        },
    )
) -> ImageReviewResult:
    config = ReviewConfig(
        safety_threshold=action.threshold,
        brand_detection_enabled=action.review_type in {"brand", "all"},
        deepfake_detection_enabled=action.review_type in {"deepfake", "all"},
        ocr_enabled=action.extract_text,
        object_detection_enabled=action.detect_objects,
    )
    reviewer = MultiModalReviewer(config)
    return reviewer.review_image(action.image_base64, review_type=action.review_type)


@router.post("/multimodal/audio", response_model=AudioReviewResult)
async def review_audio(
    action: ReviewAudioAction = Body(
        ..., 
        examples={
            "basic": {
                "summary": "Toxicity + sentiment",
                "value": {
                    "action_type": "review_audio",
                    "audio_base64": "<base64>",
                    "language": "en",
                    "detect_voice_clone": True,
                    "sentiment_analysis": True,
                    "toxicity_detection": True,
                    "speaker_diarization": True,
                },
            }
        },
    )
) -> AudioReviewResult:
    reviewer = MultiModalReviewer()
    return reviewer.review_audio(action.audio_base64, language=action.language)


@router.post("/multimodal/video", response_model=VideoReviewResult)
async def review_video(
    action: ReviewVideoAction = Body(
        ..., 
        examples={
            "basic": {
                "summary": "Deepfake + brand",
                "value": {
                    "action_type": "review_video",
                    "video_base64": "<base64>",
                    "frame_interval": 30,
                    "max_frames": 60,
                    "detect_deepfake": True,
                    "detect_brand_violations": True,
                    "extract_audio": True,
                },
            }
        },
    )
) -> VideoReviewResult:
    config = ReviewConfig(
        deepfake_detection_enabled=action.detect_deepfake,
        brand_detection_enabled=action.detect_brand_violations,
    )
    reviewer = MultiModalReviewer(config)
    return reviewer.review_video(
        action.video_base64,
        frame_interval=action.frame_interval,
        max_frames=action.max_frames,
    )


def _summarize_result(result: ImageReviewResult | AudioReviewResult | VideoReviewResult) -> tuple[str, float]:
    if isinstance(result, ImageReviewResult):
        avg_score = (
            result.overall_safety_score
            + result.brand_compliance_score
            + result.authenticity_score
        ) / 3
        summary = (
            "Image review complete. "
            f"Safety={result.overall_safety_score:.2f}, "
            f"Brand={result.brand_compliance_score:.2f}, "
            f"Authenticity={result.authenticity_score:.2f}."
        )
        return summary, avg_score

    if isinstance(result, AudioReviewResult):
        summary = (
            "Audio review complete. "
            f"Overall={result.overall_score:.2f}, "
            f"Toxicity={result.overall_toxicity:.2f}, "
            f"VoiceClone={result.voice_clone_confidence:.2f}."
        )
        return summary, result.overall_score

    summary = (
        "Video review complete. "
        f"Overall={result.overall_score:.2f}, "
        f"Safety={result.safety_score:.2f}, "
        f"Authenticity={result.authenticity_score:.2f}."
    )
    return summary, result.overall_score


@router.post("/multimodal/session-step", response_model=StepResponse)
async def multimodal_session_step(
    request: MultiModalSessionRequest = Body(
        ..., 
        examples={
            "image": {
                "summary": "Session-based image review",
                "value": {
                    "session_id": "<session-id>",
                    "action": {
                        "action_type": "review_image",
                        "image_base64": "<base64>",
                        "review_type": "all",
                        "threshold": 0.7,
                        "detect_objects": True,
                        "extract_text": True,
                    },
                },
            },
            "audio": {
                "summary": "Session-based audio review",
                "value": {
                    "session_id": "<session-id>",
                    "action": {
                        "action_type": "review_audio",
                        "audio_base64": "<base64>",
                        "language": "en",
                        "detect_voice_clone": True,
                        "sentiment_analysis": True,
                        "toxicity_detection": True,
                        "speaker_diarization": True,
                    },
                },
            },
            "video": {
                "summary": "Session-based video review",
                "value": {
                    "session_id": "<session-id>",
                    "action": {
                        "action_type": "review_video",
                        "video_base64": "<base64>",
                        "frame_interval": 30,
                        "max_frames": 60,
                        "detect_deepfake": True,
                        "detect_brand_violations": True,
                        "extract_audio": True,
                    },
                },
            },
        },
    )
) -> StepResponse:
    session = session_store.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    action = request.action
    if isinstance(action, ReviewImageAction):
        config = ReviewConfig(
            safety_threshold=action.threshold,
            brand_detection_enabled=action.review_type in {"brand", "all"},
            deepfake_detection_enabled=action.review_type in {"deepfake", "all"},
            ocr_enabled=action.extract_text,
            object_detection_enabled=action.detect_objects,
        )
        reviewer = MultiModalReviewer(config)
        result = reviewer.review_image(action.image_base64, review_type=action.review_type)
    elif isinstance(action, ReviewAudioAction):
        reviewer = MultiModalReviewer()
        result = reviewer.review_audio(action.audio_base64, language=action.language)
    else:
        config = ReviewConfig(
            deepfake_detection_enabled=action.detect_deepfake,
            brand_detection_enabled=action.detect_brand_violations,
        )
        reviewer = MultiModalReviewer(config)
        result = reviewer.review_video(
            action.video_base64,
            frame_interval=action.frame_interval,
            max_frames=action.max_frames,
        )

    summary, _score = _summarize_result(result)
    env_action = Action(
        action_type=ActionType.submit,
        content=summary,
        modality="structured",
        structured_data=result.model_dump(),
        metadata={"multimodal": True},
    )

    response = _env.step(state=session.state, obs=session.obs, action=env_action)
    session_store.update(request.session_id, session.state, response.observation)
    return response
