"""
Core processing logic for handling transcript files.
"""
import logging
from typing import List, Dict, Any, Optional, Union, IO

from ..parser import VTTFormat, consolidate_speakers, parse_vtt, replace_names
from ..exporters.excel import generate_excel
from ..exporters.markdown import generate_markdown
from ..utils.chinese_converter import convert_to_traditional

logger = logging.getLogger(__name__)

def format_transcript(
    file_content: str,
    output_format: str = 'markdown',
    coach_name: Optional[str] = None,
    client_name: Optional[str] = None,
    convert_to_traditional_chinese: bool = False,
    format_type: Optional[VTTFormat] = None,
) -> Union[str, bytes]:
    """
    Processes the content of a transcript file and returns the formatted output.

    Args:
        file_content: The string content of the input VTT file.
        output_format: Output format ('markdown' or 'excel').
        coach_name: Name of the coach in the transcript.
        client_name: Name of the client in the transcript.
        convert_to_traditional_chinese: Flag to convert to Traditional Chinese.
        format_type: Optional format type (MS_TEAMS, MAC_WHISPER). Auto-detected if None.

    Returns:
        The formatted transcript as a string (for Markdown) or bytes (for Excel).
    """
    try:
        # Parse the VTT content
        parsed_data = parse_vtt(file_content, format_type)
        logger.debug(f'Successfully parsed {len(parsed_data)} entries')

        # Consolidate consecutive speeches from the same speaker
        consolidated_data = consolidate_speakers(parsed_data)
        logger.debug(f'Consolidated to {len(consolidated_data)} entries')

        # Replace names with roles if coach and client names are provided
        if coach_name and client_name:
            logger.debug(f'Replacing names - Coach: {coach_name}, Client: {client_name}')
            processed_data = replace_names(consolidated_data, coach_name, client_name)
        else:
            processed_data = consolidated_data

        # Convert to Traditional Chinese if requested
        if convert_to_traditional_chinese:
            logger.info('Converting content to Traditional Chinese')
            processed_data = convert_to_traditional(processed_data)

        # Generate output in the specified format
        logger.info(f'Generating {output_format} output')

        if output_format.lower() == 'markdown':
            return generate_markdown(processed_data)
        elif output_format.lower() == 'excel':
            return generate_excel(processed_data)
        else:
            raise ValueError(f'Unsupported output format: {output_format}')

    except Exception as e:
        logger.error(f'Error processing transcript content: {str(e)}')
        logger.exception('Detailed error:')
        raise
