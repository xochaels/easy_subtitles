import os
import html
import chardet


total_shifted_milliseconds = {}

def shift_subtitle(subtitle_file, milliseconds):
    global total_shifted_milliseconds
    try:
        with open(subtitle_file, 'rb') as file:
            raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding']
            lines = raw_data.decode(encoding).splitlines()
    except Exception as e:
        print(f"Error loading subtitle file: {str(e)}", "error")
        return

    directory_path = os.path.dirname(subtitle_file)
    filename = os.path.basename(subtitle_file)
    new_lines = []

    # Calculate total shifted milliseconds for the current subtitle file
    if subtitle_file in total_shifted_milliseconds:
        total_shifted = total_shifted_milliseconds[subtitle_file] + milliseconds
    else:
        total_shifted = milliseconds

    for raw_line in lines:
        if isinstance(raw_line, bytes):  # Check if line is still bytes and needs decoding
            try:
                line = raw_line.decode(encoding)
            except UnicodeDecodeError:
                print("Error decoding line, skipping...", "error")
                continue
        else:
            line = raw_line

        if '-->' in line:  # Check if the line contains time information
            parts = line.strip().split(' --> ')
            start_time, end_time = parts

            # Parse time string to milliseconds
            start_hours, start_minutes, start_seconds_milliseconds = start_time.split(':')
            end_hours, end_minutes, end_seconds_milliseconds = end_time.split(':')
            start_seconds, start_milliseconds = start_seconds_milliseconds.split(',')
            end_seconds, end_milliseconds = end_seconds_milliseconds.split(',')

            start_total_milliseconds = (int(start_hours) * 3600 + int(start_minutes) * 60 + int(start_seconds)) * 1000 + int(start_milliseconds)
            end_total_milliseconds = (int(end_hours) * 3600 + int(end_minutes) * 60 + int(end_seconds)) * 1000 + int(end_milliseconds)

            # Shift the time by the specified milliseconds
            start_total_milliseconds += milliseconds
            end_total_milliseconds += milliseconds

            # Convert negative milliseconds to positive if needed
            start_total_milliseconds = max(start_total_milliseconds, 0)
            end_total_milliseconds = max(end_total_milliseconds, 0)

            # Convert milliseconds to time string format
            shifted_start_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                (start_total_milliseconds // 3600000),
                (start_total_milliseconds // 60000) % 60,
                (start_total_milliseconds // 1000) % 60,
                start_total_milliseconds % 1000
            )
            shifted_end_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                (end_total_milliseconds // 3600000),
                (end_total_milliseconds // 60000) % 60,
                (end_total_milliseconds // 1000) % 60,
                end_total_milliseconds % 1000
            )

            new_line = f"{shifted_start_time} --> {shifted_end_time}"
            new_lines.append(new_line)
        else:
            # Preserve HTML tags in subtitle text
            line = html.unescape(line)
            new_lines.append(line)

    desktop_path = os.path.join(os.getcwd(),directory_path)
    new_subtitle_file = os.path.join(desktop_path, f"{total_shifted}ms_{filename}")

    try:
        with open(new_subtitle_file, 'wb') as file:
            file.write('\n'.join(new_lines).encode(encoding))
        total_shifted_milliseconds[subtitle_file] = total_shifted
    except Exception as e:
        print(f"Error saving subtitle file: {str(e)}", "error")

if __name__ == "__main__":
    shift_subtitle('downloaded_srt_eng/episode_1.srt',1000)
    #00:01:41,894 --> 00:01:43,604





