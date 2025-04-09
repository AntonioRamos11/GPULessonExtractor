import os
import json
import glob
from collections import Counter
import re

def load_results(results_dir='data/processed'):
    """Load all JSON result files"""
    result_files = glob.glob(os.path.join(results_dir, "gpu_videos_*.json"))
    
    # Sort by modification time (newest first)
    result_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    if not result_files:
        print(f"No result files found in {results_dir}")
        return []
    
    # Load the most recent file
    latest_file = result_files[0]
    print(f"Loading results from {latest_file}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def extract_keywords(videos):
    """Extract common keywords from GPU-related videos"""
    all_text = ""
    for video in videos:
        all_text += video.get('title', '') + " " + video.get('description', '') + " "
        if 'transcript_snippet' in video:
            all_text += video['transcript_snippet'] + " "
    
    # Clean and tokenize
    text = re.sub(r'[^\w\s]', ' ', all_text.lower())
    words = text.split()
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                   'is', 'was', 'be', 'as', 'this', 'that', 'it', 'by', 'from', 'not',
                   'what', 'all', 'are', 'but', 'so', 'no', 'yes', 'we', 'you', 'i', 'he',
                   'she', 'they', 'how', 'why', 'when', 'where', 'which', 'who', 'or'}
    
    filtered_words = [word for word in words if word not in common_words and len(word) > 2]
    word_counts = Counter(filtered_words)
    
    return word_counts

def main():
    results = load_results()
    
    if not results:
        print("No results to analyze")
        return
    
    # Separate GPU vs non-GPU videos
    gpu_videos = [r for r in results if r['is_gpu_related']]
    non_gpu_videos = [r for r in results if not r['is_gpu_related']]
    
    print(f"\n===== ANALYSIS OF {len(results)} VIDEOS =====")
    print(f"GPU-related videos: {len(gpu_videos)} ({len(gpu_videos)/len(results)*100:.1f}%)")
    print(f"Non-GPU videos: {len(non_gpu_videos)} ({len(non_gpu_videos)/len(results)*100:.1f}%)")
    
    # Analyze GPU video content
    if gpu_videos:
        print("\n===== GPU VIDEOS KEYWORD ANALYSIS =====")
        word_counts = extract_keywords(gpu_videos)
        
        print("Top 20 keywords in GPU-related videos:")
        for word, count in word_counts.most_common(20):
            print(f"  {word}: {count}")
    
    # Show most confident classifications
    print("\n===== MOST CONFIDENT GPU CLASSIFICATIONS =====")
    sorted_by_confidence = sorted(gpu_videos, key=lambda x: x['confidence'], reverse=True)
    for video in sorted_by_confidence[:5]:
        print(f"• {video['title']} (confidence: {video['confidence']:.2f})")
        print(f"  {video['url']}")
        print(f"  Reasoning: {video['reasoning'][:100]}...")

if __name__ == "__main__":
    main()