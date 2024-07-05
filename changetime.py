import html
import chardet

total_shifted_milliseconds = {}

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        return chardet.detect(raw_data)['encoding']

def read_lines(file_path, encoding):
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read().splitlines()

def convert_time_to_milliseconds(hours, minutes, seconds, milliseconds):
    return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(milliseconds)

def convert_milliseconds_to_time(ms):
    hours = ms // 3600000
    minutes = (ms // 60000) % 60
    seconds = (ms // 1000) % 60
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def shift_time(line, milliseconds):
    start_time, end_time = line.strip().split(' --> ')
    start_hours, start_minutes, start_seconds_milliseconds = start_time.split(':')
    end_hours, end_minutes, end_seconds_milliseconds = end_time.split(':')
    start_seconds, start_milliseconds = start_seconds_milliseconds.split(',')
    end_seconds, end_milliseconds = end_seconds_milliseconds.split(',')

    start_total_milliseconds = convert_time_to_milliseconds(start_hours, start_minutes, start_seconds, start_milliseconds)
    end_total_milliseconds = convert_time_to_milliseconds(end_hours, end_minutes, end_seconds, end_milliseconds)

    start_total_milliseconds = max(start_total_milliseconds + milliseconds, 0)
    end_total_milliseconds = max(end_total_milliseconds + milliseconds, 0)

    return f"{convert_milliseconds_to_time(start_total_milliseconds)} --> {convert_milliseconds_to_time(end_total_milliseconds)}"

def shift_subtitle(subtitle_file, output_path, *, milliseconds):
    global total_shifted_milliseconds

    try:
        encoding = detect_encoding(subtitle_file)
        lines = read_lines(subtitle_file, encoding)
    except Exception as e:
        print(f"Error loading subtitle file: {str(e)}")
        return

    if subtitle_file in total_shifted_milliseconds:
        total_shifted = total_shifted_milliseconds[subtitle_file] + milliseconds
    else:
        total_shifted = milliseconds

    new_lines = []
    for line in lines:
        if '-->' in line:
            new_lines.append(shift_time(line, milliseconds))
        else:
            new_lines.append(html.unescape(line))

    try:
        with open(output_path, 'w', encoding=encoding) as file:
            file.write('\n'.join(new_lines))
        total_shifted_milliseconds[subtitle_file] = total_shifted
    except Exception as e:
        print(f"Error saving subtitle file: {str(e)}")
