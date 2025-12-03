#!/usr/bin/env python3
"""
Parse HTML taxonomy tree cards and convert to CSV format for Birds of Prey Urban Niche Space dataset.
"""

import csv
import re
from html.parser import HTMLParser
from pathlib import Path
import sys


class TaxonomyCardParser(HTMLParser):
    """Parse HTML to extract bird species information from taxonomy cards."""

    def __init__(self):
        super().__init__()
        self.birds = []
        self.current_bird = {}
        self.in_heading_main = False
        self.in_heading_sub = False
        self.in_iucn_badge = False
        self.capture_text = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Start of a new card - get species code
        if tag == 'div' and 'data-speciescode' in attrs_dict:
            self.current_bird = {'species_code': attrs_dict['data-speciescode']}

        # Common name
        if tag == 'span' and attrs_dict.get('class') == 'Heading-main':
            self.in_heading_main = True
            self.capture_text = True

        # Scientific name
        if tag == 'span' and 'Heading-sub--sci' in attrs_dict.get('class', ''):
            self.in_heading_sub = True
            self.capture_text = True

        # IUCN status
        if tag == 'span' and attrs_dict.get('class') == 'Badge-label':
            self.in_iucn_badge = True
            self.capture_text = True

    def handle_data(self, data):
        if not self.capture_text:
            return

        data = data.strip()
        if not data:
            return

        if self.in_heading_main:
            # Append and normalize whitespace (in case text is split across multiple data calls)
            existing = self.current_bird.get('common_name', '')
            self.current_bird['common_name'] = ' '.join((existing + ' ' + data).split())

        if self.in_heading_sub:
            # Append and normalize whitespace
            existing = self.current_bird.get('scientific_name', '')
            self.current_bird['scientific_name'] = ' '.join((existing + ' ' + data).split())

        if self.in_iucn_badge:
            # Extract just the code (CR, LC, VU, etc.)
            iucn_code = data.split()[0]
            if iucn_code in ['CR', 'EN', 'VU', 'NT', 'LC', 'DD', 'EW', 'EX']:
                self.current_bird['iucn_status'] = iucn_code

    def handle_endtag(self, tag):
        if tag == 'span':
            self.in_heading_main = False
            self.in_heading_sub = False
            self.in_iucn_badge = False
            self.capture_text = False

        # End of card
        if tag == 'li' and self.current_bird:
            # Only add if we have all required fields
            if all(key in self.current_bird for key in ['common_name', 'scientific_name']):
                self.birds.append(self.current_bird.copy())
            self.current_bird = {}


def determine_order(html_file_path):
    """Determine the taxonomic order based on the filename."""
    filename = Path(html_file_path).stem.lower()

    # Map of filename patterns to orders
    order_map = {
        'cathar': 'Cathartiformes',
        'accip': 'Accipitriformes',
        'strig': 'Strigiformes',
        'falcon': 'Falconiformes',
    }

    for pattern, order in order_map.items():
        if pattern in filename:
            return order

    return ''  # Return empty string if unknown


def parse_html_to_csv(html_file_path, output_csv_path=None):
    """
    Parse HTML taxonomy file and generate CSV with bird data.

    Args:
        html_file_path: Path to the HTML file to parse
        output_csv_path: Path for output CSV (optional, will auto-generate if not provided)
    """
    html_file = Path(html_file_path)

    if not html_file.exists():
        print(f"Error: File not found: {html_file_path}")
        sys.exit(1)

    # Read HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Parse HTML
    parser = TaxonomyCardParser()
    parser.feed(html_content)

    if not parser.birds:
        print("Warning: No birds found in HTML file")
        return

    # Determine order from filename
    order = determine_order(html_file_path)

    # Generate output filename if not provided
    if output_csv_path is None:
        output_csv_path = html_file.stem + '_birds.csv'

    # CSV column headers (matching the existing dataset)
    headers = [
        'Species',
        'CommonName',
        'Order',
        'IUCN_Status',
        'HabitatGeneralistSpecialist',
        'Nest_Location_>1',
        'Nest_Structure_>1',
        'General_Nesting_Location',
        'General_Nesting_Structure',
        'Nesting_On_Artificial',
        'Nest_Elevation_Min',
        'Nest_Elevation_Max',
        'Urban_Nester_YN',
        'Urban_Forager_YN',
        'AcceptsProvisions_YN',
        'Urban_NestMortality',
        'Exurban_NestMortality',
        'Urban_RangeSize',
        'Exurban_RangeSize',
        'Urban_Primary_Diet',
        'Exurban_Primary_Diet'
    ]

    # Write CSV
    output_path = Path(output_csv_path)
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for bird in parser.birds:
            row = {header: '' for header in headers}  # Initialize all fields as empty
            row['Species'] = bird.get('scientific_name', '')
            row['CommonName'] = bird.get('common_name', '')
            row['Order'] = order
            row['IUCN_Status'] = bird.get('iucn_status', '')
            writer.writerow(row)

    print(f"Successfully parsed {len(parser.birds)} birds from {html_file.name}")
    print(f"Output written to: {output_path}")
    print(f"\nExtracted birds:")
    for bird in parser.birds:
        print(f"  - {bird.get('common_name')} ({bird.get('scientific_name')}) - {bird.get('iucn_status', 'N/A')}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_taxonomy_to_csv.py <html_file> [output_csv]")
        print("\nExample:")
        print("  python parse_taxonomy_to_csv.py cathar.html")
        print("  python parse_taxonomy_to_csv.py cathar.html my_output.csv")
        sys.exit(1)

    html_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None

    parse_html_to_csv(html_file, output_csv)
