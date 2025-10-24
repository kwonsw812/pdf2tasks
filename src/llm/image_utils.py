"""Utilities for integrating image analysis with LLM prompts."""

from typing import List, Dict, Optional
from ..types.models import (
    ImageAnalysis,
    Section,
    PageRange,
    UIComponent,
)


def find_related_images(
    page_range: PageRange,
    image_analyses: List[ImageAnalysis]
) -> List[ImageAnalysis]:
    """
    Find image analyses that fall within a specific page range.

    Args:
        page_range: Page range to search within
        image_analyses: List of image analysis results

    Returns:
        List of image analyses within the page range
    """
    related_images = []
    for image in image_analyses:
        if page_range.start <= image.page_number <= page_range.end:
            related_images.append(image)
    return related_images


def map_images_to_sections(
    sections: List[Section],
    image_analyses: List[ImageAnalysis]
) -> Dict[int, List[ImageAnalysis]]:
    """
    Map image analyses to sections based on page ranges.

    Args:
        sections: List of document sections
        image_analyses: List of image analysis results

    Returns:
        Dictionary mapping section index to related images
    """
    section_images = {}

    for idx, section in enumerate(sections):
        related_images = find_related_images(section.page_range, image_analyses)
        if related_images:
            section_images[idx] = related_images

    return section_images


def format_ui_component(component: UIComponent) -> str:
    """
    Format a single UI component for prompt inclusion.

    Args:
        component: UI component to format

    Returns:
        Formatted string representation
    """
    parts = [f"- {component.type}"]

    if component.label:
        parts.append(f'"{component.label}"')

    if component.position:
        parts.append(f"({component.position})")

    parts.append(f": {component.description}")

    return " ".join(parts)


def format_image_analysis_for_prompt(
    analysis: ImageAnalysis,
    include_components: bool = True,
    max_components: int = 10
) -> str:
    """
    Format an ImageAnalysis result for inclusion in LLM prompt.

    Args:
        analysis: Image analysis result
        include_components: Whether to include UI component details
        max_components: Maximum number of components to include

    Returns:
        Formatted markdown string
    """
    lines = []

    # Header
    title = analysis.screen_title or f"{analysis.screen_type} 화면"
    lines.append(f"### 관련 화면 설계: {title}")
    lines.append(f"**(페이지 {analysis.page_number}, 이미지: {analysis.image_path})**")
    lines.append("")

    # Screen type
    lines.append(f"- **화면 유형**: {analysis.screen_type}")

    # UI Components
    if include_components and analysis.ui_components:
        lines.append(f"- **UI 컴포넌트** ({len(analysis.ui_components)}개):")

        # Limit components to max_components
        components_to_show = analysis.ui_components[:max_components]
        for component in components_to_show:
            lines.append(f"  {format_ui_component(component)}")

        if len(analysis.ui_components) > max_components:
            remaining = len(analysis.ui_components) - max_components
            lines.append(f"  ...(외 {remaining}개 컴포넌트)")

    # Layout structure
    if analysis.layout_structure:
        lines.append(f"- **레이아웃**: {analysis.layout_structure}")

    # User flow
    if analysis.user_flow:
        lines.append(f"- **사용자 흐름**: {analysis.user_flow}")

    # Confidence
    lines.append(f"- **신뢰도**: {analysis.confidence:.1f}%")
    lines.append("")

    return "\n".join(lines)


def format_section_with_images(
    section: Section,
    section_idx: int,
    related_images: List[ImageAnalysis],
    max_components: int = 10
) -> str:
    """
    Format a section with its related image analyses for prompt.

    Args:
        section: Document section
        section_idx: Section index
        related_images: Related image analyses
        max_components: Maximum components per image

    Returns:
        Formatted markdown string
    """
    lines = []

    # Section header
    lines.append(f"## 섹션 {section_idx + 1}: {section.title}")
    lines.append(f"**(페이지 {section.page_range.start}-{section.page_range.end}, 레벨 {section.level})**")
    lines.append("")

    # Section content (truncated)
    content = section.content
    if len(content) > 2000:
        content = content[:2000] + "\n...(내용 생략)"
    lines.append(content)
    lines.append("")

    # Related images
    if related_images:
        lines.append("---")
        lines.append("")
        for image in related_images:
            lines.append(format_image_analysis_for_prompt(
                image,
                include_components=True,
                max_components=max_components
            ))

    return "\n".join(lines)


def format_task_related_images(
    task_related_sections: List[int],
    sections: List[Section],
    image_analyses: List[ImageAnalysis],
    max_images: int = 3
) -> str:
    """
    Format images related to a task for TaskWriter prompt.

    Args:
        task_related_sections: Section indices related to task
        sections: All document sections
        image_analyses: All image analyses
        max_images: Maximum images to include

    Returns:
        Formatted markdown string or empty if no images
    """
    if not image_analyses:
        return ""

    # Collect all images from related sections
    related_images = []
    for section_idx in task_related_sections:
        if 0 <= section_idx < len(sections):
            section = sections[section_idx]
            section_images = find_related_images(section.page_range, image_analyses)
            related_images.extend(section_images)

    if not related_images:
        return ""

    # Remove duplicates (same image_path)
    seen = set()
    unique_images = []
    for img in related_images:
        if img.image_path not in seen:
            seen.add(img.image_path)
            unique_images.append(img)

    # Limit to max_images
    images_to_show = unique_images[:max_images]

    lines = []
    lines.append("=" * 80)
    lines.append("## 관련 화면 설계")
    lines.append("")

    for img in images_to_show:
        lines.append(format_image_analysis_for_prompt(
            img,
            include_components=True,
            max_components=8
        ))

    if len(unique_images) > max_images:
        remaining = len(unique_images) - max_images
        lines.append(f"...(외 {remaining}개 화면 설계 이미지)")

    lines.append("")

    return "\n".join(lines)


def get_image_summary(image_analyses: List[ImageAnalysis]) -> str:
    """
    Get a summary of image analyses for logging.

    Args:
        image_analyses: List of image analyses

    Returns:
        Summary string
    """
    if not image_analyses:
        return "이미지 없음"

    screen_types = {}
    for img in image_analyses:
        screen_types[img.screen_type] = screen_types.get(img.screen_type, 0) + 1

    type_summary = ", ".join([f"{t}({c})" for t, c in screen_types.items()])

    return f"{len(image_analyses)}개 화면 ({type_summary})"
