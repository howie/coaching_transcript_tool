#!/usr/bin/env python3
"""
Module for exporting transcript data to Excel format.
"""
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def generate_excel(
    data: List[Dict[str, Any]], 
    output_file: str, 
    coach_color: str = 'D8E4F0', 
    font_size: int = 16, 
    content_width: int = 40
) -> None:
    """
    Generate an Excel file from the parsed data with formatting.
    
    Args:
        data: List of dictionaries with time, speaker, and content
        output_file: Path to save the Excel file
        coach_color: Hex color code to highlight coach rows (default: light blue D8E4F0)
        font_size: Default font size for all cells (default: 16)
        content_width: Width of the content column in characters (default: 40)
    """
    # Create a new workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Transcript"
    
    # Add headers
    headers = ['Time', 'Role', 'Content']
    ws.append(headers)
    
    # Add data rows
    for item in data:
        ws.append([item['time'], item['speaker'], item['content']])
    
    # Set column widths
    ws.column_dimensions['A'].width = 15  # Time column
    ws.column_dimensions['B'].width = 15  # Role column
    ws.column_dimensions['C'].width = content_width  # Content column
    
    # Create styles
    header_font = Font(bold=True, size=font_size)
    cell_font = Font(size=font_size)
    alignment = Alignment(wrap_text=True, vertical='top')
    coach_fill = PatternFill(start_color=coach_color, end_color=coach_color, fill_type='solid')
    
    # Apply styles to header
    for cell in ws[1]:
        cell.font = header_font
    
    # Apply styles to data cells
    for row in ws.iter_rows(min_row=2, max_row=len(data)+1, min_col=1, max_col=3):
        speaker = row[1].value  # Column B contains the speaker
        
        for cell in row:
            cell.font = cell_font
            cell.alignment = alignment
            
            # Apply fill to coach rows
            if speaker == 'Coach':
                cell.fill = coach_fill
    
    # Save the workbook
    wb.save(output_file)
