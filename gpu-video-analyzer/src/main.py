# main.py
import os
import json
from datetime import datetime
from extractors.caption_extractor import CaptionExtractor
from extractors.metadata_extractor import MetadataExtractor
from analyzers.text_analyzer import TextAnalyzer
from analyzers.gpu_classifier import GPUClassifier
from utils.youtube_scraper import *

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def process_video(video_data):
    """Process a single video"""
    try:
        # Extract metadata from video data
        video_id = video_data['id']
        title = video_data['title']
        description = video_data.get('description', '')
        
        # Check if the video is GPU related
        gpu_classifier = GPUClassifier()
        is_gpu_related, confidence, explanation = gpu_classifier.is_gpu_related(title, description)
        
        result = {
            'video_id': video_id,
            'title': title,
            'is_gpu_related': is_gpu_related,
            'confidence': confidence,
            'reasoning': explanation,
            'url': f"https://youtube.com/watch?v={video_id}"
        }
        
        if is_gpu_related:
            print(f"📊 GPU-related video found: {title}")
            
            # Get transcript
            try:
                transcript = get_video_transcript(video_id)
                if transcript:
                    max_length = 500
                    result['transcript_snippet'] = transcript[:max_length] + ('...' if len(transcript) > max_length else '')
                    result['has_transcript'] = True
                else:
                    result['has_transcript'] = False
            except Exception as e:
                print(f"Error fetching transcript: {str(e)}")
                result['has_transcript'] = False
        else:
            print(f"⏭️ Skipping non-GPU video: {title}")
            
        return result
    except Exception as e:
        print(f"Error processing video {video_data.get('id', 'unknown')}: {str(e)}")
        return None

def main():
    # Load configuration
    cleanup()
    try:
        config = load_config()
        output_dir = config.get('output', {}).get('processed_data_path', 'data/processed')
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        output_dir = 'data/processed'
    
    # Channel to analyze
    channel_id = "@geohotarchive"
    
    # Get timestamp for videos published in the last year
    published_after = get_last_year_timestamp()
    
    print(f"Fetching videos from {channel_id} published after {published_after}")
    
    # Get videos from channel for the last year - limit to 20 to avoid long processing time
    max_videos = 30
    videos = get_channel_videos(channel_id, published_after, max_results=max_videos)
    print(f"Processing {len(videos)} videos (limited to {max_videos} for efficiency)")
    
    results = []
    for i, video in enumerate(videos):
        print(f"Processing video {i+1}/{len(videos)}: {video.get('title', 'Unknown title')}")
        result = process_video(video)
        if result:
            results.append(result)
            # Early save of partial results in case of failure
            if (i+1) % 5 == 0:
                temp_file = os.path.join(output_dir, f"gpu_videos_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                os.makedirs(output_dir, exist_ok=True)
                with open(temp_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Saved partial results to {temp_file}")
    
    # Save final results
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"gpu_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {output_file}")
    
    # Print summary
    gpu_videos = [r for r in results if r['is_gpu_related']]
    print(f"Summary: Found {len(gpu_videos)} GPU-related videos out of {len(results)} total videos.")
    
    if gpu_videos:
        print("\nGPU-related videos:")
        for video in gpu_videos:
            print(f"- {video['title']} ({video['url']})")

if __name__ == "__main__":
    main()# main.py
import os
import json
from datetime import datetime
from extractors.caption_extractor import CaptionExtractor
from extractors.metadata_extractor import MetadataExtractor
from analyzers.text_analyzer import TextAnalyzer
from analyzers.gpu_classifier import GPUClassifier
from utils.youtube_scraper import (
    get_video_details, 
    get_video_transcript,
    get_channel_videos,
    get_last_year_timestamp
)

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def process_video(video_data):
    """Process a single video"""
    try:
        # Extract metadata from video data
        video_id = video_data['id']
        title = video_data['title']
        description = video_data.get('description', '')
        
        # Check if the video is GPU related
        gpu_classifier = GPUClassifier()
        is_gpu_related, confidence, explanation = gpu_classifier.is_gpu_related(title, description)
        
        result = {
            'video_id': video_id,
            'title': title,
            'is_gpu_related': is_gpu_related,
            'confidence': confidence,
            'reasoning': explanation,
            'url': f"https://youtube.com/watch?v={video_id}"
        }
        
        if is_gpu_related:
            print(f"📊 GPU-related video found: {title}")
            
            # Get transcript
            try:
                transcript = get_video_transcript(video_id)
                if transcript:
                    max_length = 500
                    result['transcript_snippet'] = transcript[:max_length] + ('...' if len(transcript) > max_length else '')
                    result['has_transcript'] = True
                else:
                    result['has_transcript'] = False
            except Exception as e:
                print(f"Error fetching transcript: {str(e)}")
                result['has_transcript'] = False
        else:
            print(f"⏭️ Skipping non-GPU video: {title}")
            
        return result
    except Exception as e:
        print(f"Error processing video {video_data.get('id', 'unknown')}: {str(e)}")
        return None

def main():
    # Load configuration
    try:
        config = load_config()
        output_dir = config.get('output', {}).get('processed_data_path', 'data/processed')
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        output_dir = 'data/processed'
    
    # Channel to analyze
    channel_id = "@geohotarchive"
    
    # Get timestamp for videos published in the last year
    published_after = get_last_year_timestamp()
    
    print(f"Fetching videos from {channel_id} published after {published_after}")
    
    # Get videos from channel for the last year - limit to 20 to avoid long processing time
    max_videos = 20
    videos = get_channel_videos(channel_id, published_after, max_results=max_videos)
    print(f"Processing {len(videos)} videos (limited to {max_videos} for efficiency)")
    
    results = []
    for i, video in enumerate(videos):
        print(f"Processing video {i+1}/{len(videos)}: {video.get('title', 'Unknown title')}")
        result = process_video(video)
        if result:
            results.append(result)
            # Early save of partial results in case of failure
            if (i+1) % 5 == 0:
                temp_file = os.path.join(output_dir, f"gpu_videos_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                os.makedirs(output_dir, exist_ok=True)
                with open(temp_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Saved partial results to {temp_file}")
    
    # Save final results
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"gpu_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {output_file}")
    
    # Print summary
    gpu_videos = [r for r in results if r['is_gpu_related']]
    print(f"Summary: Found {len(gpu_videos)} GPU-related videos out of {len(results)} total videos.")
    
    if gpu_videos:
        print("\nGPU-related videos:")
        for video in gpu_videos:
            print(f"- {video['title']} ({video['url']})")

if __name__ == "__main__":
    main()