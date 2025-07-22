#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="importlib._bootstrap")

"""
Main script for converting VTT files to Markdown or Excel format.
"""
import sys
import re
import sys
import logging
import warnings
import argparse
from typing import List, Dict, Any, Optional, Union

# Import from our modules
from parser import parse_vtt, VTTFormat, detect_format, consolidate_speakers, replace_names
from exporters.markdown import generate_markdown
from exporters.excel import generate_excel
from utils.chinese_converter import convert_to_traditional, is_conversion_available

# Suppress specific warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Proactor .* is not implemented")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Version
__version__ = '1.3.0'

def process_vtt(input_file: str, output_file: str, output_format: str = 'markdown',
               coach_name: str = None, client_name: str = None, debug: bool = False,
               format_type: VTTFormat = None, convert_to_traditional_chinese: bool = False) -> None:
    """
    Process a VTT file and generate output in the specified format.
    
    Args:
        input_file: Path to the input VTT file
        output_file: Path to the output file
        output_format: Output format ('markdown' or 'excel')
        coach_name: Name of the coach in the transcript
        client_name: Name of the client in the transcript
        debug: Enable debug logging
        format_type: Optional format type (MS_TEAMS, MAC_WHISPER). Auto-detected if None.
    """
    if debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f'Processing input file: {input_file}')
    
    try:
        # Parse the VTT file
        parsed_data = parse_vtt(input_file, format_type)
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
        logger.info(f'Generating {output_format} output to {output_file}')
        
        if output_format.lower() == 'markdown':
            markdown_content = generate_markdown(processed_data)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        elif output_format.lower() == 'excel':
            generate_excel(processed_data, output_file)
        else:
            raise ValueError(f'Unsupported output format: {output_format}')
            
        logger.info(f'Successfully generated {output_format} file: {output_file}')
        
    except Exception as e:
        logger.error(f'Error processing VTT file: {str(e)}')
        if debug:
            logger.exception('Detailed error:')
        raise

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert VTT to Markdown or Excel')
    
    # Required arguments
    parser.add_argument('input_file', nargs='?', help='Input VTT file')
    parser.add_argument('output_file', nargs='?', help='Output file (use .md for Markdown or .xlsx for Excel)')
    
    # Optional arguments
    parser.add_argument('--format', '-f', choices=['markdown', 'excel'], 
                       help='Output format (default: inferred from output file extension)')
    parser.add_argument('--coach', '-c', help='Name of the coach (will be replaced with "Coach")')
    parser.add_argument('--client', '-u', help='Name of the client (will be replaced with "Client")')
    parser.add_argument('--convert-to-traditional', '-t', action='store_true',
                      help='Convert Simplified Chinese to Traditional Chinese')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', '-v', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-color', default='D8E4F0', help='Hex color code for highlighting coach rows (default: D8E4F0 light blue)')
    parser.add_argument('-font_size', type=int, default=16, help='Font size for Excel output (default: 16)')
    parser.add_argument('-content_width', type=int, default=160, help='Width of content column in characters (default: 160 for Excel, 80 for Markdown)')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Enable debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
        
    logger.debug(f"Command line arguments: {args}")
    
    # Validate required arguments
    if not all([args.input_file, args.output_file]):
        logger.error("Error: Both input_file and output_file are required")
        print("\nUsage:")
        print("  vtt.py input_file output_file [options]")
        print("\nOptions:")
        print("  -v, --version      Show version information and exit")
        print("  --debug            Enable debug logging")
        print("  -c, --coach NAME   Name of the coach")
        print("  -u, --client NAME  Name of the client")
        print("  -t, --convert-to-traditional  Convert Simplified Chinese to Traditional Chinese")
        print("  -color HEX         Hex color for coach rows (default: D8E4F0)")
        print("  -font_size N       Font size for Excel (default: 16)")
        print("  -content_width N   Content width in characters (default: 160)")
        sys.exit(1)
        
    logger.debug(f"Starting VTT conversion with args: {args}")

    try:
        # Determine output format
        if args.format:
            output_format = args.format
        elif args.output_file.lower().endswith('.md'):
            output_format = 'markdown'
            # Use a more reasonable content width for markdown if not explicitly set
            content_width = min(args.content_width, 80) if args.content_width != 160 else 80
        elif args.output_file.lower().endswith(('.xlsx', '.xls')):
            output_format = 'excel'
            content_width = args.content_width
        else:
            logger.error("Unsupported output format. Use .md for Markdown or .xlsx for Excel.")
            sys.exit(1)
            
        logger.debug(f"Processing with format: {output_format}, font_size: {args.font_size}, content_width: {content_width}")
        
        # Check if conversion is available if requested
        if args.convert_to_traditional and not is_conversion_available():
            print("Warning: opencc-python-reimplemented is not installed. Chinese conversion will be skipped.")
            print("Please install it with: pip install opencc-python-reimplemented")
        
        # Process the VTT file
        process_vtt(
            args.input_file,
            args.output_file,
            output_format=output_format,
            coach_name=args.coach,
            client_name=args.client,
            debug=args.debug,
            convert_to_traditional_chinese=args.convert_to_traditional
        )
        
        logger.info(f"Successfully generated {output_format} file: {args.output_file}")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=args.debug)
        sys.exit(1)

if __name__ == "__main__":
    main()
