# 语音转文本

| 模型/工具包 | 中文优化 | 流式支持 | 模型大小 | 部署难度 | 推荐场景 |
|------------|---------|----------|---------|----------|----------|
| FunASR | ✅ 极佳 | ✅ | 小~中 | ⭐⭐ | 通用首选（高精度+轻量） |
| Whisper 中文版 | ✅ 好 | ❌ | 大 | ⭐⭐ | 离线高精度（带标点） |
| WeNet | ✅ 好 | ✅ | 中 | ⭐⭐⭐ | 实时语音输入、低延迟 |
| PaddleSpeech | ✅ 好 | ✅ | 中 | ⭐⭐ | 百度生态、快速集成 |
| ESPnet | ⚠️ 需微调 | ✅ | 中~大 | ⭐⭐⭐⭐ | 学术研究、自定义训练 |

我们使用funasr的SenseVoiceSmall模型进行语音转文本。

安装环境：`pip3 install -U funasr -i https://pypi.tuna.tsinghua.edu.cn/simple`

# 文本转语音

| 模型名称 | 中文优化 | 质量评分 | 个性化支持 | 部署难度 | 许可证类型 | 推荐场景 |
|---------|---------|---------|-----------|----------|-----------|----------|
| ChatTTS | ✅ 极佳 | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐ | Apache 2.0 | 对话、播客、短视频 |
| PaddleSpeech | ✅ 好 | ⭐⭐⭐⭐ | ❌ | ⭐⭐ | Apache 2.0 | 工业部署、通用 TTS |
| OpenVoice | ✅ 好 | ⭐⭐⭐⭐ | ✅ 零样本 | ⭐⭐⭐ | MIT | 个性化配音、虚拟人 |
| VITS 中文版 | ⚠️ 一般 | ⭐⭐⭐⭐ | ✅（需参考音频） | ⭐⭐⭐⭐ | 多为非商用 | 研究、定制音色 |
| Coqui TTS | ✅ 有模型 | ⭐⭐⭐ | ⚠️ 有限 | ⭐⭐⭐ | MPL 2.0 | 研究、多语言 |
| Bert-VITS2 | ✅ 社区强 | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐ | 多为非商用 | 动漫配音、二次元 |

我们使用ChatTTS进行文本转语音。

安装环境：
```shell
pip3 install -U ChatTTS -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install transformers==4.53.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

