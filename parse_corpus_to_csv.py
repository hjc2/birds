#!/usr/bin/env python3
"""
Parse large HTML corpus file containing multiple taxonomy families and convert to CSV
for Birds of Prey Urban Niche Space dataset.
"""

import csv
import re
from html.parser import HTMLParser
from pathlib import Path
import sys


class MultiTaxonomyParser(HTMLParser):
    """Parse HTML to extract bird species from multiple taxonomy family sections."""

    # Map family indices to taxonomic orders
    FAMILY_ORDER_MAP = {
        'fam_32': 'Cathartiformes',    # New World Vultures
        'fam_33': 'Accipitriformes',   # Hawks, Eagles, Kites, etc.
        'fam_34': 'Strigiformes',      # Owls
        'fam_42': 'Falconiformes',     # Falcons and Caracaras
    }

    def __init__(self):
        super().__init__()
        self.birds = []
        self.current_bird = {}
        self.current_order = ''
        self.in_heading_main = False
        self.in_heading_sub = False
        self.in_iucn_badge = False
        self.capture_text = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Detect family index to determine order
        if tag == 'ol' and 'data-familyindex' in attrs_dict:
            family_index = attrs_dict['data-familyindex']
            # Extract family number (e.g., 'fam_32_0' -> 'fam_32')
            family_key = '_'.join(family_index.split('_')[:2])
            self.current_order = self.FAMILY_ORDER_MAP.get(family_key, '')

        # Start of a new card - get species code
        if tag == 'div' and 'data-speciescode' in attrs_dict:
            self.current_bird = {
                'species_code': attrs_dict['data-speciescode'],
                'order': self.current_order
            }

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


def parse_corpus_to_csv(html_file_path, output_csv_path='birds_corpus.csv'):
    """
    Parse HTML corpus file containing multiple taxonomy families and generate CSV.

    Args:
        html_file_path: Path to the HTML corpus file
        output_csv_path: Path for output CSV (default: 'birds_corpus.csv')
    """
    html_file = Path(html_file_path)

    if not html_file.exists():
        print(f"Error: File not found: {html_file_path}")
        sys.exit(1)

    print(f"Reading {html_file.name}...")

    # Read HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Parse HTML
    parser = MultiTaxonomyParser()
    parser.feed(html_content)

    if not parser.birds:
        print("Warning: No birds found in HTML file")
        return

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
            row['Order'] = bird.get('order', '')
            row['IUCN_Status'] = bird.get('iucn_status', '')
            writer.writerow(row)

    # Print summary statistics
    print(f"\n{'='*60}")
    print(f"Successfully parsed {len(parser.birds)} birds from {html_file.name}")
    print(f"Output written to: {output_path}")
    print(f"{'='*60}")

    # Count by order
    order_counts = {}
    for bird in parser.birds:
        order = bird.get('order', 'Unknown')
        order_counts[order] = order_counts.get(order, 0) + 1

    print(f"\nBreakdown by Order:")
    for order, count in sorted(order_counts.items()):
        print(f"  {order:20s}: {count:4d} species")

    # Show first few birds from each order
    print(f"\nSample species extracted:")
    current_order = None
    sample_count = 0
    for bird in parser.birds:
        if bird.get('order') != current_order:
            current_order = bird.get('order')
            sample_count = 0
            print(f"\n  {current_order}:")

        if sample_count < 3:  # Show first 3 from each order
            iucn = bird.get('iucn_status', 'N/A')
            print(f"    - {bird.get('common_name')} ({bird.get('scientific_name')}) [{iucn}]")
            sample_count += 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_corpus_to_csv.py <html_file> [output_csv]")
        print("\nExample:")
        print("  python parse_corpus_to_csv.py corpus.html")
        print("  python parse_corpus_to_csv.py corpus.html all_birds.csv")
        sys.exit(1)

    html_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else 'birds_corpus.csv'

    parse_corpus_to_csv(html_file, output_csv)
