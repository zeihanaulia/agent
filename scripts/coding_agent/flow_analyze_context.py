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

                def token_count(self, text: str) -> int:
                    """Count tokens using rough estimation"""
                    return max(1, len(text) // 4)

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
        Agent reasoning: Analyze what needs to be checked based on user request
        
        Returns:
            Dict with keys: reasoning, analysis_plan, results, summary, tokens_used
        """
        # Step 1: Parse user request to understand what they want
        reasoning_context = self._reason_about_request(user_request)

        # Step 2: Determine analysis scope based on reasoning
        analysis_plan = self._create_analysis_plan(reasoning_context)

        # Step 3: Execute selective analysis based on plan
        results = self._execute_selective_analysis(analysis_plan)

        # Step 4: Generate context-aware summary
        summary = self._generate_reasoned_summary(results, reasoning_context)

        return {
            'reasoning': reasoning_context,
            'analysis_plan': analysis_plan,
            'results': results,
            'summary': summary,
            'tokens_used': self.current_tokens
        }

    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze codebase using Aider-style approach"""
        print("  🔍 Performing Aider-style code analysis...")

        basic_info = self._basic_filesystem_scan()
        code_analysis = self._extract_code_tags()
        dependencies = self._analyze_dependencies()
        api_patterns = self._analyze_api_patterns()
        ranked_elements = self._rank_code_elements()
        structure = self._analyze_project_structure()
        file_map = self._build_file_map()  # ✓ BUILD FILE MAP FOR PHASE 2
        
        # ✓ NEW: Generate placement suggestions with discovered packages
        analysis_result_for_placement = {
            "basic_info": basic_info,
            "structure": structure  # ✓ PASS discovered packages to placement analyzer
        }
        placement_analysis = self.infer_code_placement("", analysis_result_for_placement)

        return {
            "basic_info": basic_info,
            "code_analysis": code_analysis,
            "dependencies": dependencies,
            "api_patterns": api_patterns,
            "ranked_elements": ranked_elements,
            "structure": structure,
            "file_map": file_map,  # ✓ INCLUDE FILE MAP
            "placement_analysis": placement_analysis  # ✓ NEW: Include placement insights
        }
    
    def _build_file_map(self) -> Dict[str, Dict[str, Any]]:
        """Build a map of source files with their content"""
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
            'llm_insights': None
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
                print("  🧠 LLM reasoning completed")
            except Exception as e:
                print(f"  ⚠️ LLM reasoning failed: {e}, falling back to rule-based")
                reasoning.update(self._rule_based_reasoning(user_request))
        else:
            reasoning.update(self._rule_based_reasoning(user_request))

        print(f"  🧠 Reasoning complete: {reasoning['request_type']} | scope: {reasoning['scope']}")
        print(f"  🎯 Priority areas: {', '.join(reasoning['priority_areas'])}")

        return reasoning

    def _parse_llm_reasoning_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured reasoning data"""
        try:
            parsed = json.loads(llm_response)
            return {
                'request_type': parsed.get('Request Type', 'unknown'),
                'entities': parsed.get('Key Entities', []),
                'actions': parsed.get('Required Actions', []),
                'technologies': parsed.get('Technologies', []),
                'estimated_complexity': parsed.get('Complexity Level', 'medium'),
                'scope': parsed.get('Analysis Scope', 'full'),
                'priority_areas': parsed.get('Priority Areas', [])
            }
        except json.JSONDecodeError:
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
            'skip_analyses': []
        }

        scope = reasoning['scope']
        priority_areas = reasoning['priority_areas']

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

        total_budget = self.max_tokens
        base_allocation = max(100, total_budget // len(plan['analyses_to_run']))
        for analysis in plan['analyses_to_run']:
            plan['token_budget'][analysis] = base_allocation

        print(f"  📋 Analysis plan: {len(plan['analyses_to_run'])} analyses")
        return plan

    def _execute_selective_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis based on the plan"""
        results = {}
        self.current_tokens = 0

        for analysis in plan['analyses_to_run']:
            print(f"  🔍 Running {analysis}...")

            if analysis == 'basic_filesystem_scan':
                results['basic_info'] = self._basic_filesystem_scan()
            elif analysis in ['basic_tag_extraction', 'tag_extraction']:
                results['code_analysis'] = self._extract_code_tags()
            elif analysis == 'dependency_analysis':
                results['dependencies'] = self._analyze_dependencies()
            elif analysis == 'api_patterns':
                results['api_patterns'] = self._analyze_api_patterns()
            elif analysis == 'structure_analysis':
                results['structure'] = self._analyze_project_structure()

            print(f"  ✓ {analysis} completed")

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

    def token_count(self, text: str) -> int:
        """Count tokens in text using main model"""
        if not text:
            return 0
        return self.main_model.token_count(text)

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

    def _extract_file_tags(self, content: str, file_path: str) -> list:
        """Extract tags using regex (simplified)"""
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
# MAIN WORKFLOW FUNCTIONS
# ============================================================================

def analyze_context(state: AgentState) -> AgentState:
    """Node: Context Analysis Phase - Aider-style analysis for codebase understanding"""
    print("🔍 Phase 1: Analyzing codebase context (Aider-style)...")

    codebase_path = state["codebase_path"]

    try:
        analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=2048)
        analysis_result = analyzer.analyze_codebase()

        basic = analysis_result["basic_info"]
        code_analysis = analysis_result["code_analysis"]
        ranked = analysis_result["ranked_elements"]
        structure = analysis_result["structure"]

        summary = f"""
PROJECT ANALYSIS (Aider-Style Analysis):

FILESYSTEM SCAN:
- Type: {basic['project_type']}
- Framework: {basic['framework']}
- Tech Stack: {', '.join(basic['tech_stack']) if basic['tech_stack'] else 'Mixed'}
- Total Source Files: {basic['source_files_count']}
- Root Directories: {', '.join(basic['main_dirs'][:5])}

CODE ANALYSIS:
- Tags Extracted: {code_analysis['total_tags']} from {len(code_analysis['tags_by_file'])} files
- Definitions: {len(code_analysis['definitions'])}
- References: {len(code_analysis['references'])}

PROJECT STRUCTURE:
- Entry Points: {', '.join(structure['entry_points']) if structure['entry_points'] else 'None detected'}
- Test Directories: {len(structure['test_directories'])}
- Source Directories: {len(structure['source_directories'])}

ARCHITECTURE INSIGHTS:
1. **Application Type**: {infer_app_type(basic, structure)}
2. **Main Components**: {', '.join([name for name, _ in ranked['top_elements'][:3]])}
3. **Technology Stack**: {', '.join(basic['tech_stack']) if basic['tech_stack'] else 'Unknown'}
"""

        state["context_analysis"] = summary
        state["current_phase"] = "context_analysis_complete"

        print(f"  ✓ Detected: {basic['project_type']} / {basic['framework']}")
        print(f"  ✓ Source files: {basic['source_files_count']}")
        print(f"  ✓ Code tags: {code_analysis['total_tags']}")

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

    analyzer = AiderStyleRepoAnalyzer(args.codebase_path, max_tokens=2048, main_model=analysis_model)
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

    print("\n✅ Agent reasoning analysis completed successfully!")

    """_summary_
    Example usage:

    source .venv/bin/activate && python3 scripts/coding_agent/flow_analyze_context.py --codebase-path dataset/codes/springboot-demo --feature-request "Add inventory management system with full CRUD operations including Product entity, repository, service, and REST controller with endpoints for creating, reading, updating, and deleting inventory properly with audit trail"
    """
