"""
PROGRESS TRACKER - Clear visualization of agent work
===================================================

Shows what files are created, modified, tests written, etc.
With visual checkmarks and status indicators.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status of a task"""
    PENDING = "⏳ Pending"
    IN_PROGRESS = "🔄 In Progress"
    COMPLETED = "✅ Completed"
    FAILED = "❌ Failed"
    SKIPPED = "⊘ Skipped"


@dataclass
class FileTask:
    """Represents a file that needs to be created/modified"""
    name: str
    filepath: str
    file_type: str  # "entity", "controller", "service", "dto", "test", etc.
    layer: str  # "model", "controller", "service", "repository", "dto", etc.
    status: TaskStatus = TaskStatus.PENDING
    lines_of_code: int = 0
    error_message: str = ""
    completed_at: Optional[datetime] = None
    
    def mark_completed(self, loc: int = 0):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.lines_of_code = loc
        self.completed_at = datetime.now()
    
    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error_message = error


@dataclass
class ThinkingStep:
    """Represents a thinking/reasoning step in agent process"""
    step_number: int
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    
    def mark_completed(self):
        """Mark step as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()


@dataclass
class WorkProgress:
    """Tracks overall progress of agent work"""
    feature_name: str
    feature_request: str
    framework: str
    
    files_to_create: List[FileTask] = field(default_factory=list)
    files_to_modify: List[FileTask] = field(default_factory=list)
    thinking_steps: List[ThinkingStep] = field(default_factory=list)
    tests_created: int = 0
    total_loc: int = 0
    
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def add_file_task(self, file_task: FileTask):
        """Add a file task to track"""
        self.files_to_create.append(file_task)
    
    def add_thinking_step(self, title: str, description: str):
        """Add a thinking step"""
        step_number = len(self.thinking_steps) + 1
        step = ThinkingStep(
            step_number=step_number,
            title=title,
            description=description
        )
        self.thinking_steps.append(step)
        return step
    
    def complete_thinking_step(self, step_number: int):
        """Mark a thinking step as completed"""
        if 0 < step_number <= len(self.thinking_steps):
            self.thinking_steps[step_number - 1].mark_completed()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        total_files = len(self.files_to_create)
        completed = sum(1 for f in self.files_to_create if f.status == TaskStatus.COMPLETED)
        failed = sum(1 for f in self.files_to_create if f.status == TaskStatus.FAILED)
        pending = total_files - completed - failed
        
        total_loc = sum(f.lines_of_code for f in self.files_to_create)
        
        return {
            "total_files": total_files,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "completion_percent": (completed / total_files * 100) if total_files > 0 else 0,
            "total_loc": total_loc,
            "tests_created": self.tests_created,
        }
    
    def display_progress(self):
        """Display progress in a nice format"""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("📊 PROGRESS TRACKER - Agent Work Summary")
        print("="*70)
        
        print(f"\n🎯 Feature: {self.feature_name}")
        # print(f"📝 Request: {self.feature_request[:70]}...")
        print(f"🔧 Framework: {self.framework}")
        
        # Display thinking steps
        if self.thinking_steps:
            print("\n💭 Thinking Process:")
            for step in self.thinking_steps:
                status_icon = step.status.value.split()[0]  # Get emoji
                print(f"   {status_icon} Step {step.step_number}: {step.title}")
                # Print description with indentation
                for line in step.description.split('\n'):
                    if line.strip():
                        print(f"      • {line.strip()}")
        
        # Progress bar
        total = summary['total_files']
        completed = summary['completed']
        percent = summary['completion_percent']
        bar_length = 50
        filled = int(bar_length * completed / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\n📈 Overall Progress: [{bar}] {percent:.1f}%")
        print(f"   ✅ Completed: {completed}/{total} files")
        print(f"   ⏳ Pending: {summary['pending']}/{total} files")
        if summary['failed'] > 0:
            print(f"   ❌ Failed: {summary['failed']}/{total} files")
        
        # Files breakdown
        print("\n📋 Files Created:")
        for file_task in self.files_to_create:
            status_icon = file_task.status.value.split()[0]  # Get emoji
            loc_info = f" ({file_task.lines_of_code} LOC)" if file_task.lines_of_code > 0 else ""
            print(f"   {status_icon} {file_task.name}{loc_info}")
            if file_task.error_message:
                print(f"      └─ Error: {file_task.error_message}")
        
        # Statistics
        print("\n📊 Statistics:")
        print(f"   • Total Lines of Code: {summary['total_loc']}")
        print(f"   • Tests Created: {summary['tests_created']}")
        print(f"   • Duration: {self._get_duration()}")
        
        print("\n" + "="*70)
    
    def _get_duration(self) -> str:
        """Get duration of work"""
        end = self.end_time or datetime.now()
        duration = (end - self.start_time).total_seconds()
        
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            return f"{duration/60:.1f}m"
        else:
            return f"{duration/3600:.1f}h"
    
    def display_finished_summary(self):
        """Display final summary when finished"""
        self.end_time = datetime.now()
        
        print("\n" + "="*70)
        print("🎉 FINISHED WORKING")
        print("="*70)
        
        summary = self.get_summary()
        
        # Completed tasks
        if summary['completed'] > 0:
            print(f"\n✅ Successfully Created: {summary['completed']} files")
            for file_task in self.files_to_create:
                if file_task.status == TaskStatus.COMPLETED:
                    print(f"   • {file_task.name} ({file_task.file_type} - {file_task.layer})")
        
        # Failed tasks
        if summary['failed'] > 0:
            print(f"\n❌ Failed: {summary['failed']} files")
            for file_task in self.files_to_create:
                if file_task.status == TaskStatus.FAILED:
                    print(f"   • {file_task.name}")
                    if file_task.error_message:
                        print(f"     └─ {file_task.error_message}")
        
        # Pending tasks
        if summary['pending'] > 0:
            print(f"\n⏳ Pending: {summary['pending']} files (timeout or incomplete)")
            for file_task in self.files_to_create:
                if file_task.status == TaskStatus.PENDING:
                    print(f"   • {file_task.name}")
        
        # Overall statistics
        print("\n📊 Final Statistics:")
        print(f"   Completion Rate: {summary['completion_percent']:.1f}%")
        print(f"   Total Lines Generated: {summary['total_loc']}")
        print(f"   Tests Created: {summary['tests_created']}")
        print(f"   Duration: {self._get_duration()}")
        
        print("\n" + "="*70)


# Example usage
if __name__ == "__main__":
    # Create progress tracker
    progress = WorkProgress(
        feature_name="Order Management System",
        feature_request="Add order management with order tracking and payment processing",
        framework="Spring Boot"
    )
    
    # Add files to create
    files_to_create = [
        FileTask(
            name="Order.java",
            filepath="src/main/java/com/example/springboot/model/Order.java",
            file_type="entity",
            layer="model"
        ),
        FileTask(
            name="OrderRepository.java",
            filepath="src/main/java/com/example/springboot/repository/OrderRepository.java",
            file_type="repository",
            layer="repository"
        ),
        FileTask(
            name="OrderService.java",
            filepath="src/main/java/com/example/springboot/service/OrderService.java",
            file_type="service",
            layer="service"
        ),
        FileTask(
            name="OrderController.java",
            filepath="src/main/java/com/example/springboot/controller/OrderController.java",
            file_type="controller",
            layer="controller"
        ),
        FileTask(
            name="OrderTest.java",
            filepath="src/test/java/com/example/springboot/OrderTest.java",
            file_type="test",
            layer="test"
        ),
    ]
    
    for file_task in files_to_create:
        progress.add_file_task(file_task)
    
    # Simulate progress
    print("Starting work...")
    progress.display_progress()
    
    import time
    
    # Simulate file creation
    progress.files_to_create[0].mark_completed(45)
    time.sleep(0.5)
    progress.display_progress()
    
    progress.files_to_create[1].mark_completed(52)
    time.sleep(0.5)
    progress.display_progress()
    
    progress.files_to_create[2].mark_completed(156)
    time.sleep(0.5)
    progress.display_progress()
    
    progress.files_to_create[3].mark_completed(89)
    time.sleep(0.5)
    progress.display_progress()
    
    progress.files_to_create[4].mark_completed(120)
    progress.tests_created = 1
    
    # Final summary
    progress.display_finished_summary()
