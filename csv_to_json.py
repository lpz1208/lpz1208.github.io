import csv
import json
import os

# Define file paths relative to the script location
# Use os.path.abspath to ensure the path is correct even if run from elsewhere
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, 'data', 'data.csv')
json_file_path = os.path.join(script_dir, 'output.json')

structured_data = {}
encodings_to_try = ['utf-8', 'gbk'] # Prioritize utf-8, fallback to gbk
read_successful = False
processed_lines = 0
skipped_lines = 0

print(f"Script directory: {script_dir}")
print(f"Looking for CSV at: {csv_file_path}")
print(f"Will write JSON to: {json_file_path}")


if not os.path.exists(csv_file_path):
    print(f"Error: CSV file not found at the expected location: {csv_file_path}")
else:
    for encoding in encodings_to_try:
        try:
            print(f"Attempting to read CSV with encoding: {encoding}")
            with open(csv_file_path, mode='r', newline='', encoding=encoding) as csvfile:
                # Standard comma delimiter, default quote character (")
                reader = csv.reader(csvfile)
                line_num = 0

                try:
                    header = next(reader) # Read header row
                    line_num += 1
                    print(f"Header found: {header}") # Optional debug print
                    if not header or len(header) < 5:
                         print(f"Warning: Unexpected header format with encoding {encoding}: {header}")
                         structured_data = {} # Reset data
                         skipped_lines = 0
                         processed_lines = 0
                         continue # Try next encoding if header looks wrong

                    # Expected header names (case-sensitive)
                    expected_headers = ['国家', '指数名称', '日期', '值']
                    # Check if essential columns exist (based on indices used later)
                    if not all(h in header for h in expected_headers):
                         print(f"Warning: Missing expected headers with encoding {encoding}. Found: {header}")
                         structured_data = {} # Reset data
                         skipped_lines = 0
                         processed_lines = 0
                         continue # Try next encoding

                except StopIteration:
                    print(f"Warning: CSV file is empty or contains only header with encoding {encoding}.")
                    structured_data = {} # Reset data
                    skipped_lines = 0
                    processed_lines = 0
                    continue # Try next encoding
                except csv.Error as e:
                     print(f"CSV error reading header with encoding {encoding}: {e}")
                     structured_data = {} # Reset data
                     skipped_lines = 0
                     processed_lines = 0
                     continue


                structured_data = {} # Reset data for this encoding attempt
                skipped_lines = 0
                processed_lines = 0

                for row in reader:
                    line_num += 1
                    # Handle potential extra empty fields caused by trailing commas
                    # We only need the first 5 columns based on header structure
                    if len(row) < 5:
                        # print(f"Skipping line {line_num}: Row has less than 5 columns. Row: {row}")
                        skipped_lines += 1
                        continue

                    # Extract data based on expected positions (0-based index)
                    # csv.reader automatically handles quotes if they are standard double quotes
                    country = row[0].strip()
                    index_name = row[1].strip()
                    date_str = row[3].strip()
                    value_str = row[4].strip()

                    # Validate and process data
                    if not country or not index_name or not date_str or not value_str:
                        # print(f"Skipping line {line_num}: Missing essential data. Row: {row}")
                        skipped_lines += 1
                        continue

                    # Extract year
                    try:
                        year = date_str.split('-')[0]
                        if len(year) != 4 or not year.isdigit():
                             raise ValueError("Year is not four digits")
                        int(year) # Validate year is numeric
                    except (IndexError, ValueError) as e:
                        # print(f"Skipping line {line_num}: Invalid date/year format '{date_str}' ({e}). Row: {row}")
                        skipped_lines += 1
                        continue

                    # Convert value to float
                    try:
                        # Handle potential commas as thousands separators if needed (replace before float conversion)
                        # value_str = value_str.replace(',', '') # Uncomment if values might have commas e.g., "1,234.5"
                        value = float(value_str)
                    except ValueError:
                        # print(f"Skipping line {line_num}: Invalid value format '{value_str}'. Row: {row}")
                        skipped_lines += 1
                        continue

                    # Structure the data
                    if country not in structured_data:
                        structured_data[country] = {}
                    if index_name not in structured_data[country]:
                        structured_data[country][index_name] = []

                    structured_data[country][index_name].append({"year": year, "value": value})
                    processed_lines += 1

                # If we reach here without errors for this encoding, it worked.
                read_successful = True
                print(f"Successfully processed CSV with encoding: {encoding}")
                print(f"Processed lines: {processed_lines}, Skipped lines: {skipped_lines}")
                break # Exit the loop

        except FileNotFoundError:
            # This case is handled by the initial check, but kept for robustness
            print(f"Error: CSV file not found at {csv_file_path}")
            break # Stop trying encodings if file not found
        except UnicodeDecodeError:
            print(f"Failed to decode CSV with encoding {encoding}.")
            structured_data = {} # Reset data
            skipped_lines = 0
            processed_lines = 0
            continue # Try next encoding
        except csv.Error as e:
            print(f"CSV parsing error with encoding {encoding} near line {line_num}: {e}")
            structured_data = {} # Reset data
            skipped_lines = 0
            processed_lines = 0
            continue # Try next encoding
        except Exception as e:
            print(f"An unexpected error occurred during CSV reading/processing with encoding {encoding}: {e}")
            # Optionally re-raise if it's a critical error: raise e
            structured_data = {} # Reset data
            skipped_lines = 0
            processed_lines = 0
            continue # Try next encoding

    # Proceed only if reading was successful and data was extracted
    if read_successful and structured_data:
        # Sort the year data within each index_name list
        print("Sorting data by year...")
        for country in structured_data:
            for index_name in structured_data[country]:
                # Sort by year (as integers)
                try:
                    structured_data[country][index_name].sort(key=lambda x: int(x['year']))
                except ValueError as e:
                    print(f"Error sorting data for {country} - {index_name}: Invalid year found? {e}")
                    # Decide how to handle: skip sorting for this entry, remove entry, etc.

        # Write the structured data to a JSON file
        try:
            print(f"Writing structured data to JSON: {json_file_path}")
            with open(json_file_path, mode='w', encoding='utf-8') as jsonfile:
                json.dump(structured_data, jsonfile, ensure_ascii=False, indent=4)
            print(f"Successfully converted CSV to JSON.")
            print(f"Total countries processed: {len(structured_data)}")

        except IOError as e:
            print(f"Error writing JSON file: {e}")
        except TypeError as e:
             print(f"Error during JSON serialization (possibly due to data types): {e}")
        except Exception as e:
            print(f"An unexpected error occurred during JSON writing: {e}")

    elif not read_successful:
        print("Failed to read or process the CSV file with all attempted encodings.")
    else: # read_successful is True but structured_data is empty
         print("CSV processed, but no valid data found to write to JSON.") 