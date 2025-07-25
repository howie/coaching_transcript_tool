import logging
from pathlib import Path
from typing import Optional

import typer

from coaching_assistant.core.processor import format_transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="transcript-tool",
    help="A CLI tool to format coaching transcript files (VTT) into Markdown or Excel.",
)

@app.callback()
def callback():
    """Callback to ensure help is shown when no command is provided."""

@app.command()
def format_command(
    input_file: Path = typer.Argument(
        ..., 
        exists=True, 
        file_okay=True, 
        dir_okay=False, 
        readable=True,
        help="The path to the input VTT transcript file."
    ),
    output_file: Path = typer.Argument(
        ..., 
        file_okay=True, 
        dir_okay=False, 
        writable=True,
        help="The path to save the formatted output file."
    ),
    output_format: str = typer.Option(
        "markdown", 
        "--format", 
        "-f",
        help="The desired output format ('markdown' or 'excel')."
    ),
    coach_name: Optional[str] = typer.Option(
        None, 
        help="Name of the coach to be replaced with 'Coach'."
    ),
    client_name: Optional[str] = typer.Option(
        None, 
        help="Name of the client to be replaced with 'Client'."
    ),
    convert_to_traditional_chinese: bool = typer.Option(
        False, 
        "--traditional",
        help="Convert Simplified Chinese to Traditional Chinese."
    ),
):
    """
    Processes a VTT file and saves the formatted version to a new file.
    """
    logger.info(f"Reading file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content_str = f.read()

        result = format_transcript(
            file_content=content_str,
            output_format=output_format,
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_to_traditional_chinese,
        )

        logger.info(f"Writing output to: {output_file}")
        if output_format.lower() == 'excel':
            # The result is a BytesIO object
            with open(output_file, 'wb') as f:
                f.write(result.getvalue())
        elif output_format.lower() == 'markdown':
            # The result is a string
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
        else:
            typer.echo(f"Error: Invalid output format '{output_format}'.", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"Successfully formatted transcript and saved to {output_file}")

    except Exception as e:
        logger.exception("An error occurred during processing:")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
