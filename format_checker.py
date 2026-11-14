
import os
import sys
import re


# ============================================================
# 1. FILE-LEVEL VALIDATION
# ============================================================

def first_line_starts_with_segment_id(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()
        return first_line.startswith("<segment_id=")


def last_line_ends_with_segment_id(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        return False

    return lines[-1].endswith("</segment_id>")


def second_line_starts_with_hash(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    if len(lines) < 2:
        return False

    return lines[1].strip().startswith("#")


def check_file_level_format(
    file_path,
    skip_keywords,
    pronoun_list,
    output_file
):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        if len(lines) < 2:
            return

        seen_indices = set()

        for line in lines[2:]:

            line_content = line.strip()

            if not line_content:
                continue

            if any(
                keyword in line_content.lower()
                for keyword in skip_keywords
            ):
                if not line_content.startswith('%'):
                    print(
                        f"{file_path}\tSentence type should start with '%'.",
                        file=output_file
                    )
                break

            columns = re.split(r'\s+', line_content)

            if len(columns) < 2:
                continue

            concept = columns[0]
            index = columns[1]

            # Check concept index
            if index.isdigit():

                if index in seen_indices:
                    print(
                        f"{file_path}\tIndex {index} in index column is repeated.",
                        file=output_file
                    )
                else:
                    seen_indices.add(index)

            else:
                print(
                    f"{file_path}\t{concept} concept's index is incorrect. "
                    f"Found '{index}' as index.",
                    file=output_file
                )

            # Pronoun validation
            if concept.lstrip('$') in pronoun_list:

                if not line_content.startswith('$'):
                    print(
                        f"{file_path}\tPronoun {concept} should start with '$'.",
                        file=output_file
                    )

            # Check special $wyax row
            if concept == "$wyax":

                if len(columns) < 7 or columns[6] not in [
                    "proximal", "distal"
                ]:
                    print(
                        f"{file_path}\tRow with '$wyax' should have "
                        f"'proximal' or 'distal' in column[6].",
                        file=output_file
                    )

    except Exception as e:
        print(
            f"Error validating file format {file_path}: {e}",
            file=output_file
        )


# ============================================================
# 2. USR-LEVEL VALIDATION
# ============================================================

def validate_usr_rows(file_path, output_file):

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        current_sentence_id = "UNKNOWN"

        for line_number, line in enumerate(lines, start=1):

            line_content = line.strip()

            if not line_content:
                continue

            # Extract sentence ID
            segment_match = re.search(
                r'<segment_id=(.*?)>',
                line_content
            )

            if segment_match:
                current_sentence_id = segment_match.group(1)
                continue

            # Ignore comments and sentence metadata
            if (
                line_content.startswith('#')
                or line_content.startswith('%')
                or line_content.startswith('<')
            ):
                continue

            columns = re.split(r'\s+', line_content)

            # Ignore non-USR lines
            if not columns:
                continue

            # Check incorrect number of columns
            if len(columns) != 9:

                print(
                    f"{current_sentence_id}\t"
                    f"Incorrect number of columns: {len(columns)} "
                    f"(expected 9)",
                    file=output_file
                )

                continue

            # ------------------------------------------------
            # Check malformed discourse information
            # ------------------------------------------------

            # This detects the specific malformed pattern:
            # yoga_ch1_su1_para1_sent3.2coref
            #
            # Expected separator between index and coref
            # must be confirmed against your USR convention.

            for column_index, value in enumerate(columns):

                if re.search(
                    r'_sent\d+\.\d+coref\b',
                    value,
                    re.IGNORECASE
                ):

                    print(
                        f"{current_sentence_id}\t"
                        f"Malformed discourse_info: {value}",
                        file=output_file
                    )

    except Exception as e:
        print(
            f"{os.path.basename(file_path)}\tUSR parsing error: {e}",
            file=output_file
        )


# ============================================================
# 3. PROCESS FILES
# ============================================================

def process_files(
    folder_path,
    format_output_path,
    usr_output_path,
    skip_keywords,
    pronoun_list
):

    with open(format_output_path, 'w', encoding='utf-8') as format_file, \
         open(usr_output_path, 'w', encoding='utf-8') as usr_file:

        if not os.path.isdir(folder_path):

            print(
                f"The folder '{folder_path}' does not exist "
                f"or is not a directory.",
                file=format_file
            )
            return

        for filename in sorted(os.listdir(folder_path)):

            file_path = os.path.join(folder_path, filename)

            if not os.path.isfile(file_path):
                continue

            try:

                # --------------------------------------------
                # FILE-LEVEL CHECKS
                # --------------------------------------------

                if not first_line_starts_with_segment_id(file_path):

                    print(
                        f"{file_path}\tThe first line does not start "
                        f"with '<segment_id='.",
                        file=format_file
                    )

                if not last_line_ends_with_segment_id(file_path):

                    print(
                        f"{file_path}\tThe last line does not end "
                        f"with '</segment_id>'.",
                        file=format_file
                    )

                if not second_line_starts_with_hash(file_path):

                    print(
                        f"{file_path}\tThe second line does not "
                        f"start with hash (#).",
                        file=format_file
                    )

                check_file_level_format(
                    file_path,
                    skip_keywords,
                    pronoun_list,
                    format_file
                )

                # --------------------------------------------
                # USR-LEVEL CHECKS
                # --------------------------------------------

                validate_usr_rows(
                    file_path,
                    usr_file
                )

            except UnicodeDecodeError as e:

                print(
                    f"{filename}\tError reading file: {e}",
                    file=format_file
                )


# ============================================================
# 4. SORT ERROR REPORTS
# ============================================================

def sort_error_file(input_file_path):

    try:

        with open(
            input_file_path,
            'r',
            encoding='utf-8'
        ) as file:
            lines = file.readlines()

        lines.sort(
            key=lambda line: line.split('\t')[0].strip()
        )

        with open(
            input_file_path,
            'w',
            encoding='utf-8'
        ) as file:
            file.writelines(lines)

    except Exception as e:

        print(
            f"Error sorting {input_file_path}: {e}"
        )


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    folder_path = sys.argv[1]

    # Separate output files
    format_output_path = "format_error.tsv"
    usr_output_path = "usr_parsing_errors.tsv"

    skip_keywords = [
        "affirmative",
        "negative",
        "yn_interrogative",
        "interrogative",
        "imperative",
        "pass_affirmative",
        "pass_negative",
        "pass_interrogative",
        "pass_yn_interrogative",
        "fragment",
        "title",
        "heading",
        "term",
        "sent_id"
    ]

    pronoun_list = [
        "wyax",
        "yax",
        "speaker",
        "addressee",
        "kim"
    ]

    # Run validation
    process_files(
        folder_path,
        format_output_path,
        usr_output_path,
        skip_keywords,
        pronoun_list
    )

    # Sort both reports
    sort_error_file(format_output_path)
    sort_error_file(usr_output_path)

    print("\nValidation completed.")

    print("File-level errors:", format_output_path)
    print("USR-level errors:", usr_output_path)
