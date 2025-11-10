from ast import main
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

model_dir = "iic/SenseVoiceSmall"

model = AutoModel(
    model=model_dir,
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
)

def speech_to_text_api(audio_file_path: str) -> str:
    res = model.generate(
        input=audio_file_path,
        cache={},
        language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,  #
        merge_length_s=15,
    )
    text = rich_transcription_postprocess(res[0]["text"])
    return text


if __name__ == "__main__":
    audio_file_path = "basic_output.wav"
    text = speech_to_text_api(audio_file_path)
    print(text)
