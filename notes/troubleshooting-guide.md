# Troubleshooting Guide

## Common Issues and Solutions

### Framework Detection Issues

#### Issue: Framework Not Detected
**Symptoms**: Agent reports "Unknown framework" or falls back to generic detection

**Possible Causes**:
- Missing framework-specific files
- Unusual project structure
- Mixed technology stack
- Missing dependencies

**Solutions**:
1. **Verify Framework Files**:
   ```bash
   # For Spring Boot - check for these files:
   ls -la pom.xml build.gradle application.properties application.yml
   
   # For FastAPI - check for these files:
   ls -la requirements.txt pyproject.toml main.py app.py
   
   # For Express.js - check for these files:
   ls -la package.json server.js app.js index.js
   ```

2. **Check Dependencies**:
   ```bash
   # Java projects
   grep -i "spring-boot\|fastapi\|express" pom.xml pyproject.toml package.json
   
   # Python projects  
   grep -i "fastapi\|django\|flask" requirements.txt pyproject.toml
   
   # Node.js projects
   grep -i "express\|fastify\|koa" package.json
   ```

3. **Validate Project Structure**:
   ```bash
   # Check for typical framework structure
   find . -name "*.java" -o -name "*.py" -o -name "*.js" | head -20
   ```

4. **Enable Debug Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Run detection with debug output
   detector = UniversalStackDetector()
   framework_info = detector.detect_framework(codebase_path)
   ```

#### Issue: Wrong Framework Detected
**Symptoms**: Agent detects a different framework than expected

**Solutions**:
1. **Check Mixed Dependencies**:
   - Remove unused dependencies from build files
   - Ensure primary framework dependencies are clearly defined

2. **Explicit Framework Configuration**:
   ```yaml
   # .agnostic-agent.yml
   framework:
     override: "spring_boot"  # Force specific framework
     version: "3.1.0"
   ```

3. **Clean Project Structure**:
   - Remove legacy or experimental framework files
   - Ensure consistent naming conventions

### Template Generation Issues

#### Issue: Template Not Found Error
**Symptoms**: `TemplateNotFoundError: Template 'entity' not found for framework 'spring_boot'`

**Solutions**:
1. **Verify Template Registry**:
   ```python
   from scripts.template_engine import TemplateRegistry
   
   registry = TemplateRegistry()
   templates = registry.get_available_templates("spring_boot")
   print("Available templates:", templates)
   ```

2. **Check Template Files**:
   ```bash
   # Verify template files exist
   find templates/ -name "*.j2" | grep spring_boot
   ```

3. **Register Missing Templates**:
   ```python
   registry = TemplateRegistry()
   registry.register_template("spring_boot", "entity", "spring_boot/entity.j2")
   ```

#### Issue: Template Rendering Fails
**Symptoms**: `TemplateRenderError: Undefined variable 'model_name'`

**Solutions**:
1. **Check Template Variables**:
   ```python
   # Debug template context
   context = GenerationContext(...)
   print("Template variables:", context.template_variables)
   ```

2. **Validate Required Variables**:
   ```jinja2
   {# Add default values in template #}
   {{ model_name | default('DefaultModel') }}
   {{ package_name | default('com.example') }}
   ```

3. **Complete Context Setup**:
   ```python
   context = GenerationContext(
       framework=framework_info,
       template_variables={
           'model_name': 'User',
           'package_name': 'com.example.entity',
           'fields': [...],
           'table_name': 'users'
       }
   )
   ```

### Research Integration Issues

#### Issue: Tavily API Connection Fails
**Symptoms**: `ResearchError: Failed to connect to Tavily API`

**Solutions**:
1. **Check API Key**:
   ```bash
   echo $TAVILY_API_KEY
   # Should output your API key, not empty
   ```

2. **Verify Network Connection**:
   ```bash
   curl -H "Authorization: Bearer $TAVILY_API_KEY" \
        https://api.tavily.com/search
   ```

3. **Check Rate Limits**:
   ```python
   client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
   status = client.get_rate_limit_status()
   print(f"Remaining requests: {status.remaining_requests}")
   ```

4. **Configure Timeout and Retries**:
   ```python
   client = TavilyClient(
       api_key=api_key,
       timeout=30,
       max_retries=3,
       retry_delay=1.0
   )
   ```

#### Issue: Research Results Are Poor Quality
**Symptoms**: Generated code doesn't follow best practices

**Solutions**:
1. **Refine Search Queries**:
   ```python
   # Instead of generic queries
   query = "authentication"
   
   # Use specific, targeted queries
   query = "Spring Boot JWT authentication best practices 2024"
   ```

2. **Include Domain Filters**:
   ```python
   results = await client.search(
       query=query,
       include_domains=["spring.io", "baeldung.com", "official_docs"]
   )
   ```

3. **Cache High-Quality Results**:
   ```python
   # Cache results for reuse
   cache_key = f"{framework}_{topic}_{version}"
   cached = knowledge_cache.get(cache_key)
   ```

### File Placement Issues

#### Issue: Files Placed in Wrong Directory
**Symptoms**: Generated files appear in unexpected locations

**Solutions**:
1. **Check Placement Rules**:
   ```python
   rules = FastAPIPlacementRules()
   placement = rules.determine_placement(artifact, context)
   print(f"Target directory: {placement.target_directory}")
   ```

2. **Verify Project Structure Detection**:
   ```python
   structure = rules._detect_structure_pattern(codebase_path)
   print(f"Detected structure: {structure}")
   ```

3. **Override Placement**:
   ```yaml
   # .agnostic-agent.yml
   placement:
     spring_boot:
       entity: "src/main/java/com/custom/entity"
       controller: "src/main/java/com/custom/web"
   ```

#### Issue: Import Statements Incorrect
**Symptoms**: Generated code has wrong import statements

**Solutions**:
1. **Check Package Detection**:
   ```python
   package_name = rules._detect_base_package(codebase_path)
   print(f"Base package: {package_name}")
   ```

2. **Validate Import Calculation**:
   ```python
   imports = rules._calculate_imports(artifact, placement_info, context)
   for imp in imports:
       print(f"Import: {imp}")
   ```

3. **Manual Import Override**:
   ```python
   context.add_variable('custom_imports', [
       'import com.example.custom.BaseEntity',
       'import org.springframework.data.jpa.repository.JpaRepository'
   ])
   ```

### Agent Coordination Issues

#### Issue: Agent Tasks Fail
**Symptoms**: `CoordinationError: SecurityAgent failed with timeout`

**Solutions**:
1. **Check Agent Status**:
   ```python
   coordinator = AgentCoordinator()
   available_agents = coordinator.get_available_agents()
   print(f"Available agents: {available_agents}")
   ```

2. **Increase Timeouts**:
   ```python
   coordinator = AgentCoordinator(
       task_timeout=120,  # 2 minutes
       coordination_timeout=300  # 5 minutes
   )
   ```

3. **Debug Agent Execution**:
   ```python
   # Enable agent-specific logging
   logging.getLogger('scripts.agents.security_agent').setLevel(logging.DEBUG)
   ```

4. **Run Agents Individually**:
   ```python
   security_agent = SecurityAgent()
   analysis = await security_agent.analyze_requirements(specification)
   ```

### Code Generation Issues

#### Issue: Generated Code Has Syntax Errors
**Symptoms**: Code fails to compile or has syntax issues

**Solutions**:
1. **Enable Syntax Validation**:
   ```python
   validator = SyntaxValidator()
   result = validator.validate(generated_code, language)
   print(f"Syntax errors: {result.errors}")
   ```

2. **Check Template Syntax**:
   ```bash
   # Test template rendering in isolation
   python scripts/template_engine/test_template.py \
     --template "spring_boot/entity.j2" \
     --context context.json
   ```

3. **Validate Template Variables**:
   ```jinja2
   {# Add type checking in templates #}
   {% if model_name is string %}
   public class {{ model_name }} {
   {% else %}
   public class DefaultModel {
   {% endif %}
   ```

#### Issue: Generated Code Doesn't Follow Framework Conventions
**Symptoms**: Code works but doesn't follow best practices

**Solutions**:
1. **Update Pattern Validation**:
   ```python
   validator = PatternValidator()
   result = validator.validate(code, framework)
   for issue in result.issues:
       print(f"Pattern issue: {issue.message}")
   ```

2. **Enhance Templates**:
   ```jinja2
   {# Add framework-specific annotations #}
   {% if framework.name == "spring_boot" %}
   @RestController
   @RequestMapping("/api/{{ endpoint_prefix }}")
   {% elif framework.name == "fastapi" %}
   router = APIRouter(prefix="/{{ endpoint_prefix }}")
   {% endif %}
   ```

3. **Update Research Queries**:
   ```python
   queries = [
       f"{framework} {component_type} best practices",
       f"{framework} {component_type} conventions 2024",
       f"{framework} {component_type} security patterns"
   ]
   ```

### Performance Issues

#### Issue: Slow Framework Detection
**Symptoms**: Detection takes longer than expected

**Solutions**:
1. **Enable Caching**:
   ```python
   detector = UniversalStackDetector(enable_cache=True)
   ```

2. **Limit File Scanning**:
   ```python
   detector = UniversalStackDetector(
       max_files_to_scan=1000,
       exclude_patterns=['node_modules/', '.git/', 'target/', 'build/']
   )
   ```

3. **Use Parallel Processing**:
   ```python
   detector = UniversalStackDetector(parallel_processing=True, max_workers=4)
   ```

#### Issue: High Memory Usage
**Symptoms**: System runs out of memory during processing

**Solutions**:
1. **Enable Streaming Processing**:
   ```python
   analyzer = RepoAnalyzer(streaming=True, chunk_size=100)
   ```

2. **Limit Context Size**:
   ```python
   context = GenerationContext(
       max_context_size=8192,
       token_limit=6000
   )
   ```

3. **Clear Caches Periodically**:
   ```python
   # Clear caches every 100 operations
   if operation_count % 100 == 0:
       knowledge_cache.clear()
       template_cache.clear()
   ```

### Configuration Issues

#### Issue: Environment Variables Not Loading
**Symptoms**: API keys or configuration not found

**Solutions**:
1. **Check .env File**:
   ```bash
   cat .env | grep -E "(OPENAI_API_KEY|TAVILY_API_KEY|ANTHROPIC_API_KEY)"
   ```

2. **Verify File Loading**:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   print(f"OpenAI Key: {os.getenv('OPENAI_API_KEY', 'Not Found')}")
   ```

3. **Use Explicit Path**:
   ```python
   load_dotenv('/absolute/path/to/.env')
   ```

#### Issue: Invalid Configuration Values
**Symptoms**: System uses wrong settings

**Solutions**:
1. **Validate Configuration**:
   ```python
   config = SystemConfiguration()
   validation_result = config.validate_configuration()
   if not validation_result.is_valid:
       print(f"Config errors: {validation_result.errors}")
   ```

2. **Use Configuration Schema**:
   ```yaml
   # config/schema.yml
   required_fields:
     - OPENAI_API_KEY
     - TAVILY_API_KEY
   optional_fields:
     - ANTHROPIC_API_KEY
     - LANGCHAIN_API_KEY
   ```

### Debugging Strategies

#### Enable Comprehensive Logging

```python
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Enable specific component logging
logging.getLogger('scripts.framework_detection').setLevel(logging.DEBUG)
logging.getLogger('scripts.template_engine').setLevel(logging.DEBUG)
logging.getLogger('scripts.agent_coordination').setLevel(logging.DEBUG)
```

#### Use Debug Mode

```bash
# Run with debug flag
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path /path/to/project \
  --feature-request-spec spec.md \
  --debug \
  --verbose
```

#### Validate Each Component

```python
# Test components individually
def test_components():
    # 1. Test framework detection
    detector = UniversalStackDetector()
    framework_info = detector.detect_framework(codebase_path)
    print(f"Framework: {framework_info}")
    
    # 2. Test template engine
    engine = InstructionTemplateEngine()
    templates = engine.get_available_templates(framework_info.name)
    print(f"Templates: {templates}")
    
    # 3. Test research integration
    client = TavilyClient(api_key=api_key)
    results = await client.search("test query")
    print(f"Research results: {len(results.results)}")
    
    # 4. Test agent coordination
    coordinator = AgentCoordinator()
    agents = coordinator.get_available_agents()
    print(f"Agents: {agents}")
```

## Getting Help

### Log Analysis
Check these log files for detailed information:
- `logs/agent-execution.log` - Main execution log
- `logs/framework-detection.log` - Framework detection details
- `logs/template-generation.log` - Template generation details
- `logs/research-integration.log` - Research API interactions
- `logs/agent-coordination.log` - Multi-agent coordination

### Support Resources
- **Documentation**: Check all documentation files in `notes/` directory
- **Examples**: Review sample projects in `dataset/` directory
- **Test Suite**: Run test suite to identify issues: `python -m pytest tests/`
- **GitHub Issues**: Report bugs and request features
- **Community**: Join discussions for tips and solutions

### Diagnostic Commands

```bash
# System health check
python scripts/diagnostics/system_check.py

# Framework detection test
python scripts/diagnostics/test_detection.py --path /project/path

# Template validation
python scripts/diagnostics/validate_templates.py

# API connectivity test
python scripts/diagnostics/test_apis.py

# Performance benchmark
python scripts/diagnostics/benchmark.py --project-size large
```

This troubleshooting guide covers the most common issues you might encounter when using the Framework-Agnostic Coding Agent. For additional help, refer to the complete documentation or reach out to the community.