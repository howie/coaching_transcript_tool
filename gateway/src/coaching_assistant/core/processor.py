"""
Core processing logic for handling transcript files.
Cloudflare Workers 優化版本。
"""
import logging
from typing import List, Dict, Any, Optional, Union, IO

from ..parser import (VTTFormat, UnrecognizedFormatError, consolidate_speakers, parse_vtt, replace_names)
from ..exporters.excel import generate_excel
from ..exporters.markdown import generate_markdown
from ..utils.chinese_converter import convert_to_traditional
# from ..utils.s3_uploader import upload_snippet_to_s3  # CF Workers 將使用 R2

logger = logging.getLogger(__name__)

def format_transcript(
    file_content: bytes,  # Changed from str to bytes
    original_filename: str,
    output_format: str = 'markdown',
    coach_name: Optional[str] = None,
    client_name: Optional[str] = None,
    convert_to_traditional_chinese: bool = False,
    format_type: Optional[VTTFormat] = None,
) -> Union[str, bytes]:
    """
    Processes the content of a transcript file and returns the formatted output.
    CF Workers 優化版本。

    Args:
        file_content: The bytes content of the input VTT file.
        original_filename: Original filename for logging purposes.
        output_format: Output format ('markdown' or 'excel').
        coach_name: Name of the coach in the transcript.
        client_name: Name of the client in the transcript.
        convert_to_traditional_chinese: Flag to convert to Traditional Chinese.
        format_type: Optional format type (MS_TEAMS, MAC_WHISPER). Auto-detected if None.

    Returns:
        The formatted transcript as a string (for Markdown) or bytes (for Excel).
    """
    try:
        # Decode file content to string for parsing
        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, it's likely not a valid text file.
            raise UnrecognizedFormatError("File is not valid UTF-8 text.")

        # Parse the VTT content
        parsed_data = parse_vtt(content_str, format_type)
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
            excel_buffer = generate_excel(processed_data)
            excel_buffer.seek(0)  # Reset buffer position to beginning
            return excel_buffer.getvalue()
        else:
            raise ValueError(f'Unsupported output format: {output_format}')

    except UnrecognizedFormatError as e:
        logger.warning(f"Unrecognized format for file '{original_filename}': {e}")
        # TODO: 實作 CF R2 檔案上傳用於問題診斷
        # upload_snippet_to_r2(file_content, original_filename)
        # Re-raise the exception to be handled by the API layer
        raise

    except Exception as e:
        logger.error(f'Error processing transcript content: {str(e)}')
        logger.exception('Detailed error:')
        raise
