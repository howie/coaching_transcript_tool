#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="importlib._bootstrap")

"""
Main script for converting VTT files to Markdown or Excel format.
"""
import sys
import re
import logging
import argparse
from typing import List, Dict, Any

# Local imports
from parser import parse_vtt, consolidate_speakers, replace_names
from exporters.markdown import generate_markdown
from exporters.excel import generate_excel

# Version information
__version__ = '1.2.0'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)





def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert VTT to Markdown or Excel')
    
    # Required arguments
    parser.add_argument('input_file', nargs='?', help='Input VTT file')
    parser.add_argument('output_file', nargs='?', help='Output file (use .md for Markdown or .xlsx for Excel)')
    
    # Optional arguments
    parser.add_argument('-v', '--version', action='store_true', help='Show version information and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-Coach', help='Name of the coach')
    parser.add_argument('-Client', help='Name of the client')
    parser.add_argument('-color', default='D8E4F0', help='Hex color code for highlighting coach rows (default: D8E4F0 light blue)')
    parser.add_argument('-font_size', type=int, default=16, help='Font size for Excel output (default: 16)')
    parser.add_argument('-content_width', type=int, default=160, help='Width of content column in characters (default: 160 for Excel, 80 for Markdown)')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Handle version flag
    if args.version:
        print(f"VTT Converter v{__version__}")
        sys.exit(0)
        
    # Enable debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Validate required arguments if not showing version
    if not all([args.input_file, args.output_file]):
        logger.error("Error: Both input_file and output_file are required")
        print("\nUsage:")
        print("  vtt.py input_file output_file [options]")
        print("\nOptions:")
        print("  -v, --version      Show version information and exit")
        print("  --debug            Enable debug logging")
        print("  -Coach NAME        Name of the coach")
        print("  -Client NAME       Name of the client")
        print("  -color HEX         Hex color for coach rows (default: D8E4F0)")
        print("  -font_size N       Font size for Excel (default: 16)")
        print("  -content_width N   Content width in characters (default: 160)")
        sys.exit(1)
        
    logger.debug(f"Starting VTT conversion with args: {args}")

    try:
        logger.info(f"Processing input file: {args.input_file}")
        data = parse_vtt(args.input_file)
        logger.debug(f"Parsed {len(data)} entries from VTT file")
        
        consolidated_data = consolidate_speakers(data)
        logger.debug(f"Consolidated to {len(consolidated_data)} entries")

        if args.Coach and args.Client:
            logger.debug(f"Replacing names - Coach: {args.Coach}, Client: {args.Client}")
            consolidated_data = replace_names(consolidated_data, args.Coach, args.Client)

        logger.info(f"Generating output file: {args.output_file}")
        if args.output_file.endswith('.md'):
            # For Markdown, use a more reasonable content width if not explicitly set
            md_content_width = min(args.content_width, 80) if args.content_width != 160 else 80
            logger.debug(f"Generating Markdown with content width: {md_content_width}")
            output = generate_markdown(consolidated_data, md_content_width)
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"Markdown file created successfully: {args.output_file}")
            
        elif args.output_file.endswith('.xlsx'):
            logger.debug(f"Generating Excel with font size: {args.font_size}, content width: {args.content_width}")
            generate_excel(consolidated_data, args.output_file, args.color, args.font_size, args.content_width)
            logger.info(f"Excel file created successfully: {args.output_file}")
            
        else:
            logger.error("Unsupported output format. Use .md for Markdown or .xlsx for Excel.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=args.debug)
        sys.exit(1)

if __name__ == "__main__":
    main()
