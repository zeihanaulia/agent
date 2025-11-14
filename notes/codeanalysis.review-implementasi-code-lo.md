# Review Implementasi Code Lo 🔍

Gw bakal breakdown implementasinya dan kasih feedback + improvement suggestions.

---

## **✅ Yang Udah Bagus**

### 1. **Architecture Pattern**
```python
class AiderStyleRepoAnalyzer:
    def analyze_with_reasoning() -> Dict[str, Any]:
        reasoning = self._reason_about_request()      # Step 1: Understand
        plan = self._create_analysis_plan()           # Step 2: Plan  
        results = self._execute_selective_analysis()  # Step 3: Execute
        summary = self._generate_reasoned_summary()   # Step 4: Summarize
```
✅ **Clean separation of concerns** - mirip LangGraph pattern
✅ **Multi-phase workflow** - reasoning → planning → execution
✅ **Selective analysis** - gak scan semua file

### 2. **Token Management**
```python
self.max_tokens = max_tokens
self.current_tokens = 0
```
✅ Awareness tentang token budget

### 3. **LLM Integration**
```python
def _create_real_llm_model(self):
    # Uses LiteLLM with fallback
```
✅ Ada fallback ke rule-based reasoning

### 4. **Tree-sitter Support**
```python
if TREE_SITTER_AVAILABLE:
    self._setup_tree_sitter_parsers()
```
✅ Graceful degradation kalau tree-sitter gak ada

---

## **⚠️ Issues & Improvements**

### **CRITICAL ISSUE #1: Token Counting Tapi Gak Dipakai**

```python
# Lo declare token management tapi gak dipake!
self.current_tokens = 0  # ❌ Never updated!

def token_count(self, text: str) -> int:
    return self.main_model.token_count(text)  # ❌ Never called!
```

**Problem:** Lo aware sama token usage tapi **gak actually track**.

**Fix:**
```python
def _execute_selective_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    results = {}
    self.current_tokens = 0  # Reset
    
    for analysis in plan['analyses_to_run']:
        # ✅ TRACK TOKENS BEFORE ANALYSIS
        before_tokens = self.current_tokens
        
        if analysis == 'basic_filesystem_scan':
            results['basic_info'] = self._basic_filesystem_scan()
            # ✅ COUNT TOKENS USED
            result_str = str(results['basic_info'])
            self.current_tokens += self.token_count(result_str)
        
        elif analysis == 'tag_extraction':
            results['code_analysis'] = self._extract_code_tags()
            result_str = str(results['code_analysis'])
            self.current_tokens += self.token_count(result_str)
        
        tokens_used = self.current_tokens - before_tokens
        print(f"  ✓ {analysis} completed ({tokens_used} tokens)")
        
        # ✅ CHECK BUDGET
        budget = plan['token_budget'].get(analysis, float('inf'))
        if tokens_used > budget:
            print(f"  ⚠️ Exceeded budget: {tokens_used}/{budget} tokens")
    
    return results
```

---

### **CRITICAL ISSUE #2: File Map Build Tapi Gak Dipakai di Reasoning**

```python
def analyze_codebase(self) -> Dict[str, Any]:
    file_map = self._build_file_map()  # ✅ Build map
    return {
        "file_map": file_map  # ❌ Cuma return, gak dipake untuk selection
    }
```

**Problem:** Lo build file map **TAPI** gak dipake buat **selective file loading**.

**Expected Flow:**
```
User Request → Reasoning → Select Relevant Files → Load ONLY Those Files
```

**Current Flow:**
```
User Request → Reasoning → Load Everything → Return Everything ❌
```

**Fix:**
```python
def _execute_selective_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    results = {}
    
    # ✅ BUILD FILE MAP FIRST (lightweight)
    file_map = self._build_lightweight_file_map()  # Just paths + metadata
    results['file_map_summary'] = {
        'total_files': len(file_map),
        'by_language': self._count_by_language(file_map)
    }
    
    # ✅ SELECT RELEVANT FILES based on reasoning
    if 'select_relevant_files' in plan['analyses_to_run']:
        relevant_files = self._select_relevant_files(
            plan['focus_areas'],
            file_map
        )
        results['relevant_files'] = relevant_files
        
        # ✅ LOAD ONLY SELECTED FILES (not all!)
        results['file_contents'] = {}
        for file_path in relevant_files[:10]:  # Max 10 files
            try:
                with open(self.codebase_path / file_path, 'r') as f:
                    results['file_contents'][file_path] = f.read()
            except Exception as e:
                print(f"  ⚠️ Failed to load {file_path}: {e}")
    
    return results

def _build_lightweight_file_map(self) -> Dict[str, Dict[str, Any]]:
    """Build map WITHOUT loading file contents"""
    file_map = {}
    
    for root, dirs, files in os.walk(self.codebase_path):
        for file in files:
            if file.endswith(('.py', '.java', '.js', '.go')):
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(self.codebase_path))
                
                # ✅ ONLY metadata, NO content loading yet
                file_map[rel_path] = {
                    'size': file_path.stat().st_size,
                    'language': file_path.suffix[1:],
                    'last_modified': file_path.stat().st_mtime
                }
    
    return file_map

def _select_relevant_files(
    self,
    focus_areas: list,
    file_map: Dict[str, Any]
) -> list:
    """Select files based on reasoning focus areas"""
    scores = {}
    
    for file_path, metadata in file_map.items():
        score = 0
        
        # Score based on focus areas
        if 'api_endpoints' in focus_areas:
            if 'controller' in file_path.lower() or 'api' in file_path.lower():
                score += 5
        
        if 'data_models' in focus_areas:
            if 'entity' in file_path.lower() or 'model' in file_path.lower():
                score += 5
        
        if 'business_logic' in focus_areas:
            if 'service' in file_path.lower():
                score += 5
        
        if score > 0:
            scores[file_path] = score
    
    # Return top scored files
    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [f[0] for f in sorted_files]
```

---

### **ISSUE #3: Code Placement Reasoning Gak Dipanggil di Main Flow**

```python
def infer_code_placement(self, feature_request: str, ...) -> Dict[str, Any]:
    # ✅ Good logic here
    reasoning_result = self._reason_placement_with_context(...)
    
# ❌ BUT: Method ini dipanggil di analyze_codebase()
# yang berarti SELALU run, even kalau user gak butuh placement
```

**Problem:** Placement reasoning should be **conditional**, tapi lo run **always**.

**Fix:**
```python
def _execute_selective_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    results = {}
    
    # ... other analyses ...
    
    # ✅ CONDITIONAL placement analysis
    if 'code_placement' in plan['analyses_to_run']:
        print("  📍 Analyzing code placement...")
        placement = self.infer_code_placement(
            feature_request=plan.get('feature_request', ''),
            analysis_result=results
        )
        results['placement_analysis'] = placement
    
    return results

def _create_analysis_plan(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
    plan = {
        'analyses_to_run': ['basic_filesystem_scan'],
        # ...
    }
    
    # ✅ ONLY add placement if request involves creating new code
    if reasoning['request_type'] in ['feature_implementation', 'refactoring']:
        plan['analyses_to_run'].append('code_placement')
    
    return plan
```

---

### **ISSUE #4: LLM Reasoning Response Parsing Brittle**

```python
def _parse_llm_reasoning_response(self, llm_response: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(llm_response)  # ❌ Assumes perfect JSON
        return {...}
    except json.JSONDecodeError:
        return self._parse_llm_text_response(llm_response)
```

**Problem:** LLM sering return JSON wrapped in ```json blocks atau dengan preamble.

**Fix:**
```python
def _parse_llm_reasoning_response(self, llm_response: str) -> Dict[str, Any]:
    try:
        # ✅ CLEAN response first
        cleaned = llm_response.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith('```'):
            # Extract content between ```json and ```
            start = cleaned.find('```json')
            if start >= 0:
                cleaned = cleaned[start + 7:]  # Skip ```json
            else:
                start = cleaned.find('```')
                if start >= 0:
                    cleaned = cleaned[start + 3:]
            
            end = cleaned.find('```')
            if end >= 0:
                cleaned = cleaned[:end]
        
        # Find first { and last }
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        
        if start_idx >= 0 and end_idx >= 0:
            json_str = cleaned[start_idx:end_idx+1]
            parsed = json.loads(json_str)
            
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
            raise json.JSONDecodeError("No JSON found", cleaned, 0)
            
    except (json.JSONDecodeError, Exception) as e:
        print(f"  ⚠️ Failed to parse JSON: {e}")
        return self._parse_llm_text_response(llm_response)
```

---

### **ISSUE #5: Tree-sitter Parser Created But Rarely Used**

```python
def _setup_tree_sitter_parsers(self):
    # ✅ Setup parsers
    self.parsers['.py'] = Parser(PY_LANGUAGE)
    
def _extract_file_tags(self, content: str, file_path: str) -> list:
    # ❌ BUT: Uses regex instead!
    if file_path.endswith('.py'):
        for i, line in enumerate(lines):  # Regex approach
            if line.startswith(('def ', 'class ')):
```

**Problem:** Lo setup tree-sitter tapi **fallback ke regex** immediately.

**Fix:**
```python
def _extract_file_tags(self, content: str, file_path: str) -> list:
    ext = Path(file_path).suffix
    
    # ✅ TRY tree-sitter first
    if ext in self.parsers and TREE_SITTER_AVAILABLE:
        try:
            return self._extract_tags_with_tree_sitter(content, file_path, ext)
        except Exception as e:
            print(f"  ⚠️ Tree-sitter failed for {file_path}: {e}, falling back to regex")
    
    # ✅ FALLBACK to regex
    return self._extract_tags_with_regex(content, file_path)

def _extract_tags_with_tree_sitter(
    self,
    content: str,
    file_path: str,
    ext: str
) -> list:
    """Extract tags using tree-sitter (accurate)"""
    parser = self.parsers[ext]
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
        
        for child in node.children:
            traverse(child)
    
    traverse(tree.root_node)
    return tags

def _extract_tags_with_regex(self, content: str, file_path: str) -> list:
    """Fallback regex-based extraction"""
    # Your current implementation
    tags = []
    lines = content.split('\n')
    # ... regex logic ...
    return tags
```

---

## **💡 Suggested Architecture Improvements**

### **Better Flow dengan Actual File Selection**

```python
class AiderStyleRepoAnalyzer:
    
    def analyze_with_reasoning(self, user_request: str) -> Dict[str, Any]:
        """Main entry point"""
        
        # Step 1: Build lightweight repo map (NO file loading)
        print("📂 Building repository map...")
        self.repo_map = self._build_repo_map()  # Just structure, no content
        
        # Step 2: Reason about request
        print("🤔 Reasoning about request...")
        reasoning = self._reason_about_request(user_request)
        
        # Step 3: Create analysis plan
        print("📋 Creating analysis plan...")
        plan = self._create_analysis_plan(reasoning)
        
        # Step 4: Select relevant files (BASED ON REASONING)
        print("🎯 Selecting relevant files...")
        relevant_files = self._select_relevant_files(
            reasoning, 
            plan, 
            self.repo_map
        )
        
        # Step 5: Load ONLY selected files
        print(f"📖 Loading {len(relevant_files)} relevant files...")
        file_contents = self._load_selected_files(relevant_files)
        
        # Step 6: Analyze selected files
        print("🔍 Analyzing selected files...")
        analysis_results = self._analyze_selected_files(
            file_contents,
            reasoning
        )
        
        # Step 7: Generate summary
        print("📝 Generating summary...")
        summary = self._generate_reasoned_summary(
            analysis_results,
            reasoning
        )
        
        return {
            'reasoning': reasoning,
            'selected_files': relevant_files,
            'analysis': analysis_results,
            'summary': summary,
            'tokens_used': self.current_tokens
        }
    
    def _build_repo_map(self) -> Dict[str, Any]:
        """Build lightweight map WITHOUT loading file contents"""
        repo_map = {
            'files': {},
            'structure': {},
            'statistics': {}
        }
        
        for root, dirs, files in os.walk(self.codebase_path):
            for file in files:
                if file.endswith(('.py', '.java', '.js', '.go')):
                    file_path = Path(root) / file

        
        return repo_map
    
    def _select_relevant_files(
        self,
        reasoning: Dict[str, Any],
        plan: Dict[str, Any],
        repo_map: Dict[str, Any]
    ) -> list:
        """Smart file selection based on reasoning"""
        
        # Use LLM to select if available
        if LLM_AVAILABLE:
            return self._llm_select_files(reasoning, repo_map)
        
        # Fallback to keyword matching
        return self._keyword_select_files(reasoning, repo_map)
    
    def _llm_select_files(
        self,
        reasoning: Dict[str, Any],
        repo_map: Dict[str, Any]
    ) -> list:
        """Use cheap LLM to select relevant files"""
        
        # Build lightweight file list
        file_summaries = []
        for path, metadata in list(repo_map['files'].items())[:100]:  # Limit to 100
            file_summaries.append({
                'path': path,
                'size': metadata['size'],
                'type': metadata['ext']
            })
        
        prompt = f"""
Given this request: "{reasoning.get('original_request', '')}"

Select the 10 most relevant files from this list:
{json.dumps(file_summaries, indent=2)}

Return ONLY a JSON array of file paths: ["path1", "path2", ...]
"""
        
        response = self.generate_llm_reasoning(prompt, max_tokens=300)
        
        try:
            # Parse response
            cleaned = response.strip()
            if cleaned.startswith('['):
                selected = json.loads(cleaned)
                return selected[:10]
        except:
            pass
        
        # Fallback
        return self._keyword_select_files(reasoning, repo_map)
    
    def _keyword_select_files(
        self,
        reasoning: Dict[str, Any],
        repo_map: Dict[str, Any]
    ) -> list:
        """Keyword-based file selection"""
        scores = {}
        
        keywords = (
            reasoning.get('entities', []) +
            reasoning.get('actions', []) +
            reasoning.get('technologies', [])
        )
        
        for file_path in repo_map['files'].keys():
            score = 0
            file_lower = file_path.lower()
            
            for keyword in keywords:
                if keyword.lower() in file_lower:
                    
            
            # Boost files in priority areas
            for area in reasoning.get('priority_areas', []):
                if area.replace('_', '') in file_lower:
                    
            
            if score > 0:
                scores[file_path] = score
        
        # Sort and return top files
        sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_files[:10]]
    
    def _load_selected_files(self, file_paths: list) -> Dict[str, str]:
        """Load ONLY selected files"""
        contents = {}
        tokens_loaded = 0
        
        for file_path in file_paths:
            try:
                full_path = self.codebase_path / file_path
                with open(full_path, 'r', encoding='utf-8') as f:
                    /* Line 564 omitted */
                
                # Track tokens
                file_tokens = self.token_count(content)
                
                # Check if we're within budget
                if tokens_loaded + file_tokens > self.max_tokens:
                    /* Lines 571-572 omitted */
                
                contents[file_path] = content
                tokens_loaded += file_tokens
                
            except Exception as e:
                print(f"  ⚠️ Failed to load {file_path}: {e}")
        
        self.current_tokens += tokens_loaded
        print(f"  ✓ Loaded {len(contents)} files ({tokens_loaded} tokens)")
        
        return contents
```

---

## **📊 Comparison: Before vs After**

| Aspect | Current Implementation | Suggested Implementation |
|--------|----------------------|-------------------------|
| **File Loading** | Loads all files in `_build_file_map()` | Loads only selected 5-10 files |
| **Token Usage** | Declared but not tracked | Actually tracked & enforced |
| **File Selection** | No selection, returns everything | LLM or keyword-based selection |
| **Tree-sitter** | Setup but uses regex | Try tree-sitter first, fallback regex |
| **Placement** | Always runs | Conditional based on request type |
| **Token Efficiency** | ~500K tokens for 1000 files | ~5K tokens for 10 files |

---

## **🎯 Next Steps**

1. **Implement actual file selection** (CRITICAL - ini yang paling hemat token)
2. **Fix token tracking** (biar lo bisa monitor usage)
3. **Use tree-sitter properly** (more accurate parsing)
4. **Make placement conditional** (don't always run)
5. **Better JSON parsing** (handle LLM response edge cases)

Mau gw bikinin **complete refactored version** yang implement semua improvements ini?
