# Deep Agents: Introduction & Learning Notes

## Apa itu Deep Agents?

Deep Agents adalah arsitektur agent AI yang dirancang untuk menangani tugas-tugas kompleks dan multi-step dengan lebih efektif daripada agent tradisional. Berbeda dengan agent sederhana yang hanya memanggil tools dalam loop, deep agents mengimplementasikan kombinasi empat komponen kunci:

1. **Planning Tool** - Kemampuan untuk merencanakan dan mengelola tugas kompleks
2. **Sub Agents** - Spawning agent khusus untuk isolasi konteks
3. **File System Access** - Mengelola konteks panjang dan memori
4. **Detailed Prompting** - Instruksi yang komprehensif untuk behavior agent

## Arsitektur Deep Agents

### Core Components

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

...(content truncated, identical to original)
