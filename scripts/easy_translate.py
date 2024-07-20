import pysrt
from easygoogletranslate import EasyGoogleTranslate
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def translate_text(translator, text, target_language):
    return translator.translate(text, target_language)

def translate_subtitles(subtitle_path, target_path, *, target_language):
    subs = pysrt.open(subtitle_path)
    translator = EasyGoogleTranslate(target_language=target_language, timeout=10)

    max_workers = 10

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(translate_text, translator, sub.text, target_language): sub
            for sub in subs
        }

        with tqdm(total=len(subs), desc="Translating subtitles", unit="sub") as pbar:
            for future in as_completed(futures):
                sub = futures[future]
                try:
                    translated_text = future.result()
                    sub.text = translated_text
                except Exception as e:
                    print(f"Failed to translate subtitle: {e}")
                finally:
                    pbar.update(1)

    subs.save(target_path, encoding='utf-8')
