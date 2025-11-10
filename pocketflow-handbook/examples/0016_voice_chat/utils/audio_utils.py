import sounddevice as sd
import numpy as np

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_SIZE_MS = 50  # Process audio in 50ms chunks for VAD
DEFAULT_SILENCE_THRESHOLD_RMS = 0.01 # RMS value, needs tuning
DEFAULT_MIN_SILENCE_DURATION_MS = 1000 # 1 second of silence to stop
DEFAULT_MAX_RECORDING_DURATION_S = 15 # Safety cap for recording
DEFAULT_PRE_ROLL_CHUNKS = 3 # Number of chunks to keep before speech starts

def record_audio(sample_rate = DEFAULT_SAMPLE_RATE,
                 channels = DEFAULT_CHANNELS,
                 chunk_size_ms = DEFAULT_CHUNK_SIZE_MS,
                 silence_threshold_rms = DEFAULT_SILENCE_THRESHOLD_RMS,
                 min_silence_duration_ms = DEFAULT_MIN_SILENCE_DURATION_MS,
                 max_recording_duration_s = DEFAULT_MAX_RECORDING_DURATION_S,
                 pre_roll_chunks_count = DEFAULT_PRE_ROLL_CHUNKS):
    """
    Records audio from the microphone with silence-based VAD.
    Returns in-memory audio data (NumPy array of float32) and sample rate.
    Returns (None, sample_rate) if recording fails or max duration is met without speech.
    """
    chunk_size_frames = int(sample_rate * chunk_size_ms / 1000)
    min_silence_chunks = int(min_silence_duration_ms / chunk_size_ms)
    max_chunks = int(max_recording_duration_s * 1000 / chunk_size_ms)

    print(f"Listening... (max {max_recording_duration_s}s). Speak when ready.")
    print(f"(Silence threshold RMS: {silence_threshold_rms}, Min silence duration: {min_silence_duration_ms}ms)")

    recorded_frames = []
    pre_roll_frames = []
    is_recording = False
    silence_counter = 0
    chunks_recorded = 0

    with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='float32') as stream:

        for i in range(max_chunks):
            audio_chunk, overflowed = stream.read(chunk_size_frames)
            if overflowed:
                print("Warning: Audio buffer overflowed!")
            
            rms = np.sqrt(np.mean(audio_chunk**2))

            if is_recording:
                recorded_frames.append(audio_chunk)
                chunks_recorded += 1
                if rms < silence_threshold_rms:
                    silence_counter += 1
                    if silence_counter >= min_silence_chunks:
                        print("Silence detected, stopping recording.")
                        break
                else:
                    silence_counter = 0 # Reset silence counter on sound
            else:
                pre_roll_frames.append(audio_chunk)
                if len(pre_roll_frames) > pre_roll_chunks_count:
                    pre_roll_frames.pop(0)
                
                if rms > silence_threshold_rms:
                    print("Speech detected, starting recording.")
                    is_recording = True
                    for frame_to_add in pre_roll_frames:
                        recorded_frames.append(frame_to_add)
                    chunks_recorded = len(recorded_frames)
                    pre_roll_frames.clear()
            
            if i == max_chunks - 1 and not is_recording:
                print("No speech detected within the maximum recording duration.")
                return None, sample_rate

        if not recorded_frames and is_recording:
            print("Recording started but captured no frames before stopping. This might be due to immediate silence.")

    if not recorded_frames:
        print("No audio was recorded.")
        return None, sample_rate

    audio_data = np.concatenate(recorded_frames)
    print(f"Recording finished. Total duration: {len(audio_data)/sample_rate:.2f}s")
    return audio_data, sample_rate

def play_audio_data(audio_data, sample_rate, device=None):
    """Plays in-memory audio data (NumPy array) with fallback to file saving.
    
    Args:
        audio_data: NumPy array containing audio samples
        sample_rate: Sample rate in Hz
        device: Optional device index or None to use default
    """
    print(f"Playing in-memory audio data (Sample rate: {sample_rate} Hz, Duration: {len(audio_data)/sample_rate:.2f}s)")
    
    # 尝试播放音频，但不抛出异常
    try:
        # 简化设备设置，避免复杂的设备索引操作
        if device is not None:
            try:
                sd.play(audio_data, sample_rate, device=device)
                print(f"Using specified audio device: {device}")
            except Exception as device_error:
                print(f"Failed to use specified device {device}: {device_error}")
                print("Falling back to default device")
                # 尝试不带设备参数直接播放
                sd.play(audio_data, sample_rate)
        else:
            # 直接使用默认设置播放，不尝试复杂的设备查询
            sd.play(audio_data, sample_rate)
        
        # 等待播放完成
        try:
            sd.wait()
            print("Playback from memory finished successfully.")
            return  # 播放成功，提前返回
        except Exception as wait_error:
            print(f"Playback wait error: {wait_error}")
            # 继续执行，尝试保存到文件
    except Exception as e:
        print(f"Audio playback failed: {e}")
    
    # 如果播放失败，保存音频到文件作为备选
    print("Audio playback skipped or failed.")
    try:
        import scipy.io.wavfile
        import os
        # 生成唯一的文件名，使用时间戳避免命名冲突
        import time
        timestamp = int(time.time())
        output_filename = f"audio_output_{timestamp}.wav"
        
        # 确保音频数据格式正确 - wav文件通常需要16位整数格式
        try:
            # 检查音频数据类型，如果是浮点数，转换为16位整数
            if np.issubdtype(audio_data.dtype, np.floating):
                # 归一化到[-1, 1]范围
                audio_data = audio_data / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else audio_data
                # 转换为16位整数
                audio_data = (audio_data * 32767).astype(np.int16)
            elif not np.issubdtype(audio_data.dtype, np.integer):
                # 如果不是整数也不是浮点数，尝试转换为16位整数
                audio_data = audio_data.astype(np.int16)
            
            # 保存音频到文件
            scipy.io.wavfile.write(output_filename, sample_rate, audio_data)
            print(f"音频数据成功保存为WAV文件: {output_filename}")
            print(f"保存参数: 采样率={sample_rate} Hz, 数据类型={audio_data.dtype}")
        except Exception as write_error:
            print(f"写入WAV文件时出错: {write_error}")
            # 尝试使用更简单的格式进行保存
            try:
                # 创建一个简单的正弦波作为测试，验证保存功能
                test_audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.int16)
                test_filename = f"test_audio_{timestamp}.wav"
                scipy.io.wavfile.write(test_filename, 44100, test_audio)
                print(f"已创建测试音频文件以验证保存功能: {test_filename}")
            except:
                print("无法创建测试音频文件")
    except Exception as save_error:
        print(f"Failed to save audio to file as fallback: {save_error}")


if __name__ == "__main__":
    print("--- Testing audio_utils.py ---")

    # Test 1: record_audio() and play_audio_data() (in-memory)
    print("\n--- Test: Record and Play In-Memory Audio ---")
    print("Please speak into the microphone. Recording will start on sound and stop on silence.")
    recorded_audio, rec_sr = record_audio(
        sample_rate=DEFAULT_SAMPLE_RATE,
        silence_threshold_rms=0.02, 
        min_silence_duration_ms=1500,
        max_recording_duration_s=10
    )

    if recorded_audio is not None and rec_sr is not None:
        print(f"Recorded audio data shape: {recorded_audio.shape}, Sample rate: {rec_sr} Hz")
        play_audio_data(recorded_audio, rec_sr)
    else:
        print("No audio recorded or recording failed.")

    print("\n--- audio_utils.py tests finished. ---")