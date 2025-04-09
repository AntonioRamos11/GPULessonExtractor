class CaptionExtractor:
    def __init__(self, youtube_api):
        self.youtube_api = youtube_api

    def extract_captions(self, video_id):
        captions = self.youtube_api.get_captions(video_id)
        return captions