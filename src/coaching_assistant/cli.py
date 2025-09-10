import logging
from pathlib import Path
from typing import Optional

import typer

from coaching_assistant.core.processor import format_transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="transcript-tool",
    help="""A powerful CLI tool to process and format coaching transcript files (VTT) into structured Markdown or Excel documents.

    Examples:

    1. Convert VTT to Markdown:
       transcript-tool format-command input.vtt output.md

    2. Convert VTT to Excel:
       transcript-tool format-command input.vtt output.xlsx --format excel

    3. Anonymize speaker names:
       transcript-tool format-command input.vtt output.md --coach "John Doe" --client "Jane Smith"

    4. Convert to Traditional Chinese:
       transcript-tool format-command input.vtt output.md --traditional
    """,
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def callback(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        is_eager=True,
    )
):
    """CLI for processing coaching transcripts."""
    if version:
        from coaching_assistant import __version__

        typer.echo(f"transcript-tool v{__version__}")
        raise typer.Exit()


@app.command()
def format_command(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="The path to the input VTT transcript file.",
    ),
    output_file: Path = typer.Argument(
        ...,
        file_okay=True,
        dir_okay=False,
        writable=True,
        help="The path to save the formatted output file.",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="The desired output format ('markdown' or 'excel').",
    ),
    coach_name: Optional[str] = typer.Option(
        None, help="Name of the coach to be replaced with 'Coach'."
    ),
    client_name: Optional[str] = typer.Option(
        None, help="Name of the client to be replaced with 'Client'."
    ),
    convert_to_traditional_chinese: bool = typer.Option(
        False,
        "--traditional",
        help="Convert Simplified Chinese to Traditional Chinese.",
    ),
):
    """
    Process a VTT file and save the formatted version to a new file.

    The tool supports converting VTT files to either Markdown (.md) or Excel (.xlsx) format.
    You can also perform additional processing like speaker anonymization and Chinese conversion.

    Args:
        input_file: Path to the input VTT file
        output_file: Path where to save the converted file
        output_format: Output format (markdown or excel)
        coach_name: Name to replace with 'Coach' in the transcript
        client_name: Name to replace with 'Client' in the transcript
        convert_to_traditional_chinese: Convert Simplified Chinese to Traditional Chinese
    """
    logger.info(f"Reading file: {input_file}")
    try:
        with open(input_file, "rb") as f:
            content_bytes = f.read()

        result = format_transcript(
            file_content=content_bytes,
            original_filename=input_file.name,
            output_format=output_format,
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_to_traditional_chinese,
        )

        logger.info(f"Writing output to: {output_file}")
        if isinstance(result, bytes):
            # For Excel output
            with open(output_file, "wb") as f:
                f.write(result)
        elif isinstance(result, str):
            # For Markdown output
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            typer.echo(
                f"Error: Invalid output format '{output_format}'.", err=True
            )
            raise typer.Exit(code=1)

        typer.echo(
            f"Successfully formatted transcript and saved to {output_file}"
        )

    except Exception as e:
        logger.exception("An error occurred during processing:")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
