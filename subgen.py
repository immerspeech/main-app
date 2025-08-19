import datetime
import json


def read_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(data)
        return data
    except FileNotFoundError:
        print(f"Error: The file at '{filepath}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at '{filepath}'.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def create_srt_from_json_data(json_data, output_srt_filepath):
    """
    Converts a list of dictionaries (with 'start', 'end', 'text' keys)
    into a standard .srt subtitle file.

    Args:
        json_data (list): A list of dictionaries, where each dictionary
                          represents a subtitle entry with 'start' (float, seconds),
                          'end' (float, seconds), and 'text' (str) keys.
        output_srt_filepath (str): The path to the output .srt file.

    Returns:
        bool: True if the SRT file was created successfully, False otherwise.
    """
    if not isinstance(json_data, list):
        print("Error: Input json_data must be a list.")
        return False

    try:
        with open(output_srt_filepath, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(json_data):
                # Ensure required keys exist
                if not all(k in entry for k in ['start', 'end', 'text']):
                    print(f"Warning: Skipping entry {i} due to missing 'start', 'end', or 'text' key: {entry}")
                    continue

                # Get start and end times in seconds (float)
                start_seconds = entry['start']
                end_seconds = 0.0
                # if (i+1 < len(json_data)):
                #     end_seconds = json_data[i+1]['start']
                # else:
                #     end_seconds = entry['end']
                end_seconds = entry['end']
                text = entry['text']

                # Format time to SRT standard: HH:MM:SS,ms
                # Using datetime.timedelta for robust time calculations
                start_timedelta = datetime.timedelta(seconds=start_seconds)
                end_timedelta = datetime.timedelta(seconds=end_seconds)

                # Split seconds into hours, minutes, seconds, milliseconds
                # For start time
                hours_start, remainder_start = divmod(start_timedelta.total_seconds(), 3600)
                minutes_start, seconds_start = divmod(remainder_start, 60)
                milliseconds_start = int((seconds_start - int(seconds_start)) * 1000)
                seconds_start = int(seconds_start)

                # For end time
                hours_end, remainder_end = divmod(end_timedelta.total_seconds(), 3600)
                minutes_end, seconds_end = divmod(remainder_end, 60)
                milliseconds_end = int((seconds_end - int(seconds_end)) * 1000)
                seconds_end = int(seconds_end)

                # Format as HH:MM:SS,ms
                start_time_str = f"{int(hours_start):02}:{int(minutes_start):02}:{int(seconds_start):02},{milliseconds_start:03}"
                end_time_str = f"{int(hours_end):02}:{int(minutes_end):02}:{int(seconds_end):02},{milliseconds_end:03}"

                # Write to file
                f.write(f"{i + 1}\n")  # Subtitle index (starts from 1)
                f.write(f"{start_time_str} --> {end_time_str}\n")
                f.write(f"{text}\n\n")

        print(f"Successfully created SRT file: {output_srt_filepath}")
        return True
    except IOError as e:
        print(f"Error writing to file '{output_srt_filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during SRT creation: {e}")
        return False


def group_and_create_srt(word_level_data, output_srt_filepath, group_size=3):

    if not isinstance(word_level_data, list):
        print("Error: Input word_level_data must be a list.")
        return False
    if not all(isinstance(d, dict) and 'start' in d and 'end' in d and 'text' in d for d in word_level_data):
        print("Error: Each item in word_level_data must be a dictionary with 'start', 'end', and 'text' keys.")
        return False
    if not isinstance(group_size, int) or group_size <= 0:
        print("Error: group_size must be a positive integer.")
        return False

    grouped_subtitles = []
    current_group_texts = []
    group_start_time = -1.0
    group_end_time = -1.0

    for i, word_info in enumerate(word_level_data):
        if group_start_time == -1.0:
            group_start_time = word_info['start']

        current_group_texts.append(word_info['text'])
        group_end_time = 0.0
        # if (i+1 < len(word_level_data)):
        #     group_end_time = word_level_data[i+1]['start']
        # else:
        #     group_end_time = word_info['end']
        group_end_time = word_info['end']

        if (i + 1) % group_size == 0 or (i + 1) == len(word_level_data):
            combined_text = " ".join(current_group_texts)
            grouped_subtitles.append({
                "start": group_start_time,
                "end": group_end_time,
                "text": combined_text.strip() # .strip() removes leading/trailing whitespace
            })
            current_group_texts = []
            group_start_time = -1.0
            group_end_time = -1.0 

    try:
        with open(output_srt_filepath, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(grouped_subtitles):
                start_seconds = entry['start']
                end_seconds = 0.0
                # if (i+1 < len(grouped_subtitles)):
                #     end_seconds = grouped_subtitles[i+1]['start']
                # else:
                #     end_seconds = entry['end']
                end_seconds = entry['end']
                text = entry['text']

                start_timedelta = datetime.timedelta(seconds=start_seconds)
                end_timedelta = datetime.timedelta(seconds=end_seconds)

                hours_start, remainder_start = divmod(start_timedelta.total_seconds(), 3600)
                minutes_start, seconds_start = divmod(remainder_start, 60)
                milliseconds_start = int((seconds_start - int(seconds_start)) * 1000)
                seconds_start = int(seconds_start)

                hours_end, remainder_end = divmod(end_timedelta.total_seconds(), 3600)
                minutes_end, seconds_end = divmod(remainder_end, 60)
                milliseconds_end = int((seconds_end - int(seconds_end)) * 1000)
                seconds_end = int(seconds_end)

                start_time_str = f"{int(hours_start):02}:{int(minutes_start):02}:{int(seconds_start):02},{milliseconds_start:03}"
                end_time_str = f"{int(hours_end):02}:{int(minutes_end):02}:{int(seconds_end):02},{milliseconds_end:03}"

                f.write(f"{i + 1}\n")
                f.write(f"{start_time_str} --> {end_time_str}\n")
                f.write(f"{text}\n\n")

        print(f"Successfully created SRT file with grouped subtitles: {output_srt_filepath}")
        return True
    except IOError as e:
        print(f"Error writing to file '{output_srt_filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during SRT creation: {e}")
        return False

STT_FILENAME = "ravdees_alignment_src.json"


if __name__ == "__main__":

    file_name = STT_FILENAME
    json_content = read_json_file(file_name)

    if json_content:
        print("\nSuccessfully read JSON content:")
        for item in json_content:
            print(f"  Start: {item['start']}, End: {item['end']}, Text: '{item['text']}', Score: {item['score']}")

    output_file = "my_subtitles.srt"
    if create_srt_from_json_data(json_content, output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            print("\nContent of the generated SRT file:")
            print(f.read())
    else:
        print("\nFailed to create SRT file.")

    output_srt_file_eights = "eight_word_subtitles.srt"
    output_srt_file_quads = "four_word_subtitles.srt"
    output_srt_file_sixs = "six_word_subtitles.srt"

    print("--- Generating triplets (group_size=3) ---")
    group_and_create_srt(json_content, output_srt_file_eights, group_size=8)

    print("\n--- Generating quads (group_size=4) ---")
    group_and_create_srt(json_content, output_srt_file_quads, group_size=4)

    print("\n--- Generating six-groups (group_size=2) ---")
    group_and_create_srt(json_content, output_srt_file_sixs, group_size=6)
