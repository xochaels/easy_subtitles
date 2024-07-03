import os
import json
import time
from openai import OpenAI
from pysrt import SubRipFile, SubRipItem
import pysrt

# Load configuration
with open('./config.json', 'r') as f:
    config = json.load(f)

# Initialize OpenAI API
openai_api_key = config['OPENAI_API_KEY']
openai = OpenAI(api_key=openai_api_key)

# Directory paths
src_dir = './src'
res_dir = './res'

# Supported subtitle extensions
support_extensions = ['srt', 'vtt']

# Get list of subtitle files
subtitle_files = [f for f in os.listdir(src_dir) if f.split('.')[-1] in support_extensions]


def translate_subtitles(subtitle_file):
    # Read and parse subtitle file
    subtitle_path = os.path.join(src_dir, subtitle_file)
    subs = pysrt.open(subtitle_path)

    previous_subtitles = []
    target_language = config['TARGET_LANGUAGE']

    for i, sub in enumerate(subs):
        text = sub.text
        input_data = {'Input': text}

        if i + 1 < len(subs):
            input_data['Next'] = subs[i + 1].text

        while True:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a program responsible for translating subtitles. Your task is to output "
                                f"the specified target language based on the input text. Please do not create the "
                                f"following subtitles on your own. Please do not output any text other than the translation. "
                                f"You will receive the subtitles as array that needs to be translated, as well as the previous "
                                f"translation results and next subtitle. If you need to merge the subtitles with the following "
                                f"line, simply repeat the translation. Please transliterate the person's name into the local "
                                f"language. Target language: {target_language}"
                            )
                        },
                        *previous_subtitles[-4:],
                        {
                            "role": "user",
                            "content": json.dumps(input_data)
                        }
                    ],
                    timeout=60
                )
                break
            except Exception as e:
                print(f"Error: {e}")
                print('retrying...')

        result = response['choices'][0]['message']['content']

        try:
            result = json.loads(result)['Input']
        except json.JSONDecodeError:
            try:
                result = re.search(r'"Input":"(.*?)"', result).group(1)
            except Exception as e:
                print('###')
                print(e)
                print(result)
                print('###')

        previous_subtitles.append({"role": "user", "content": json.dumps(input_data)})
        previous_subtitles.append({"role": 'assistant', "content": json.dumps({**input_data, 'Input': result})})

        sub.text = f"{result}\n{text}"

        print('-----------------')
        print(f"{i + 1} / {len(subs)}")
        print(f"{result}")
        print(f"{text}")

    # Write translated subtitles to file
    res_path = os.path.join(res_dir, subtitle_file)
    subs.save(res_path, encoding='utf-8')


# Process each subtitle file
for subtitle_file in subtitle_files:
    translate_subtitles(subtitle_file)
