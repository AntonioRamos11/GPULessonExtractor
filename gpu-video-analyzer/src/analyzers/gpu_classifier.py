import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import logging

class GPUClassifier:
    def __init__(self, model_name="deepseek-ai/deepseek-coder-7b-base", use_fallback=True):
        self.use_llm = True
        self.use_fallback = use_fallback
        self.gpu_keywords = ['GPU', 'graphics card', 'video card', 'NVIDIA', 'AMD', 
                            'GeForce', 'Radeon', 'RTX', 'GTX', 'RX', 'DLSS', 'ray tracing']
        
        try:
            logging.info(f"Loading {model_name} model...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                torch_dtype=torch.float16,
                device_map="auto"
            )
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            self.use_llm = False
            if not self.use_fallback:
                raise e
            logging.warning("Falling back to keyword-based classification")
    
    def is_gpu_related(self, title, description=None, transcript=None):
        """
        Determine if content is GPU-related using the deepseek model
        
        Args:
            title (str): Video title
            description (str, optional): Video description
            transcript (str, optional): Video transcript/captions
            
        Returns:
            tuple: (is_gpu_related, confidence_score, reasoning)
        """
        # Fallback to keyword matching if LLM isn't available
        if not self.use_llm:
            return self._keyword_classification(title)
        
        # Prepare content for analysis
        content = f"Title: {title}\n"
        if description:
            content += f"Description: {description}\n"
        if transcript:
            # Use a snippet of transcript if it's too long
            content += f"Transcript snippet: {transcript[:500]}...\n" if len(transcript) > 500 else f"Transcript: {transcript}\n"
        
        # Create prompt for the model
        prompt = f"""Analyze the following YouTube video content and determine if it's primarily about GPUs or graphics cards.
        
{content}

Consider specific GPU models, graphics technologies, performance metrics, or gaming graphics discussions as GPU-related.

Question: Is this content primarily about GPUs, graphics cards, or graphics technology?
Answer with 'Yes' or 'No', followed by your confidence score (0-100%) and a brief explanation.
"""
        
        # Generate response from model
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=200,
                    temperature=0.1
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            # Extract decision from model response
            is_gpu_related = "yes" in response.lower()[:10]
            
            # Try to extract confidence score
            confidence_score = 0.7  # Default if we can't parse one
            
            # Extract explanation
            explanation = response
            
            return (is_gpu_related, confidence_score, explanation)
            
        except Exception as e:
            logging.error(f"Error using LLM for classification: {str(e)}")
            if self.use_fallback:
                return self._keyword_classification(title)
            raise e
    
    def _keyword_classification(self, title):
        """Fallback keyword-based classification method"""
        title_lower = title.lower()
        is_match = any(keyword.lower() in title_lower for keyword in self.gpu_keywords)
        confidence = 0.9 if is_match else 0.2  # High confidence for keyword matches
        explanation = f"Keyword match found: {title}" if is_match else "No GPU-related keywords found"
        return (is_match, confidence, explanation)