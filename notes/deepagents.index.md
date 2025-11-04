# Deep Agents Documentation Index

## 📋 Overview
Dokumentasi lengkap untuk Deep Agents architecture - framework agent AI yang menangani tugas kompleks dengan planning, sub-agents, filesystem access, dan detailed prompting.

## 🎯 Learning Path

### Level 1: Introduction (30 min)
1. **[Deep Agents Notes](deepagents.deep_agents_notes.md)** - Pengenalan arsitektur Deep Agents dan komponen utama

### Level 2: Components (45 min)
1. **[Deep Agents Notes](deepagents.deep_agents_notes.md)** - Planning tools, sub-agent spawning, filesystem middleware

### Level 3: Implementation (60 min)
1. **[Deep Agents Notes](deepagents.deep_agents_notes.md)** - Detailed prompting patterns dan use cases

### Level 4: Advanced Patterns (90 min)
1. **[Deep Agents Notes](deepagents.deep_agents_notes.md)** - Complex agent architectures dan scaling patterns

## 📁 File Structure

### Core Documentation
- `deepagents.deep_agents_notes.md` - Comprehensive guide to Deep Agents architecture

## 🚀 Quick Start

### Basic Deep Agent
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    system_prompt="You are a helpful AI assistant",
    model="gpt-4",
    backend=filesystem_backend  # Optional
)

result = agent.invoke("Analyze this codebase")
```

### With Planning
```python
# Agent with planning capabilities
agent = create_deep_agent(
    system_prompt="""You are a planning agent.
    Always break down complex tasks into steps.""",
    model="gpt-4",
    planning=True
)
```

### Sub-Agent Spawning
```python
# Agent that can spawn sub-agents
agent = create_deep_agent(
    system_prompt="""You are a coordinator agent.
    Spawn sub-agents for specialized tasks.""",
    model="gpt-4",
    allow_sub_agents=True
)
```

## 🔧 Key Components

### Core Components
- **Planning Tool** - Kemampuan merencanakan tugas kompleks
- **Sub Agents** - Spawning agent khusus untuk isolasi konteks
- **File System Access** - Mengelola konteks panjang via filesystem
- **Detailed Prompting** - Instruksi komprehensif untuk behavior agent

### Architecture Pattern
```
┌─────────────────┐
│   Main Agent    │
│                 │
│  ┌────────────┐ │
│  │ Planning   │ │
│  │ Tool       │ │
│  └────────────┘ │
│                 │
│  ┌────────────┐ │
│  │ Sub Agent  │ │
│  │ Spawning   │ │
│  └────────────┘ │
│                 │
│  ┌────────────┐ │
│  │ File System│ │
│  │ Tools      │ │
│  └────────────┘ │
└─────────────────┘
```

### Use Cases
- **Code Analysis** - Menganalisis struktur dan isi codebase
- **Feature Implementation** - Implementasi fitur kompleks dengan planning
- **Multi-step Tasks** - Tugas yang memerlukan beberapa langkah
- **Context Management** - Mengelola konteks panjang via filesystem

## 📊 Comparison with Simple Agents

| Aspect | Simple Agent | Deep Agent |
|--------|--------------|------------|
| **Task Complexity** | Single step | Multi-step planning |
| **Context Management** | Limited | Filesystem-based |
| **Sub-tasks** | Manual | Automatic spawning |
| **Error Recovery** | Basic | Sophisticated |
| **Scalability** | Limited | High |

## 📚 References

- **DeepAgents Documentation**: https://docs.langchain.com/oss/python/deepagents/overview
- **Planning Patterns**: https://docs.langchain.com/oss/python/deepagents/planning
- **Sub-Agent Guide**: https://docs.langchain.com/oss/python/deepagents/sub-agents

## 🎯 Next Steps

1. **Start Learning**: Read `deepagents.deep_agents_notes.md`
2. **Try Basic Agent**: Create simple deep agent
3. **Explore Planning**: Implement planning patterns
4. **Build Complex Systems**: Combine with filesystem backends

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Documentation Organized  
**Learning Path**: 4 levels, ~3 hours total