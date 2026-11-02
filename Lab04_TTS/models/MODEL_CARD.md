---
language:
- vi
license: other
library_name: sherpa-onnx
pipeline_tag: text-to-speech
tags:
- piper
- vits
- onnx
- vietnamese
- tts
---

# Vietnamese Piper voices (medium)

Three single-speaker Vietnamese narrator voices in Piper/VITS format (22,050 Hz, ~63 MB each), ready for
[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx): the `.onnx` files carry sherpa-onnx metadata and each
folder ships a `tokens.txt`. Phonemization uses eSpeak NG (`vi`); `espeak-ng-data` is not included.

| Folder | Voice |
|---|---|
| `vits-piper-vi_VN-tramvang-medium` | Male, Northern accent, deep and resonant storyteller |
| `vits-piper-vi_VN-diemdam-medium` | Male, Northern accent, calm and mellow |
| `vits-piper-vi_VN-altotram-medium` | Female, Northern accent, warm low alto |

None of the voices belongs to a real person: each was designed from a text description with
VoxCPM2 Voice Design.

## Usage (sherpa-onnx, Python)

```python
import sherpa_onnx
d = "vits-piper-vi_VN-altotram-medium"
tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
        model=f"{d}/vi_VN-altotram-medium.onnx", tokens=f"{d}/tokens.txt",
        data_dir="espeak-ng-data"))))
audio = tts.generate("Xin chào, đây là giọng đọc tiếng Việt.", sid=0, speed=1.0)
```

## How they were made

1. **Training data.** For each voice, roughly 5,000 Vietnamese sentences were synthesized with
   [VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) (Apache-2.0). About 30% of the sentences contain English
   names and terms, so the voices learn eSpeak's English phonemes. Every clip was transcribed back with Whisper,
   and clips with a high character error rate, an off-target pitch or an outlier speaking rate were discarded.
2. **Training.** Each voice was fine-tuned with [piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) for
   80 epochs, starting from an earlier Vietnamese Piper checkpoint.

## Lineage and license

The warm-start checkpoint descends from Piper's `vi_VN-vais1000-medium`. That voice was trained on the
[VAIS-1000 corpus](https://ieee-dataport.org/documents/vais-1000-vietnamese-speech-synthesis-corpus)
(CC BY 4.0) and was itself fine-tuned from Piper's `en_US-lessac-medium`. The Lessac / Blizzard 2013 data
behind `en_US-lessac-medium` is licensed for research use only. Check whether that lineage is acceptable for
your use before relying on these weights.
