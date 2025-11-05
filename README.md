
# AI Agent Research & Development

Educational repository demonstrating chronological progression from basic ML to production AI agents. Learn through hands-on implementation across 5 development phases.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd agent
pip install -r requirements.txt

# Run basic ML demo
python gradio/gradio_image_classification.py
```

## 📚 Complete Documentation

### Learning Path
- **[📚 Complete Learning Path](notes/learning-path.md)** - Detailed 5-phase educational progression with hands-on projects
- **[🛠️ Advanced Setup Guide](notes/advanced-setup.md)** - Complete setup instructions for each development phase
- **[🔧 Technical Stack Evolution](notes/technical-stack-evolution.md)** - Evolution of technologies and patterns across phases

### Phase Documentation
- **[Phase 2: Code Analysis](notes/codeanalysis.index.md)** - DeepAgents + FilesystemBackend implementation
- **[Phase 2: Deep Agents](notes/deepagents.index.md)** - Agent architecture patterns and planning
- **[Phase 3: E2B Sandbox](notes/e2b.index.md)** - Secure code execution and streaming
- **[Phase 4: Feature Request Agent](notes/featurerequestagent.index.md)** - Multi-phase agent with middleware
- **[Phase 5: Project Completion](notes/project.completion-summary.md)** - Production Spring Boot generation

### Roadmap & Planning
- **[🚀 Technical Roadmap](notes/roadmap.md)** - Detailed development roadmap with implementation plans

## 🏗️ Project Structure

```
├── notebooks/          # Jupyter notebooks (educational progression)
├── gradio/            # Interactive web demos (by phase)
├── scripts/           # CLI tools & agents (evolution of capabilities)
├── dataset/           # Sample data & codebases
├── notes/             # Documentation (chronological by development phase)
│   ├── learning-path.md           # 📚 Complete learning guide
│   ├── advanced-setup.md          # 🛠️ Detailed setup instructions
│   ├── technical-stack-evolution.md # 🔧 Technology evolution
│   ├── roadmap.md                 # 🚀 Development roadmap
│   ├── codeanalysis.*             # Phase 2: Agent fundamentals
│   ├── deepagents.*               # Phase 2: Architecture patterns
│   ├── e2b.*                     # Phase 3: Sandbox execution
│   ├── featurerequest.*          # Phase 4: Feature implementation
│   ├── project.*                 # Phase 5: Production completion
│   └── testing.*                 # Phase 5: Validation results
└── requirements.txt   # Python dependencies (evolving)
```

## 🎯 Current Focus

**"Generate → Build → Test → Repair" automated pipeline:**

- ✅ **Generate**: Feature request → code implementation (Phase 4-5 agents)
- 🚧 **Build**: Persistent sandbox dengan Maven cache (`~/.m2`)
- 🚧 **Test**: Automated testing dalam sandbox environment
- 🚧 **Repair**: Error parsing → agent-driven fixes

## Token Optimization Implementation (Tomorrow)

**Goal: Reduce token usage by 56% for large project scalability**

### Phase 1: Quick Wins (1 week, -38% tokens)
- [ ] Implement context pruning in phase transitions
  - Remove duplicate context_analysis data passed to each phase
  - Add context deduplication before phase execution
- [ ] Add caching for repeated context retrieval
  - Cache file contents and analysis results
  - Implement LRU cache with configurable size limits
- [ ] Test with existing Test 3 scenario
  - Validate 30-40% token reduction achieved
  - Ensure no regression in feature functionality

### Phase 2: Enhanced Filtering (1 week, -18% additional tokens)
- [ ] Implement semantic file filtering
  - Analyze only relevant files based on feature request context
  - Skip unrelated files (tests, docs, config) unless specifically requested
- [ ] Add selective analysis for large codebases
  - Focus analysis on modified/changed files
  - Implement dependency-aware filtering
- [ ] Validate with large project simulation
  - Test with Casdoor-like codebase (300+ files)
  - Confirm token usage stays under 500K threshold

### Phase 3: Advanced Optimizations (2 weeks, -15% additional tokens)
- [ ] Implement RAG backend for context retrieval
  - Replace full context passing with semantic retrieval
  - Use vector embeddings for relevant code chunk retrieval
- [ ] Add message compression strategies
  - Compress repeated patterns in context
  - Implement hierarchical context summarization
- [ ] Final validation and benchmarking
  - Re-run all Test 1-3 scenarios
  - Document final token usage metrics

**Success Criteria:**
- 56% total token reduction achieved
- Large projects (300+ files) remain under 500K tokens
- No regression in agent functionality
- All E2B tests continue to pass

## Contributing

Repository ini educational - contributions untuk:
- New experiment notebooks (following phase progression)
- Documentation improvements dengan chronological context
- Bug fixes dan enhancements
- Additional model integrations
- Framework extensions

## License

Consider adding LICENSE and CONTRIBUTING.md for public sharing.
