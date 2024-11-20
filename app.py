import streamlit as st
import subprocess
import zipfile
import logging
from pathlib import Path
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Function to apply ReplayGain to MP3 files
def apply_replaygain(output_dir):
    logger.info("Applying ReplayGain to MP3 files.")
    mp3_files = list(output_dir.glob("*.mp3"))
    for mp3_file in mp3_files:
        try:
            subprocess.run(
                ["mp3gain", "-r", "-k", str(mp3_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"ReplayGain applied to {mp3_file.name}.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply ReplayGain to {mp3_file.name}: {e}")

# Function to process FLAC files and convert them to MP3
def process_files(flac_files, output_dir):
    logger.info("Processing FLAC files and converting them to MP3.")
    flac_files = list(set(flac_files))  # Deduplicate files
    for flac_file in flac_files:
        output_file = output_dir / flac_file.with_suffix(".mp3").name
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(flac_file), "-map_metadata", "0", str(output_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"Converted {flac_file.name} to {output_file.name}.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing {flac_file.name}: {e}")
    apply_replaygain(output_dir)

# Function to clear directories
def clear_directories(temp_dir, output_dir):
    logger.info("Clearing temporary and output directories.")
    for dir_path in [temp_dir, output_dir]:
        for file in dir_path.glob("*"):
            if file.suffix.lower() in [".flac", ".mp3", ".zip"]:
                file.unlink()
                logger.info(f"Deleted file: {file.name}")

# Function to validate CUE and FLAC match by comparing duration
def validate_cue_and_flac(cue_file, flac_file):
    try:
        # Read the cue file to extract the duration information
        with open(cue_file, 'r') as cue:
            cue_content = cue.read()

        # Extract duration from CUE file using regex
        duration_match = re.search(r"duration=(\d+\.\d+)", cue_content)
        if duration_match:
            cue_duration = float(duration_match.group(1))  # Convert to float
        else:
            raise ValueError("Duration not found in CUE file.")

        # Use ffmpeg to extract duration from FLAC file
        flac_duration_command = ["ffmpeg", "-i", str(flac_file), "-f", "null", "-"]
        result = subprocess.run(flac_duration_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        flac_duration_output = result.stderr.decode('utf-8')
        flac_duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", flac_duration_output)
        if flac_duration_match:
            flac_duration = float(flac_duration_match.group(1)) * 3600 + float(flac_duration_match.group(2)) * 60 + float(flac_duration_match.group(3))
        else:
            raise ValueError("Duration not found for FLAC file.")

        # Compare durations (e.g., if they match within a small tolerance)
        if abs(cue_duration - flac_duration) > 1.0:  # Adjust tolerance as needed
            raise ValueError("CUE file does not match the FLAC file. Skipping processing.")

    except Exception as e:
        logger.error(f"Error while validating CUE and FLAC match: {e}")
        return False
    return True

# Main Streamlit app
def main():
    st.title("FLAC to MP3 Converter with ReplayGain")

    temp_dir = Path("/tmp/flac_to_mp3")
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize uploader key in session state
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # Clear uploads button
    if st.button("Clear Uploads"):
        st.session_state.uploader_key += 1  # Increment key to reset uploader
        clear_directories(temp_dir, output_dir)
        st.write("Uploads cleared!")

    # File uploader with dynamic key
    uploaded_files = st.file_uploader(
        "Upload FLAC files or ZIPs",
        type=["flac", "zip", "cue"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )

    processing_success = True  # Flag to track processing status

    # Process files when the button is clicked
    if st.button("Process Files"):
        if uploaded_files:
            clear_directories(temp_dir, output_dir)  # Remove existing files in directories
            flac_files = []
            cue_file = None
            logger.info("Processing uploaded files.")
            for uploaded_file in uploaded_files:
                try:
                    # Handle ZIP files
                    if uploaded_file.name.endswith(".zip"):
                        zip_path = temp_dir / uploaded_file.name
                        with open(zip_path, "wb") as f:
                            f.write(uploaded_file.read())
                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(temp_dir)
                        flac_files.extend([file for file in temp_dir.glob("*.flac")])
                        # Check if CUE file is in the ZIP
                        cue_file = next((file for file in temp_dir.glob("*.cue")), None)

                    # Handle individual FLAC files
                    else:
                        file_path = temp_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.read())
                        flac_files.append(file_path)

                except Exception as e:
                    logger.error(f"Error processing {uploaded_file.name}: {e}")
                    processing_success = False

            # Validate CUE and FLAC match if both files exist
            if cue_file and flac_files and processing_success:
                if not validate_cue_and_flac(cue_file, flac_files[0]):
                    logger.error("CUE and FLAC file mismatch detected. Skipping processing.")
                    st.error("CUE and FLAC file mismatch detected. Skipping processing.")
                    processing_success = False

            # Process files if FLAC files exist and no errors occurred
            if flac_files and processing_success:
                process_files(flac_files, output_dir)

                # Provide download button for ZIP of processed files
                zip_file = output_dir / "processed_files.zip"
                with zipfile.ZipFile(zip_file, "w") as zipf:
                    for mp3_file in output_dir.glob("*.mp3"):
                        zipf.write(mp3_file, arcname=mp3_file.name)
                        logger.info(f"Added {mp3_file.name} to ZIP.")
                with open(zip_file, "rb") as f:
                    st.download_button(
                        "Download Processed Files",
                        data=f,
                        file_name="processed_files.zip",
                    )
            else:
                logger.warning("No valid FLAC files found or processing failed.")
                st.warning("No valid FLAC files found or an error occurred during processing.")
        else:
            logger.warning("No files uploaded.")
            st.warning("No files uploaded.")

if __name__ == "__main__":
    main()
