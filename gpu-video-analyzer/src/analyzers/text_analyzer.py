class TextAnalyzer:
    def analyze_text(self, text):
        # Process the extracted captions to identify relevant information
        # This is a placeholder for the actual analysis logic
        relevant_info = []
        lines = text.splitlines()
        for line in lines:
            # Example logic to identify relevant information
            if "GPU" in line or "graphics" in line:
                relevant_info.append(line)
        return relevant_info