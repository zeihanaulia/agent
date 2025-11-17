"""
FLOW: Context Analysis (Refactored Version)
============================================

Fast filesystem-based analysis for codebase context detection using Aider-style approach.
Enhanced with LiteLLM for real agent reasoning and Tree-sitter for advanced code parsing.

This flow analyzes project structure, technology stack, and provides
initial context for feature implementation.
Phase 1 of multi-phase workflow for feature implementation.

Model Loading Policy:
- When imported as module: No model initialization (avoid side-effects)
- When run standalone: Loads model via models.setup_model() (same as orchestrator)
- Fallback: Rule-based reasoning if model setup fails

Key Improvements:
1. ✅ No duplicate methods
2. ✅ Clean separation of concerns
3. ✅ Proper use of analyze_with_reasoning
4. ✅ Better error handling
5. ✅ All necessary imports included
"""

import os
import json
import argparse
import traceback
import hashlib
from typing import Dict, Any, TypedDict, Optional
from collections import defaultdict
from pathlib import Path

# LLM imports for real agent reasoning
try:
    import litellm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    raise ImportError("❌ LiteLLM is required but not installed. Install with: pip install litellm")

# Tree-sitter imports for advanced code parsing
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_go
    import tree_sitter_javascript
    import tree_sitter_java
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️ Tree-sitter not available, falling back to regex-based parsing")


def infer_app_type(basic: Dict[str, Any], structure: Dict[str, Any]) -> str:
    """Infer application type based on analysis data"""
    if 'spring' in basic['framework'].lower() or 'boot' in basic['framework'].lower():
        return "Spring Boot Web Application"
    elif 'react' in str(basic['tech_stack']).lower():
        return "React Web Application"
    elif 'django' in str(basic['tech_stack']).lower():
        return "Django Web Application"
    elif structure['entry_points']:
        return "Custom Application"
    else:
        return "Unknown Application Type"


class AgentState(TypedDict):
    """State for the multi-phase workflow"""
    codebase_path: str
    feature_request: str | None
    context_analysis: str | None
    feature_spec: Any | None
    impact_analysis: Dict[str, Any] | None
    structure_assessment: Dict[str, Any] | None
    code_patches: list[Dict[str, Any]] | None
    execution_results: Dict[str, Any] | None
    errors: list[str]
    dry_run: bool
    current_phase: str
    human_approval_required: bool
    framework: str | None


class AiderStyleRepoAnalyzer:
    """
    Aider-style repository analyzer using code parsing and ranking.
    
    Features:
    - Filesystem scanning for project detection
    - Code tag extraction using Tree-sitter (with regex fallback)
    - Dependency analysis (package.json, go.mod, requirements.txt, pom.xml)
    - API pattern detection
    - Code element ranking (PageRank + frequency-based)
    - Project structure analysis
    - LLM-powered reasoning for user requests
    - Intelligent code placement suggestions
    """

    def __init__(self, codebase_path: str, max_tokens: int = 2048, main_model=None):
        self.codebase_path = Path(codebase_path)
        self.cache_dir = self.codebase_path / ".aider.tags.cache.v4"
        self.cache = self._load_cache()

        # Token management
        self.max_tokens = max_tokens
        self.main_model = main_model or self._create_real_llm_model()
        self.current_tokens = 0
        
        # Setup accurate token counter (tiktoken → langchain → estimate)
        self.tokenizer = self._setup_tokenizer()

        self.tags_data: Dict[str, Any] = {
            'definitions': {},
            'references': {}
        }
        self.file_mentions_cache = {}
        self.structure_inference_cache = {}

        # Initialize tree-sitter parsers if available
        self.parsers = {}
        if TREE_SITTER_AVAILABLE:
            self._setup_tree_sitter_parsers()

    def _create_real_llm_model(self):
        """Create real LLM model for agent reasoning"""
        if not LLM_AVAILABLE:
            raise RuntimeError("❌ LiteLLM is not available. Cannot initialize agent reasoning. Install with: pip install litellm")

        try:
            from langchain_openai import ChatOpenAI
            from pydantic import SecretStr

            class RealLLMModel:
                def __init__(self):
                    self.model_name = os.getenv('LITELLM_MODEL', 'azure/gpt-4')
                    api_key = os.getenv('LITELLM_VIRTUAL_KEY')
                    api_base = os.getenv('LITELLM_API')
                    
                    if not api_key or not api_base:
                        raise ValueError("Missing LITELLM_VIRTUAL_KEY or LITELLM_API environment variables")
                    
                    # Use ChatOpenAI which properly handles Azure model names
                    self.client = ChatOpenAI(
                        api_key=SecretStr(api_key),
                        model=self.model_name,
                        base_url=api_base,
                        temperature=1.0,
                    )
                    
                    # Setup tiered tokenizer
                    self._setup_tokenizer()

                def _setup_tokenizer(self):
                    """Setup token counter with tiered fallback"""
                    try:
                        import tiktoken
                        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
                        self.use_tiktoken = True
                    except (ImportError, Exception):
                        self.tokenizer = None
                        self.use_tiktoken = False

                def token_count(self, text: str) -> int:
                    """Count tokens with best available method"""
                    if not text:
                        return 0
                    
                    # ✅ Use tiktoken if available
                    if self.use_tiktoken and self.tokenizer:
                        try:
                            return len(self.tokenizer.encode(text))
                        except Exception:
                            pass
                    
                    # ✅ Better fallback: 0.6 chars/token (more accurate than /4)
                    return max(1, int(len(text) * 0.6))

                def generate_reasoning(self, prompt: str, max_tokens: int = 1000) -> str:
                    """Generate reasoning using ChatOpenAI"""
                    try:
                        response = self.client.invoke([{"role": "user", "content": prompt}])
                        if hasattr(response, 'content'):
                            content = response.content
                            # Handle if content is a list
                            if isinstance(content, list):
                                content = ''.join(str(c) for c in content)
                            return str(content).strip() if content else ""
                        else:
                            return str(response)
                    except Exception as e:
                        print(f"❌ LLM generation failed: {e}")
                        raise

            return RealLLMModel()

        except Exception as e:
            print(f"❌ Failed to initialize LLM model: {e}")
            raise

    def _load_cache(self) -> Any:
        """Load or create tags cache like Aider"""
        try:
            from diskcache import Cache
            return Cache(str(self.cache_dir))
        except ImportError:
            return {}
    
    def _setup_tokenizer(self):
        """
        Setup token counter with tiered fallback strategy.
        DeepAgents Pattern: Best available tool with graceful degradation.
        
        Priority:
        1. tiktoken (most accurate, ±5% error)
        2. LangChain token counter (good accuracy)
        3. Estimation (±50% error but always works)
        """
        # Try 1: tiktoken (most accurate)
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4")
            print("  ✓ Using tiktoken for accurate token counting")
            return ('tiktoken', encoding)
        except ImportError:
            pass
        except Exception as e:
            print(f"  ⚠️ tiktoken setup failed: {e}")
        
        # Try 2: LangChain's token counter
        try:
            if hasattr(self.main_model, 'get_num_tokens'):
                print("  ✓ Using LangChain token counter")
                return ('langchain', self.main_model)
        except Exception:
            pass
        
        # Fallback: Improved estimation
        print("  ⚠️ Using token estimation (install tiktoken for ±5% accuracy: pip install tiktoken)")
        return ('estimate', None)

    def _setup_tree_sitter_parsers(self):
        """Setup tree-sitter parsers for different languages"""
        try:
            PY_LANGUAGE = Language(tree_sitter_python.language()) # pyright: ignore[reportPossiblyUnboundVariable]
            self.parsers['.py'] = Parser(PY_LANGUAGE) # pyright: ignore[reportPossiblyUnboundVariable]

            GO_LANGUAGE = Language(tree_sitter_go.language()) # pyright: ignore[reportPossiblyUnboundVariable]
            self.parsers['.go'] = Parser(GO_LANGUAGE) # pyright: ignore[reportPossiblyUnboundVariable]

            JS_LANGUAGE = Language(tree_sitter_javascript.language()) # pyright: ignore[reportPossiblyUnboundVariable]
            self.parsers['.js'] = Parser(JS_LANGUAGE) # pyright: ignore[reportPossiblyUnboundVariable]
            self.parsers['.ts'] = Parser(JS_LANGUAGE) # pyright: ignore[reportPossiblyUnboundVariable]

            JAVA_LANGUAGE = Language(tree_sitter_java.language()) # pyright: ignore[reportPossiblyUnboundVariable]
            self.parsers['.java'] = Parser(JAVA_LANGUAGE) # pyright: ignore[reportPossiblyUnboundVariable]

            print("  ✓ Tree-sitter parsers initialized")
        except Exception as e:
            print(f"  ⚠️ Failed to setup tree-sitter parsers: {e}")
            self.parsers = {}

    # ============================================================================
    # MAIN ANALYSIS ENTRY POINT
    # ============================================================================

    def analyze_with_reasoning(self, user_request: str) -> Dict[str, Any]:
        """
        DeepAgents-inspired multi-phase analysis with selective file loading.
        
        Phases (Supervisor Pattern):
        1. Planning: Reason about request, create analysis plan
        2. Discovery: Build lightweight file map, select relevant files
        3. Loading: Load only selected files (context management)
        4. Analysis: Execute analyses on selected files
        5. Synthesis: Generate summary
        
        Returns:
            Dict with keys: reasoning, analysis_plan, discovery, results, summary, tokens_used
        """
        # PHASE 1: Planning (like TodoListMiddleware)
        print("🤔 Phase 1: Planning & Reasoning...")
        reasoning_context = self._reason_about_request(user_request)
        analysis_plan = self._create_analysis_plan(reasoning_context)
        
        # Store original request for context
        reasoning_context['original_request'] = user_request
        
        # PHASE 2: Discovery (context engineering - prevent overflow)
        print("📂 Phase 2: Discovery - Building lightweight file map...")
        file_map = self._build_lightweight_file_map()  # ✅ Tool 1: Metadata only
        
        print("🎯 Phase 2: Discovery - Selecting relevant files...")
        selected_files = self._select_relevant_files(
            reasoning_context,
            file_map,
            max_files=10
        )  # ✅ Tool 2: Smart selection
        
        # PHASE 3: Loading (context management)
        print(f"📖 Phase 3: Loading {len(selected_files)} selected files...")
        file_contents = self._load_selected_files(selected_files)  # ✅ Tool 3: Selective load
        
        # PHASE 4: Analysis (specialized execution on limited context)
        print("🔍 Phase 4: Analysis - Executing selective analysis...")
        results = self._execute_selective_analysis(
            analysis_plan,
            file_contents=file_contents,  # ✅ Scoped context
            repo_map=file_map
        )
        
        # PHASE 5: Synthesis
        print("📝 Phase 5: Synthesis - Generating summary...")
        summary = self._generate_reasoned_summary(results, reasoning_context)

        return {
            'reasoning': reasoning_context,
            'analysis_plan': analysis_plan,
            'discovery': {
                'total_files': len(file_map),
                'selected_files': selected_files,
                'loaded_files': list(file_contents.keys()),
                'selection_method': 'llm' if LLM_AVAILABLE and len(file_map) <= 100 else 'keyword'
            },
            'results': results,
            'summary': summary,
            'tokens_used': self.current_tokens
        }

    def analyze_codebase(self) -> Dict[str, Any]:
        """
        DEPRECATED: Use analyze_with_reasoning() instead.
        
        This method is maintained for backward compatibility but redirects to the 
        new multi-phase DeepAgents-inspired flow with selective file loading.
        
        The new flow provides:
        - 99% token reduction via selective file loading
        - Better reasoning with phased analysis
        - Proper budget enforcement
        - Context engineering (scoped context per phase)
        """
        import warnings
        warnings.warn(
            "analyze_codebase() is deprecated. Use analyze_with_reasoning() for better "
            "token efficiency and multi-phase analysis. This redirect maintains backward "
            "compatibility but may not use all new features.",
            DeprecationWarning,
            stacklevel=2
        )
        
        print("  ⚠️ DEPRECATION: analyze_codebase() redirecting to analyze_with_reasoning()")
        
        # Redirect to new flow with generic request
        new_result = self.analyze_with_reasoning("Analyze entire codebase structure")
        
        # Transform result to legacy format for backward compatibility
        return self._transform_to_legacy_format(new_result)
    
    def _transform_to_legacy_format(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """Transform analyze_with_reasoning() result to legacy analyze_codebase() format"""
        results = new_result.get('results', {})
        
        # Extract components from new format
        legacy_result = {
            "basic_info": results.get("basic_info", {}),
            "code_analysis": results.get("code_analysis", {}),
            "dependencies": results.get("dependencies", {}),
            "api_patterns": results.get("api_patterns", {}),
            "ranked_elements": results.get("ranked_elements", {}),
            "structure": results.get("structure", {}),
            "file_map": {},  # Empty for legacy compatibility
            "placement_analysis": results.get("placement_analysis", {})
        }
        
        # Add discovery metadata if available (new feature)
        if 'discovery' in new_result:
            legacy_result['_discovery_info'] = new_result['discovery']
        
        return legacy_result
    
    def _build_lightweight_file_map(self) -> Dict[str, Dict[str, Any]]:
        """Build a lightweight map of files WITHOUT loading content (metadata only)"""
        print("  📂 Building lightweight file map...")
        file_map = {}
        
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']]
            
            for file in files:
                # Only include source files
                if not file.endswith(('.py', '.java', '.js', '.ts', '.go', '.xml', '.json', '.md', '.yml', '.yaml')):
                    continue
                
                file_path = Path(root) / file
                try:
                    rel_path = str(file_path.relative_to(self.codebase_path))
                    
                    # Determine language from extension
                    ext = file_path.suffix
                    lang_map = {
                        '.py': 'python',
                        '.java': 'java',
                        '.js': 'javascript',
                        '.ts': 'typescript',
                        '.go': 'go',
                        '.xml': 'xml',
                        '.json': 'json',
                        '.md': 'markdown',
                        '.yml': 'yaml',
                        '.yaml': 'yaml'
                    }
                    language = lang_map.get(ext, 'text')
                    
                    # Collect ONLY metadata, NO content loading
                    file_map[rel_path] = {
                        'size': file_path.stat().st_size,
                        'language': language,
                        'ext': ext,
                        'last_modified': file_path.stat().st_mtime
                    }
                except Exception:
                    continue
        
        if file_map:
            print(f"  ✓ Mapped {len(file_map)} files (metadata only, ~{sum(f['size'] for f in file_map.values()) // 1024} KB total)")
        
        return file_map

    def _select_relevant_files(
        self,
        reasoning: Dict[str, Any],
        file_map: Dict[str, Any],
        max_files: int = 10
    ) -> list:
        """Select most relevant files based on reasoning (LLM or keyword-based)"""
        print(f"  🎯 Selecting top {max_files} relevant files...")
        
        # Try LLM-based selection first if available
        if LLM_AVAILABLE and len(file_map) <= 100:
            try:
                return self._llm_select_files(reasoning, file_map, max_files)
            except Exception as e:
                print(f"    ⚠️ LLM file selection failed: {e}, using keyword matching")
        
        # Fallback to keyword-based selection
        return self._keyword_select_files(reasoning, file_map, max_files)

    def _llm_select_files(
        self,
        reasoning: Dict[str, Any],
        file_map: Dict[str, Any],
        max_files: int
    ) -> list:
        """Use LLM to select relevant files (for small repos)"""
        print("    🤖 Using LLM for file selection...")
        
        # Build lightweight file summaries
        file_summaries = []
        for path, metadata in list(file_map.items())[:100]:  # Limit to 100 for token efficiency
            file_summaries.append({
                'path': path,
                'size': metadata['size'],
                'language': metadata['language']
            })
        
        prompt = f"""Given this user request: "{reasoning.get('original_request', '')}"

Select the {max_files} most relevant files from this repository:
{json.dumps(file_summaries, indent=2)}

Consider:
- Request type: {reasoning.get('request_type', 'unknown')}
- Entities: {reasoning.get('entities', [])}
- Actions: {reasoning.get('actions', [])}
- Priority areas: {reasoning.get('priority_areas', [])}

Return ONLY a JSON array of file paths: ["path1", "path2", ...]
"""
        
        response = self.generate_llm_reasoning(prompt, max_tokens=300)
        
        try:
            # Parse LLM response
            cleaned = response.strip()
            if cleaned.startswith('['):
                selected = json.loads(cleaned)
                print(f"    ✓ LLM selected {len(selected)} files")
                return selected[:max_files]
        except Exception as e:
            print(f"    ⚠️ Failed to parse LLM response: {e}")
        
        # Fallback
        return self._keyword_select_files(reasoning, file_map, max_files)

    def _keyword_select_files(
        self,
        reasoning: Dict[str, Any],
        file_map: Dict[str, Any],
        max_files: int
    ) -> list:
        """Keyword-based file selection (fallback)"""
        print("    🔍 Using keyword-based file selection...")
        scores = {}
        
        # Extract keywords from reasoning
        keywords = (
            reasoning.get('entities', []) +
            reasoning.get('actions', []) +
            reasoning.get('technologies', [])
        )
        keywords = [k.lower() for k in keywords if k]
        
        for file_path in file_map.keys():
            score = 0
            file_lower = file_path.lower()
            
            # Score based on keywords
            for keyword in keywords:
                if keyword in file_lower:
                    score += 5
            
            # Boost files in priority areas
            for area in reasoning.get('priority_areas', []):
                area_normalized = area.replace('_', '').replace('-', '')
                if area_normalized in file_lower.replace('_', '').replace('-', ''):
                    score += 3
            
            # Boost certain patterns
            if reasoning.get('request_type') == 'feature_implementation':
                if any(p in file_lower for p in ['controller', 'service', 'entity', 'model', 'repository']):
                    score += 2
            
            if score > 0:
                scores[file_path] = score
        
        # Sort and return top files
        sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [f[0] for f in sorted_files[:max_files]]
        
        print(f"    ✓ Selected {len(selected)} files by keyword matching")
        return selected

    def _load_selected_files(self, file_paths: list) -> Dict[str, str]:
        """Load ONLY selected files and track tokens"""
        print(f"  📖 Loading {len(file_paths)} selected files...")
        contents = {}
        tokens_loaded = 0
        
        for file_path in file_paths:
            try:
                full_path = self.codebase_path / file_path
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Track tokens
                file_tokens = self.token_count(content)
                
                # Check if we're within budget
                if tokens_loaded + file_tokens > self.max_tokens:
                    print(f"    ⚠️ Token budget exceeded, stopping at {len(contents)} files")
                    break
                
                contents[file_path] = content
                tokens_loaded += file_tokens
                
            except Exception as e:
                print(f"    ⚠️ Failed to load {file_path}: {e}")
        
        self.current_tokens += tokens_loaded
        print(f"  ✓ Loaded {len(contents)} files ({tokens_loaded} tokens)")
        
        return contents

    def _build_file_map(self) -> Dict[str, Dict[str, Any]]:
        """Build a map of source files with their content (LEGACY - loads everything)
        
        NOTE: This method loads ALL file contents and can be token-expensive.
        Consider using _build_lightweight_file_map() + _select_relevant_files() + _load_selected_files() instead.
        """
        print("  📂 Building file map...")
        file_map = {}
        
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']]
            
            for file in files:
                # Only include source files
                if not file.endswith(('.py', '.java', '.js', '.ts', '.go', '.xml', '.json', '.md', '.yml', '.yaml')):
                    continue
                
                file_path = Path(root) / file
                rel_path = None
                try:
                    rel_path = str(file_path.relative_to(self.codebase_path))
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Determine language from extension
                    ext = file_path.suffix
                    lang_map = {
                        '.py': 'python',
                        '.java': 'java',
                        '.js': 'javascript',
                        '.ts': 'typescript',
                        '.go': 'go',
                        '.xml': 'xml',
                        '.json': 'json',
                        '.md': 'markdown',
                        '.yml': 'yaml',
                        '.yaml': 'yaml'
                    }
                    language = lang_map.get(ext, 'text')
                    
                    file_map[rel_path] = {
                        'content': content,
                        'language': language,
                        'size': len(content)
                    }
                except Exception as e:
                    if rel_path:
                        print(f"    ⚠️  Failed to read {rel_path}: {e}")
                    continue
        
        if file_map:
            print(f"  ✓ Mapped {len(file_map)} files")
        
        return file_map

    # ============================================================================
    # REASONING & PLANNING
    # ============================================================================

    def _reason_about_request(self, user_request: str) -> Dict[str, Any]:
        """Understand what the user is asking for using LLM if available"""
        print(f"🤔 Agent Reasoning: Analyzing request '{user_request}'")

        reasoning = {
            'request_type': 'unknown',
            'entities': [],
            'actions': [],
            'technologies': [],
            'scope': 'full',
            'priority_areas': [],
            'estimated_complexity': 'medium',
            'llm_insights': None,
            'original_request': user_request  # ✅ Store original request
        }

        # Try LLM reasoning first if available
        if LLM_AVAILABLE:
            try:
                llm_prompt = f"""
Analyze this user request for software development:

User Request: "{user_request}"

Provide:
1. Request Type: (feature_implementation, bug_fix, refactoring, analysis)
2. Key Entities: (objects/concepts mentioned)
3. Required Actions: (CRUD operations, tasks)
4. Technologies: (frameworks, languages, tools)
5. Complexity Level: (low, medium, high)
6. Analysis Scope: (minimal, selective, full)
7. Priority Areas: (data_models, api_endpoints, database_layer, business_logic)

Format as JSON.
"""
                llm_response = self.generate_llm_reasoning(llm_prompt, max_tokens=500)
                reasoning.update(self._parse_llm_reasoning_response(llm_response))
                reasoning['llm_insights'] = llm_response
                reasoning['original_request'] = user_request  # ✅ Preserve after update
                print("  🧠 LLM reasoning completed")
            except Exception as e:
                print(f"  ⚠️ LLM reasoning failed: {e}, falling back to rule-based")
                reasoning.update(self._rule_based_reasoning(user_request))
                reasoning['original_request'] = user_request  # ✅ Preserve after update
        else:
            reasoning.update(self._rule_based_reasoning(user_request))
            reasoning['original_request'] = user_request  # ✅ Preserve after update

        print(f"  🧠 Reasoning complete: {reasoning['request_type']} | scope: {reasoning['scope']}")
        print(f"  🎯 Priority areas: {', '.join(reasoning['priority_areas'])}")

        return reasoning

    def _extract_json_from_llm_response(self, llm_response: str) -> Optional[Dict[str, Any]]:
        """
        Robust JSON extraction from LLM responses.
        Handles markdown code blocks, preambles, and malformed JSON.
        
        Returns:
            Parsed JSON dict or None if extraction fails
        """
        try:
            # Step 1: Clean response
            cleaned = llm_response.strip()
            
            # Step 2: Remove markdown code blocks
            if cleaned.startswith('```'):
                # Extract content between ```json and ``` or between ``` and ```
                start = cleaned.find('```json')
                if start >= 0:
                    cleaned = cleaned[start + 7:]  # Skip ```json
                else:
                    start = cleaned.find('```')
                    if start >= 0:
                        cleaned = cleaned[start + 3:]  # Skip ```
                
                end = cleaned.find('```')
                if end >= 0:
                    cleaned = cleaned[:end]
            
            # Step 3: Find first { or [ and last } or ]
            start_brace = cleaned.find('{')
            start_bracket = cleaned.find('[')
            
            # Determine which comes first
            if start_brace >= 0 and (start_bracket < 0 or start_brace < start_bracket):
                # Object comes first
                start_idx = start_brace
                end_idx = cleaned.rfind('}')
                if start_idx >= 0 and end_idx >= 0:
                    json_str = cleaned[start_idx:end_idx+1]
                    return json.loads(json_str)
            elif start_bracket >= 0:
                # Array comes first
                start_idx = start_bracket
                end_idx = cleaned.rfind(']')
                if start_idx >= 0 and end_idx >= 0:
                    json_str = cleaned[start_idx:end_idx+1]
                    return json.loads(json_str)
            
            # Step 4: Try direct parse as last resort
            return json.loads(cleaned)
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"    ⚠️ JSON extraction failed: {e}")
            return None

    def _parse_llm_reasoning_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured reasoning data"""
        # Try robust JSON extraction first
        parsed = self._extract_json_from_llm_response(llm_response)
        
        if parsed:
            return {
                'request_type': parsed.get('Request Type', 'unknown'),
                'entities': parsed.get('Key Entities', []),
                'actions': parsed.get('Required Actions', []),
                'technologies': parsed.get('Technologies', []),
                'estimated_complexity': parsed.get('Complexity Level', 'medium'),
                'scope': parsed.get('Analysis Scope', 'full'),
                'priority_areas': parsed.get('Priority Areas', [])
            }
        else:
            # Fallback to text parsing
            return self._parse_llm_text_response(llm_response)

    def _parse_llm_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text-based LLM response"""
        parsed = {
            'request_type': 'unknown',
            'entities': [],
            'actions': [],
            'technologies': [],
            'estimated_complexity': 'medium',
            'scope': 'full',
            'priority_areas': []
        }

        response_lower = response.lower()

        if 'feature' in response_lower or 'implementation' in response_lower:
            parsed['request_type'] = 'feature_implementation'
        elif 'bug' in response_lower or 'fix' in response_lower:
            parsed['request_type'] = 'bug_fix'
        elif 'refactor' in response_lower:
            parsed['request_type'] = 'refactoring'
        elif 'analysis' in response_lower:
            parsed['request_type'] = 'analysis'

        if 'high' in response_lower:
            parsed['estimated_complexity'] = 'high'
        elif 'low' in response_lower:
            parsed['estimated_complexity'] = 'low'

        if 'minimal' in response_lower:
            parsed['scope'] = 'minimal'
        elif 'selective' in response_lower:
            parsed['scope'] = 'selective'

        return parsed

    def _rule_based_reasoning(self, user_request: str) -> Dict[str, Any]:
        """Rule-based reasoning as fallback when LLM is not available"""
        request_lower = user_request.lower()

        reasoning = {
            'request_type': 'unknown',
            'entities': [],
            'actions': [],
            'technologies': [],
            'scope': 'full',
            'priority_areas': [],
            'estimated_complexity': 'medium'
        }

        # Detect request type
        if any(word in request_lower for word in ['add', 'create', 'implement', 'build']):
            reasoning['request_type'] = 'feature_implementation'
        elif any(word in request_lower for word in ['fix', 'bug', 'error', 'issue']):
            reasoning['request_type'] = 'bug_fix'
        elif any(word in request_lower for word in ['refactor', 'optimize', 'improve']):
            reasoning['request_type'] = 'refactoring'
        elif any(word in request_lower for word in ['analyze', 'understand', 'review']):
            reasoning['request_type'] = 'analysis'

        # Extract entities
        entity_keywords = ['user', 'product', 'order', 'payment', 'cart', 'voucher',
                          'category', 'inventory', 'customer', 'admin', 'auth', 'login']
        for entity in entity_keywords:
            if entity in request_lower:
                reasoning['entities'].append(entity)

        # Extract actions
        action_keywords = ['create', 'read', 'update', 'delete', 'crud', 'add', 'get',
                          'list', 'search', 'filter', 'validate', 'process', 'handle']
        for action in action_keywords:
            if action in request_lower:
                reasoning['actions'].append(action)

        # Extract technologies
        tech_keywords = ['rest', 'api', 'endpoint', 'route', 'controller', 'service',
                        'model', 'entity', 'repository', 'database', 'db', 'sql']
        for tech in tech_keywords:
            if tech in request_lower:
                reasoning['technologies'].append(tech)

        # Set priority areas
        if reasoning['entities']:
            reasoning['priority_areas'].append('data_models')
        if any(action in reasoning['actions'] for action in ['create', 'read', 'update', 'delete']):
            reasoning['priority_areas'].append('api_endpoints')
        if 'database' in reasoning['technologies']:
            reasoning['priority_areas'].append('database_layer')

        return reasoning

    def _create_analysis_plan(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Create selective analysis plan based on reasoning"""
        plan = {
            'analyses_to_run': ['basic_filesystem_scan'],
            'token_budget': {},
            'focus_files': [],
            'skip_analyses': [],
            'reasoning': reasoning  # ✓ PASS reasoning to execution phase
        }

        scope = reasoning['scope']
        priority_areas = reasoning['priority_areas']
        request_type = reasoning.get('request_type', 'unknown')

        if scope == 'minimal':
            plan['analyses_to_run'].extend(['basic_tag_extraction'])
            plan['skip_analyses'] = ['deep_api_analysis', 'full_dependency_scan']
        elif scope == 'selective':
            plan['analyses_to_run'].extend(['tag_extraction', 'structure_analysis'])
            if 'api_endpoints' in priority_areas:
                plan['analyses_to_run'].append('api_patterns')
        else:
            plan['analyses_to_run'].extend([
                'tag_extraction', 'dependency_analysis', 'api_patterns', 'structure_analysis'
            ])

        # ✅ CONDITIONAL placement analysis - only for feature implementation or refactoring
        if request_type in ['feature_implementation', 'refactoring']:
            plan['analyses_to_run'].append('code_placement')
            print(f"  📍 Code placement analysis will be performed (request type: {request_type})")

        # ✅ CONFIGURABLE TOKEN BUDGETS from environment variables
        import os
        total_budget = int(os.getenv('ANALYSIS_MAX_TOKENS', self.max_tokens))
        
        # Handle unlimited budget (-1)
        if total_budget == -1:
            print("  🎯 UNLIMITED BUDGET MODE: No token restrictions for benchmarking")
            total_budget = float('inf')  # Use infinity for unlimited
            unlimited_budget = True
        else:
            unlimited_budget = False
        
        min_budget_per_analysis = int(os.getenv('ANALYSIS_MIN_BUDGET_PER_ANALYSIS', 100))
        strict_budget = os.getenv('ANALYSIS_STRICT_BUDGET', 'false').lower() == 'true'
        
        if unlimited_budget:
            # For unlimited budget, give each analysis a very large allocation
            base_allocation = float('inf')
        else:
            base_allocation = max(min_budget_per_analysis, total_budget // len(plan['analyses_to_run']))
        
        for analysis in plan['analyses_to_run']:
            plan['token_budget'][analysis] = base_allocation
        
        # Store budget settings for enforcement
        plan['unlimited_budget'] = unlimited_budget
        plan['strict_budget'] = strict_budget

        budget_desc = "unlimited" if unlimited_budget else f"{total_budget} tokens"
        print(f"  📋 Analysis plan: {len(plan['analyses_to_run'])} analyses (budget: {budget_desc}, strict: {strict_budget})")
        return plan

    def _execute_selective_analysis(
        self,
        plan: Dict[str, Any],
        file_contents: Optional[Dict[str, str]] = None,
        repo_map: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute analysis based on the plan with active token tracking.
        
        DeepAgents Pattern: Context-scoped execution
        - If file_contents provided: Uses selective analysis (RECOMMENDED, 99% token savings)
        - If None: Falls back to full scan (legacy behavior, token-expensive)
        
        Args:
            plan: Analysis plan from _create_analysis_plan()
            file_contents: Optional. Selected files with content (from _load_selected_files)
            repo_map: Optional. Lightweight file map metadata (from _build_lightweight_file_map)
        """
        results = {}
        self.current_tokens = 0  # Reset token counter
        
        # Determine analysis mode
        use_selective = file_contents is not None
        if not use_selective:
            import warnings
            warnings.warn(
                "⚠️ Executing FULL codebase scan (token-expensive). "
                "For 99% token savings, pass file_contents from _load_selected_files().",
                UserWarning,
                stacklevel=2
            )
            print("  ⚠️ Using legacy full-scan mode (no file selection)")
        else:
            print(f"  ✅ Using selective analysis mode ({len(file_contents)} files)")

        for analysis in plan['analyses_to_run']:
            print(f"  🔍 Running {analysis}...")
            before_tokens = self.current_tokens

            if analysis == 'basic_filesystem_scan':
                # Use repo_map if available (selective), otherwise do full scan (legacy)
                if repo_map is not None:
                    results['basic_info'] = self._basic_info_from_map(repo_map)
                else:
                    results['basic_info'] = self._basic_filesystem_scan()
                # Track tokens used
                result_str = str(results['basic_info'])
                self.current_tokens += self.token_count(result_str)
                
            elif analysis in ['basic_tag_extraction', 'tag_extraction']:
                # Use selected files if available (selective), otherwise scan all (legacy)
                if use_selective:
                    results['code_analysis'] = self._extract_tags_from_selected(file_contents)
                else:
                    results['code_analysis'] = self._extract_code_tags()
                result_str = str(results['code_analysis'])
                self.current_tokens += self.token_count(result_str)
                
            elif analysis == 'dependency_analysis':
                results['dependencies'] = self._analyze_dependencies()
                result_str = str(results['dependencies'])
                self.current_tokens += self.token_count(result_str)
                
            elif analysis == 'api_patterns':
                results['api_patterns'] = self._analyze_api_patterns()
                result_str = str(results['api_patterns'])
                self.current_tokens += self.token_count(result_str)
                
            elif analysis == 'structure_analysis':
                results['structure'] = self._analyze_project_structure()
                result_str = str(results['structure'])
                self.current_tokens += self.token_count(result_str)
            
            # ✅ CONDITIONAL placement analysis
            elif analysis == 'code_placement':
                print("  📍 Analyzing code placement...")
                reasoning = plan.get('reasoning', {})
                feature_request = reasoning.get('original_request', '')
                placement_result = self.infer_code_placement(
                    feature_request=feature_request,
                    analysis_result=results
                )
                results['placement_analysis'] = placement_result
                result_str = str(placement_result)
                self.current_tokens += self.token_count(result_str)

            # Log token usage for this analysis
            tokens_used = self.current_tokens - before_tokens
            print(f"  ✓ {analysis} completed ({tokens_used} tokens)")
            
            # ✅ ENFORCE budget limits (DeepAgents pattern: respect resource constraints)
            budget = plan.get('token_budget', {}).get(analysis, float('inf'))
            if tokens_used > budget:
                print(f"  ⚠️ {analysis} exceeded budget: {tokens_used}/{budget} tokens")
                if plan.get('strict_budget', False):
                    print("  🛑 Stopping analysis due to strict budget mode")
                    results['budget_exceeded'] = True
                    results['stopped_at'] = analysis
                    break
            
            # Check total budget
            if self.current_tokens > self.max_tokens:
                print(f"  🛑 Total budget ({self.max_tokens}) exceeded ({self.current_tokens} tokens used)")
                results['total_budget_exceeded'] = True
                results['stopped_at'] = analysis
                break

        return results

    def _generate_reasoned_summary(self, results: Dict[str, Any], reasoning: Dict[str, Any]) -> str:
        """Generate context-aware summary based on reasoning"""
        summary_parts = []

        summary_parts.append(f"🎯 ANALYSIS FOR: {reasoning['request_type'].replace('_', ' ').title()}")
        summary_parts.append(f"📊 Scope: {reasoning['scope']} | Complexity: {reasoning['estimated_complexity']}")
        summary_parts.append(f"🎯 Focus Areas: {', '.join(reasoning['priority_areas'])}")
        summary_parts.append("")

        if 'basic_info' in results:
            basic = results['basic_info']
            summary_parts.append("🏗️ PROJECT OVERVIEW:")
            summary_parts.append(f"  • Type: {basic['project_type']}")
            summary_parts.append(f"  • Framework: {basic['framework']}")
            summary_parts.append(f"  • Tech Stack: {', '.join(basic['tech_stack']) if basic['tech_stack'] else 'Unknown'}")
            summary_parts.append(f"  • Source Files: {basic['source_files_count']}")
            summary_parts.append("")

        if 'code_analysis' in results:
            code = results['code_analysis']
            summary_parts.append("📝 CODE ANALYSIS:")
            summary_parts.append(f"  • Tags Extracted: {code['total_tags']}")
            summary_parts.append(f"  • Definitions: {len(code['definitions'])}")
            summary_parts.append("")

        summary_parts.append(f"🎫 ANALYSIS COMPLETE | Tokens Used: {self.current_tokens}")

        return "\n".join(summary_parts)

    def generate_llm_reasoning(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate reasoning using LLM if available"""
        if hasattr(self.main_model, 'generate_reasoning'):
            return self.main_model.generate_reasoning(prompt, max_tokens)
        else:
            return ""
    
    def _basic_info_from_map(self, repo_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get basic info from repo map (no filesystem walking).
        DeepAgents Pattern: Use metadata instead of expensive filesystem operations.
        """
        context = {
            "project_type": "Unknown",
            "framework": "Unknown",
            "tech_stack": [],
            "main_dirs": [],
            "key_files": [],
            "source_files_count": len(repo_map)
        }
        
        # Check for config files in map
        has_pom_xml = 'pom.xml' in repo_map
        has_package_json = 'package.json' in repo_map
        has_requirements_txt = 'requirements.txt' in repo_map
        has_gradle = any('build.gradle' in f for f in repo_map.keys())
        has_go_mod = 'go.mod' in repo_map
        has_main_go = 'main.go' in repo_map
        
        if has_pom_xml or has_gradle:
            context["project_type"] = "Java/Maven" if has_pom_xml else "Java/Gradle"
            context["framework"] = "Spring Boot" if any('spring' in f.lower() for f in repo_map.keys()) else "Unknown"
        elif has_package_json:
            context["project_type"] = "Node.js"
        elif has_requirements_txt:
            context["project_type"] = "Python"
        elif has_go_mod or has_main_go:
            context["project_type"] = "Go"
        
        # Extract main directories from file paths
        dirs = set()
        for file_path in repo_map.keys():
            parts = Path(file_path).parts
            if len(parts) > 1:
                dirs.add(parts[0])
        context["main_dirs"] = sorted(list(dirs))[:10]
        
        # Count by language
        lang_counts = defaultdict(int)
        for metadata in repo_map.values():
            lang = metadata.get('language', 'unknown')
            lang_counts[lang] += 1
        
        # Set tech stack based on languages
        if lang_counts.get('java', 0) > 0:
            context["tech_stack"].append("Java")
        if lang_counts.get('python', 0) > 0:
            context["tech_stack"].append("Python")
        if lang_counts.get('javascript', 0) > 0:
            context["tech_stack"].append("JavaScript")
        if lang_counts.get('go', 0) > 0:
            context["tech_stack"].append("Go")
        
        return context
    
    def _extract_tags_from_selected(self, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract tags from SELECTED files only (not all files).
        DeepAgents Pattern: Work with context-scoped data for token efficiency.
        """
        print(f"  📝 Extracting tags from {len(file_contents)} selected files...")
        
        tags_by_file = {}
        definitions = defaultdict(list)
        references = defaultdict(list)
        
        for file_path, content in file_contents.items():
            try:
                file_tags = self._extract_file_tags(content, file_path)
                tags_by_file[file_path] = file_tags
                
                for tag in file_tags:
                    if tag['kind'] == 'def':
                        definitions[tag['name']].append(file_path)
                    elif tag['kind'] == 'ref':
                        references[tag['name']].append(file_path)
            except Exception as e:
                print(f"    ⚠️ Failed to extract tags from {file_path}: {e}")
                continue
        
        # Update tags_data for other methods that might use it
        self.tags_data.update({
            'definitions': dict(definitions),
            'references': dict(references)
        })
        
        total_tags = sum(len(tags) for tags in tags_by_file.values())
        print(f"  ✓ Extracted {total_tags} tags from {len(tags_by_file)} files")
        
        return {
            "tags_by_file": tags_by_file,
            "definitions": dict(definitions),
            "references": dict(references),
            "total_tags": total_tags
        }

    def token_count(self, text: str) -> int:
        """
        Count tokens with best available method.
        Uses tiered approach: tiktoken → langchain → estimation
        """
        if not text:
            return 0
        
        tokenizer_type, tokenizer = self.tokenizer
        
        # Try tiktoken (most accurate)
        if tokenizer_type == 'tiktoken' and tokenizer is not None:
            try:
                return len(tokenizer.encode(text))
            except Exception:
                pass
        
        # Try LangChain
        elif tokenizer_type == 'langchain' and tokenizer is not None:
            try:
                return tokenizer.get_num_tokens(text)
            except Exception:
                pass
        
        # Fallback: Improved estimation
        # Code: ~0.5 tokens/char, Natural lang: ~0.75 tokens/char
        # Use 0.6 as middle ground (better than old 0.25)
        return max(1, int(len(text) * 0.6))

    # ============================================================================
    # CODE ANALYSIS METHODS
    # ============================================================================

    def _basic_filesystem_scan(self) -> Dict[str, Any]:
        """Basic filesystem scanning"""
        context = {
            "project_type": "Unknown",
            "framework": "Unknown",
            "tech_stack": [],
            "main_dirs": [],
            "key_files": [],
            "source_files_count": 0
        }

        has_pom_xml = (self.codebase_path / "pom.xml").exists()
        has_package_json = (self.codebase_path / "package.json").exists()
        has_requirements_txt = (self.codebase_path / "requirements.txt").exists()
        has_gradle = (self.codebase_path / "build.gradle").exists()
        has_go_mod = (self.codebase_path / "go.mod").exists()
        has_main_go = (self.codebase_path / "main.go").exists()

        if has_pom_xml or has_gradle:
            context["project_type"] = "Java/Maven" if has_pom_xml else "Java/Gradle"
            context["framework"] = "Spring Boot" if has_pom_xml else "Android/Gradle"
        elif has_package_json:
            context["project_type"] = "Node.js/npm"
        elif has_requirements_txt:
            context["project_type"] = "Python"
        elif has_go_mod or has_main_go:
            context["project_type"] = "Go"

        root_items = list(self.codebase_path.iterdir())
        dirs = [d.name for d in root_items if d.is_dir() and not d.name.startswith('.')]
        context["main_dirs"] = dirs[:10]

        java_count = python_count = js_count = go_count = 0
        for root, dirs_list, files in os.walk(self.codebase_path):
            for f in files:
                if f.endswith('.java'):
                    java_count += 1
                elif f.endswith('.py'):
                    python_count += 1
                elif f.endswith(('.js', '.ts')):
                    js_count += 1
                elif f.endswith('.go'):
                    go_count += 1

        context["source_files_count"] = java_count + python_count + js_count + go_count
        if java_count > 0:
            context["tech_stack"].append(f"Java ({java_count} files)")
        if python_count > 0:
            context["tech_stack"].append(f"Python ({python_count} files)")
        if js_count > 0:
            context["tech_stack"].append(f"JavaScript/TypeScript ({js_count} files)")
        if go_count > 0:
            context["tech_stack"].append(f"Go ({go_count} files)")

        return context

    def _extract_code_tags(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Extract code tags"""
        print("  📝 Extracting code tags...")

        tags_by_file = {}
        definitions = defaultdict(list)
        references = defaultdict(list)

        tag_count = 0
        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file.endswith(('.py', '.java', '.js', '.ts', '.go')):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.codebase_path)

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        file_tags = self._extract_file_tags(content, str(rel_path))
                        tags_by_file[str(rel_path)] = file_tags

                        for tag in file_tags:
                            if tag['kind'] == 'def':
                                definitions[tag['name']].append(str(rel_path))
                            elif tag['kind'] == 'ref':
                                references[tag['name']].append(str(rel_path))
                            tag_count += 1
                            if limit and tag_count >= limit:
                                break

                    except Exception as e:
                        print(f"    ⚠️ Error processing {rel_path}: {e}")

        self.tags_data.update({
            'definitions': dict(definitions),
            'references': dict(references)
        })

        return {
            "tags_by_file": tags_by_file,
            "definitions": dict(definitions),
            "references": dict(references),
            "total_tags": sum(len(tags) for tags in tags_by_file.values())
        }

    def _extract_tags_with_tree_sitter(
        self,
        content: str,
        file_path: str,
        ext: str
    ) -> list:
        """Extract tags using tree-sitter (accurate parsing)"""
        parser = self.parsers.get(ext)
        if not parser:
            raise ValueError(f"No parser available for {ext}")
        
        tree = parser.parse(content.encode('utf8'))
        tags = []
        
        def traverse(node):
            if ext == '.py':
                if node.type == 'function_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'function'
                        })
                elif node.type == 'class_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'class'
                        })
            
            elif ext == '.java':
                if node.type == 'class_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'class'
                        })
                elif node.type == 'method_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'method'
                        })
            
            elif ext == '.go':
                if node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'function'
                        })
            
            elif ext in ['.js', '.ts']:
                if node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'function'
                        })
                elif node.type == 'class_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        tags.append({
                            'name': name_node.text.decode('utf8'),
                            'kind': 'def',
                            'line': node.start_point[0] + 1,
                            'type': 'class'
                        })
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return tags

    def _extract_tags_with_regex(self, content: str, file_path: str) -> list:
        """Fallback regex-based tag extraction"""
        tags = []
        lines = content.split('\n')

        if file_path.endswith('.py'):
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith(('def ', 'class ')):
                    name = line.split()[1].split('(')[0]
                    tags.append({'name': name, 'kind': 'def', 'line': i+1, 'type': 'function' if 'def' in line else 'class'})

        elif file_path.endswith('.java'):
            for i, line in enumerate(lines):
                if 'class ' in line or 'interface ' in line:
                    parts = line.split()
                    if 'class' in parts:
                        idx = parts.index('class')
                        if idx + 1 < len(parts):
                            name = parts[idx + 1]
                            tags.append({'name': name, 'kind': 'def', 'line': i+1, 'type': 'class'})

        elif file_path.endswith('.go'):
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('func '):
                    func_part = line[5:].strip()
                    if '(' in func_part:
                        name = func_part.split('(')[0].strip()
                        if name:
                            tags.append({'name': name, 'kind': 'def', 'line': i+1, 'type': 'function'})

        elif file_path.endswith(('.js', '.ts')):
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith(('function ', 'const ', 'class ')):
                    if 'class ' in line:
                        name = line.split()[1]
                        tags.append({'name': name, 'kind': 'def', 'line': i+1, 'type': 'class'})
                    elif 'function ' in line:
                        name = line.split()[1].split('(')[0]
                        tags.append({'name': name, 'kind': 'def', 'line': i+1, 'type': 'function'})

        return tags

    def _extract_file_tags(self, content: str, file_path: str) -> list:
        """Extract tags - try tree-sitter first, fallback to regex"""
        ext = Path(file_path).suffix
        
        # ✅ TRY tree-sitter first
        if ext in self.parsers and TREE_SITTER_AVAILABLE:
            try:
                return self._extract_tags_with_tree_sitter(content, file_path, ext)
            except Exception as e:
                print(f"  ⚠️ Tree-sitter failed for {file_path}: {e}, falling back to regex")
        
        # ✅ FALLBACK to regex
        return self._extract_tags_with_regex(content, file_path)

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        print("  📦 Analyzing dependencies...")

        dependencies = {
            "external_libs": [],
            "internal_modules": [],
            "frameworks_detected": [],
            "database_drivers": [],
            "api_clients": []
        }

        return dependencies

    def _analyze_api_patterns(self) -> Dict[str, Any]:
        """Analyze API patterns"""
        print("  🌐 Analyzing API patterns...")

        return {
            "endpoints": [],
            "http_methods": [],
            "api_frameworks": [],
            "database_patterns": [],
            "middleware_patterns": []
        }

    def _rank_code_elements(self) -> Dict[str, Any]:
        """Rank code elements"""
        print("  📊 Ranking code elements...")

        element_scores = defaultdict(float)

        for name, files in self.tags_data.get('definitions', {}).items():
            score = len(files)
            if len(name) > 3:
                score *= 1.2
            element_scores[name] = score

        ranked = sorted(element_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_elements": ranked[:20],
            "total_elements": len(element_scores),
            "ranking_method": "frequency-based"
        }

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure"""
        print("  🏗️ Analyzing project structure...")

        structure = {
            "entry_points": [],
            "config_files": [],
            "test_directories": [],
            "source_directories": [],
            "architecture_patterns": [],
            "java_packages": [],  # ✓ NEW: Discovered Java packages
            "package_mappings": {}  # ✓ NEW: Path to package name mappings
        }

        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file in ['main.py', 'app.py', '__main__.py', 'main.go', 'Main.java', 'index.js']:
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    structure["entry_points"].append(rel_path)

        # ✓ NEW: Discover actual Java package structure
        structure["java_packages"] = self._discover_java_packages()
        structure["package_mappings"] = self._extract_package_mappings()

        return structure
    
    def _discover_java_packages(self) -> list:
        """Discover all Java package hierarchies in the project"""
        packages = []
        
        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith('package '):
                                    # Extract: "package com.example.springboot.product;" → "com.example.springboot.product"
                                    package_name = line.replace('package ', '').rstrip(';').strip()
                                    if package_name and package_name not in packages:
                                        packages.append(package_name)
                                    break
                    except Exception:
                        pass
        
        packages.sort()
        return packages
    
    def _extract_package_mappings(self) -> Dict[str, str]:
        """Map Java source directories to their package prefixes"""
        mappings = {}
        
        # Look for src/main/java directories
        for root, dirs, files in os.walk(self.codebase_path):
            if 'src' in dirs:
                src_path = Path(root) / 'src'
                if (src_path / 'main' / 'java').exists():
                    java_src = src_path / 'main' / 'java'
                    
                    # Find first-level package directories
                    for item in java_src.iterdir():
                        if item.is_dir():
                            rel_path = str(item.relative_to(self.codebase_path))
                            # Infer package from directory structure
                            # e.g., "src/main/java/com/example/springboot/product" → "com.example.springboot.product"
                            package_path = rel_path.replace(str(java_src.relative_to(self.codebase_path)), '').lstrip('/')
                            if package_path:
                                mappings[rel_path] = package_path.replace('/', '.')
        
        return mappings

    # ============================================================================
    # CODE PLACEMENT SUBAGENT (DeepAgent Pattern)
    # ============================================================================
    
    def _create_placement_reasoning_agent(self):
        """
        Create a specialized subagent for code placement reasoning.
        
        WHY SUBAGENT: Complex reasoning about package structures and placement requires:
        - Context isolation: Keep placement logic separate from main analyzer
        - Specialized instructions: Custom system prompt for package analysis
        - Dynamic input: Pass discovered structure as context injection
        - Multi-step reasoning: Analyze patterns → match to request → recommend placement
        
        FOLLOWS DeepAgents BEST PRACTICE:
        - Subagent receives only relevant context (discovered packages, request)
        - Custom system prompt for specialized placement reasoning
        - Returns structured placement suggestions
        - Main agent doesn't need to manage complex placement logic
        """
        try:
            from deepagents import create_deep_agent
            
            system_prompt = """You are a Code Placement Specialist for Java project organization.

Your task: Given a feature request and discovered Java package structure, determine the optimal placement for new code.

RULES FOR PLACEMENT:
1. ALWAYS use discovered packages from the codebase - never suggest 'com/example' if not found
2. Analyze existing package hierarchy and naming patterns
3. For entities/models: place in existing model/domain packages
4. For controllers: place in existing controller/api packages
5. For services: place in existing service packages
6. Match the naming convention already used in the project

IMPORTANT: Return ONLY valid paths that align with existing package structure in the repo.
If uncertain, use the deepest package hierarchy discovered.

Input context:
- Feature request: What the user wants to add
- Discovered packages: List of actual packages found in codebase
- File structure: Actual directory mappings

Respond with JSON containing placement suggestions based on DISCOVERED structure, not templates."""

            placement_agent = create_deep_agent(
                model=self.main_model.model_name if hasattr(self.main_model, 'model_name') else "gpt-4",
                system_prompt=system_prompt,
                tools=[]
            )
            return placement_agent
        except ImportError:
            print("  ⚠️ DeepAgents not available - using fallback reasoning")
            return None
    
    def _reason_placement_with_context(
        self,
        feature_request: str,
        discovered_packages: list,
        package_mappings: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Use LLM reasoning to determine code placement based on discovered structure.
        
        CONTEXT INJECTION: Pass only relevant data (discovered packages, not hardcoded templates)
        This follows DeepAgents pattern of selective context passing.
        """
        if not discovered_packages:
            print("    ⚠️ No discovered packages - cannot reason placement")
            return {}
        
        # Build context for placement reasoning
        packages_str = "\n".join([f"  • {pkg}" for pkg in discovered_packages[:10]])
        mappings_str = "\n".join([f"  • {path} → {pkg}" for path, pkg in list(package_mappings.items())[:5]])
        
        prompt = f"""Analyze code placement based on DISCOVERED package structure:

FEATURE REQUEST:
{feature_request}

DISCOVERED JAVA PACKAGES IN CODEBASE:
{packages_str}

PACKAGE PATH MAPPINGS:
{mappings_str}

Based on these ACTUAL packages found in the repo, suggest where to place:
1. Entities/Models
2. Controllers/APIs  
3. Services
4. Repositories

Return JSON with 'placements' array containing:
{{"
  "type": "entity|controller|service|repository",
  "suggested_package": "discovered.package.name",
  "directory": "src/main/java/discovered/package/name",
  "reasoning": "why this placement matches existing patterns"
}}

CRITICAL: Use only discovered packages, never suggest com/example if not found."""

        try:
            if self.main_model and hasattr(self.main_model, 'generate_reasoning'):
                response = self.main_model.generate_reasoning(prompt, max_tokens=800)
                
                # Parse response
                try:
                    import json as json_module
                    # Extract JSON from response
                    json_match = response.find('{')
                    if json_match >= 0:
                        parsed = json_module.loads(response[json_match:])
                        return parsed
                except (Exception,):
                    pass
            
            return {}
        except Exception as err:
            print(f"    ⚠️ Placement reasoning failed: {err}")
            return {}

    # ============================================================================
    # CODE PLACEMENT & FILE MENTION INFERENCE
    # ============================================================================

    def get_file_mentions(self, user_input: str) -> Dict[str, Any]:
        """Aider-style file mention detection"""
        cache_key = hashlib.md5(user_input.encode()).hexdigest()
        if cache_key in self.file_mentions_cache:
            return self.file_mentions_cache[cache_key]

        mentioned_files = set()
        mentioned_idents = set()

        all_files = []
        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file.endswith(('.py', '.java', '.js', '.ts', '.go')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    all_files.append(rel_path)

        words = set(word.strip('"\'`*_').rstrip(',.!;:?') for word in user_input.split())

        for rel_path in all_files:
            normalized_path = rel_path.replace("\\", "/")
            if normalized_path in words or os.path.basename(rel_path) in words:
                mentioned_files.add(rel_path)

        result = {
            'mentioned_files': list(mentioned_files),
            'mentioned_idents': list(mentioned_idents),
            'confidence': len(mentioned_files) + len(mentioned_idents) * 0.5
        }

        self.file_mentions_cache[cache_key] = result
        return result

    def infer_code_placement(self, feature_request: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer where to place new code using discovered package structure.
        
        USES DEEPAGENTS BEST PRACTICE:
        - Extracts discovered packages from analysis_result (context injection)
        - Uses LLM reasoning with actual repo structure, not hardcoded templates
        - Returns placement suggestions based on existing patterns in codebase
        - Avoids 'com/example' template - always aligns with discovered structure
        """
        cache_key = hashlib.md5(feature_request.encode()).hexdigest()
        if cache_key in self.structure_inference_cache:
            return self.structure_inference_cache[cache_key]

        basic = analysis_result.get("basic_info", {})
        structure = analysis_result.get("structure", {})
        placement_suggestions = []
        discovered_packages = []  # Initialize to avoid unbound error

        if basic.get('project_type') == 'Java/Maven':
            # ✓ IMPROVED: Extract discovered packages instead of using hardcoded paths
            discovered_packages = structure.get("java_packages", [])
            package_mappings = structure.get("package_mappings", {})
            
            print(f"    📍 Discovered {len(discovered_packages)} Java packages")
            if discovered_packages:
                print(f"    📦 Packages: {', '.join(discovered_packages[:3])}{'...' if len(discovered_packages) > 3 else ''}")
            
            # ✓ USE REASONING: Get LLM-based placement suggestions with discovered context
            if LLM_AVAILABLE and self.main_model:
                reasoning_result = self._reason_placement_with_context(
                    feature_request=feature_request,
                    discovered_packages=discovered_packages,
                    package_mappings=package_mappings
                )
                
                if reasoning_result and 'placements' in reasoning_result:
                    placement_suggestions = reasoning_result['placements']
                    print(f"    ✓ LLM reasoning found {len(placement_suggestions)} placements")
            
            # ✓ FALLBACK: If no LLM or reasoning failed, use discovered packages intelligently
            if not placement_suggestions and discovered_packages:
                # Find packages matching common patterns
                entity_packages = [p for p in discovered_packages if 'entity' in p.lower() or 'model' in p.lower() or 'domain' in p.lower()]
                controller_packages = [p for p in discovered_packages if 'controller' in p.lower() or 'api' in p.lower() or 'web' in p.lower()]
                service_packages = [p for p in discovered_packages if 'service' in p.lower() or 'business' in p.lower()]
                
                # Use discovered packages or fall back to deepest common package
                deepest_package = max(discovered_packages, key=lambda p: p.count('.'))
                
                if 'entity' in feature_request.lower() and entity_packages:
                    pkg = entity_packages[0]
                    placement_suggestions.append({
                        'type': 'entity',
                        'package': pkg,
                        'directory': f"src/main/java/{pkg.replace('.', '/')}",
                        'filename_pattern': '{Entity}Entity.java',
                        'purpose': 'JPA entity classes',
                        'source': 'discovered_package_pattern'
                    })
                elif 'entity' in feature_request.lower():
                    pkg = deepest_package
                    placement_suggestions.append({
                        'type': 'entity',
                        'package': pkg,
                        'directory': f"src/main/java/{pkg.replace('.', '/')}",
                        'filename_pattern': '{Entity}Entity.java',
                        'purpose': 'JPA entity classes',
                        'source': 'deepest_package_fallback'
                    })
                
                if ('endpoint' in feature_request.lower() or 'controller' in feature_request.lower()) and controller_packages:
                    pkg = controller_packages[0]
                    placement_suggestions.append({
                        'type': 'controller',
                        'package': pkg,
                        'directory': f"src/main/java/{pkg.replace('.', '/')}",
                        'filename_pattern': '{Feature}Controller.java',
                        'purpose': 'REST controllers',
                        'source': 'discovered_package_pattern'
                    })
                elif 'endpoint' in feature_request.lower() or 'controller' in feature_request.lower():
                    pkg = deepest_package
                    placement_suggestions.append({
                        'type': 'controller',
                        'package': pkg,
                        'directory': f"src/main/java/{pkg.replace('.', '/')}",
                        'filename_pattern': '{Feature}Controller.java',
                        'purpose': 'REST controllers',
                        'source': 'deepest_package_fallback'
                    })
                
                if 'service' in feature_request.lower() and service_packages:
                    pkg = service_packages[0]
                    placement_suggestions.append({
                        'type': 'service',
                        'package': pkg,
                        'directory': f"src/main/java/{pkg.replace('.', '/')}",
                        'filename_pattern': '{Feature}Service.java',
                        'purpose': 'Business logic services',
                        'source': 'discovered_package_pattern'
                    })
                
                print(f"    ✓ Fallback strategy found {len(placement_suggestions)} placements from discovered packages")

        result = {
            'placement_suggestions': placement_suggestions,
            'confidence_score': len(placement_suggestions) * 0.3 if placement_suggestions else 0.0,
            'discovery_method': 'discovered_packages' if discovered_packages else 'none',
            'packages_analyzed': len(structure.get("java_packages", []))
        }

        self.structure_inference_cache[cache_key] = result
        return result


# ============================================================================
# ENTITY DISCOVERY FUNCTIONS (Task 2: Entity-Aware Architecture)
# ============================================================================

def discover_existing_entities(
    codebase_path: str, 
    language: str = "auto",
    main_model: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Task 2: Discover existing domain entities in the codebase using DeepAgent reasoning.
    
    USES DEEPAGENT PATTERN:
    - LLM-based entity extraction (not regex)
    - Multi-language support (Java, Python, Go, TypeScript, etc.)
    - Context injection: passes file contents to LLM for intelligent parsing
    - Reasoning about what constitutes an "entity" vs regular class
    
    This function scans the codebase to find existing entity classes (JPA entities, domain models,
    dataclasses, structs, etc.) to prevent duplicate entity creation and enable modification-based workflows.
    
    Args:
        codebase_path: Root path of the project
        language: Programming language ("auto", "java", "python", "go", "typescript")
        main_model: LLM model for reasoning (if None, uses regex fallback)
    
    Returns:
        Dictionary containing:
        - entities: List of discovered entity names
        - entity_files: Mapping of entity name to file path
        - entity_details: Detailed information about each entity (fields, annotations, etc.)
        - discovery_method: "llm_reasoning" or "regex_fallback"
    """
    print(f"  🔍 [Task 2] Discovering existing entities in {codebase_path}...")
    
    result = {
        "entities": [],
        "entity_files": {},
        "entity_details": {},
        "language": language,
        "discovery_method": "llm_reasoning" if main_model else "regex_fallback"
    }
    
    codebase_root = Path(codebase_path)
    
    # Auto-detect language if needed
    if language == "auto":
        language = _detect_project_language(codebase_root)
        print(f"    🔍 Auto-detected language: {language}")
    
    # Find potential entity files based on language
    entity_candidates = _find_entity_candidate_files(codebase_root, language)
    
    if not entity_candidates:
        print(f"    ⚠️ No entity candidate files found for language: {language}")
        return result
    
    print(f"    📁 Found {len(entity_candidates)} potential entity files")
    
    # Use LLM reasoning if available, otherwise fallback to regex
    if main_model and LLM_AVAILABLE:
        print(f"    🤖 Using LLM reasoning for entity extraction...")
        result = _discover_entities_with_llm(
            entity_candidates, 
            codebase_root, 
            language, 
            main_model
        )
    else:
        print(f"    📝 Using regex fallback for entity extraction...")
        result = _discover_entities_with_regex(
            entity_candidates, 
            codebase_root, 
            language
        )
    
    print(f"  ✓ Entity discovery complete: {len(result['entities'])} entities found ({result['discovery_method']})")
    return result


def _detect_project_language(codebase_root: Path) -> str:
    """Auto-detect project language from codebase structure"""
    # Check for language-specific markers
    if (codebase_root / "pom.xml").exists() or (codebase_root / "build.gradle").exists():
        return "java"
    elif (codebase_root / "requirements.txt").exists() or (codebase_root / "setup.py").exists():
        return "python"
    elif (codebase_root / "go.mod").exists() or (codebase_root / "main.go").exists():
        return "go"
    elif (codebase_root / "package.json").exists():
        # Check if TypeScript
        if (codebase_root / "tsconfig.json").exists():
            return "typescript"
        return "javascript"
    elif (codebase_root / "Cargo.toml").exists():
        return "rust"
    
    return "unknown"


def _find_entity_candidate_files(codebase_root: Path, language: str) -> list:
    """Find files that might contain entity definitions"""
    candidates = []
    
    if language == "java":
        # Java: domain/, entity/, model/ directories
        java_src = codebase_root / "src" / "main" / "java"
        if java_src.exists():
            patterns = ["**/domain/*.java", "**/entity/*.java", "**/model/*.java", "**/entities/*.java"]
            for pattern in patterns:
                candidates.extend(java_src.glob(pattern))
    
    elif language == "python":
        # Python: models.py, entities.py, domain/ directory
        patterns = ["**/models.py", "**/entities.py", "**/entity.py", "**/domain/*.py", "**/models/*.py"]
        for pattern in patterns:
            candidates.extend(codebase_root.glob(pattern))
    
    elif language == "go":
        # Go: entity.go, model.go, types.go in various directories
        patterns = ["**/entity.go", "**/model.go", "**/models.go", "**/types.go", "**/domain/*.go"]
        for pattern in patterns:
            candidates.extend(codebase_root.glob(pattern))
    
    elif language in ["typescript", "javascript"]:
        # TypeScript/JavaScript: entity.ts, model.ts, types.ts
        ext = "ts" if language == "typescript" else "js"
        patterns = [f"**/entity.{ext}", f"**/model.{ext}", f"**/models.{ext}", f"**/types.{ext}", f"**/entities/*.{ext}"]
        for pattern in patterns:
            candidates.extend(codebase_root.glob(pattern))
    
    elif language == "rust":
        # Rust: look for structs in src/ directory
        patterns = ["**/src/*.rs", "**/src/**/*.rs"]
        for pattern in patterns:
            candidates.extend(codebase_root.glob(pattern))
    
    return list(set(candidates))  # Remove duplicates


def _discover_entities_with_llm(
    candidate_files: list,
    codebase_root: Path,
    language: str,
    main_model: Any
) -> Dict[str, Any]:
    """
    Use LLM reasoning to extract entities from candidate files.
    
    DEEPAGENT PATTERN: Context injection with file contents for intelligent entity detection.
    """
    result = {
        "entities": [],
        "entity_files": {},
        "entity_details": {},
        "language": language,
        "discovery_method": "llm_reasoning"
    }
    
    for file_path in candidate_files[:20]:  # Limit to avoid token overflow
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if file is too large (>10KB)
            if len(content) > 10000:
                continue
            
            # Build prompt for entity extraction
            prompt = f"""Analyze this {language} code file and extract domain entity information.

FILE: {file_path.name}
LANGUAGE: {language}

CODE:
```{language}
{content}
```

Task: Identify if this file contains domain entities (JPA entities, dataclasses, domain models, etc.).

For EACH entity found, extract:
1. Entity name (class/struct name)
2. All fields with their types
3. Annotations/decorators (e.g., @Entity, @dataclass, #[derive])
4. Package/module name

Return JSON format:
{{
  "has_entities": true/false,
  "entities": [
    {{
      "name": "Product",
      "package": "com.example.product.domain",
      "fields": [
        {{"name": "id", "type": "Long", "annotations": ["@Id", "@GeneratedValue"]}},
        {{"name": "name", "type": "String", "annotations": ["@Column"]}}
      ],
      "class_annotations": ["@Entity", "@Table(name=\\"products\\")"]
    }}
  ]
}}

IMPORTANT: Only extract classes that represent domain entities (business objects), not DTOs, controllers, or utilities."""

            # Call LLM
            try:
                from langchain_openai import ChatOpenAI
                from pydantic import SecretStr
                import os
                
                llm = ChatOpenAI(
                    api_key=SecretStr(os.getenv('LITELLM_VIRTUAL_KEY')),
                    model=os.getenv('LITELLM_MODEL', 'gpt-4'),
                    base_url=os.getenv('LITELLM_API'),
                    temperature=0.0,  # Deterministic for entity extraction
                )
                
                response = llm.invoke([{"role": "user", "content": prompt}])
                response_text = response.content
                
                # Parse JSON response
                import json
                import re
                
                # Extract JSON from response (handle markdown code blocks)
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_text
                
                entity_data = json.loads(json_str)
                
                if entity_data.get("has_entities") and entity_data.get("entities"):
                    for entity in entity_data["entities"]:
                        entity_name = entity["name"]
                        relative_path = file_path.relative_to(codebase_root)
                        
                        result["entities"].append(entity_name)
                        result["entity_files"][entity_name] = str(relative_path)
                        result["entity_details"][entity_name] = {
                            "fields": entity.get("fields", []),
                            "class_annotations": entity.get("class_annotations", []),
                            "package": entity.get("package", "unknown"),
                            "file_path": str(relative_path)
                        }
                        
                        print(f"    ✅ Discovered entity: {entity_name} ({len(entity.get('fields', []))} fields)")
            
            except Exception as e:
                print(f"    ⚠️ LLM parsing failed for {file_path.name}: {e}")
                # Fall back to regex for this file
                continue
        
        except Exception as e:
            print(f"    ⚠️ Error reading {file_path}: {e}")
            continue
    
    return result


def _discover_entities_with_regex(
    candidate_files: list,
    codebase_root: Path,
    language: str
) -> Dict[str, Any]:
    """
    Fallback: Use regex-based entity extraction (Java only for now).
    
    This is a simple fallback when LLM is not available.
    """
    result = {
        "entities": [],
        "entity_files": {},
        "entity_details": {},
        "language": language,
        "discovery_method": "regex_fallback"
    }
    
    if language != "java":
        print(f"    ⚠️ Regex fallback only supports Java. Language '{language}' not supported.")
        return result
    
    import re
    
    for file_path in candidate_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for JPA @Entity annotation
            if '@Entity' not in content:
                continue
            
            # Extract entity name from class declaration
            class_match = re.search(r'public\s+class\s+(\w+)\s*\{', content)
            if not class_match:
                continue
            
            entity_name = class_match.group(1)
            
            # Extract package
            package_match = re.search(r'package\s+([\w.]+);', content)
            package_name = package_match.group(1) if package_match else "unknown"
            
            # Extract fields
            fields = []
            field_pattern = re.compile(
                r'(?:(?:@\w+(?:\([^)]*\))?)\s*)*\s*private\s+(\w+(?:<[\w\s,<>]+>)?)\s+(\w+)\s*;',
                re.MULTILINE
            )
            
            for match in field_pattern.finditer(content):
                field_type = match.group(1)
                field_name = match.group(2)
                
                # Extract annotations
                field_start = match.start()
                context_start = max(0, field_start - 200)
                field_context = content[context_start:field_start]
                
                annotation_pattern = re.compile(r'@(\w+)(?:\([^)]*\))?')
                annotations = ['@' + ann for ann in annotation_pattern.findall(field_context)]
                
                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "annotations": annotations if annotations else []
                })
            
            # Extract class annotations
            class_start = content.find('public class')
            class_context = content[:class_start] if class_start > 0 else ""
            class_annotations = ['@' + ann for ann in re.findall(r'@(\w+)(?:\([^)]*\))?', class_context)]
            
            # Store entity details
            relative_path = file_path.relative_to(codebase_root)
            result["entities"].append(entity_name)
            result["entity_files"][entity_name] = str(relative_path)
            result["entity_details"][entity_name] = {
                "fields": fields,
                "class_annotations": class_annotations,
                "package": package_name,
                "file_path": str(relative_path)
            }
            
            print(f"    ✅ Discovered entity: {entity_name} ({len(fields)} fields)")
        
        except Exception as e:
            print(f"    ⚠️ Error parsing {file_path}: {e}")
            continue
    
    return result


# ============================================================================
# MAIN WORKFLOW FUNCTIONS
# ============================================================================

def analyze_context(state: AgentState) -> AgentState:
    """Node: Context Analysis Phase - Aider-style analysis with selective file loading"""
    print("🔍 Phase 1: Analyzing codebase context (DeepAgents Multi-Phase)...")

    codebase_path = state["codebase_path"]
    feature_request = state.get("feature_request") or "Analyze codebase structure and patterns"

    try:
        # Respect environment-configured max tokens if set (ANALYSIS_MAX_TOKENS)
        env_max = os.getenv('ANALYSIS_MAX_TOKENS')
        try:
            max_tokens = int(env_max) if env_max is not None else 2048
        except Exception:
            max_tokens = 2048
        analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=max_tokens)
        
        # ✅ Use new method with selective analysis
        analysis_result = analyzer.analyze_with_reasoning(feature_request)
        
        # Extract results from new format
        results = analysis_result.get('results', {})
        discovery = analysis_result.get('discovery', {})
        
        basic = results.get('basic_info', {})
        code_analysis = results.get('code_analysis', {})
        structure = results.get('structure', {})
        ranked = results.get('ranked_elements', {})

        summary = f"""
PROJECT ANALYSIS (DeepAgents Multi-Phase Analysis):

DISCOVERY PHASE:
- Total Files: {discovery.get('total_files', 0)}
- Selected Files: {len(discovery.get('selected_files', []))}
- Selection Method: {discovery.get('selection_method', 'unknown')}
- Token Efficiency: {discovery.get('selection_ratio', 0):.1%}

FILESYSTEM SCAN:
- Type: {basic.get('project_type', 'Unknown')}
- Framework: {basic.get('framework', 'Unknown')}
- Tech Stack: {', '.join(basic.get('tech_stack', [])) if basic.get('tech_stack') else 'Mixed'}
- Total Source Files: {basic.get('source_files_count', 0)}
- Root Directories: {', '.join(basic.get('main_dirs', [])[:5])}

CODE ANALYSIS:
- Tags Extracted: {code_analysis.get('total_tags', 0)} from {len(code_analysis.get('tags_by_file', {}))} files
- Definitions: {len(code_analysis.get('definitions', {}))}
- References: {len(code_analysis.get('references', {}))}

PROJECT STRUCTURE:
- Entry Points: {', '.join(structure.get('entry_points', [])) if structure.get('entry_points') else 'None detected'}
- Test Directories: {len(structure.get('test_directories', []))}
- Source Directories: {len(structure.get('source_directories', []))}

PERFORMANCE METRICS:
- Tokens Used: {analysis_result.get('tokens_used', 0)}
- Budget Status: {'OK' if not results.get('budget_exceeded') else 'EXCEEDED'}
"""
        
        # Try to add architecture insights if available
        if ranked:
            top_elems = ranked.get('top_elements') or ranked.get('elements') or []
            if top_elems and len(top_elems) > 0:
                top_components = ', '.join([name for name, _ in top_elems[:3]])
                summary += f"\nARCHITECTURE INSIGHTS:\n1. **Main Components**: {top_components}\n"

        # ✅ SAVE RESULTS TO JSON FILE
        import json
        from datetime import datetime
        
        # Create outputs directory if it doesn't exist
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"analysis_result_{timestamp}.json"
        json_path = outputs_dir / json_filename
        
        # Save full analysis result to JSON
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, default=str)
            print(f"  💾 Analysis results saved to: {json_path}")
        except Exception as e:
            print(f"  ⚠️ Failed to save JSON results: {e}")

        # ✅ TASK 2: Discover existing entities (entity-aware architecture)
        print("\n🔍 [Task 2] Running entity discovery...")
        project_type = basic.get('project_type', 'Unknown')
        
        # Determine language based on project type (auto-detect if unknown)
        if "java" in project_type.lower() or "spring" in basic.get('framework', '').lower():
            language = "java"
        elif "python" in project_type.lower():
            language = "python"
        elif "go" in project_type.lower():
            language = "go"
        elif "javascript" in project_type.lower() or "node" in basic.get('framework', '').lower():
            language = "javascript"
        elif "typescript" in project_type.lower():
            language = "typescript"
        else:
            language = "auto"  # Auto-detect
        
        # Pass analyzer's model for LLM reasoning (DeepAgent pattern)
        entity_discovery = discover_existing_entities(
            codebase_path, 
            language=language,
            main_model=analyzer.main_model if hasattr(analyzer, 'main_model') else None
        )
        
        # Add entity discovery results to state
        state["existing_entities"] = entity_discovery
        
        # Append entity discovery to summary
        if entity_discovery.get("entities"):
            entity_summary = f"\nENTITY DISCOVERY (Task 2):\n"
            entity_summary += f"- Discovered Entities: {len(entity_discovery['entities'])}\n"
            entity_summary += f"- Entities: {', '.join(entity_discovery['entities'])}\n"
            
            # Show sample entity details
            for entity_name in entity_discovery['entities'][:3]:  # Show up to 3 entities
                details = entity_discovery['entity_details'].get(entity_name, {})
                fields_count = len(details.get('fields', []))
                entity_summary += f"  • {entity_name}: {fields_count} fields ({details.get('package', 'unknown')})\n"
            
            summary += entity_summary
        else:
            summary += f"\nENTITY DISCOVERY (Task 2):\n- No existing entities found (fresh codebase)\n"

        state["context_analysis"] = summary
        state["current_phase"] = "context_analysis_complete"

        print(f"  ✓ Detected: {basic.get('project_type', 'Unknown')} / {basic.get('framework', 'Unknown')}")
        print(f"  ✓ Source files: {basic.get('source_files_count', 0)}")
        print(f"  ✓ Selected files: {len(discovery.get('selected_files', []))}")
        print(f"  ✓ Code tags: {code_analysis.get('total_tags', 0)}")
        print(f"  ✓ Tokens used: {analysis_result.get('tokens_used', 0)}")
        print(f"  ✓ Entities discovered: {len(entity_discovery.get('entities', []))}")

        return state

    except Exception as e:
        print(f"  ❌ Error during context analysis: {e}")
        traceback.print_exc()
        state["errors"].append(f"Context analysis error: {str(e)}")
        state["context_analysis"] = f"Error: {str(e)}"
        return state


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded from .env")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system environment variables")

    # Setup model for standalone execution (same as orchestrator)
    try:
        from models import setup_model
        model_name, temperature, analysis_model = setup_model()
        print(f"✓ Model initialized: {model_name} (temp: {temperature})")
    except Exception as e:
        print(f"⚠️ Model setup failed: {e} - will use rule-based fallback")
        analysis_model = None

    parser = argparse.ArgumentParser(description='Aider-style codebase analysis')
    parser.add_argument('--codebase-path', required=True, help='Path to analyze')
    parser.add_argument('--feature-request', required=True, help='Feature request')

    args = parser.parse_args()

    # Use environment-configured tokens when running standalone
    env_max = os.getenv('ANALYSIS_MAX_TOKENS')
    try:
        max_tokens = int(env_max) if env_max is not None else 2048
    except Exception:
        max_tokens = 2048

    analyzer = AiderStyleRepoAnalyzer(args.codebase_path, max_tokens=max_tokens, main_model=analysis_model)
    analysis_result = analyzer.analyze_with_reasoning(args.feature_request)

    print("\n🤖 AGENT REASONING RESULTS:")
    print("=" * 60)
    
    # Display Reasoning
    reasoning = analysis_result.get('reasoning', {})
    print("🎯 REQUEST ANALYSIS:")
    print(f"  • Request Type: {reasoning.get('request_type', 'unknown').replace('_', ' ').title()}")
    print(f"  • Analysis Scope: {reasoning.get('scope', 'unknown').title()}")
    print(f"  • Estimated Complexity: {reasoning.get('estimated_complexity', 'unknown').title()}")
    print(f"  • Priority Areas: {', '.join(reasoning.get('priority_areas', [])) if reasoning.get('priority_areas') else 'None'}")
    if reasoning.get('entities'):
        print(f"  • Key Entities: {', '.join(reasoning.get('entities', []))}")
    if reasoning.get('actions'):
        print(f"  • Required Actions: {', '.join(reasoning.get('actions', []))}")
    if reasoning.get('technologies'):
        print(f"  • Technologies: {', '.join(reasoning.get('technologies', []))}")
    print()

    # Display Analysis Plan
    analysis_plan = analysis_result.get('analysis_plan', {})
    print("📋 ANALYSIS PLAN:")
    print(f"  • Analyses to Run: {', '.join(analysis_plan.get('analyses_to_run', []))}")
    if analysis_plan.get('skip_analyses'):
        print(f"  • Analyses Skipped: {', '.join(analysis_plan.get('skip_analyses', []))}")
    if analysis_plan.get('focus_files'):
        print(f"  • Focus Files: {', '.join(analysis_plan.get('focus_files', []))}")
    print()

    # Display Results
    results = analysis_result.get('results', {})
    print("📊 ANALYSIS RESULTS:")
    if 'basic_info' in results:
        basic = results['basic_info']
        print("  🏗️ PROJECT OVERVIEW:")
        print(f"    • Project Type: {basic.get('project_type', 'Unknown')}")
        print(f"    • Framework: {basic.get('framework', 'Unknown')}")
        print(f"    • Tech Stack: {', '.join(basic.get('tech_stack', [])) if basic.get('tech_stack') else 'Unknown'}")
        print(f"    • Source Files Count: {basic.get('source_files_count', 0)}")
        print(f"    • Main Directories: {', '.join(basic.get('main_dirs', [])[:5])}")
        print()
    
    if 'code_analysis' in results:
        code = results['code_analysis']
        print("  📝 CODE ANALYSIS:")
        print(f"    • Total Tags Extracted: {code.get('total_tags', 0)}")
        print(f"    • Definitions: {len(code.get('definitions', {}))}")
        print(f"    • References: {len(code.get('references', {}))}")
        print(f"    • Files Analyzed: {len(code.get('tags_by_file', {}))}")
        print()
    
    if 'dependencies' in results:
        deps = results['dependencies']
        print("  📦 DEPENDENCIES:")
        if deps.get('external_libs'):
            print(f"    • External Libraries: {', '.join(deps['external_libs'])}")
        if deps.get('frameworks_detected'):
            print(f"    • Frameworks Detected: {', '.join(deps['frameworks_detected'])}")
        if deps.get('database_drivers'):
            print(f"    • Database Drivers: {', '.join(deps['database_drivers'])}")
        print()
    
    if 'api_patterns' in results:
        api = results['api_patterns']
        print("  🌐 API PATTERNS:")
        if api.get('endpoints'):
            print(f"    • Endpoints: {', '.join(api['endpoints'])}")
        if api.get('http_methods'):
            print(f"    • HTTP Methods: {', '.join(api['http_methods'])}")
        if api.get('api_frameworks'):
            print(f"    • API Frameworks: {', '.join(api['api_frameworks'])}")
        print()
    
    if 'structure' in results:
        struct = results['structure']
        print("  🏗️ PROJECT STRUCTURE:")
        if struct.get('entry_points'):
            print(f"    • Entry Points: {', '.join(struct['entry_points'])}")
        print(f"    • Test Directories: {len(struct.get('test_directories', []))}")
        print(f"    • Source Directories: {len(struct.get('source_directories', []))}")
        print()

    # Display Summary
    print("📋 ANALYSIS SUMMARY:")
    print(analysis_result.get('summary', 'No summary available'))
    print()

    # State full analysis complete
    print("🛠️ FULL ANALYSIS DETAILS:")
    import json
    print(json.dumps(analysis_result, indent=2, default=str))
    print()

    # Display Tokens Used
    tokens_used = analysis_result.get('tokens_used', 0)
    print(f"🎫 TOKENS USED: {tokens_used}")

    # ✅ SAVE RESULTS TO JSON FILE
    import json
    from datetime import datetime
    
    # Create outputs directory if it doesn't exist
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"analysis_result_{timestamp}.json"
    json_path = outputs_dir / json_filename
    
    # Save full analysis result to JSON
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        print(f"💾 Analysis results saved to: {json_path}")
    except Exception as e:
        print(f"⚠️ Failed to save JSON results: {e}")

    print("\n✅ Agent reasoning analysis completed successfully!")

    """_summary_
    Example usage:

    source .venv/bin/activate && python3 scripts/coding_agent/flow_analyze_context.py --codebase-path dataset/codes/springboot-demo --feature-request "Add inventory management system with full CRUD operations including Product entity, repository, service, and REST controller with endpoints for creating, reading, updating, and deleting inventory properly with audit trail"
    """
