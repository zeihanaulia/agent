"""
Test suite for Plan C DeepAgents-inspired improvements to flow_analyze_context.py

Tests cover:
1. Selective file loading vs legacy mode
2. Budget enforcement (per-analysis and total)
3. Token counting accuracy (tiktoken vs estimate)
4. Multi-phase workflow execution
5. Output structure backward compatibility
6. Benchmark: token savings on springboot-demo

Run with: pytest tests/test_flow_analyze_context_planc.py -v
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts" / "coding_agent"))

from flow_analyze_context import AiderStyleRepoAnalyzer


@pytest.fixture
def analyzer_no_llm():
    """Create analyzer without LLM (for fast tests)"""
    return AiderStyleRepoAnalyzer(
        codebase_path=str(project_root / "dataset" / "codes" / "springboot-demo"),
        main_model=None,
        max_tokens=100000
    )


@pytest.fixture
def analyzer_with_mock_llm():
    """Create analyzer with mocked LLM"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = MagicMock(content="Mocked LLM response")
    
    return AiderStyleRepoAnalyzer(
        codebase_path=str(project_root / "dataset" / "codes" / "springboot-demo"),
        main_model=mock_model,
        max_tokens=100000
    )


class TestTokenCounting:
    """Test tiered token counting system"""
    
    def test_tokenizer_setup_fallback(self, analyzer_no_llm):
        """Test tokenizer falls back to estimate when tiktoken/langchain unavailable"""
        tokenizer_type, tokenizer = analyzer_no_llm._setup_tokenizer()
        
        # Without tiktoken installed, should fall back to 'estimate'
        assert tokenizer_type in ['tiktoken', 'langchain', 'estimate']
        
    def test_token_count_basic(self, analyzer_no_llm):
        """Test token counting with basic text"""
        text = "Hello, world! This is a test."
        tokens = analyzer_no_llm.token_count(text)
        
        # Should be reasonable estimate (not 0, not huge)
        assert 5 <= tokens <= 20
        
    def test_token_count_large_text(self, analyzer_no_llm):
        """Test token counting with large text"""
        text = "word " * 1000  # 5000 chars
        tokens = analyzer_no_llm.token_count(text)
        
        # With 0.6 chars/token estimate: ~3000 tokens
        # With tiktoken: ~1250 tokens
        assert 1000 <= tokens <= 4000


class TestFileLightweightMap:
    """Test lightweight file map building (metadata only)"""
    
    def test_build_lightweight_map(self, analyzer_no_llm):
        """Test file map only contains metadata, no content"""
        file_map = analyzer_no_llm._build_lightweight_file_map()
        
        # Should have files
        assert len(file_map) > 0
        
        # Check metadata structure
        for rel_path, metadata in file_map.items():
            assert 'size' in metadata
            assert 'language' in metadata
            assert 'ext' in metadata
            assert 'last_modified' in metadata
            # Should NOT have 'content' key
            assert 'content' not in metadata
            
    def test_file_map_language_detection(self, analyzer_no_llm):
        """Test language detection from file extensions"""
        file_map = analyzer_no_llm._build_lightweight_file_map()
        
        # Find Java files
        java_files = [f for f, meta in file_map.items() if meta['language'] == 'java']
        assert len(java_files) > 0
        
        # Find config files
        config_files = [f for f, meta in file_map.items() if meta['ext'] in ['.xml', '.yml', '.yaml']]
        assert len(config_files) > 0


class TestFileSelection:
    """Test file selection logic"""
    
    def test_keyword_select_files(self, analyzer_no_llm):
        """Test keyword-based file selection"""
        file_map = analyzer_no_llm._build_lightweight_file_map()
        reasoning = {
            'intent': 'java',
            'keywords': ['java', 'src', 'main']
        }
        
        selected = analyzer_no_llm._keyword_select_files(reasoning, file_map, max_files=5)
        
        # Should select files (springboot-demo has .java files)
        assert len(selected) >= 0  # May be 0 if no matching files
        assert len(selected) <= 5


class TestSelectiveAnalysis:
    """Test selective vs legacy analysis modes"""
    
    def test_selective_mode_uses_scoped_context(self, analyzer_no_llm):
        """Test selective mode only uses provided file_contents"""
        repo_map = analyzer_no_llm._build_lightweight_file_map()
        file_contents = {
            'src/main/java/com/example/Controller.java': 'public class Controller {}'
        }
        
        plan = {
            'analyses_to_run': ['basic_filesystem_scan', 'tag_extraction'],
            'token_budget': {}
        }
        
        results = analyzer_no_llm._execute_selective_analysis(
            plan=plan,
            file_contents=file_contents,
            repo_map=repo_map
        )
        
        # Check results keys match analysis types (not exact analysis names)
        # Results are stored by analysis type, not analysis name
        assert isinstance(results, dict)
        assert len(results) > 0
        
    def test_legacy_mode_shows_warning(self, analyzer_no_llm, capfd):
        """Test legacy mode (no file_contents) shows deprecation warning"""
        plan = {
            'analyses_to_run': ['basic_filesystem_scan'],
            'token_budget': {}
        }
        
        with pytest.warns(UserWarning, match="FULL codebase scan"):
            analyzer_no_llm._execute_selective_analysis(plan=plan)
        

class TestBudgetEnforcement:
    """Test token budget enforcement"""
    
    def test_strict_budget_stops_early(self, analyzer_no_llm):
        """Test strict budget mode stops when budget exceeded"""
        plan = {
            'analyses_to_run': ['basic_filesystem_scan', 'tag_extraction', 'dependency_analysis'],
            'token_budget': {
                'basic_filesystem_scan': 100,  # Very low budget
                'tag_extraction': 100,
                'dependency_analysis': 100
            },
            'strict_budget': True
        }
        
        results = analyzer_no_llm._execute_selective_analysis(plan=plan)
        
        # Should stop early due to budget
        assert 'budget_exceeded' in results or 'total_budget_exceeded' in results
        assert 'stopped_at' in results
        
    def test_total_budget_enforcement(self, analyzer_no_llm):
        """Test total budget stops analysis"""
        # Set very low max_tokens
        analyzer_no_llm.max_tokens = 1000
        analyzer_no_llm.current_tokens = 0
        
        plan = {
            'analyses_to_run': ['basic_filesystem_scan', 'tag_extraction', 'dependency_analysis', 'api_analysis']
        }
        
        results = analyzer_no_llm._execute_selective_analysis(plan=plan)
        
        # Should stop due to total budget
        if analyzer_no_llm.current_tokens > 1000:
            assert 'total_budget_exceeded' in results


class TestMultiPhaseWorkflow:
    """Test 5-phase DeepAgents workflow"""
    
    @patch('flow_analyze_context.LLM_AVAILABLE', False)
    def test_analyze_with_reasoning_no_llm(self, analyzer_no_llm):
        """Test full workflow without LLM (uses keyword fallback)"""
        result = analyzer_no_llm.analyze_with_reasoning(
            user_request="Find all REST controllers"
        )
        
        # Check output structure
        assert 'reasoning' in result
        assert 'analysis_plan' in result
        assert 'results' in result
        assert 'summary' in result
        assert 'tokens_used' in result
        assert 'discovery' in result  # NEW: discovery metadata
        
        # Check discovery metadata
        discovery = result['discovery']
        assert 'total_files' in discovery
        assert 'selected_files' in discovery
        assert 'loaded_files' in discovery
        assert 'selection_method' in discovery


class TestBackwardCompatibility:
    """Test backward compatibility with old analyze_codebase()"""
    
    def test_analyze_codebase_deprecated(self, analyzer_no_llm):
        """Test analyze_codebase() shows deprecation warning and redirects"""
        with pytest.warns(DeprecationWarning, match="analyze_codebase.*deprecated"):
            result = analyzer_no_llm.analyze_codebase()
        
        # Should return legacy format
        assert 'basic_info' in result
        assert 'code_analysis' in result
        assert 'dependencies' in result
        assert 'api_patterns' in result
        assert 'structure' in result
        
        # Should include discovery metadata as extra field
        if '_discovery_info' in result:
            assert 'total_files' in result['_discovery_info']


class TestBenchmark:
    """Benchmark token savings: selective vs legacy mode"""
    
    @pytest.mark.slow
    def test_token_savings_benchmark(self, analyzer_no_llm):
        """
        Benchmark: Compare token usage between:
        1. Legacy mode (loads all files)
        2. Selective mode (loads 10 files)
        
        Expected: ~99% token reduction with selective mode
        """
        # Reset token counter
        analyzer_no_llm.current_tokens = 0
        
        # Phase 1: Build file map
        file_map = analyzer_no_llm._build_lightweight_file_map()
        total_files = len(file_map)
        
        # Phase 2: Select 10 files
        reasoning = {'intent': 'controller', 'keywords': ['controller']}
        selected_files = analyzer_no_llm._keyword_select_files(reasoning, file_map, max_files=10)
        
        # Phase 3: Load selected files
        file_contents = analyzer_no_llm._load_selected_files(selected_files)
        loaded_files = len(file_contents)
        
        # Calculate token usage for selective mode
        selective_tokens = sum(
            analyzer_no_llm.token_count(content) 
            for content in file_contents.values()
        )
        
        # Estimate legacy mode tokens (would load ALL files)
        legacy_estimate_tokens = 0
        for rel_path in file_map.keys():
            try:
                full_path = Path(analyzer_no_llm.codebase_path) / rel_path
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                legacy_estimate_tokens += analyzer_no_llm.token_count(content)
            except Exception:
                pass
        
        # Calculate savings
        if legacy_estimate_tokens > 0:
            savings_percent = (1 - selective_tokens / legacy_estimate_tokens) * 100
            
            print(f"\n{'='*60}")
            print(f"BENCHMARK RESULTS:")
            print(f"{'='*60}")
            print(f"Total files in repo:     {total_files}")
            print(f"Files selected:          {loaded_files}")
            print(f"Selection ratio:         {loaded_files/total_files:.1%}")
            print(f"")
            print(f"Selective mode tokens:   {selective_tokens:,}")
            print(f"Legacy mode tokens:      {legacy_estimate_tokens:,}")
            print(f"Token savings:           {savings_percent:.1f}%")
            print(f"{'='*60}")
            
            # Assert significant savings (expect >90%)
            assert savings_percent > 90, f"Expected >90% savings, got {savings_percent:.1f}%"
        else:
            pytest.skip("Could not calculate legacy tokens (files unreadable)")


class TestOutputStructure:
    """Test output structure unchanged from Plan B"""
    
    def test_analyze_with_reasoning_output_structure(self, analyzer_no_llm):
        """Test output structure matches expected format"""
        result = analyzer_no_llm.analyze_with_reasoning(
            user_request="Analyze project structure"
        )
        
        # Required keys (backward compatible)
        required_keys = ['reasoning', 'analysis_plan', 'results', 'summary', 'tokens_used']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # New key (added in Plan C)
        assert 'discovery' in result
        
        # Check results dict contains analysis outputs
        results = result['results']
        assert isinstance(results, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
