import pysrt
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def llm_model(model, url, texts, target_language):
    data = {
        "model": model,
        "prompt": f"""
                        You are an API developed to translate subtitles accurately and maintain the context,
                        tone, and style of the original language. Your primary task is to translate subtitles 
                        from one language to another while preserving the original meaning and ensuring readability.
                        Example:
                        user : I got unlucky in my marriage, but I'm glad I have you.
                        assistant : Saya tidak beruntung dalam pernikahan, tapi saya senang memilikimu.
                        Task :
                        Translate the following subtitles to {target_language}.Do not explain it or adding some note.
                        Remove all of it, Only return the translated subtitles.

                        Here is the subtitle text to be translated : {texts}
                    """,
        "options": {
            "temperature": 2
        },
        "stream": False
    }

    response = requests.post(url, json=data)
    response.raise_for_status()  # Raise an exception for HTTP errors
    response_data = response.json()
    translated_text = response_data['response']

    return translated_text

def translate_subtitle_segment(model, url, subs_segment, target_language):
    for sub in subs_segment:
        sub.text = llm_model(model, url, sub.text, target_language)
    return subs_segment


def get_llm_translate(subtitle_path, target_path, *, target_language, model, url, num_workers=10):
    subs = pysrt.open(subtitle_path)
    subtitles_list = list(subs)

    # Divide the subtitles into segments for parallel processing
    segment_size = len(subtitles_list) // num_workers
    segments = [subtitles_list[i:i + segment_size] for i in range(0, len(subtitles_list), segment_size)]

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(translate_subtitle_segment, model, url, segment, target_language) for segment in
                   segments]

        with tqdm(total=len(subtitles_list), desc="Translating subtitles", unit="sub") as pbar:
            for future in as_completed(futures):
                result = future.result()
                pbar.update(len(result))

    translated_subs = [sub for segment in segments for sub in segment]
    subs = pysrt.SubRipFile(translated_subs)

    subs.save(target_path, encoding='utf-8')