import ChatTTS
import torch
import torchaudio
import io

chat = ChatTTS.Chat()
chat.load(compile=False) # Set to True for better performance

def text_to_speech_api(text_to_synthesize: str):
    if isinstance(text_to_synthesize, str):
        texts = [text_to_synthesize]
    else:
        texts = text_to_synthesize

    wavs = chat.infer(texts)
    if not wavs:
        return None, None
    
    # ChatTTS的采样率是24000
    sample_rate = 24000
    
    # 将numpy数组转换为音频字节
    wav_tensor = torch.from_numpy(wavs[0]).unsqueeze(0)
    buffer = io.BytesIO()
    
    try:
        # 尝试使用unsqueeze格式
        torchaudio.save(buffer, wav_tensor, sample_rate, format="wav")
    except:
        # 如果失败，尝试直接使用
        wav_tensor = torch.from_numpy(wavs[0])
        torchaudio.save(buffer, wav_tensor, sample_rate, format="wav")
    
    audio_bytes = buffer.getvalue()
    return audio_bytes, sample_rate

if __name__ == "__main__":
    print("Testing Text-to-Speech API...")
    # The OpenAI client will raise an error if API key is not found or invalid.
    # No explicit check here to keep it minimal.
    text = "Hello from PocketFlow! This is a test of the text-to-speech functionality."
    wavs = chat.infer([text])
    print(wavs)
    if wavs:
        try:
            torchaudio.save(f"basic_output.wav", torch.from_numpy(wavs[0]).unsqueeze(0), 24000)
        except:
            torchaudio.save(f"basic_output.wav", torch.from_numpy(wavs[0]), 24000)
        print("Saved TTS output to basic_output.wav")
    else: 
        print("Failed to convert text to speech (API returned empty data).")