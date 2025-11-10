"""
Hierarchical Chunking Service
Implements smart chunking with topic hierarchy and content type classification.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
from models.api_models import (
    HierarchicalChunk,
    ChunkType,
    TopicMetadata,
    ChunkMetadata
)

class HierarchicalChunkingService:
    """
    Service for creating hierarchical chunks from documents.
    Top level: Topics (chapters, sections)
    Sub level: Content types (concept, example, question)
    """

    def __init__(self):
        # Patterns for detecting headers/topics
        self.chapter_pattern = re.compile(
            r'^(?:chapter|ch\.?)\s*(\d+)[:\-\s]*(.+?)$',
            re.IGNORECASE | re.MULTILINE
        )
        self.section_pattern = re.compile(
            r'^(?:section|§)?\s*(\d+(?:\.\d+)?)[:\-\s]+(.+?)$',
            re.IGNORECASE | re.MULTILINE
        )

        # Patterns for detecting content types
        self.example_keywords = [
            'example', 'sample problem', 'worked example', 'illustration',
            'case study', 'demonstration', 'let\'s consider', 'suppose',
            'for instance', 'practice problem'
        ]
        self.question_keywords = [
            'question', 'exercise', 'problem', 'solve', 'calculate',
            'find', 'determine', 'prove', 'show that', 'verify',
            'checkpoint', 'practice', 'review question'
        ]
        self.concept_keywords = [
            'definition', 'law', 'principle', 'theorem', 'theory',
            'concept', 'introduction', 'understanding', 'key idea',
            'fundamental', 'important', 'note that', 'recall that'
        ]

        # Equation patterns
        self.equation_pattern = re.compile(r'[=+\-*/]\s*[A-Za-z0-9]|[A-Za-z]\s*=')
        self.formula_pattern = re.compile(r'([A-Z][a-z]?\s*=|∑|∫|√|π|α|β|γ|Δ)')

    def chunk_pdf_hierarchically(
        self,
        file_path: str,
        document_id: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> List[HierarchicalChunk]:
        """
        Extract and chunk a PDF hierarchically.

        Args:
            file_path: Path to PDF file
            document_id: Unique identifier for the document
            chunk_size: Target size for text chunks (in characters)
            chunk_overlap: Overlap between chunks

        Returns:
            List of hierarchical chunks
        """
        chunks = []

        try:
            with pdfplumber.open(file_path) as pdf:
                # First pass: Extract structure and identify topics
                topics = self._extract_topics(pdf)

                # Second pass: Process content within each topic
                for topic in topics:
                    topic_chunks = self._process_topic(
                        pdf,
                        topic,
                        document_id,
                        chunk_size,
                        chunk_overlap
                    )
                    chunks.extend(topic_chunks)

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []

        return chunks

    def _extract_topics(self, pdf) -> List[Dict[str, Any]]:
        """
        Extract topics/headers from PDF to create hierarchy.

        Returns:
            List of topic dictionaries with metadata
        """
        topics = []
        current_chapter = None
        current_section = None

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = text.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Check for chapter headers
                chapter_match = self.chapter_pattern.match(line)
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    chapter_title = chapter_match.group(2).strip()
                    current_chapter = {
                        'chapter_num': chapter_num,
                        'chapter_title': chapter_title,
                        'page_start': page_num,
                        'section_num': None,
                        'section_title': None,
                        'content_start_line': i,
                        'content_start_page': page_num
                    }
                    topics.append(current_chapter)
                    current_section = None
                    continue

                # Check for section headers (only if we're in a chapter)
                section_match = self.section_pattern.match(line)
                if section_match and current_chapter:
                    section_num = section_match.group(1)
                    section_title = section_match.group(2).strip()
                    current_section = {
                        'chapter_num': current_chapter['chapter_num'],
                        'chapter_title': current_chapter['chapter_title'],
                        'section_num': section_num,
                        'section_title': section_title,
                        'page_start': page_num,
                        'content_start_line': i,
                        'content_start_page': page_num
                    }
                    topics.append(current_section)

        # If no topics found, create a default one
        if not topics:
            topics.append({
                'chapter_num': None,
                'chapter_title': 'Document Content',
                'section_num': None,
                'section_title': None,
                'page_start': 1,
                'content_start_line': 0,
                'content_start_page': 1
            })

        return topics

    def _process_topic(
        self,
        pdf,
        topic: Dict[str, Any],
        document_id: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[HierarchicalChunk]:
        """
        Process a single topic and create typed chunks.
        """
        chunks = []
        topic_id = str(uuid.uuid4())

        # Extract content for this topic
        topic_content = self._extract_topic_content(pdf, topic)

        if not topic_content:
            return chunks

        # Split content into paragraphs
        paragraphs = self._split_into_paragraphs(topic_content)

        # Group paragraphs into chunks by type
        current_text = ""
        current_type = ChunkType.OTHER

        for para in paragraphs:
            # Classify paragraph type
            para_type = self._classify_content_type(para)

            # If type changes or chunk gets too large, create a chunk
            if (para_type != current_type and current_text) or \
               len(current_text) >= chunk_size:

                if current_text.strip():
                    chunk = self._create_chunk(
                        document_id=document_id,
                        topic=topic,
                        topic_id=topic_id,
                        text=current_text.strip(),
                        chunk_type=current_type
                    )
                    chunks.append(chunk)

                current_text = para
                current_type = para_type
            else:
                current_text += "\n\n" + para
                if current_type == ChunkType.OTHER:
                    current_type = para_type

        # Add remaining content
        if current_text.strip():
            chunk = self._create_chunk(
                document_id=document_id,
                topic=topic,
                topic_id=topic_id,
                text=current_text.strip(),
                chunk_type=current_type
            )
            chunks.append(chunk)

        return chunks

    def _extract_topic_content(
        self,
        pdf,
        topic: Dict[str, Any]
    ) -> str:
        """
        Extract text content for a specific topic from PDF.
        """
        content_parts = []
        start_page = topic['content_start_page'] - 1  # 0-indexed

        # For now, extract from start page to end (or until next topic)
        # In production, you'd want to track end pages too
        for page_num in range(start_page, len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text() or ""
            content_parts.append(text)

            # Stop after collecting reasonable amount
            if len(' '.join(content_parts)) > 5000:
                break

        return '\n'.join(content_parts)

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into meaningful paragraphs.
        """
        # Split on double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)

        # Filter out very short paragraphs (likely artifacts)
        return [p.strip() for p in paragraphs if len(p.strip()) > 50]

    def _classify_content_type(self, text: str) -> ChunkType:
        """
        Classify a text segment into Concept, Example, or Question.
        """
        text_lower = text.lower()

        # Count keyword matches
        example_score = sum(
            1 for keyword in self.example_keywords
            if keyword in text_lower
        )
        question_score = sum(
            1 for keyword in self.question_keywords
            if keyword in text_lower
        )
        concept_score = sum(
            1 for keyword in self.concept_keywords
            if keyword in text_lower
        )

        # Additional heuristics
        # Questions often end with question marks or have "find", "calculate"
        if '?' in text or any(word in text_lower[:100] for word in ['calculate', 'solve', 'find the']):
            question_score += 2

        # Examples often have numbers and calculations
        if re.search(r'\d+', text) and self.equation_pattern.search(text):
            example_score += 1

        # Concepts often have definitions or explanations
        if any(phrase in text_lower for phrase in ['is defined as', 'refers to', 'means that']):
            concept_score += 2

        # Determine type based on highest score
        scores = {
            ChunkType.CONCEPT: concept_score,
            ChunkType.EXAMPLE: example_score,
            ChunkType.QUESTION: question_score
        }

        max_score = max(scores.values())
        if max_score == 0:
            return ChunkType.OTHER

        return max(scores, key=scores.get)

    def _create_chunk(
        self,
        document_id: str,
        topic: Dict[str, Any],
        topic_id: str,
        text: str,
        chunk_type: ChunkType
    ) -> HierarchicalChunk:
        """
        Create a hierarchical chunk with metadata.
        """
        chunk_id = str(uuid.uuid4())

        # Extract metadata
        key_terms = self._extract_key_terms(text)
        equations = self._extract_equations(text)

        topic_metadata = TopicMetadata(
            chapter_num=topic.get('chapter_num'),
            chapter_title=topic.get('chapter_title'),
            section_num=topic.get('section_num'),
            section_title=topic.get('section_title'),
            page_start=topic.get('page_start'),
            page_end=topic.get('page_start')  # For now, same page
        )

        chunk_metadata = ChunkMetadata(
            chunk_type=chunk_type,
            topic_id=topic_id,
            key_terms=key_terms,
            equations=equations,
            has_equations=len(equations) > 0,
            has_diagrams=self._has_diagram_reference(text)
        )

        return HierarchicalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            topic_metadata=topic_metadata,
            chunk_metadata=chunk_metadata,
            text=text
        )

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text (simplified version).
        """
        # Look for capitalized terms (potential key concepts)
        # This is a simple heuristic - in production, use NLP
        terms = []

        # Find terms in quotes
        quoted = re.findall(r'"([^"]+)"', text)
        terms.extend(quoted)

        # Find capitalized multi-word terms (not at sentence start)
        capitalized = re.findall(r'(?<!^)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        terms.extend(capitalized)

        return list(set(terms))[:10]  # Limit to 10 terms

    def _extract_equations(self, text: str) -> List[str]:
        """
        Extract equations from text.
        """
        equations = []

        # Find lines with equals signs and mathematical operators
        lines = text.split('\n')
        for line in lines:
            if self.equation_pattern.search(line) or self.formula_pattern.search(line):
                # Clean up the equation
                eq = line.strip()
                if len(eq) < 100:  # Reasonable equation length
                    equations.append(eq)

        return equations[:5]  # Limit to 5 equations

    def _has_diagram_reference(self, text: str) -> bool:
        """
        Check if text references diagrams or figures.
        """
        diagram_keywords = ['figure', 'diagram', 'fig.', 'illustration', 'graph', 'chart']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in diagram_keywords)
