#!/usr/bin/env python3
import argparse
import re
from collections import defaultdict
import pandas as pd

def parse_vtt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n<v ([^>]+)>(.+?)</v>'
    matches = re.findall(pattern, content, re.DOTALL)

    parsed_data = []
    for start_time, _, speaker, text in matches:
        parsed_data.append({
            'time': start_time,
            'speaker': speaker.strip(),
            'content': text.strip().replace('\n', ' ')
        })

    return parsed_data

def consolidate_speakers(data):
    consolidated = []
    current_speaker = None
    current_content = []
    current_time = None

    for item in data:
        if item['speaker'] != current_speaker:
            if current_speaker:
                consolidated.append({
                    'time': current_time,
                    'speaker': current_speaker,
                    'content': ' '.join(current_content)
                })
            current_speaker = item['speaker']
            current_content = [item['content']]
            current_time = item['time']
        else:
            current_content.append(item['content'])

    if current_speaker:
        consolidated.append({
            'time': current_time,
            'speaker': current_speaker,
            'content': ' '.join(current_content)
        })

    return consolidated

def replace_names(data, coach, client):
    for item in data:
        if item['speaker'] == coach:
            item['speaker'] = 'Coach'
        elif item['speaker'] == client:
            item['speaker'] = 'Client'
    return data

def generate_markdown(data):
    markdown = "| Time | Role | Content |\n"
    markdown += "| ---- | ---- | ------- |\n"
    for item in data:
        markdown += f"| {item['time']} | {item['speaker']} | {item['content']} |\n"
    return markdown

def generate_excel(data, output_file):
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)

def main():
    parser = argparse.ArgumentParser(description='Convert VTT to Markdown or Excel')
    parser.add_argument('input_file', help='Input VTT file')
    parser.add_argument('output_file', help='Output file (use .md for Markdown or .xlsx for Excel)')
    parser.add_argument('-Coach', help='Name of the coach')
    parser.add_argument('-Client', help='Name of the client')
    args = parser.parse_args()

    data = parse_vtt(args.input_file)
    consolidated_data = consolidate_speakers(data)

    if args.Coach and args.Client:
        consolidated_data = replace_names(consolidated_data, args.Coach, args.Client)

    if args.output_file.endswith('.md'):
        output = generate_markdown(consolidated_data)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(output)
    elif args.output_file.endswith('.xlsx'):
        generate_excel(consolidated_data, args.output_file)
    else:
        print("Unsupported output format. Use .md for Markdown or .xlsx for Excel.")

if __name__ == "__main__":
    main()
