import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from gtts import gTTS

# Configurable parameters
INPUT_IMAGE = "input.jpg"   
OUTPUT_VIDEO = "output.mp4"  
BACKGROUND_MUSIC = "background.mp3"  
OVERLAY_TEXT = "This is the overlay text."
CAPTION_TEXT = "Hello, this is the Engineering building on my campus."  # Used for both narration & captions
FONT_PATH = "resources/Roboto-Bold.ttf"  
DURATION = 10  
CAPTION_START = 1 # Start showing captions at 1 sec.
CAPTION_COLOR = "yellow" # Change as needed

# Step 1: Load Image and Apply Transformations
print("Loading and transforming image...")
image = Image.open(INPUT_IMAGE)
image = image.convert("L")  
image = ImageEnhance.Contrast(image).enhance(1.5)  
image = image.rotate(90)

# Step 2: Overlay Text on Image (For Debugging)
draw = ImageDraw.Draw(image)
try:
    font = ImageFont.truetype(FONT_PATH, 100)
except IOError:
    print("Warning: Font file not found, using default font.")
    font = ImageFont.load_default()

draw.text((50, 50), OVERLAY_TEXT, font=font, fill="white")
transformed_image_path = "transformed_image.jpg"
image.save(transformed_image_path)
print("Image transformation complete.")

# Step 2: Generate Voice Narration
print("Generating voice narration...")
narration_audio = "narration.mp3"
tts = gTTS(CAPTION_TEXT)
tts.save(narration_audio)

# Step 3: Process Audio
print("Processing audio files...")
processed_narration, processed_music = "processed_narration.mp3", "processed_music.mp3"
mono_narration, mono_music, mixed_audio = "mono_narration.mp3", "mono_music.mp3", "mixed_audio.mp3"

subprocess.run(["ffmpeg", "-y", "-i", narration_audio, "-af", f"apad=pad_dur={DURATION-0.5}:whole_dur={DURATION}", "-t", str(DURATION), "-c:a", "libmp3lame", processed_narration])
subprocess.run(["ffmpeg", "-y", "-i", BACKGROUND_MUSIC, "-t", str(DURATION), "-c:a", "libmp3lame", processed_music])
subprocess.run(["ffmpeg", "-y", "-i", processed_narration, "-ac", "1", "-c:a", "libmp3lame", mono_narration])
subprocess.run(["ffmpeg", "-y", "-i", processed_music, "-ac", "1", "-c:a", "libmp3lame", mono_music])

print("Mixing audio files...")
subprocess.run(["ffmpeg", "-y", "-i", mono_narration, "-i", mono_music, "-filter_complex", "[0:a]volume=1.0[a1]; [1:a]volume=0.5[a2]; [a1][a2]amix=inputs=2:duration=first[a]", "-map", "[a]", "-c:a", "libmp3lame", mixed_audio])

# Step 4: Create Video
print("Creating video from image...")
subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(DURATION), "-i", transformed_image_path, "-vf", "scale=1280:720", "-c:v", "libx264", "-pix_fmt", "yuv420p", "temp_video.mp4"])

# Step 5: Generate FFmpeg DrawText for Word-by-Word Captions
words = CAPTION_TEXT.split()
caption_commands = []
word_duration = DURATION / (len(words) + 1)  # Time each word stays visible

for i, word in enumerate(words):
    start_time = CAPTION_START + i * word_duration
    end_time = start_time + word_duration
    caption_commands.append(f"drawtext=text='{word}':fontfile={FONT_PATH}:fontsize=40:fontcolor={CAPTION_COLOR}:x=(w-text_w)/2:y=h-100:enable='between(t,{start_time},{end_time})'")

captions_filter = ",".join(caption_commands)

# Step 6: Apply Captions
print("Adding animated captions...")
captions_video = "video_with_captions.mp4"
subprocess.run(["ffmpeg", "-y", "-i", "temp_video.mp4", "-vf", captions_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", captions_video])

# Step 7: Merge Video with Audio
print("Merging final video with audio...")
subprocess.run(["ffmpeg", "-y", "-i", captions_video, "-i", mixed_audio, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", "-map", "0:v:0", "-map", "1:a:0", OUTPUT_VIDEO])

# Step 8: Cleanup
for f in ["temp_video.mp4", captions_video, processed_narration, processed_music, mono_narration, mono_music, mixed_audio, narration_audio, transformed_image_path]:
    os.remove(f)

print(f"Video generated successfully: {OUTPUT_VIDEO}")
