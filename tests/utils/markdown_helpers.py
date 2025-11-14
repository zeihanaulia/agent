from typing import Dict


def extract_markdown_sections(content: str) -> Dict[str, str]:
    """Extract markdown sections keyed by their headings."""
    sections: Dict[str, str] = {}
    lines = content.split('\n')
    current_section: str | None = None
    current_content: list[str] = []

    for line in lines:
        if line.startswith('## '):
            if current_section:
                sections[current_section.lower()] = '\n'.join(current_content).strip()

            current_section = line.strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section.lower()] = '\n'.join(current_content).strip()

    return sections
