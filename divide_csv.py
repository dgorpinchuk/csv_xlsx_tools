import os
import csv

INPUT_FILE = 'merged_output.csv'  # замените на ваш путь к файлу
OUTPUT_DIR = 'output'
MAX_SIZE_MB = 20
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

os.makedirs(OUTPUT_DIR, exist_ok=True)

def split_csv(input_file, output_dir, max_size_bytes):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)

        file_index = 1
        outfile_path = os.path.join(output_dir, f'part_{file_index}.csv')
        outfile = open(outfile_path, 'w', newline='', encoding='utf-8')
        writer = csv.writer(outfile)
        writer.writerow(header)

        current_size = outfile.tell()

        for row in reader:
            writer.writerow(row)
            current_size = outfile.tell()

            if current_size >= max_size_bytes:
                outfile.close()
                file_index += 1
                outfile_path = os.path.join(output_dir, f'part_{file_index}.csv')
                outfile = open(outfile_path, 'w', newline='', encoding='utf-8')
                writer = csv.writer(outfile)
                writer.writerow(header)
                current_size = outfile.tell()

        outfile.close()

split_csv(INPUT_FILE, OUTPUT_DIR, MAX_SIZE_BYTES)
