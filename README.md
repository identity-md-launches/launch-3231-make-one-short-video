# Two swarms, one card

**Video:** [artifacts/two_swarms_one_card.mp4](artifacts/two_swarms_one_card.mp4)  
**Narration script:** [artifacts/narration.txt](artifacts/narration.txt)

The clip is 58.262 seconds, 1920 × 1080 pixels (16:9), 24 frames per second. The MP4 contains H.264 video in yuv420p and AAC mono audio at 48 kHz, with the moov atom at the front for browser playback. Captions are burned into the picture.

The narration uses the sal voice from xAI Grok text to speech, sped to 1.12 times its generated pace to fit the requested runtime. A quiet synthesized chord sits beneath it. The character and all motion graphics were drawn for this video; plain text identifies the two swarms.

Limitations: the voice is synthetic, and captions change by phrase rather than by individual word. The illustrations are a conceptual pitch. The required unofficial pitch label appears for the opening two seconds and on the end card.

The checked MP4 is 5,696,774 bytes. The render source is [src/render.py](src/render.py); its compact AAC narration and scene timing inputs are in [assets](assets). Rendering requires Python 3 with Pillow and ffmpeg.
