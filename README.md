# Coaching Transcript Tool

A tool for converting coaching transcripts from VTT to Markdown or Excel.

## Installation

### Option 1: Install from PyPI (Not yet available)

```bash
pip install coaching-transcript-tool
```

### Option 2: Install from Source

Clone the repository and install:

```bash
git clone https://github.com/howie/coaching_transcript_tool.git
cd coaching_transcript_tool
pip install -e .
```

### Option 3: Install from Distribution Package

Build and install the package:

```bash
# Build the package
make dist

# Install the package
make dist-install
# OR
pip install dist/coaching_transcript_tool-0.1.0-py3-none-any.whl
```

### Option 4: Use Docker

Build and run using Docker:

```bash
# Build the Docker image
make docker

# Run the Docker container
docker run -v $(pwd):/data coaching_transcript_tool:latest -m src.vtt --help
```

## Usage

### Command Line Usage

After installation, you can use the tool in several ways:

#### 1. Using the Entry Point (After pip install)

```bash
vtt-convert input.vtt output.xlsx -Coach "Coach Name" -Client "Client Name"
```

#### 2. As a Python Module

```bash
python -m src.vtt input.vtt output.xlsx -Coach "Coach Name" -Client "Client Name"
```

#### 3. Using Docker

```bash
docker run -v $(pwd):/data coaching_transcript_tool:latest -m src.vtt /data/input.vtt /data/output.xlsx -Coach "Coach Name" -Client "Client Name"
```

### Command Line Options

```
usage: vtt.py [-h] [-Coach COACH] [-Client CLIENT] [-color COLOR] [-font_size FONT_SIZE] [-content_width CONTENT_WIDTH]
              input_file output_file

positional arguments:
  input_file            Input VTT file
  output_file           Output file (use .md for Markdown or .xlsx for Excel)

options:
  -h, --help            show this help message and exit
  -Coach COACH          Name of the coach
  -Client CLIENT        Name of the client
  -color COLOR          Hex color code for highlighting coach rows (default: D8E4F0 light blue)
  -font_size FONT_SIZE  Font size for Excel output (default: 16)
  -content_width CONTENT_WIDTH
                        Width of content column in characters (default: 160 for Excel, 80 for Markdown)
```

### Examples

#### Convert VTT to Excel with default settings

```bash
vtt-convert input.vtt output.xlsx -Coach "Howie Yu" -Client "CaRy"
```

#### Convert VTT to Excel with custom formatting

```bash
vtt-convert input.vtt output.xlsx -Coach "Howie Yu" -Client "CaRy" -color "FFD700" -font_size 14 -content_width 70
```

#### Convert VTT to Markdown

```bash
vtt-convert input.vtt output.md -Coach "Howie Yu" -Client "CaRy" -content_width 60
```

### Python API Usage

You can also use the tool as a Python library:

```python
from src import vtt

# Parse VTT file
data = vtt.parse_vtt('input.vtt')
consolidated_data = vtt.consolidate_speakers(data)

# Replace names with roles
consolidated_data = vtt.replace_names(consolidated_data, 'Coach Name', 'Client Name')

# Generate Excel output
vtt.generate_excel(
    consolidated_data, 
    'output.xlsx', 
    coach_color='D8E4F0',  # Light blue color for coach rows
    font_size=16, 
    content_width=160
)

# OR generate Markdown output
markdown = vtt.generate_markdown(consolidated_data, content_width=80)
with open('output.md', 'w', encoding='utf-8') as f:
    f.write(markdown)
```

## Development

Setup development environment:
```bash
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
```

Run tests:
```bash
pytest
```

## Building and Packaging

The project includes a Makefile with various targets for building, testing, and packaging.

### Using the Makefile

```bash
# Show all available commands
make help

# Build the package
make build

# Install locally in development mode
make install

# Run tests
make test

# Create distribution package
make dist

# Build Docker image
make docker

# Run Docker container (shows help)
make docker-run
```

### Docker Usage

After building the Docker image, you can run the VTT conversion tool with:

```bash
# Convert VTT to Excel
docker run -v /path/to/local/data:/data coaching_transcript_tool python -m src.vtt /data/input.vtt /data/output.xlsx -Coach "Coach Name" -Client "Client Name"

# Convert VTT to Markdown
docker run -v /path/to/local/data:/data coaching_transcript_tool python -m src.vtt /data/input.vtt /data/output.md -Coach "Coach Name" -Client "Client Name"
```

### Pip Installation

You can install the package directly from the repository:

```bash
pip install git+https://github.com/howie/coaching_transcript_tool.git
```

Or build and install locally:

```bash
make dist-install
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[MIT](https://choosealicense.com/licenses/mit/)
