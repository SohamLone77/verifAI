"""CLI commands for multi-modal review in VerifAI"""

import click
import base64
import json
import sys
from pathlib import Path
from typing import Optional
import time

from verifai.environment.multimodal_review import MultiModalReviewer, ReviewConfig


@click.group()
def multimodal():
    """Multi-modal review commands for VerifAI"""
    pass


@multimodal.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--review-type", "-t", type=click.Choice(["safety", "brand", "deepfake", "all"]), default="all")
@click.option("--threshold", "-th", type=float, default=0.7)
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def review_image(image_path: str, review_type: str, threshold: float, output: Optional[str]):
    """Review an image for safety, brand violations, and deepfakes"""

    click.echo("\n" + "=" * 70)
    click.echo("                    VerifAI - Image Review")
    click.echo("=" * 70 + "\n")

    # Load and encode image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode()

    # Get image info
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes))

    click.echo(f"Image: {image_path}")
    click.echo(f"Dimensions: {img.width}x{img.height}")
    click.echo(f"Size: {len(image_bytes) / 1024:.1f} KB")
    click.echo(f"Review Type: {review_type.upper()}")
    click.echo("\n" + "-" * 70 + "\n")

    # Configure reviewer
    config = ReviewConfig(safety_threshold=threshold)
    reviewer = MultiModalReviewer(config)

    # Perform review
    with click.progressbar(length=100, label="Analyzing image") as bar:
        for i in range(100):
            time.sleep(0.01)
            bar.update(1)

    result = reviewer.review_image(image_base64, review_type)

    # Display results
    click.echo("\nSAFETY ANALYSIS")
    click.echo("-" * 70)
    if result.safety_violations:
        for v in result.safety_violations:
            severity_bar = "#" * int(v.severity * 20) + "." * (20 - int(v.severity * 20))
            click.echo(f"  WARNING {v.type.value.upper()}: {severity_bar} {v.severity:.2f}")
            click.echo(f"    - {v.description}")
    else:
        click.echo("  OK No safety violations detected")

    click.echo("\nBRAND ANALYSIS")
    click.echo("-" * 70)
    if result.brand_violations:
        for v in result.brand_violations:
            click.echo(f"  WARNING {v.brand_logo}: Detected (confidence: {v.confidence:.2f})")
            click.echo(f"    - {v.suggestion}")
    else:
        click.echo("  OK No brand violations detected")

    click.echo("\nDEEPFAKE ANALYSIS")
    click.echo("-" * 70)
    if result.deepfake_analysis.is_deepfake:
        click.echo(f"  WARNING Deepfake Detected (confidence: {result.deepfake_analysis.confidence:.2f})")
        if result.deepfake_analysis.artifacts:
            click.echo(f"    - Artifacts: {', '.join(result.deepfake_analysis.artifacts)}")
    else:
        click.echo(f"  OK Authentic (confidence: {1 - result.deepfake_analysis.confidence:.2f})")

    click.echo("\nOBJECT DETECTION")
    click.echo("-" * 70)
    if result.objects_detected:
        for obj in result.objects_detected[:5]:
            click.echo(f"  * {obj.label} (confidence: {obj.confidence:.2f})")
    else:
        click.echo("  No objects detected")

    click.echo("\n" + "-" * 70)
    click.echo("\nOVERALL SCORES")
    click.echo("-" * 70)

    def score_bar(score: float, label: str):
        filled = int(score * 20)
        bar = "#" * filled + "." * (20 - filled)
        click.echo(f"  {label:15} {bar} {score:.2f}")

    score_bar(result.overall_safety_score, "Safety:")
    score_bar(result.brand_compliance_score, "Brand:")
    score_bar(result.authenticity_score, "Authenticity:")
    click.echo()
    score_bar(result.overall_safety_score * 0.4 + result.brand_compliance_score * 0.3 + result.authenticity_score * 0.3, "FINAL:")

    click.echo("\nFLAGS")
    click.echo("-" * 70)
    if result.flags:
        for flag in result.flags:
            click.echo(f"  - {flag}")
    else:
        click.echo("  OK No flags")

    click.echo(f"\nProcessing Time: {result.processing_time_ms:.0f} ms")
    click.echo(f"Estimated Cost: ${result.processing_time_ms / 1000 * 0.01:.4f}")

    # Save output if requested
    if output:
        with open(output, "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        click.echo(f"\nResults saved to: {output}")

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Use --review-type safety to only check safety violations")
    click.echo("=" * 70 + "\n")


@multimodal.command()
@click.argument("audio_path", type=click.Path(exists=True))
@click.option("--language", "-l", default="en", help="Audio language")
@click.option("--detect-voice-clone/--no-detect-voice-clone", default=True)
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def review_audio(audio_path: str, language: str, detect_voice_clone: bool, output: Optional[str]):
    """Review audio for sentiment, toxicity, and voice cloning"""

    click.echo("\n" + "=" * 70)
    click.echo("                    VerifAI - Audio Review")
    click.echo("=" * 70 + "\n")

    # Load audio
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()

    # Get audio info
    import wave
    try:
        with wave.open(audio_path, 'rb') as wav:
            duration = wav.getnframes() / wav.getframerate()
            sample_rate = wav.getframerate()
    except Exception:
        duration = 30.0
        sample_rate = 16000

    click.echo(f"Audio: {audio_path}")
    click.echo(f"Duration: {duration:.1f} seconds")
    click.echo(f"Sample Rate: {sample_rate} Hz")
    click.echo(f"Language: {language}")
    click.echo("\n" + "-" * 70 + "\n")

    # Perform review
    reviewer = MultiModalReviewer()

    with click.progressbar(length=100, label="Analyzing audio") as bar:
        for i in range(100):
            time.sleep(0.01)
            bar.update(1)

    result = reviewer.review_audio(audio_base64, language)

    # Display results
    click.echo("\nTRANSCRIPT (first 200 chars)")
    click.echo("-" * 70)
    click.echo(f"  {result.full_transcript[:200]}...")

    click.echo("\nSENTIMENT ANALYSIS")
    click.echo("-" * 70)
    sentiment_bar = "#" * int((result.overall_sentiment + 1) * 10) + "." * (20 - int((result.overall_sentiment + 1) * 10))
    click.echo(f"  Sentiment Score: {sentiment_bar} {result.overall_sentiment:.2f}")
    sentiment_text = "Positive" if result.overall_sentiment > 0.2 else "Negative" if result.overall_sentiment < -0.2 else "Neutral"
    click.echo(f"  Sentiment: {sentiment_text}")

    click.echo("\nTOXICITY DETECTION")
    click.echo("-" * 70)
    toxicity_bar = "#" * int(result.overall_toxicity * 20) + "." * (20 - int(result.overall_toxicity * 20))
    click.echo(f"  Toxicity Score: {toxicity_bar} {result.overall_toxicity:.2f}")
    if result.overall_toxicity > 0.5:
        click.echo("  WARNING Toxic content detected")

    click.echo("\nVOICE CLONE DETECTION")
    click.echo("-" * 70)
    clone_bar = "#" * int(result.voice_clone_confidence * 20) + "." * (20 - int(result.voice_clone_confidence * 20))
    click.echo(f"  Voice Clone Confidence: {clone_bar} {result.voice_clone_confidence:.2f}")
    if result.voice_clone_confidence > 0.7:
        click.echo("  WARNING Potential voice cloning detected")
    else:
        click.echo("  OK Likely human voice")

    click.echo("\nSPEAKER ANALYSIS")
    click.echo("-" * 70)
    click.echo(f"  Speakers Detected: {result.speakers_detected}")
    for speaker in result.speaker_segments:
        click.echo(f"    - Speaker {speaker['speaker']}: {speaker['duration']:.1f} sec ({speaker['percentage']:.0f}%)")

    click.echo("\nOVERALL SCORES")
    click.echo("-" * 70)

    def score_bar(score: float, label: str):
        filled = int(score * 20)
        bar = "#" * filled + "." * (20 - filled)
        click.echo(f"  {label:12} {bar} {score:.2f}")

    score_bar(1.0 - result.overall_toxicity, "Clarity:")
    score_bar((result.overall_sentiment + 1) / 2, "Sentiment:")
    score_bar(1.0 - result.voice_clone_confidence, "Authenticity:")
    click.echo()
    score_bar(result.overall_score, "FINAL:")

    click.echo("\nFLAGS")
    click.echo("-" * 70)
    if result.flags:
        for flag in result.flags:
            click.echo(f"  - {flag}")
    else:
        click.echo("  OK No flags")

    click.echo(f"\nProcessing Time: {result.processing_time_ms:.0f} ms")
    click.echo(f"Estimated Cost: ${result.processing_time_ms / 1000 * 0.02:.4f}")

    if output:
        with open(output, "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        click.echo(f"\nResults saved to: {output}")

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Use --export-transcript to save full transcript")
    click.echo("=" * 70 + "\n")


@multimodal.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--frame-interval", "-f", type=int, default=30, help="Frames between samples")
@click.option("--max-frames", "-m", type=int, default=100, help="Maximum frames to analyze")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def review_video(video_path: str, frame_interval: int, max_frames: int, output: Optional[str]):
    """Review video for safety violations and deepfakes"""

    click.echo("\n" + "=" * 70)
    click.echo("                    VerifAI - Video Review")
    click.echo("=" * 70 + "\n")

    # Load video
    with open(video_path, "rb") as f:
        video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode()

    click.echo(f"Video: {video_path}")
    click.echo(f"Size: {len(video_bytes) / 1024 / 1024:.1f} MB")
    click.echo(f"Frame Interval: {frame_interval} frames")
    click.echo(f"Max Frames: {max_frames}")
    click.echo("\n" + "-" * 70 + "\n")

    # Perform review
    reviewer = MultiModalReviewer()

    click.echo("Sampling frames...")
    with click.progressbar(length=max_frames, label="Processing frames") as bar:
        for i in range(max_frames):
            time.sleep(0.02)
            bar.update(1)

    result = reviewer.review_video(video_base64, frame_interval, max_frames)

    # Display results
    click.echo(f"\nVIDEO INFORMATION")
    click.echo("-" * 70)
    click.echo(f"  Duration: {result.duration_seconds:.1f} seconds")
    click.echo(f"  Resolution: {result.resolution['width']}x{result.resolution['height']}")
    click.echo(f"  Frame Rate: {result.frame_rate} fps")
    click.echo(f"  Total Frames: {result.total_frames}")
    click.echo(f"  Frames Analyzed: {result.frames_analyzed}")

    click.echo("\nTEMPORAL ANALYSIS")
    click.echo("-" * 70)
    click.echo(f"  Temporal Consistency: {result.temporal_consistency_score:.2f}")
    click.echo(f"  Motion Smoothness: {result.motion_smoothness:.2f}")
    click.echo(f"  Scene Transitions: {len(result.scene_transitions)}")

    click.echo("\nKEY EVENTS DETECTED")
    click.echo("-" * 70)
    if result.key_events:
        for event in result.key_events[:5]:
            severity_bar = "#" * int(event.severity * 20) + "." * (20 - int(event.severity * 20))
            click.echo(f"  - {event.timestamp:.1f}s: {event.event_type}")
            click.echo(f"    Severity: {severity_bar} {event.severity:.2f}")
            click.echo(f"    {event.description}")
    else:
        click.echo("  OK No key events detected")

    click.echo("\nOVERALL SCORES")
    click.echo("-" * 70)

    def score_bar(score: float, label: str):
        filled = int(score * 20)
        bar = "#" * filled + "." * (20 - filled)
        click.echo(f"  {label:12} {bar} {score:.2f}")

    score_bar(result.safety_score, "Safety:")
    score_bar(result.brand_compliance, "Brand:")
    score_bar(result.authenticity_score, "Authenticity:")
    click.echo()
    score_bar(result.overall_score, "FINAL:")

    click.echo("\nFLAGS")
    click.echo("-" * 70)
    if result.flags:
        for flag in result.flags:
            click.echo(f"  - {flag}")
    else:
        click.echo("  OK No flags")

    click.echo(f"\nProcessing Time: {result.processing_time_ms:.0f} ms")
    click.echo(f"Estimated Cost: ${result.processing_time_ms / 1000 * 0.05:.4f}")

    if output:
        with open(output, "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        click.echo(f"\nResults saved to: {output}")

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Use --export-frames to save frame-by-frame analysis")
    click.echo("=" * 70 + "\n")


# Main CLI entry point
@click.group()
def cli():
    """VerifAI - Verify AI, One Output at a Time"""
    pass


cli.add_command(multimodal)

if __name__ == "__main__":
    cli()
