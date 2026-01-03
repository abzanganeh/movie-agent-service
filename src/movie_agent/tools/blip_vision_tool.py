from typing import Optional, Any, Dict
from pathlib import Path
import os
import torch
from PIL import Image

from .vision_tool import VisionTool  # protocol
from ..schemas import PosterAnalysisResponse


class BLIPVisionTool(VisionTool):
    """
    Concrete VisionTool implementation using BLIP for movie poster analysis.
    
    Implements the VisionTool protocol and follows separation of concerns:
    - Model loading is separate from inference
    - Image processing is separate from model operations
    - Response formatting is separate from inference logic
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        model_path: Optional[str] = None,
        model: Any = None,
        device: Optional[str] = None
    ):
        """
        Initialize BLIP vision tool.
        
        :param model_name: HuggingFace model name (e.g., "Salesforce/blip-image-captioning-base")
        :param model_path: Optional local path to model files
        :param model: Optional pre-loaded model dict (for dependency injection/testing)
        :param device: Device to run on ("cuda", "cpu", or None for auto-detect)
        """
        self.model_name = model_name or "Salesforce/blip-image-captioning-base"
        self.model_path = model_path
        self.device = device or self._detect_device()
        
        # Dependency injection: allow pre-loaded model for testing
        if model is not None:
            self._processor = model.get("processor")
            self._blip_model = model.get("model")
            self._is_loaded = True
        else:
            self._processor = None
            self._blip_model = None
            self._is_loaded = False

    def _detect_device(self) -> str:
        """Detect available device (CUDA or CPU)."""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _load_model(self):
        """
        Load BLIP model and processor.
        Separated from __init__ for lazy loading and better error handling.
        """
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
        except ImportError:
            raise ImportError(
                "transformers or torch not installed. "
                "Install with: pip install transformers torch"
            )

        try:
            # Prefer safetensors to avoid torch.load vulnerability and version constraints
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            common_kwargs = {
                "use_safetensors": True,
                "dtype": dtype,
                "low_cpu_mem_usage": True,
            }

            if self.model_path and os.path.exists(self.model_path):
                # Load from local path
                self._processor = BlipProcessor.from_pretrained(self.model_path)
                self._blip_model = BlipForConditionalGeneration.from_pretrained(
                    self.model_path,
                    **common_kwargs,
                )
            else:
                # Load from HuggingFace
                self._processor = BlipProcessor.from_pretrained(self.model_name)
                self._blip_model = BlipForConditionalGeneration.from_pretrained(
                    self.model_name,
                    **common_kwargs,
                )
            
            # Move model to device
            self._blip_model.to(self.device)
            self._blip_model.eval()  # Set to evaluation mode
            self._is_loaded = True
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to load BLIP model '{self.model_name}': {str(e)}"
            ) from e

    def _ensure_model_loaded(self):
        """Ensure model is loaded (lazy loading)."""
        if not self._is_loaded:
            self._load_model()

    def _load_image(self, image_path: str) -> Image.Image:
        """
        Load and validate image file.
        Separated for better error handling and testability.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return image
        except Exception as e:
            raise ValueError(f"Failed to load image '{image_path}': {str(e)}") from e

    def _generate_caption(self, image: Image.Image) -> str:
        """
        Generate caption from image using BLIP model.
        Core inference logic, separated from response formatting.
        """
        self._ensure_model_loaded()
        
        try:
            # Process image
            inputs = self._processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self._blip_model.generate(**inputs, max_length=50)
            
            # Decode caption
            caption = self._processor.decode(generated_ids[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            raise RuntimeError(f"BLIP inference failed: {str(e)}") from e

    def _extract_genres_from_caption(self, caption: str) -> list[str]:
        """
        Extract genre information from BLIP caption.
        Uses keyword matching - can be enhanced with LLM or ML classifier.
        """
        caption_lower = caption.lower()
        genre_keywords = {
            "action": ["action", "fight", "battle", "war", "combat", "explosion"],
            "sci-fi": ["sci-fi", "science fiction", "space", "alien", "future", "robot", "cyber"],
            "horror": ["horror", "scary", "frightening", "monster", "ghost", "zombie"],
            "comedy": ["comedy", "funny", "humor", "laugh"],
            "drama": ["drama", "emotional", "serious", "tragic"],
            "thriller": ["thriller", "suspense", "mystery", "crime"],
            "romance": ["romance", "romantic", "love", "couple"],
            "fantasy": ["fantasy", "magic", "wizard", "dragon", "mythical"],
            "adventure": ["adventure", "journey", "quest", "expedition"],
        }
        
        detected_genres = []
        for genre, keywords in genre_keywords.items():
            if any(keyword in caption_lower for keyword in keywords):
                detected_genres.append(genre.title())
        
        # Default genres if none detected
        if not detected_genres:
            detected_genres = ["Drama"]  # Safe default
        
        return detected_genres[:3]  # Return top 3

    def _infer_mood_from_caption(self, caption: str) -> str:
        """
        Infer mood from caption text.
        Can be enhanced with sentiment analysis or LLM.
        """
        caption_lower = caption.lower()
        
        mood_keywords = {
            "Exciting": ["action", "fast", "intense", "thrilling", "adrenaline"],
            "Dark": ["dark", "gloomy", "sinister", "ominous", "shadow"],
            "Lighthearted": ["bright", "cheerful", "fun", "happy", "joyful"],
            "Mysterious": ["mystery", "unknown", "secret", "hidden", "enigmatic"],
            "Romantic": ["romantic", "love", "passion", "tender"],
            "Tense": ["tense", "suspense", "anxiety", "nervous"],
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in caption_lower for keyword in keywords):
                return mood
        
        return "Neutral"  # Default mood

    def _calculate_confidence(self, caption: str, genres: list[str]) -> float:
        """
        Calculate confidence score based on caption quality and genre detection.
        """
        # Base confidence
        confidence = 0.7
        
        # Increase if caption is descriptive (longer captions = more info)
        if len(caption.split()) > 5:
            confidence += 0.1
        
        # Increase if multiple genres detected (more specific)
        if len(genres) > 1:
            confidence += 0.1
        
        # Cap at 0.95 (never 100% certain)
        return min(confidence, 0.95)

    def _format_response(
        self,
        caption: str,
        genres: list[str],
        mood: str,
        confidence: float
    ) -> PosterAnalysisResponse:
        """
        Format inference results into PosterAnalysisResponse.
        Separated from inference logic for clarity.
        """
        return PosterAnalysisResponse(
            inferred_genres=genres,
            mood=mood,
            confidence=confidence
        )

    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        """
        Analyze movie poster and return structured metadata.
        
        Implements VisionTool protocol.
        Follows separation of concerns:
        1. Load image (I/O concern)
        2. Generate caption (model inference concern)
        3. Extract metadata (analysis concern)
        4. Format response (presentation concern)
        
        :param image_path: Path to poster image file
        :return: PosterAnalysisResponse with inferred genres, mood, and confidence
        :raises: FileNotFoundError, ValueError, RuntimeError
        """
        # Step 1: Load and validate image
        image = self._load_image(image_path)
        
        # Step 2: Generate caption using BLIP
        caption = self._generate_caption(image)
        
        # Step 3: Extract metadata from caption
        genres = self._extract_genres_from_caption(caption)
        mood = self._infer_mood_from_caption(caption)
        confidence = self._calculate_confidence(caption, genres)
        
        # Step 4: Format and return response
        return self._format_response(caption, genres, mood, confidence)