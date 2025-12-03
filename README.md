### Data Files

**corpus.html** - taken from the webpage

**birds_corpus.csv** - csv from the file that i made

### Scripts

**parse_taxonomy_to_csv.py** - parse a taxonomy file
```bash
python3 parse_taxonomy_to_csv.py cathar.html
```

**parse_corpus_to_csv.py** - parse a file of concatenated taxonomies
```bash
python3 parse_corpus_to_csv.py corpus.html
```

## Extracted Info

- Scientific name
- Common name
- Taxonomic order
- IUCN conservation status

Fills the rest of the columns, and leaves them blank