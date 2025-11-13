"""
E2B Sandbox Executor for Spring Boot Projects
============================================

Handles building, running, and debugging Spring Boot applications in E2B sandboxes
with intelligent error analysis and automatic fixing capabilities.
"""

import os
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from e2b import Sandbox
from dotenv import load_dotenv

# Import LLM for auto-fixing using LiteLLM pattern
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()


class ErrorType(Enum):
    """Classification of different error types"""
    COMPILATION_ERROR = "compilation"
    DEPENDENCY_ERROR = "dependency"
    RUNTIME_ERROR = "runtime"
    CONFIGURATION_ERROR = "configuration"
    NETWORK_ERROR = "network"
    UNKNOWN_ERROR = "unknown"


class AutoFixer:
    """Handles automatic code fixing using LLM"""
    
    def __init__(self):
        """Initialize LLM client using LiteLLM configuration"""
        # Get configuration from environment
        model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
        api_key = os.getenv("LITELLM_VIRTUAL_KEY")
        api_base = os.getenv("LITELLM_API")
        
        # Validate environment variables
        if not api_key or not api_base:
            raise ValueError(
                "Missing required LiteLLM environment variables:\n"
                "  LITELLM_VIRTUAL_KEY: LLM API key\n"
                "  LITELLM_API: LLM API base URL\n"
                "Please set these in your .env file."
            )
        
        # Determine if this is a reasoning model
        is_reasoning_model = any(
            keyword in model_name.lower()
            for keyword in ["gpt-5", "5-mini", "oss", "120b", "thinking", "reasoning"]
        )
        
        # Set temperature based on model type
        temperature = 1.0 if is_reasoning_model else 0.7
        
        # Initialize ChatOpenAI client with LiteLLM configuration
        self.client = ChatOpenAI(
            api_key=SecretStr(api_key),
            model=model_name,
            base_url=api_base,
            temperature=temperature,
        )
        
        print(f"🤖 AutoFixer initialized with model: {model_name}")
        
    def fix_compilation_errors(self, error_details: str, project_files: Dict[str, str]) -> Dict[str, str]:
        """
        Fix compilation errors using LLM analysis
        
        Args:
            error_details: Maven compilation error output
            project_files: Dictionary of file_path -> file_content
            
        Returns:
            Dictionary of file_path -> fixed_content for files that need changes
        """
        
        print("🔧 Analyzing compilation errors for auto-fix...")
        print(f"📋 Raw error details:\n{error_details}")
        
        # Extract error information with improved patterns
        error_lines = error_details.split('\n')
        compilation_errors = []
        error_file_references = []
        
        for line in error_lines:
            # Look for Maven compilation error patterns
            if any(keyword in line.lower() for keyword in [
                'cannot find symbol', 'method does not exist', 'compilation failure',
                'error:', '[error]', 'cannot resolve', 'unknown symbol', 'not found'
            ]):
                compilation_errors.append(line.strip())
                print(f"🔍 Found compilation error: {line.strip()}")
                
            # Extract file references from Maven error format
            # Pattern: /app/src/main/java/path/to/File.java:[line,column]
            file_match = re.search(r'/app/src/main/java/([^:\s]+\.java)(?::\[(\d+),(\d+)\])?', line)
            if file_match:
                java_file = file_match.group(1)
                error_file_references.append(java_file)
                print(f"📁 Found error in file: {java_file}")
                
        print(f"📊 Found {len(compilation_errors)} compilation error patterns")
        print(f"📁 Found {len(set(error_file_references))} files with errors")
        
        if not compilation_errors:
            print("ℹ️ No recognizable compilation errors found for auto-fix")
            return {}
            
        # Find relevant files that need fixing - use broader approach
        files_to_fix = {}
        
        # Add files referenced in errors
        for java_file in set(error_file_references):
            relative_path = f"src/main/java/{java_file}"
            if relative_path in project_files:
                files_to_fix[relative_path] = project_files[relative_path]
                print(f"✅ Added file for fixing: {relative_path}")
            else:
                print(f"⚠️ Referenced file not found in project: {relative_path}")
                # Debug: show available files
                print(f"📂 Available files: {list(project_files.keys())[:5]}...")
                
        # Fallback: if no files found via error references, try pattern matching
        if not files_to_fix:
            print("🔄 Fallback: Searching files by error content...")
            for error in compilation_errors:
                if '/app/src/main/java/' in error:
                    # Extract file path from Maven error format
                    file_match = re.search(r'/app/src/main/java/([^:]+\.java)', error)
                    if file_match:
                        java_file = file_match.group(1)
                        relative_path = f"src/main/java/{java_file}"
                        
                        if relative_path in project_files:
                            files_to_fix[relative_path] = project_files[relative_path]
                            print(f"✅ Fallback added: {relative_path}")
                        
        print(f"🎯 Found {len(files_to_fix)} files that may need fixing")
        
        if not files_to_fix:
            print("❌ No fixable files identified. Debug info:")
            print(f"   - Error patterns: {len(compilation_errors)}")
            print(f"   - File references: {len(error_file_references)}")
            print(f"   - Available project files: {len(project_files)}")
            if project_files:
                print(f"   - Sample project files: {list(project_files.keys())[:3]}")
            return {}
            
        # Use LLM to fix the errors
        fixed_files = {}
        for file_path, content in files_to_fix.items():
            print(f"🔍 Analyzing {file_path} for auto-fix...")
            print(f"📝 File content preview (first 200 chars): {content[:200]}...")
            
            try:
                fixed_content = self._fix_java_file_with_llm(file_path, content, error_details)
                if fixed_content and fixed_content != content:
                    fixed_files[file_path] = fixed_content
                    print(f"✅ Generated fix for {file_path}")
                else:
                    print(f"ℹ️ No fix needed or generated for {file_path}")
                    
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                
        return fixed_files
        
    def _fix_java_file_with_llm(self, file_path: str, content: str, error_details: str) -> Optional[str]:
        """Use LLM to fix a Java file based on compilation errors"""
        
        prompt = f"""You are an expert Java/Spring Boot developer. Fix the compilation errors in this Java file.

FILE PATH: {file_path}

COMPILATION ERRORS:
{error_details}

CURRENT FILE CONTENT:
```java
{content}
```

Please analyze the compilation errors and provide the corrected Java file content. Common issues to fix:
1. Missing @Service, @Component, @RestController annotations
2. Missing @SpringBootApplication annotation
3. Broken dependency injection (missing constructors, null assignments)
4. Wrong method names (typos in method calls)
5. Missing imports

Provide ONLY the corrected Java file content without any explanation or markdown formatting."""

        try:
            # Use ChatOpenAI invoke method with enhanced logging
            from langchain_core.messages import HumanMessage, SystemMessage
            
            print(f"🤖 Calling LLM for auto-fix of {file_path}...")
            print(f"📝 Error context length: {len(error_details)} chars")
            print(f"📄 File content length: {len(content)} chars")
            
            system_msg = SystemMessage(content="You are an expert Java/Spring Boot developer who fixes compilation errors.")
            human_msg = HumanMessage(content=prompt)
            
            print("🔄 Invoking LLM...")
            response = self.client.invoke([system_msg, human_msg])
            print("✅ LLM response received")
            
            if response and hasattr(response, 'content') and response.content:
                # Handle different response types
                content_resp = response.content
                fixed_content = ""
                
                print(f"📦 Response type: {type(content_resp)}")
                
                if isinstance(content_resp, str):
                    fixed_content = content_resp.strip()
                    print(f"📝 String response length: {len(fixed_content)}")
                elif isinstance(content_resp, list) and len(content_resp) > 0:
                    # Extract text from list response
                    fixed_content = str(content_resp[0]).strip()
                    print(f"📝 List response converted, length: {len(fixed_content)}")
                else:
                    fixed_content = str(content_resp).strip()
                    print(f"📝 Other response type converted, length: {len(fixed_content)}")
                    
                # Clean up any potential markdown formatting
                if fixed_content.startswith('```java'):
                    fixed_content = fixed_content.replace('```java', '').replace('```', '').strip()
                    print("🧹 Cleaned markdown formatting")
                
                print(f"🎯 Final fixed content length: {len(fixed_content)}")
                print(f"🔍 Fixed content preview: {fixed_content[:200]}...")
                
                # Validate that content actually changed
                if fixed_content and fixed_content != content:
                    print("✅ Content was modified by LLM")
                    return fixed_content
                else:
                    print("ℹ️ LLM returned same content or empty response")
                    return None
            else:
                print("❌ No valid content in LLM response")
                return None
            
        except Exception as e:
            print(f"❌ LLM fix failed: {e}")
            import traceback
            traceback.print_exc()
            return None


@dataclass
class BuildResult:
    """Result of a build or run operation"""
    success: bool
    output: str
    error_output: str
    error_type: Optional[ErrorType] = None
    error_details: Optional[str] = None
    suggested_fixes: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.suggested_fixes is None:
            self.suggested_fixes = []


@dataclass
class SandboxConfig:
    """Configuration for E2B sandbox"""
    template: str = 'springboot-dev'
    timeout: int = 60
    max_retries: int = 10
    build_timeout: int = 300
    run_timeout: int = 30


class ErrorAnalyzer:
    """Analyzes build and runtime errors to provide intelligent fixes"""
    
    @staticmethod
    def analyze_error(output: str, error_output: str) -> Tuple[ErrorType, str, List[str]]:
        """Analyze error output and provide classification and suggestions"""
        
        combined_output = f"{output}\n{error_output}".lower()
        
        # Dependency errors
        if any(keyword in combined_output for keyword in [
            'could not resolve dependencies',
            'dependency not found',
            'package does not exist',
            'missing artifact',
            'cannot find symbol',
            'package does not exist'
        ]):
            return ErrorType.DEPENDENCY_ERROR, "Missing or incorrect dependencies", [
                "Add missing dependencies to pom.xml",
                "Check dependency versions and compatibility",
                "Verify repository configurations"
            ]
        
        # Bean/Spring configuration errors
        if any(keyword in combined_output for keyword in [
            'bean definition with name',
            'could not register bean definition',
            'unsatisfieddependencyexception',
            'beandefinitionoverride',
            'circular dependencies',
            'qualifier'
        ]):
            return ErrorType.CONFIGURATION_ERROR, "Spring Bean configuration issue", [
                "Check for duplicate bean names",
                "Verify component scanning packages",
                "Review dependency injection annotations",
                "Check for circular dependencies"
            ]
        
        # Compilation errors
        if any(keyword in combined_output for keyword in [
            'compilation failure',
            'cannot find symbol',
            'class not found',
            'method not found',
            'variable not found'
        ]):
            return ErrorType.COMPILATION_ERROR, "Java compilation error", [
                "Fix syntax errors",
                "Add missing imports",
                "Correct method signatures",
                "Fix variable declarations"
            ]
        
        # Runtime errors
        if any(keyword in combined_output for keyword in [
            'exception in thread',
            'nullpointerexception',
            'classnotfoundexception',
            'illegalargumentexception',
            'failed to start'
        ]):
            return ErrorType.RUNTIME_ERROR, "Runtime execution error", [
                "Check for null pointer issues",
                "Verify class path and imports",
                "Review application configuration",
                "Check database connections"
            ]
        
        # Network/connection errors
        if any(keyword in combined_output for keyword in [
            'connection refused',
            'timeout',
            'network error',
            'could not connect'
        ]):
            return ErrorType.NETWORK_ERROR, "Network or connection issue", [
                "Check network connectivity",
                "Verify service endpoints",
                "Review firewall settings"
            ]
        
        return ErrorType.UNKNOWN_ERROR, "Unknown error", ["Review logs for more details"]


class SpringBootSandboxExecutor:
    """Executes Spring Boot projects in E2B sandboxes with error handling and auto-fixing"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.sandbox = None
        self.analyzer = ErrorAnalyzer()
        self.auto_fixer = AutoFixer()  # Add auto-fixer instance
        
    def __enter__(self):
        """Context manager entry"""
        self.create_sandbox()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        
    def create_sandbox(self):
        """Create E2B sandbox with proper error handling"""
        try:
            print(f"🚀 Creating E2B sandbox with template: {self.config.template}")
            self.sandbox = Sandbox.create(template=self.config.template)
            # The sandbox object doesn't have an .id attribute in newer versions
            # But the creation was successful if no exception was thrown
            print("✅ Sandbox created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create sandbox: {e}")
            return False
            
    def cleanup(self):
        """Clean up sandbox resources"""
        if self.sandbox:
            try:
                self.sandbox.kill()
                print("🧹 Sandbox cleaned up")
            except Exception as e:
                print(f"⚠️ Error cleaning up sandbox: {e}")
                
    def upload_project(self, local_project_path: str, sandbox_path: str = '/app') -> bool:
        """Upload project files to sandbox"""
        if not self.sandbox:
            print("❌ No sandbox available")
            return False
            
        print(f"📁 Uploading project from {local_project_path} to {sandbox_path}")
        
        try:
            uploaded_count = 0
            skipped_count = 0
            
            for root, dirs, files in os.walk(local_project_path):
                # Skip common build/temp directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'target', 'node_modules', '.vscode']]
                
                rel_root = os.path.relpath(root, local_project_path)
                sandbox_dir = os.path.join(sandbox_path, rel_root).replace('\\', '/')
                
                try:
                    self.sandbox.files.make_dir(sandbox_dir)
                except Exception:
                    pass  # Directory might already exist
                    
                for file in files:
                    local_file = os.path.join(root, file)
                    try:
                        with open(local_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        sandbox_file = os.path.join(sandbox_dir, file).replace('\\', '/')
                        self.sandbox.files.write(sandbox_file, content)
                        uploaded_count += 1
                        if uploaded_count % 10 == 0:  # Progress indicator
                            print(f"   📄 Uploaded {uploaded_count} files...")
                    except UnicodeDecodeError:
                        skipped_count += 1
                        # Skip binary files silently
                    except Exception as e:
                        print(f"⚠️ Error uploading {local_file}: {e}")
                        
            print(f"✅ Upload complete: {uploaded_count} files uploaded, {skipped_count} binary files skipped")
            return True
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
            
    def execute_build(self) -> BuildResult:
        """Execute Maven build with comprehensive output capture"""
        if not self.sandbox:
            return BuildResult(False, "", "No sandbox available")
            
        print("🔨 Building Spring Boot project...")
        
        build_output = []
        error_output = []
        
        def on_stdout(data):
            build_output.append(data)
            print(f"BUILD: {data.strip()}")
            
        def on_stderr(data):
            error_output.append(data)
            print(f"ERROR: {data.strip()}")
            
        try:
            self.sandbox.commands.run(
                'cd /app && mvn clean package -DskipTests -X',
                timeout=self.config.build_timeout,
                on_stdout=on_stdout,
                on_stderr=on_stderr
            )
            
            output = ''.join(build_output)
            errors = ''.join(error_output)
            
            # Check if build was successful
            success = 'BUILD SUCCESS' in output or ('BUILD FAILURE' not in output and 'ERROR' not in output)
            
            if success:
                print("✅ Build successful")
                return BuildResult(True, output, errors)
            else:
                print("❌ Build failed")
                print("🔍 ANALYZING ERROR FOR AUTO-FIX:")
                print(f"   📄 Output length: {len(output)} chars")
                print(f"   ⚠️ Error length: {len(errors)} chars")
                error_type, error_details, suggested_fixes = self.analyzer.analyze_error(output, errors)
                print(f"   🎯 Detected error type: {error_type}")
                print(f"   📝 Error details: {error_details[:200]}...")
                print(f"   💡 Suggested fixes count: {len(suggested_fixes) if suggested_fixes else 0}")
                return BuildResult(False, output, errors, error_type, error_details, suggested_fixes)
                
        except Exception as e:
            print(f"❌ Build execution failed: {e}")
            return BuildResult(False, "", str(e), ErrorType.UNKNOWN_ERROR, str(e))
            
    def execute_run(self) -> BuildResult:
        """Execute Spring Boot application with startup detection and auto-detach"""
        if not self.sandbox:
            return BuildResult(False, "", "No sandbox available")
            
        print("🏃 Running Spring Boot application...")
        
        run_output = []
        error_output = []
        startup_detected = False
        detected_ports = []
        
        def on_stdout(data):
            nonlocal startup_detected, detected_ports
            run_output.append(data)
            line = data.strip()
            print(f"RUN: {line}")
            
            # Check for startup completion
            if self._is_application_ready(line):
                startup_detected = True
                print("🎉 Application startup detected!")
                
            # Extract port information
            port_match = re.search(r'Tomcat started on port[s]?\s*[:\(]?\s*(\d+)', line, re.IGNORECASE)
            if port_match:
                port = port_match.group(1)
                if port not in detected_ports:
                    detected_ports.append(port)
        
        def on_stderr(data):
            error_output.append(data)
            line = data.strip()
            print(f"ERROR: {line}")
            
        try:
            print("🏃 Running Spring Boot application...")
            print("📊 Starting application in background with smart monitoring...")
            
            # Start application in background with log redirection (like the reference code)
            print("🚀 Starting Spring Boot application in background...")
            start_result = self.sandbox.commands.run(
                'cd /app && (java -jar target/*.jar > spring.log 2>&1 &); sleep 2',
                timeout=10
            )
            
            if start_result.exit_code != 0:
                return BuildResult(
                    success=False,
                    output=''.join(run_output),
                    error_output=f"Failed to start application: {start_result.stderr}",
                    error_details="Application startup command failed"
                )
            
            print("✅ Application started in background")
            print("📋 Monitoring startup progress...")
            
            # Monitor startup by checking logs and testing connectivity (like the reference code)
            startup_detected = False
            critical_error = False
            detected_ports = ['8080']  # Default Spring Boot port
            max_wait_time = 60  # 60 seconds max
            check_interval = 2  # Check every 2 seconds
            startup_logs = []
            
            import time  # Make sure time is imported
            
            for i in range(0, max_wait_time, check_interval):
                time.sleep(check_interval)
                
                # Check application logs
                log_result = self.sandbox.commands.run(
                    'cd /app && tail -n 20 spring.log 2>/dev/null || echo "No logs yet"',
                    timeout=5
                )
                
                if log_result.stdout:
                    startup_logs.append(log_result.stdout)
                    on_stdout(log_result.stdout)
                    
                    # Check for critical startup errors first
                    if self._is_critical_error(log_result.stdout):
                        critical_error = True
                        print("❌ Critical startup error detected!")
                        break
                    
                    # Check if startup is complete using our existing detection method
                    if self._is_application_ready(log_result.stdout):
                        startup_detected = True
                        print("🎉 Application startup detected!")
                        break
                
                # Test connectivity as additional check (after 10 seconds)
                if i >= 10:  # Start testing after 10 seconds
                    test_result = self.sandbox.commands.run(
                        'curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/actuator/health 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000"',
                        timeout=5
                    )
                    
                    if test_result.stdout and test_result.stdout.strip() in ['200', '404']:
                        startup_detected = True
                        print("🌐 Application responding to HTTP requests!")
                        break
                
                print(f"⏱️  Waiting for startup... ({i+check_interval}s)")
            
            # Collect all logs for output
            all_logs = ''.join(startup_logs) if startup_logs else ''.join(run_output)
            
            # Check for critical errors first
            if critical_error:
                print("❌ Critical startup error detected - aborting")
                return BuildResult(
                    success=False,
                    output=all_logs,
                    error_output=''.join(error_output),
                    error_details="Critical startup error detected in application logs"
                )
            
            # Final validation
            if startup_detected:
                port_info = f" on port(s): {', '.join(detected_ports)}" if detected_ports else ""
                success_msg = f"🎉 Application started successfully{port_info}"
                print(success_msg)
                print("📋 Log stream detached - application is running in background")
                
                # Test a few endpoints to confirm functionality (like the reference code)
                print("🧪 Quick functionality test...")
                test_result = self.sandbox.commands.run(
                    'curl -s http://localhost:8080/ || echo "Endpoint test completed"',
                    timeout=5
                )
                print(f"📡 Test response: {test_result.stdout[:100]}...")
                
                return BuildResult(
                    success=True, 
                    output=all_logs, 
                    error_output=''.join(error_output),
                    error_details=f"Application running successfully{port_info}"
                )
            else:
                print("⏰ Startup timeout - checking application status...")
                # Get final logs
                final_logs = self.sandbox.commands.run(
                    'cd /app && tail -n 50 spring.log 2>/dev/null || echo "No logs available"',
                    timeout=5
                )
                
                # Fallback check - see if process is running
                process_check = self.sandbox.commands.run(
                    'cd /app && pgrep -f "java.*jar" && echo "Process running"',
                    timeout=5
                )
                
                if "Process running" in process_check.stdout:
                    print("✅ Application process is running (fallback success)")
                    return BuildResult(
                        success=True, 
                        output=final_logs.stdout if final_logs.stdout else all_logs,
                        error_output=''.join(error_output),
                        error_details="Application appears to be running (detected via process check)"
                    )
                else:
                    return BuildResult(
                        success=False,
                        output=final_logs.stdout if final_logs.stdout else all_logs,
                        error_output=''.join(error_output),
                        error_details="Application startup timeout - please check logs for errors"
                    )
                                
        except Exception as e:
            print(f"❌ Run execution failed: {e}")
            return BuildResult(False, "", str(e), ErrorType.UNKNOWN_ERROR, str(e))
            
    def _is_application_ready(self, log_line: str) -> bool:
        """Check if log line indicates application is ready"""
        ready_patterns = [
            r'Started.*Application.*in.*seconds',  # Main Spring Boot startup message
            r'ApplicationStartedEvent',             # Spring Boot event
            r'Spring Boot.*started',                # Alternative Spring Boot message
            r'Application startup complete'         # Custom startup message
        ]
        
        return any(re.search(pattern, log_line, re.IGNORECASE) for pattern in ready_patterns)
    
    def _is_critical_error(self, error_line: str) -> bool:
        """Check if error line indicates critical startup failure"""
        critical_patterns = [
            r'APPLICATION FAILED TO START',
            r'Port.*already in use',
            r'FATAL ERROR',
            r'OutOfMemoryError',
            r'ClassNotFoundException',
            r'No main class found'
        ]
        
        return any(re.search(pattern, error_line, re.IGNORECASE) for pattern in critical_patterns)
            
    def _attempt_auto_fix(self, error_details: str, project_path: str) -> bool:
        """
        Attempt to automatically fix compilation errors
        
        Args:
            error_details: Build error output
            project_path: Local project directory path
            
        Returns:
            True if fixes were applied, False otherwise
        """
        print("🔧 Starting auto-fix attempt...")
        print(f"📂 Project path: {project_path}")
        print(f"📋 Error details length: {len(error_details)} characters")
        
        try:
            # Read current project files
            print("📖 Reading project files...")
            project_files = self._read_project_files(project_path)
            print(f"📁 Found {len(project_files)} project files")
            
            # Get fixes from LLM
            print("🤖 Requesting fixes from LLM...")
            fixed_files = self.auto_fixer.fix_compilation_errors(error_details, project_files)
            print(f"🛠️ LLM provided {len(fixed_files)} file fixes")
            
            if not fixed_files:
                print("❌ No fixes provided by LLM")
                return False
                
            # Apply fixes to local files
            fixes_applied = 0
            for file_path, fixed_content in fixed_files.items():
                local_file_path = os.path.join(project_path, file_path)
                print(f"📝 Applying fix to {local_file_path}...")
                
                if os.path.exists(local_file_path):
                    try:
                        # Backup original file
                        backup_path = f"{local_file_path}.backup"
                        import shutil
                        shutil.copy2(local_file_path, backup_path)
                        print(f"💾 Backed up original to {backup_path}")
                        
                        # Write fixed content
                        with open(local_file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        print(f"✅ Applied fix to {file_path}")
                        fixes_applied += 1
                        
                        # Show diff preview
                        print(f"🔍 Fix preview for {file_path}:")
                        lines = fixed_content.split('\n')
                        preview_lines = lines[:10] if len(lines) > 10 else lines
                        for i, line in enumerate(preview_lines, 1):
                            print(f"   {i:2d}: {line}")
                        if len(lines) > 10:
                            print(f"   ... and {len(lines) - 10} more lines")
                            
                    except Exception as e:
                        print(f"❌ Failed to write fix to {file_path}: {e}")
                else:
                    print(f"⚠️ File not found for fixing: {local_file_path}")
                        
            print(f"📊 Applied {fixes_applied} fixes out of {len(fixed_files)} attempted")
            return fixes_applied > 0
            
        except Exception as e:
            print(f"❌ Auto-fix attempt failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _read_project_files(self, project_path: str) -> Dict[str, str]:
        """
        Read all Java files in the project
        
        Args:
            project_path: Local project directory path
            
        Returns:
            Dictionary of relative_path -> file_content
        """
        project_files = {}
        
        try:
            # Walk through src/main/java directory
            src_main_java = os.path.join(project_path, 'src', 'main', 'java')
            if os.path.exists(src_main_java):
                for root, dirs, files in os.walk(src_main_java):
                    for file in files:
                        if file.endswith('.java'):
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, project_path)
                            relative_path = relative_path.replace(os.sep, '/')  # Normalize path separators
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    project_files[relative_path] = f.read()
                            except UnicodeDecodeError:
                                print(f"⚠️ Skipped binary file: {relative_path}")
                                
        except Exception as e:
            print(f"❌ Error reading project files: {e}")
            
        return project_files
            
    def test_project(self, local_project_path: str) -> Dict[str, Any]:
        """Complete test workflow with error handling and retry logic"""
        results = {
            'success': False,
            'iterations': 0,
            'build_results': [],
            'run_results': [],
            'final_status': 'failed',
            'error_analysis': []
        }
        
        try:
            # Upload project
            if not self.upload_project(local_project_path):
                results['final_status'] = 'upload_failed'
                return results
                
            # Build and test with retry logic
            for iteration in range(1, self.config.max_retries + 1):
                print(f"\n🔄 Iteration {iteration}/{self.config.max_retries}")
                results['iterations'] = iteration
                
                # Build phase
                build_result = self.execute_build()
                results['build_results'].append(build_result)
                
                if build_result.success:
                    print(f"✅ Build successful on iteration {iteration}")
                    
                    # Run phase
                    run_result = self.execute_run()
                    results['run_results'].append(run_result)
                    
                    if run_result.success:
                        print(f"🎉 Application runs successfully on iteration {iteration}")
                        results['success'] = True
                        results['final_status'] = 'success'
                        return results
                    else:
                        print(f"❌ Run failed on iteration {iteration}")
                        
                        # Check if this is a critical error that should stop iterations
                        is_critical = run_result.error_details and any(
                            pattern in run_result.error_details.upper() 
                            for pattern in ['APPLICATION FAILED TO START', 'FATAL ERROR', 'OUTOFMEMORYERROR']
                        )
                        
                        if is_critical:
                            print("🚨 Critical startup error detected - stopping iterations")
                            results['final_status'] = 'critical_error'
                            results['error_analysis'].append({
                                'iteration': iteration,
                                'phase': 'run',
                                'error_type': run_result.error_type,
                                'error_details': run_result.error_details,
                                'suggested_fixes': run_result.suggested_fixes or []
                            })
                            return results
                        
                        if iteration < self.config.max_retries:
                            print("🔧 Analyzing errors for potential fixes...")
                            # Here we would apply fixes based on error analysis
                            # For now, we'll log the analysis
                            results['error_analysis'].append({
                                'iteration': iteration,
                                'phase': 'run',
                                'error_type': run_result.error_type,
                                'error_details': run_result.error_details,
                                'suggested_fixes': run_result.suggested_fixes
                            })
                else:
                    print(f"❌ Build failed on iteration {iteration}")
                    
                    # Check if this is a critical build error that should stop iterations
                    is_critical_build = build_result.error_details and any(
                        pattern in build_result.error_details.upper()
                        for pattern in ['COMPILATION ERROR', 'BUILD FAILURE', 'DEPENDENCY ERROR']
                    )
                    
                    if is_critical_build and iteration >= 2:  # Allow at least one retry for build errors
                        print("🚨 Critical build error detected - stopping iterations")
                        results['final_status'] = 'critical_build_error'
                        results['error_analysis'].append({
                            'iteration': iteration,
                            'phase': 'build',
                            'error_type': build_result.error_type,
                            'error_details': build_result.error_details,
                            'suggested_fixes': build_result.suggested_fixes or []
                        })
                        return results
                    
                    if iteration < self.config.max_retries:
                        print("🔧 Analyzing build errors for potential fixes...")
                        
                        # Store error analysis
                        results['error_analysis'].append({
                            'iteration': iteration,
                            'phase': 'build',
                            'error_type': build_result.error_type,
                            'error_details': build_result.error_details,
                            'suggested_fixes': build_result.suggested_fixes
                        })
                        
                        # Attempt auto-fix for compilation errors
                        print("🔍 AUTO-FIX CHECK:")
                        print(f"   Error type: {build_result.error_type}")
                        print(f"   Error details present: {bool(build_result.error_details)}")
                        print(f"   Is compilation error: {build_result.error_type == ErrorType.COMPILATION_ERROR}")
                        
                        if build_result.error_type == ErrorType.COMPILATION_ERROR and build_result.error_details:
                            print("🤖 Attempting auto-fix for compilation errors...")
                            if self._attempt_auto_fix(build_result.error_details, local_project_path):
                                print("✅ Auto-fix applied, re-uploading project...")
                                if not self.upload_project(local_project_path):
                                    print("❌ Failed to re-upload project after auto-fix")
                                else:
                                    print("📦 Project re-uploaded successfully")
                            else:
                                print("❌ Auto-fix failed or not applicable")
                        else:
                            print("🔧 Auto-fix not applicable - not a compilation error or no error details")
                        
                if iteration < self.config.max_retries:
                    print("⏳ Waiting before next attempt...")
                    time.sleep(2)
                    
            results['final_status'] = 'max_iterations_reached'
            return results
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            results['final_status'] = 'execution_error'
            results['error_details'] = str(e)
            return results


def test_springboot_with_e2b(project_path: str, config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
    """Main function to test Spring Boot projects with E2B sandbox"""
    
    config = config or SandboxConfig()
    
    print(f"🧪 Testing Spring Boot project: {project_path}")
    print(f"📋 Configuration: max_retries={config.max_retries}, timeout={config.timeout}")
    
    with SpringBootSandboxExecutor(config) as executor:
        return executor.test_project(project_path)


if __name__ == "__main__":
    # Test the sandbox executor
    project_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"
    
    # Configure for testing
    config = SandboxConfig(
        max_retries=3,
        timeout=60,
        build_timeout=300,
        run_timeout=30
    )
    
    results = test_springboot_with_e2b(project_path, config)
    
    print("\n" + "="*50)
    print("📊 FINAL RESULTS")
    print("="*50)
    print(f"Success: {results['success']}")
    print(f"Iterations: {results['iterations']}")
    print(f"Final Status: {results['final_status']}")
    
    if results.get('error_analysis'):
        print("\n🔍 Error Analysis:")
        for analysis in results['error_analysis']:
            print(f"  Iteration {analysis['iteration']} ({analysis['phase']}): {analysis['error_type'].value}")
            print(f"    Details: {analysis['error_details']}")
            print(f"    Suggested fixes: {', '.join(analysis['suggested_fixes'])}")