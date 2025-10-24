"""Functional grouping of sections based on keywords and content."""

from typing import List, Dict, Set
from ..types.models import Section, FunctionalGroup
from .exceptions import GroupingError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FunctionalGrouper:
    """Groups sections by functional categories."""

    def __init__(self, custom_keywords: Dict[str, List[str]] = None):
        """
        Initialize functional grouper.

        Args:
            custom_keywords: Custom keyword mapping for grouping
                            Format: {"group_name": ["keyword1", "keyword2", ...]}
        """
        # Default keyword mapping for common functional areas
        self.default_keywords = {
            "인증": [
                "로그인",
                "로그아웃",
                "회원가입",
                "탈퇴",
                "비밀번호",
                "인증",
                "권한",
                "세션",
                "토큰",
                "OAuth",
                "SSO",
            ],
            "결제": [
                "결제",
                "구매",
                "주문",
                "카드",
                "환불",
                "정산",
                "포인트",
                "쿠폰",
                "할인",
                "가격",
            ],
            "사용자관리": [
                "사용자",
                "회원",
                "프로필",
                "개인정보",
                "계정",
                "정보수정",
                "마이페이지",
            ],
            "상품관리": [
                "상품",
                "제품",
                "카탈로그",
                "재고",
                "등록",
                "수정",
                "삭제",
                "조회",
            ],
            "검색": [
                "검색",
                "필터",
                "정렬",
                "조회",
                "찾기",
            ],
            "알림": [
                "알림",
                "푸시",
                "메시지",
                "이메일",
                "SMS",
                "통지",
            ],
            "관리자": [
                "관리자",
                "admin",
                "대시보드",
                "통계",
                "모니터링",
            ],
            "데이터관리": [
                "데이터베이스",
                "백업",
                "복원",
                "마이그레이션",
                "스키마",
            ],
            "API": [
                "API",
                "엔드포인트",
                "REST",
                "GraphQL",
                "웹훅",
            ],
            "보안": [
                "보안",
                "암호화",
                "XSS",
                "CSRF",
                "SQL Injection",
                "취약점",
            ],
        }

        # Merge with custom keywords
        self.keywords = self.default_keywords.copy()
        if custom_keywords:
            for group_name, keywords in custom_keywords.items():
                if group_name in self.keywords:
                    self.keywords[group_name].extend(keywords)
                else:
                    self.keywords[group_name] = keywords

        # Normalize keywords (lowercase for matching)
        self.normalized_keywords = {
            group: [kw.lower() for kw in keywords]
            for group, keywords in self.keywords.items()
        }

    def group_sections(self, sections: List[Section]) -> List[FunctionalGroup]:
        """
        Group sections by functional categories.

        Args:
            sections: List of sections to group

        Returns:
            List of functional groups

        Raises:
            GroupingError: If grouping fails
        """
        try:
            logger.info(f"Starting functional grouping for {len(sections)} sections")

            # Flatten sections for analysis
            flat_sections = self._flatten_sections(sections)

            # Assign each section to groups
            section_groups: Dict[str, List[Section]] = {}
            section_keywords: Dict[str, Set[str]] = {}

            for section in flat_sections:
                matched_groups = self._match_section_to_groups(section)

                for group_name, keywords in matched_groups.items():
                    if group_name not in section_groups:
                        section_groups[group_name] = []
                        section_keywords[group_name] = set()

                    section_groups[group_name].append(section)
                    section_keywords[group_name].update(keywords)

            # Create functional groups
            functional_groups = []
            for group_name, group_sections in section_groups.items():
                functional_group = FunctionalGroup(
                    name=group_name,
                    sections=group_sections,
                    keywords=list(section_keywords[group_name]),
                )
                functional_groups.append(functional_group)

            # Handle ungrouped sections
            ungrouped = self._find_ungrouped_sections(flat_sections, section_groups)
            if ungrouped:
                logger.info(f"Found {len(ungrouped)} ungrouped sections")
                functional_groups.append(
                    FunctionalGroup(
                        name="기타",
                        sections=ungrouped,
                        keywords=[],
                    )
                )

            logger.info(f"Created {len(functional_groups)} functional groups")
            return functional_groups

        except Exception as e:
            logger.error(f"Functional grouping failed: {e}")
            raise GroupingError(f"Failed to group sections: {e}") from e

    def _flatten_sections(self, sections: List[Section]) -> List[Section]:
        """
        Flatten hierarchical sections into a flat list.

        Args:
            sections: Hierarchical sections

        Returns:
            Flattened list of sections
        """
        flat = []
        for section in sections:
            flat.append(section)
            if section.subsections:
                flat.extend(self._flatten_sections(section.subsections))
        return flat

    def _match_section_to_groups(
        self, section: Section
    ) -> Dict[str, Set[str]]:
        """
        Match a section to functional groups based on keywords.

        Args:
            section: Section to match

        Returns:
            Dictionary mapping group names to matched keywords
        """
        matched_groups: Dict[str, Set[str]] = {}

        # Combine title and content for matching
        text_to_match = (section.title + " " + section.content).lower()

        # Check each group's keywords
        for group_name, keywords in self.normalized_keywords.items():
            matched_keywords = set()

            for keyword in keywords:
                if keyword in text_to_match:
                    matched_keywords.add(keyword)

            if matched_keywords:
                matched_groups[group_name] = matched_keywords

        return matched_groups

    def _find_ungrouped_sections(
        self, all_sections: List[Section], section_groups: Dict[str, List[Section]]
    ) -> List[Section]:
        """
        Find sections that were not assigned to any group.

        Args:
            all_sections: All sections
            section_groups: Mapping of group names to sections

        Returns:
            List of ungrouped sections
        """
        grouped_sections = set()
        for sections in section_groups.values():
            for section in sections:
                # Use title as identifier (assuming titles are unique)
                grouped_sections.add(section.title)

        ungrouped = [
            section for section in all_sections if section.title not in grouped_sections
        ]

        return ungrouped

    def add_keyword_mapping(self, group_name: str, keywords: List[str]) -> None:
        """
        Add or update keyword mapping for a group.

        Args:
            group_name: Name of the functional group
            keywords: List of keywords to associate with the group
        """
        if group_name in self.keywords:
            self.keywords[group_name].extend(keywords)
        else:
            self.keywords[group_name] = keywords

        # Update normalized keywords
        self.normalized_keywords[group_name] = [
            kw.lower() for kw in self.keywords[group_name]
        ]

        logger.info(f"Added/updated keywords for group '{group_name}'")

    def remove_group(self, group_name: str) -> None:
        """
        Remove a functional group from keyword mappings.

        Args:
            group_name: Name of the group to remove
        """
        if group_name in self.keywords:
            del self.keywords[group_name]
        if group_name in self.normalized_keywords:
            del self.normalized_keywords[group_name]

        logger.info(f"Removed group '{group_name}'")

    def get_group_keywords(self, group_name: str) -> List[str]:
        """
        Get keywords for a specific group.

        Args:
            group_name: Name of the group

        Returns:
            List of keywords for the group
        """
        return self.keywords.get(group_name, [])

    def list_all_groups(self) -> List[str]:
        """
        List all defined functional groups.

        Returns:
            List of group names
        """
        return list(self.keywords.keys())
