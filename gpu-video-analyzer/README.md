GPULessonExtractor

A specialized tool for extracting educational content and technical knowledge from George Hotz's GPU-related YouTube videos. This tool helps you build a learning resource by identifying, cataloging, and extracting technical information about graphics cards, GPU architecture, and programming techniques.

## Features

- 🎯 Automatically detects GPU-related content in YouTube videos
- 🔍 Uses both keyword matching and machine learning classification
- 📝 Extracts video transcripts to capture technical explanations and code discussions
- 💾 Organizes content into structured learning materials for later reference
- 📊 Identifies technical terms, code snippets, and explanations for study purposes
- 📚 Creates a searchable knowledge base of GPU programming concepts

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/GPULessonExtractor.git
cd GPULessonExtractor

# Install dependencies
pip install -r requirements.txt

# Optional: Install accelerate for improved ML classification
pip install accelerate
```

## Usage

```bash
# Run the main script to extract GPU videos and their content
python src/main.py

# Create study notes from extracted content
python src/create_study_notes.py

# Search for specific GPU concepts in the extracted materials
python src/search_concepts.py "shader programming"
```

## Learning Resources Generated

After processing videos, this tool will create:

- Technical term glossary from GPU discussions
- Code snippet collections from programming segments
- Timestamped explanations of important concepts
- References to external resources mentioned in videos

This repository helps you transform casual YouTube videos into structured educational content that you can revisit and study at your own pace.