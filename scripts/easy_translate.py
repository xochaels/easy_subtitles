import pysrt
from easygoogletranslate import EasyGoogleTranslate
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def batch_translate(translator, texts, target_language):
    concatenated_text = "\n".join(texts)
    translated_text = translator.translate(concatenated_text)
    return translated_text.split('\n')


def translate_subtitles(subtitle_path, target_path, *, target_language):
    subs = pysrt.open(subtitle_path)
    translator = EasyGoogleTranslate(target_language=target_language, timeout=10)

    max_workers = 10
    batch_size = 100

    batches = [subs[i:i + batch_size] for i in range(0, len(subs), batch_size)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(batch_translate, translator, [sub.text for sub in batch], target_language): batch
            for batch in batches
        }

        with tqdm(total=len(subs), desc="Translating subtitles", unit="sub") as pbar:
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                translated_texts = future.result()

                for sub, translated_text in zip(batch, translated_texts):
                    sub.text = translated_text

                pbar.update(len(batch))

    subs.save(target_path, encoding='utf-8')
