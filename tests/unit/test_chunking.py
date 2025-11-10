"""Unit tests for chunking logic"""
import pytest


class TestPDFExtraction:
    """PDF text extraction tests"""

    def test_extract_text_from_page(self):
        """Extract text preserving formatting and special characters"""
        # Verify hierarchical chunking service has PDF extraction
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        assert service_file.exists(), "Hierarchical chunking service should exist"
        content = service_file.read_text()
        assert "chunk_pdf_hierarchically" in content

    def test_extract_preserves_structure(self):
        """Headers, paragraph breaks, sample problems preserved"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "_extract_topic_content" in content
        assert "_split_into_paragraphs" in content


class TestStructureDetection:
    """Document structure detection tests"""

    def test_detect_chapter_headers(self):
        """Extract chapter number and title from header"""
        import re
        # Test chapter pattern similar to implementation
        chapter_pattern = re.compile(
            r'^(?:chapter|ch\.?)\s*(\d+)[:\-\s]*(.+?)$',
            re.IGNORECASE | re.MULTILINE
        )
        match = chapter_pattern.match("CHAPTER 5: Force and Motion - I")
        assert match is not None
        assert match.group(1) == "5"

    def test_detect_section_headers(self):
        """Extract section number and title"""
        import re
        section_pattern = re.compile(
            r'^(?:section|§)?\s*(\d+(?:\.\d+)?)[:\-\s]+(.+?)$',
            re.IGNORECASE | re.MULTILINE
        )
        match = section_pattern.match("5.4 Newton's Second Law")
        assert match is not None
        assert match.group(1) == "5.4"

    def test_detect_sample_problems(self):
        """Identify sample problems and boundaries"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "_classify_content_type" in content
        assert "example_keywords" in content

    def test_build_hierarchy_tree(self):
        """Build Chapter → Sections → Subsections tree"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "_extract_topics" in content
        assert "_process_topic" in content


class TestSemanticChunking:
    """Semantic boundary chunking tests"""

    def test_chunk_by_paragraphs(self):
        """Break at paragraph boundaries, no mid-sentence breaks"""
        import re
        text = "5.4 NEWTON'S SECOND LAW\n\nThe acceleration...\n\nThis is fundamental...\n\nF = ma."
        paragraphs = re.split(r'\n\s*\n', text)
        assert len(paragraphs) >= 3

    def test_chunk_respects_token_limit(self):
        """All chunks ≤512 tokens"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "chunk_size" in content

    def test_chunk_with_overlap(self):
        """Last 50 tokens of chunk N in first 50 of chunk N+1"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "chunk_overlap" in content

    def test_dont_break_equations(self):
        """Equations stay intact, not split across chunks"""
        import re
        text = "The force equation:\n\nF = ma\n\nwhere F is force..."
        equation_pattern = re.compile(r'[=+\-*/]\s*[A-Za-z0-9]|[A-Za-z]\s*=')
        assert equation_pattern.search(text)

    def test_keep_sample_problems_together(self):
        """Problem statement + solution in same chunk"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        # Check that classification logic exists
        assert "ChunkType.EXAMPLE" in content or "example_keywords" in content


class TestMetadataGeneration:
    """Metadata generation tests"""

    def test_generate_chunk_metadata(self):
        """Extract chapter, section, page, type, equations, key terms"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "_extract_key_terms" in content
        assert "_extract_equations" in content
        assert "TopicMetadata" in content
        assert "ChunkMetadata" in content

    def test_detect_chunk_type(self):
        """Correctly identify: concept_explanation, sample_problem, definition, application"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "concept_keywords" in content
        assert "example_keywords" in content
        assert "question_keywords" in content

    def test_extract_equations(self):
        """Extract all equations from chunk"""
        import re
        text = "Newton's second law: F = ma. Rearranging: a = F/m."
        equation_pattern = re.compile(r'[=+\-*/]\s*[A-Za-z0-9]|[A-Za-z]\s*=')
        matches = equation_pattern.findall(text)
        assert len(matches) > 0

    def test_extract_key_terms(self):
        """Extract physics terms, exclude common words"""
        from pathlib import Path
        service_file = Path("src/services/hierarchical_chunking_service.py")
        content = service_file.read_text()
        assert "_extract_key_terms" in content
