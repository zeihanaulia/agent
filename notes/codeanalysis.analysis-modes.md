# ⚡ Analysis Modes Guide

## Overview

The Deep Code Analysis Agent now supports **two analysis modes** to balance speed vs. depth:

| Mode | Time | Output | Best For |
|------|------|--------|----------|
| 🚀 **Fast (Summary)** | 30s - 1m | Brief summary | Quick overview, large codebases |
| 📊 **Detailed (Full)** | 1m - 3m+ | Comprehensive analysis | Deep understanding, architecture |

---

## 🚀 Fast Mode (Summary)

### What it does
- Quick overview without deep diving
- Scans main directory structure
- Reads key configuration files only (README, package.json, pom.xml, requirements.txt)
- Identifies 2-3 main source files and skims them
- Generates SHORT summary (max 500 words)

### Output includes
```
✓ Project name and purpose
✓ Technology stack
✓ Main components (3-5 bullets)
```

### Typical time
```
⏱️  30 seconds - 1 minute
```

### Best use cases
```
✅ First-time exploration
✅ Large codebases (>50MB)
✅ Quick status check
✅ Snapshot comparisons
✅ Multiple repos scanning
```

### Example prompt
```
Use ls to see main directory structure
Find and skim key files: README, package.json, pom.xml, requirements.txt, main.go
Identify 2-3 main source files and read them briefly
Provide SHORT summary:
  - Project name and purpose (1-2 lines)
  - Tech stack (1 line)
  - Main components (3-5 bullets)
```

---

## 📊 Detailed Mode (Full - Default)

### What it does
- Comprehensive codebase analysis
- Full directory exploration
- Reads all key configuration files
- Deep analysis of multiple source files
- Examines architecture and design patterns
- Detailed component breakdown

### Output includes
```
✓ Project purpose and goals
✓ Technology stack and dependencies
✓ Architecture and layers
✓ Main components with descriptions
✓ Key functionalities
✓ Code relationships and data flow
```

### Typical time
```
⏱️  1-3 minutes (or more for large repos)
```

### Best use cases
```
✅ Onboarding to new codebase
✅ Code review preparation
✅ Architecture documentation
✅ Integration planning
✅ Comprehensive understanding needed
```

### Example prompt
```
1. Gather Context: Use ls and glob to explore directory structure
2. Identify Project Purpose: Read README, package.json, pom.xml, requirements.txt
3. Analyze Code Content: Read key source files
4. Examine Architecture: Map project structure
5. Summarize: Provide comprehensive overview with:
   - Project purpose and goals
   - Technology stack and dependencies
   - Architecture and main components
   - Key functionalities
```

---

## 🎯 How to Choose

### Use **Fast Mode** if:
```
⏱️  You have < 2 minutes
🏃 You want quick overview first
📁 Codebase is > 50MB
🔄 Analyzing multiple repos
📊 Just need summary stats
```

### Use **Detailed Mode** if:
```
⏰ You have 3+ minutes to spare
🔍 You need deep understanding
📚 Learning the codebase
🏗️  Planning architecture changes
📖 Writing documentation
```

---

## 💡 Pro Tips

### Tip 1: Start with Fast Mode
```
1. Run Fast Mode first (1 min)
2. Review summary
3. Then run Detailed Mode if needed (2-3 min)

Total: Flexible, can skip if summary is enough
```

### Tip 2: Fast Mode for New Repos
```
Fast Mode helps decide if you want to analyze further
Good for evaluating multiple repositories quickly
```

### Tip 3: Detailed Mode for Important Repos
```
Use when you need to really understand the system
Worth the extra 1-2 minutes for complex projects
```

### Tip 4: Monitor Progress
```
UI shows live progress updates:
  20% - Configuring AI model
  30% - Creating agent
  50% - Running analysis
  80% - Extracting results
  100% - Complete!
```

---

## ⏱️ Performance Characteristics

### Fast Mode Processing Flow
```
📋 Parse config files         → 5-10 sec
📂 Scan directories           → 5-10 sec
👀 Skim source files          → 10-20 sec
🤔 Generate summary           → 5-10 sec
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💨 TOTAL: 30-50 seconds
```

### Detailed Mode Processing Flow
```
📋 Parse all config files     → 10-15 sec
📂 Full directory exploration → 10-20 sec
📖 Deep read source files     → 20-40 sec
🏗️  Analyze architecture      → 15-30 sec
💭 Generate full report       → 15-30 sec
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TOTAL: 1-2+ minutes
```

---

## 🔧 Technical Details

### Fast Mode Prompt
```python
# Focuses agent on quick key-finding
# Uses fewer tool calls
# Limits exploration depth
# Targets main files only
```

### Detailed Mode Prompt
```python
# Encourages comprehensive exploration
# More tool calls allowed
# Deeper file analysis
# Architecture-focused
```

### Network Usage
```
Fast Mode:     ~2-3 API calls
Detailed Mode: ~8-15 API calls
```

### Token Usage (approx)
```
Fast Mode:     3,000-5,000 tokens
Detailed Mode: 10,000-20,000 tokens
```

---

## 🚨 Troubleshooting

### Q: Analysis taking > 3 minutes (Detailed Mode)?
```
A: Try Fast Mode instead - should complete in 1 minute
   Or check your network connection
   Or try a different codebase (might be very large)
```

### Q: Fast Mode output too brief?
```
A: That's expected - it's designed for summaries only
   Use Detailed Mode for full analysis
   Fast Mode is meant to be ~500 words max
```

### Q: Getting timeout error?
```
A: Codebase might be too large for Detailed Mode
   Try Fast Mode first
   Consider analyzing specific subdirectories
```

### Q: How do I switch modes mid-analysis?
```
A: 1. Select different mode from radio buttons
   2. Click Run Analysis again
   3. Previous result is replaced
```

---

## 📊 Example Outputs

### Fast Mode Output (springboot-demo)
```
**ANALYSIS SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: springboot-demo
Purpose: Minimal Spring Boot example demonstrating REST controller

Tech Stack: Java, Spring Boot, Maven
- Framework: Spring Boot 3.4.0 (starter-parent)
- Build: Maven (pom.xml)
- Main: src/main/java/com/example/springboot/
  
Main Components:
• Application.java - Spring Boot entry point
• HelloController.java - REST endpoints (/hello, /)
• Compiled: target/classes/com/example/springboot/

Time: 45 seconds
API Calls: 3
```

### Detailed Mode Output (springboot-demo)
```
**ANALYSIS SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**DETAILED ANALYSIS**

Project: springboot-demo
Purpose: A minimal Spring Boot example application demonstrating a basic REST 
controller and Application class that lists Spring beans on startup.

Architecture:
- Layer: Presentation (REST controller)
- Technology: Spring Boot REST
- Files: Application.java, HelloController.java, application.properties

Key Components:
1. Application.java
   - Entry point for Spring Boot
   - Runs on startup: prints Spring beans to console
   - Startup banner configuration

2. HelloController.java  
   - REST controller exposing endpoints
   - GET /hello - returns greeting message
   - GET / - returns "Hello World"

Technology Stack:
- Java 17+ (required by Spring Boot 3.4.0)
- Spring Boot 3.4.0 (starter-parent)
- Spring Boot Web Starter (spring-boot-starter-web)
- Spring Boot Test Starter (spring-boot-starter-test, optional scope)
- Maven as build tool (pom.xml)
- Log4j2 via Spring Boot logging

Repository Layout:
- pom.xml - Maven dependencies and build configuration
- src/main/java/com/example/springboot/
  - Application.java (main class)
  - HelloController.java (REST controller)
- target/classes/ - Compiled bytecode after build
- README.md - Documentation (if present)

Functionality:
1. Startup: Initializes Spring Boot application context, prints Spring beans
2. REST API: Listens on default port 8080
3. Endpoints: /hello and / return simple text responses
4. Testing: Spring Boot Test framework available

Time: 2 minutes 15 seconds
API Calls: 12
Tool Calls: 15
```

---

## 🎓 Learning Path

### Beginner
```
1. Try Fast Mode on springboot-demo (should be instant)
2. Review the brief output
3. Then try Detailed Mode to see full analysis
4. Compare the two outputs
```

### Intermediate
```
1. Use Fast Mode to quickly evaluate repositories
2. Use Detailed Mode only for ones you'll work with
3. Mix and match based on project size
```

### Advanced
```
1. Use Fast Mode for initial assessment
2. Run Detailed Mode on specific subdirectories
3. Combine multiple analyses for system understanding
4. Save outputs for comparison over time
```

---

## ✅ Summary

**Two modes, two use cases:**

| Need | Mode | Time |
|------|------|------|
| Quick overview | 🚀 Fast | 30-50 sec |
| Deep dive | 📊 Detailed | 1-3 min |

**Choose based on:**
- ⏱️  Available time
- 📚 Depth needed
- 📁 Codebase size
- 🎯 Your goal

**Always remember:**
- Start with summary when unsure
- Fast Mode helps decide if deeper analysis needed
- Detailed Mode worth the wait for complex projects

---

**Version**: 1.0  
**Date**: November 3, 2025  
**Status**: ✅ Live in Gradio app
