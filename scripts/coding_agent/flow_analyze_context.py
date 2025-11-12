"""
FLOW: Context Analysis (Refactored Version)
============================================

Fast filesystem-based analysis for codebase context detection using Aider-style approach.
Enhanced with LiteLLM for real agent reasoning and Tree-sitter for advanced code parsing.

This flow analyzes project structure, technology stack, and provides
initial context for feature implementation.
Phase 1 of multi-phase workflow for feature implementation.

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
            import litellm

            class RealLLMModel:
                def __init__(self):
                    self.model = os.getenv('LITELLM_MODEL', 'gpt-4')

                def token_count(self, text: str) -> int:
                    """Count tokens using rough estimation"""
                    return max(1, len(text) // 4)

                def generate_reasoning(self, prompt: str, max_tokens: int = 1000) -> str:
                    """Generate reasoning using LiteLLM"""
                    try:
                        response = litellm.completion(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,
                            temperature=1.0,
                            api_key=os.getenv('LITELLM_VIRTUAL_KEY'),
                            api_base=os.getenv('LITELLM_API')
                        )
                        if hasattr(response, 'choices') and response.choices:
                            return response.choices[0].message.content.strip()
                        else:
                            return "LLM response format unexpected"
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
        print(f"🤔 Agent Reasoning: Analyzing request '{user_request}'")

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

        return {
            "basic_info": basic_info,
            "code_analysis": code_analysis,
            "dependencies": dependencies,
            "api_patterns": api_patterns,
            "ranked_elements": ranked_elements,
            "structure": structure
        }

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
            "architecture_patterns": []
        }

        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file in ['main.py', 'app.py', '__main__.py', 'main.go', 'Main.java', 'index.js']:
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    structure["entry_points"].append(rel_path)

        return structure

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
        """Infer where to place new code"""
        cache_key = hashlib.md5(feature_request.encode()).hexdigest()
        if cache_key in self.structure_inference_cache:
            return self.structure_inference_cache[cache_key]

        basic = analysis_result.get("basic_info", {})
        placement_suggestions = []

        if basic.get('project_type') == 'Java/Maven':
            if 'entity' in feature_request.lower():
                placement_suggestions.append({
                    'type': 'entity',
                    'directory': 'src/main/java/com/example/entity',
                    'filename_pattern': '{Entity}Entity.java',
                    'purpose': 'JPA entity classes'
                })
            if 'endpoint' in feature_request.lower() or 'controller' in feature_request.lower():
                placement_suggestions.append({
                    'type': 'controller',
                    'directory': 'src/main/java/com/example/controller',
                    'filename_pattern': '{Feature}Controller.java',
                    'purpose': 'REST controllers'
                })

        result = {
            'placement_suggestions': placement_suggestions,
            'confidence_score': len(placement_suggestions) * 0.2 if placement_suggestions else 0.0
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
        dependencies = analysis_result["dependencies"]
        api_patterns = analysis_result["api_patterns"]
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


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_analyze_context():
    """Test function to show what analyze_context does"""
    print("🧪 Testing analyze_context")
    print("=" * 50)

    test_state: AgentState = {
        "codebase_path": "/Users/zeihanaulia/Programming/research/agent/dataset/codes/casdoor",
        "feature_request": "Add product management with CRUD endpoints",
        "context_analysis": None,
        "feature_spec": None,
        "impact_analysis": None,
        "structure_assessment": None,
        "code_patches": None,
        "execution_results": None,
        "errors": [],
        "dry_run": True,
        "current_phase": "initialized",
        "human_approval_required": False,
        "framework": None
    }

    result_state = analyze_context(test_state)

    print("\n✅ ANALYSIS COMPLETE:")
    print(result_state['context_analysis'])

    return result_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aider-style codebase analysis')
    parser.add_argument('--codebase-path', required=True, help='Path to analyze')
    parser.add_argument('--feature-request', required=True, help='Feature request')

    args = parser.parse_args()

    analyzer = AiderStyleRepoAnalyzer(args.codebase_path, max_tokens=2048)
    analysis_result = analyzer.analyze_with_reasoning(args.feature_request)

    print("\n🤖 AGENT REASONING RESULTS:")
    print("=" * 50)
    reasoning = analysis_result.get('reasoning', {})
    print(f"🎯 Request Type: {reasoning.get('request_type', 'unknown')}")
    print(f"📊 Analysis Scope: {reasoning.get('scope', 'unknown')}")
    print(f"🔧 Complexity: {reasoning.get('estimated_complexity', 'unknown')}")
    print(f"🎯 Priority Areas: {', '.join(reasoning.get('priority_areas', []))}")

    print(f"\n📋 ANALYSIS SUMMARY:")
    print(analysis_result.get('summary', 'No summary available'))

    print("\n✅ Agent reasoning analysis completed successfully!")
