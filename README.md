# Birds of Prey Data Parser

Simple tools to extract bird taxonomy data from HTML and convert it to CSV format.

## Files

### Data Files

**corpus.html** - Large HTML file containing taxonomy cards for 572+ birds of prey across multiple orders (vultures, hawks, owls, falcons)

**birds_corpus.csv** - Generated CSV with all bird species data in the "Birds of Prey Urban Niche Space" format

### Scripts

**parse_taxonomy_to_csv.py** - Parse a single taxonomy HTML file (one bird family)
```bash
python3 parse_taxonomy_to_csv.py cathar.html
```

**parse_corpus_to_csv.py** - Parse large HTML files with multiple bird families
```bash
python3 parse_corpus_to_csv.py corpus.html
```

## What Gets Extracted

- Scientific name
- Common name
- Taxonomic order (Cathartiformes, Accipitriformes, Strigiformes, Falconiformes)
- IUCN conservation status (CR, EN, VU, NT, LC, etc.)

The CSV has 21 columns total - the script fills in the basic info and leaves the rest blank for manual data entry.
