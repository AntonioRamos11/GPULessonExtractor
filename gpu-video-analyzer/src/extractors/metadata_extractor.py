class MetadataExtractor:
    def __init__(self, youtube_api):
        self.youtube_api = youtube_api

    def extract_metadata(self, video_id):
        video_details = self.youtube_api.get_video_details(video_id)
        title = video_details.get('title')
        description = video_details.get('description')
        return {
            'title': title,
            'description': description
        }