"""Multi-modal data models for VerifAI - Image, Audio, Video review"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List, Union, Any
from enum import Enum
from datetime import datetime


class ModalityType(str, Enum):
    """Supported input modalities"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class SafetyViolationType(str, Enum):
    """Types of safety violations"""
    NSFW = "nsfw"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    GORE = "gore"
    DRUGS = "drugs"
    WEAPONS = "weapons"


class SafetyViolation(BaseModel):
    """Detected safety violation in multi-modal content"""
    type: SafetyViolationType
    severity: float = Field(ge=0.0, le=1.0, description="Severity score 0-1")
    location: Optional[Dict[str, float]] = Field(
        default=None,
        description="Bounding box for images: {x, y, width, height}"
    )
    description: str = Field(description="Human-readable description")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    timestamp: Optional[float] = Field(default=None, description="Timestamp in seconds for audio/video")


class BrandViolation(BaseModel):
    """Brand guideline violation detection"""
    brand_logo: str = Field(description="Detected brand name")
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Where the logo was found")
    suggestion: str = Field(description="Remediation suggestion")
    bounding_box: Optional[Dict[str, float]] = Field(default=None, description="Logo location in image")


class DeepfakeDetection(BaseModel):
    """Deepfake detection results"""
    is_deepfake: bool
    confidence: float = Field(ge=0.0, le=1.0)
    artifacts: List[str] = Field(default_factory=list, description="Detected manipulation artifacts")
    manipulation_regions: List[Dict[str, float]] = Field(
        default_factory=list,
        description="Areas showing manipulation"
    )
    model_version: str = Field(default="v1.0", description="Detection model version")


class ObjectDetection(BaseModel):
    """Detected object in image/video"""
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: Dict[str, float]  # x, y, width, height
    attributes: Optional[Dict[str, Any]] = None


class TextInImage(BaseModel):
    """Text extracted from image using OCR"""
    text: str
    confidence: float
    bounding_box: Dict[str, float]


class ImageReviewResult(BaseModel):
    """Complete image review result"""
    image_id: str = Field(description="Unique identifier for the image")
    dimensions: Dict[str, int] = Field(description="Width and height in pixels")
    file_size_bytes: int
    mime_type: str

    # Safety analysis
    safety_violations: List[SafetyViolation] = Field(default_factory=list)
    nsfw_score: float = Field(ge=0.0, le=1.0, default=0.0)

    # Brand analysis
    brand_violations: List[BrandViolation] = Field(default_factory=list)

    # Deepfake analysis
    deepfake_analysis: DeepfakeDetection = Field(default_factory=lambda: DeepfakeDetection(is_deepfake=False, confidence=0.0))

    # OCR
    text_in_image: List[TextInImage] = Field(default_factory=list)

    # Object detection
    objects_detected: List[ObjectDetection] = Field(default_factory=list)

    # Overall scores
    overall_safety_score: float = Field(ge=0.0, le=1.0)
    brand_compliance_score: float = Field(ge=0.0, le=1.0)
    authenticity_score: float = Field(ge=0.0, le=1.0)

    # Flags and metadata
    flags: List[str] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class AudioSegment(BaseModel):
    """Segment of audio with analysis"""
    start_time: float
    end_time: float
    transcript: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    toxicity_score: float = Field(ge=0.0, le=1.0)
    speaker_id: Optional[int] = None
    flags: List[str] = Field(default_factory=list)


class AudioReviewResult(BaseModel):
    """Complete audio review result"""
    audio_id: str
    duration_seconds: float
    sample_rate: int
    language: str

    # Transcription
    full_transcript: str
    segments: List[AudioSegment]

    # Sentiment
    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    sentiment_trend: List[float] = Field(default_factory=list)

    # Toxicity
    overall_toxicity: float = Field(ge=0.0, le=1.0)
    toxic_segments: List[Dict] = Field(default_factory=list)

    # Voice analysis
    voice_clone_confidence: float = Field(ge=0.0, le=1.0)
    speakers_detected: int
    speaker_segments: List[Dict] = Field(default_factory=list)

    # Overall score
    overall_score: float = Field(ge=0.0, le=1.0)

    # Flags
    flags: List[str] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class VideoFrameAnalysis(BaseModel):
    """Analysis of a single video frame"""
    frame_number: int
    timestamp: float
    safety_score: float
    objects_detected: List[ObjectDetection]
    safety_violations: List[SafetyViolation]
    brand_violations: List[BrandViolation]
    deepfake_score: float


class VideoKeyEvent(BaseModel):
    """Key event detected in video"""
    timestamp: float
    event_type: Literal["safety_violation", "brand_violation", "scene_change", "audio_anomaly", "deepfake"]
    description: str
    severity: float = Field(ge=0.0, le=1.0)
    frame_number: int


class VideoReviewResult(BaseModel):
    """Complete video review result"""
    video_id: str
    duration_seconds: float
    resolution: Dict[str, int]
    frame_rate: float
    total_frames: int

    # Frame analysis
    frames_analyzed: int
    frame_results: List[VideoFrameAnalysis] = Field(default_factory=list)

    # Temporal analysis
    temporal_consistency_score: float = Field(ge=0.0, le=1.0)
    scene_transitions: List[float] = Field(default_factory=list)
    motion_smoothness: float = Field(ge=0.0, le=1.0)

    # Key events
    key_events: List[VideoKeyEvent] = Field(default_factory=list)

    # Overall scores
    safety_score: float = Field(ge=0.0, le=1.0)
    brand_compliance: float = Field(ge=0.0, le=1.0)
    authenticity_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

    # Flags
    flags: List[str] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Action Models for Multi-Modal Review
# ============================================================================

class ReviewImageAction(BaseModel):
    """Action to review an image"""
    action_type: Literal["review_image"] = "review_image"
    image_base64: str = Field(description="Base64 encoded image data")
    review_type: Literal["safety", "brand", "deepfake", "all"] = "all"
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    detect_objects: bool = Field(default=True)
    extract_text: bool = Field(default=True)
    image_id: Optional[str] = None


class ReviewAudioAction(BaseModel):
    """Action to review audio"""
    action_type: Literal["review_audio"] = "review_audio"
    audio_base64: str = Field(description="Base64 encoded audio data")
    language: str = Field(default="en")
    detect_voice_clone: bool = Field(default=True)
    sentiment_analysis: bool = Field(default=True)
    toxicity_detection: bool = Field(default=True)
    speaker_diarization: bool = Field(default=True)
    audio_id: Optional[str] = None


class ReviewVideoAction(BaseModel):
    """Action to review video"""
    action_type: Literal["review_video"] = "review_video"
    video_base64: str = Field(description="Base64 encoded video data")
    frame_interval: int = Field(default=30, description="Frames to sample")
    max_frames: int = Field(default=100, description="Maximum frames to analyze")
    detect_deepfake: bool = Field(default=True)
    detect_brand_violations: bool = Field(default=True)
    extract_audio: bool = Field(default=True)
    video_id: Optional[str] = None


# Discriminated union for multi-modal actions
MultiModalAction = ReviewImageAction | ReviewAudioAction | ReviewVideoAction


# ============================================================================
# Reward Models for Multi-Modal Review
# ============================================================================

class MultiModalRewardResult(BaseModel):
    """Reward calculation result for multi-modal review"""
    base_reward: float
    detection_bonus: float
    speed_bonus: float
    accuracy_bonus: float
    false_positive_penalty: float
    total_reward: float
    details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Utility Models
# ============================================================================

class ReviewConfig(BaseModel):
    """Configuration for multi-modal review"""
    safety_threshold: float = Field(default=0.7)
    brand_detection_enabled: bool = Field(default=True)
    deepfake_detection_enabled: bool = Field(default=True)
    ocr_enabled: bool = Field(default=True)
    object_detection_enabled: bool = Field(default=True)
    max_image_size_mb: int = Field(default=10)
    supported_image_formats: List[str] = Field(default=["jpg", "jpeg", "png", "webp"])
    supported_audio_formats: List[str] = Field(default=["wav", "mp3", "m4a", "ogg"])
    supported_video_formats: List[str] = Field(default=["mp4", "avi", "mov", "mkv"])
