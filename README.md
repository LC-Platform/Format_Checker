# Format_Checker
# USR Validation Script

## Overview
This Python script validates USR text files and generates separate reports for formatting and parsing errors.

## Requirements
- Python 3.x
- Input folder: `text_input`

## Validations
- Sentence ID and segment tags
- 9-column structure
- Token indices and duplicates
- Pronoun and `$wyax` checks
- Dependency, discourse, and construction information

## Output Files
- `format_error.tsv`: File-level formatting errors
- `usr_parsing_errors.tsv`: Sentence-level USR errors

## Run

```bash
python validation.py text_input
```

Original input files remain unchanged.
