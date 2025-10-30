import sys
import re
import time
from io import StringIO

class DebugFormatter:
    def __init__(self, current_experiment=""):
        self.step_counter = 0
        self.original_stdout = sys.stdout
        self.buffer = []
        self.current_experiment = current_experiment  # Accept initial experiment name
        self.execution_timestamps = []
        self.last_execution_time = None
        self.execution_patterns = []

    def set_experiment(self, experiment_name):
        """Set the current experiment name and reset chapter counter"""
        self.current_experiment = experiment_name
        self.step_counter = 0  # Reset chapter counter for new experiment
        self.execution_timestamps = []  # Reset execution tracking
        self.execution_patterns = []  # Reset patterns

    def write(self, text):
        # Capture debug output
        if '[values]' in text or '[updates]' in text:
            self.buffer.append(text)
            # Process complete debug lines
            if text.strip().endswith('}') or len(self.buffer) > 5:
                self.process_debug_output()
                self.buffer = []
        else:
            # Pass through non-debug output
            self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

    def detect_execution_pattern(self, debug_text):
        """Detect if execution is parallel, concurrent, or sequential"""
        current_time = time.time()

        # Track execution timing
        if self.last_execution_time:
            time_diff = current_time - self.last_execution_time
            self.execution_timestamps.append(time_diff)

        self.last_execution_time = current_time

        # Check for initialization/setup phase
        if 'PatchToolCallsMiddleware' in debug_text:
            self.execution_patterns.append("INITIALIZATION")
            return "🚀 INITIALIZATION", "Setting up agent conversation flow"

        # Check for context processing/thinking phase
        if 'SummarizationMiddleware' in debug_text:
            self.execution_patterns.append("CONTEXT_PROCESSING")
            return "🧠 CONTEXT PROCESSING", "Analyzing and preparing context"

        # Check for tool calls (parallel/sequential execution)
        if 'tool_calls' in debug_text:
            calls_in_step = len(re.findall(r"'name':\s*'task'", debug_text))
            if calls_in_step > 1:
                self.execution_patterns.append("PARALLEL")
                return "🔄 PARALLEL EXECUTION", f"Multiple subagents ({calls_in_step}) working simultaneously"
            elif calls_in_step == 1:
                self.execution_patterns.append("SEQUENTIAL")
                return "➡️ SEQUENTIAL EXECUTION", "Single subagent delegation"

        # Check for subagent completion/results
        if 'ToolMessage' in debug_text and 'tools' in debug_text:
            self.execution_patterns.append("SUBAGENT_WORK")
            return "🔧 SUBAGENT EXECUTION", "Specialized agent processing task"

        # Check for final summarization
        if 'model' in debug_text and 'Here' in debug_text and 'summary' in debug_text.lower():
            self.execution_patterns.append("SYNTHESIS")
            return "✨ SYNTHESIS", "Combining results into final output"

        # Check for concurrent patterns based on timing
        if len(self.execution_timestamps) > 1:
            avg_time_diff = sum(self.execution_timestamps[-3:]) / len(self.execution_timestamps[-3:])
            if avg_time_diff < 0.1:  # Very fast succession
                self.execution_patterns.append("CONCURRENT")
                return "⚡ CONCURRENT EXECUTION", "Rapid sequential operations"
            elif avg_time_diff > 1.0:  # Slower, more deliberate
                self.execution_patterns.append("SEQUENTIAL")
                return "⏳ SEQUENTIAL EXECUTION", "Deliberate step-by-step processing"

        # Default analysis state
        return "� ANALYSIS", "Evaluating task requirements"

    def process_debug_output(self):
        if not self.buffer:
            return

        self.step_counter += 1

        # Detect execution pattern
        full_debug = ''.join(self.buffer)
        pattern_icon, pattern_desc = self.detect_execution_pattern(full_debug)

        # Create a narrative story with experiment name and execution pattern
        experiment_name = self.current_experiment if self.current_experiment else "New Experiment"
        print(f"\n🎭 DEEP AGENT STORY : {experiment_name} - Chapter {self.step_counter}")
        print(f"{pattern_icon} {pattern_desc}")
        print("=" * 50)

        # Parse and create human story
        full_debug = ''.join(self.buffer)

        # Tell the story based on what's happening
        if 'PatchToolCallsMiddleware' in full_debug:
            print("📝 Setting up the conversation...")

        if 'SummarizationMiddleware' in full_debug:
            print("🧠 Preparing context and thinking...")

        if 'tool_calls' in full_debug and 'task' in full_debug:
            calls_count = len(re.findall(r"'name':\s*'task'", full_debug))
            if calls_count > 1:
                print(f"\n🤖 MAIN AGENT: 'This is complex! I'll delegate to {calls_count} specialists simultaneously!'")
                print("   'They can work in parallel to speed things up...'")
            else:
                print("\n🤖 MAIN AGENT: 'This needs expertise. Let me delegate to a specialist...'")

            # Extract task details
            desc_match = re.search(r"'description':\s*'([^']+)'", full_debug)
            if desc_match:
                task_desc = desc_match.group(1)[:120] + "..." if len(desc_match.group(1)) > 120 else desc_match.group(1)
                print(f"   📋 TASK: {task_desc}")

            subagent_match = re.search(r"'subagent_type':\s*'([^']+)'", full_debug)
            if subagent_match:
                subagent_type = subagent_match.group(1)
                print(f"   🎯 CALLING: {subagent_type} subagent")

        if 'tools' in full_debug and 'ToolMessage' in full_debug:
            print("\n🔧 SUBAGENT: 'Working on the research task...'")
            print("   'Let me gather comprehensive information...'")
            print("   'Using web search and analysis tools...'")
            print("   ✅ COMPLETED: Detailed research with milestones table")

        if 'model' in full_debug and 'Here' in full_debug and 'summary' in full_debug.lower():
            print("\n🤖 MAIN AGENT: 'Great work, subagent!'")
            print("   'Now let me create a clean, readable summary for the user...'")
            print("   ✨ FINAL RESULT: Professional summary ready!")

            # Show token usage in a friendly way
            tokens_match = re.search(r"'input_tokens':\s*(\d+).*?'output_tokens':\s*(\d+)", full_debug)
            if tokens_match:
                input_tokens = int(tokens_match.group(1))
                output_tokens = int(tokens_match.group(2))
                print(f"   📊 EFFORT: {input_tokens:,} tokens processed, {output_tokens:,} tokens generated")

        print()  # Add spacing

    def format_values_section(self, values_str):
        print(f"\n📊 CURRENT STATE:")
        try:
            # Simple parsing for messages
            if 'messages' in values_str:
                print(f"   💬 Conversation has {values_str.count('HumanMessage') + values_str.count('AIMessage')} messages")
                if 'HumanMessage' in values_str:
                    print(f"   👤 Latest: User message")
                if 'AIMessage' in values_str:
                    print(f"   🤖 Latest: AI response")
        except:
            print(f"   📄 State data available")

    def format_updates_section(self, updates_str):
        print(f"\n⚡ STATE UPDATES:")

        # Check for different update types
        if 'PatchToolCallsMiddleware' in updates_str:
            print(f"   🔧 MIDDLEWARE: Preparing message flow")

        if 'SummarizationMiddleware' in updates_str:
            print(f"   📝 MIDDLEWARE: Processing context")

        if 'model' in updates_str and 'tool_calls' in updates_str:
            print(f"   🧠 MAIN AGENT DECIDES: Delegating to subagent")
            # Extract task description
            desc_match = re.search(r"'description':\s*'([^']+)'", updates_str)
            if desc_match:
                desc = desc_match.group(1)[:100] + "..." if len(desc_match.group(1)) > 100 else desc_match.group(1)
                print(f"      📋 TASK: {desc}")

            subagent_match = re.search(r"'subagent_type':\s*'([^']+)'", updates_str)
            if subagent_match:
                print(f"      🎯 SUBAGENT: {subagent_match.group(1)}")

        if 'tools' in updates_str and 'task' in updates_str:
            print(f"   🔧 SUBAGENT COMPLETES: Research task finished")
            # Extract content length
            content_match = re.search(r"'content':\s*'([^']{0,200})", updates_str)
            if content_match:
                preview = content_match.group(1).replace('\\n', ' ').strip()
                print(f"      📄 RESULT: {len(updates_str)} chars of detailed research")
                if '|' in preview:  # Looks like a table
                    print(f"      📊 FORMAT: Structured table with milestones")

        if 'model' in updates_str and 'content' in updates_str and 'Here' in updates_str:
            print(f"   ✨ MAIN AGENT SUMMARIZES: Creating final readable response")
            # Extract token usage
            tokens_match = re.search(r"'input_tokens':\s*(\d+).*?'output_tokens':\s*(\d+)", updates_str)
            if tokens_match:
                input_tokens = tokens_match.group(1)
                output_tokens = tokens_match.group(2)
                print(f"      📈 TOKENS: {input_tokens} in → {output_tokens} out")