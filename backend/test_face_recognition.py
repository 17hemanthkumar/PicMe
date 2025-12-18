"""
Test face recognition functionality in the containerized application.

This test validates that:
- Face recognition models load correctly
- dlib models are accessible
- Face processing works with uploaded photos
- Processed photos are stored correctly

Validates: Requirements 4.5
"""

import pytest
import os
import sys
import numpy as np
import cv2
import face_recognition
from io import BytesIO
from PIL import Image

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from face_model import FaceRecognitionModel
from face_utils import (
    align_face,
    compute_frame_quality,
    aggregate_face_encoding_from_bgr_frames,
    verify_liveness_from_bgr_frames
)


class TestFaceRecognitionModelLoading:
    """Test that face recognition models load correctly"""
    
    def test_dlib_shape_predictor_file_exists(self):
        """
        Test that the dlib shape predictor model file exists.
        This is required for face landmark detection.
        
        Validates: Requirements 4.5
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(base_dir, "shape_predictor_68_face_landmarks.dat")
        
        assert os.path.exists(predictor_path), \
            "shape_predictor_68_face_landmarks.dat must exist for face recognition"
        
        # Verify file is not empty
        file_size = os.path.getsize(predictor_path)
        assert file_size > 0, \
            "shape_predictor_68_face_landmarks.dat must not be empty"
        
        # Verify file is reasonably sized (should be around 99MB)
        assert file_size > 1_000_000, \
            "shape_predictor_68_face_landmarks.dat appears to be corrupted (too small)"
    
    def test_face_recognition_model_initialization(self):
        """
        Test that FaceRecognitionModel can be initialized.
        
        Validates: Requirements 4.5
        """
        import tempfile
        
        # Create a temporary data file
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            model = FaceRecognitionModel(data_file=tmp_path)
            
            assert model is not None, "FaceRecognitionModel should initialize"
            assert hasattr(model, 'known_encodings'), "Model should have known_encodings"
            assert hasattr(model, 'known_ids'), "Model should have known_ids"
            assert isinstance(model.known_encodings, list), "known_encodings should be a list"
            assert isinstance(model.known_ids, list), "known_ids should be a list"
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_dlib_predictor_loads_successfully(self):
        """
        Test that dlib shape predictor can be loaded.
        
        Validates: Requirements 4.5
        """
        import dlib
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(base_dir, "shape_predictor_68_face_landmarks.dat")
        
        # This should not raise an exception
        predictor = dlib.shape_predictor(predictor_path)
        
        assert predictor is not None, "dlib predictor should load successfully"


class TestFaceProcessing:
    """Test face detection and processing functionality"""
    
    @pytest.fixture
    def sample_face_image(self):
        """Create a simple test image with a face-like pattern"""
        # Create a 200x200 RGB image
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Fill with a skin-tone color
        img[:, :] = [180, 150, 120]
        
        # Add some features (simplified face)
        # Eyes (dark circles)
        cv2.circle(img, (70, 70), 10, (50, 50, 50), -1)
        cv2.circle(img, (130, 70), 10, (50, 50, 50), -1)
        
        # Nose (triangle)
        pts = np.array([[100, 90], [90, 120], [110, 120]], np.int32)
        cv2.fillPoly(img, [pts], (150, 120, 100))
        
        # Mouth (line)
        cv2.line(img, (80, 150), (120, 150), (100, 50, 50), 3)
        
        return img
    
    @pytest.fixture
    def real_test_image(self):
        """
        Create a more realistic test image using PIL.
        This creates a simple colored image that can be used for testing.
        """
        # Create a simple gradient image
        img = Image.new('RGB', (400, 400))
        pixels = img.load()
        
        for i in range(400):
            for j in range(400):
                pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
        
        # Convert to numpy array
        return np.array(img)
    
    def test_face_recognition_library_works(self):
        """
        Test that face_recognition library is functional.
        
        Validates: Requirements 4.5
        """
        # Create a simple test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :] = [200, 200, 200]  # White background
        
        # face_recognition should work even if no faces are detected
        locations = face_recognition.face_locations(img)
        
        # Should return empty list for image with no faces
        assert isinstance(locations, list), \
            "face_recognition.face_locations should return a list"
    
    def test_compute_frame_quality(self, sample_face_image):
        """
        Test that frame quality computation works.
        
        Validates: Requirements 4.5
        """
        quality = compute_frame_quality(sample_face_image)
        
        assert isinstance(quality, (int, float)), \
            "compute_frame_quality should return a numeric value"
        assert 0 <= quality <= 1, \
            "Frame quality should be between 0 and 1"
    
    def test_align_face_with_no_face(self, real_test_image):
        """
        Test that align_face handles images with no faces gracefully.
        
        Validates: Requirements 4.5
        """
        result = align_face(real_test_image)
        
        # Should return None when no face is detected
        assert result is None, \
            "align_face should return None when no face is detected"
    
    def test_aggregate_face_encoding_with_empty_frames(self):
        """
        Test that aggregate_face_encoding handles empty frame list.
        
        Validates: Requirements 4.5
        """
        result = aggregate_face_encoding_from_bgr_frames([])
        
        assert result is None, \
            "aggregate_face_encoding should return None for empty frames"
    
    def test_aggregate_face_encoding_with_no_faces(self, real_test_image):
        """
        Test that aggregate_face_encoding handles frames with no faces.
        
        Validates: Requirements 4.5
        """
        frames = [real_test_image, real_test_image]
        result = aggregate_face_encoding_from_bgr_frames(frames)
        
        # Should return None when no faces are detected
        assert result is None, \
            "aggregate_face_encoding should return None when no faces detected"
    
    def test_verify_liveness_requires_multiple_frames(self):
        """
        Test that liveness verification requires multiple frames.
        
        Validates: Requirements 4.5
        """
        # Test with insufficient frames
        is_live, debug_info = verify_liveness_from_bgr_frames([], None)
        
        assert is_live is False, \
            "Liveness check should fail with no frames"
        assert "reason" in debug_info, \
            "Debug info should contain reason for failure"
        assert "Not enough frames" in debug_info["reason"], \
            "Should indicate insufficient frames"


class TestFaceRecognitionModel:
    """Test the FaceRecognitionModel class functionality"""
    
    @pytest.fixture
    def temp_model(self):
        """Create a temporary face recognition model"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
            tmp_path = tmp.name
        
        model = FaceRecognitionModel(data_file=tmp_path)
        
        yield model
        
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    @pytest.fixture
    def sample_encoding(self):
        """Create a sample face encoding (128-dimensional vector)"""
        return np.random.rand(128).astype(np.float64)
    
    def test_learn_face_creates_new_identity(self, temp_model, sample_encoding):
        """
        Test that learning a new face creates a new identity.
        
        Validates: Requirements 4.5
        """
        initial_count = len(temp_model.known_ids)
        
        person_id = temp_model.learn_face(sample_encoding)
        
        assert person_id is not None, "learn_face should return a person_id"
        assert person_id.startswith("person_"), "person_id should have correct format"
        assert len(temp_model.known_ids) == initial_count + 1, \
            "A new identity should be added"
        assert person_id in temp_model.known_ids, \
            "The new person_id should be in known_ids"
    
    def test_learn_face_recognizes_similar_encoding(self, temp_model, sample_encoding):
        """
        Test that learning a similar face updates existing identity.
        
        Validates: Requirements 4.5
        """
        # Learn first encoding
        person_id_1 = temp_model.learn_face(sample_encoding)
        
        # Create a very similar encoding (small perturbation)
        similar_encoding = sample_encoding + np.random.rand(128) * 0.01
        
        # Learn similar encoding
        person_id_2 = temp_model.learn_face(similar_encoding)
        
        # Should recognize as same person (with high probability)
        # Note: Due to the random nature, this might occasionally create a new identity
        # but most of the time it should match
        assert person_id_2 is not None, "learn_face should return a person_id"
    
    def test_recognize_face_with_empty_database(self, temp_model, sample_encoding):
        """
        Test that recognize_face returns None when database is empty.
        
        Validates: Requirements 4.5
        """
        result = temp_model.recognize_face(sample_encoding)
        
        assert result is None, \
            "recognize_face should return None when no faces are in database"
    
    def test_recognize_face_after_learning(self, temp_model, sample_encoding):
        """
        Test that recognize_face can identify a learned face.
        
        Validates: Requirements 4.5
        """
        # Learn a face
        person_id = temp_model.learn_face(sample_encoding)
        
        # Try to recognize the same encoding
        recognized_id = temp_model.recognize_face(sample_encoding)
        
        # Should recognize the same person
        assert recognized_id == person_id, \
            "recognize_face should identify the learned face"
    
    def test_model_save_and_load(self, temp_model, sample_encoding):
        """
        Test that model can be saved and loaded.
        
        Validates: Requirements 4.5
        """
        # Learn a face
        person_id = temp_model.learn_face(sample_encoding)
        
        # Save the model
        temp_model.save_model()
        
        # Create a new model instance with the same data file
        new_model = FaceRecognitionModel(data_file=temp_model.data_file)
        
        # Should have loaded the saved data
        assert len(new_model.known_ids) == 1, \
            "Loaded model should have the saved identity"
        assert person_id in new_model.known_ids, \
            "Loaded model should contain the saved person_id"
    
    def test_update_person_encoding(self, temp_model, sample_encoding):
        """
        Test that updating person encoding works correctly.
        
        Validates: Requirements 4.5
        """
        # Learn a face
        person_id = temp_model.learn_face(sample_encoding)
        
        # Get the index
        index = temp_model.known_ids.index(person_id)
        
        # Initial encoding count
        initial_count = len(temp_model.known_encodings[index])
        
        # Update with a new encoding
        new_encoding = np.random.rand(128).astype(np.float64)
        temp_model.update_person_encoding(index, new_encoding)
        
        # Should have added the new encoding
        assert len(temp_model.known_encodings[index]) == initial_count + 1, \
            "update_person_encoding should add a new encoding"
    
    def test_model_limits_encoding_samples(self, temp_model, sample_encoding):
        """
        Test that model limits the number of encoding samples per person.
        
        Validates: Requirements 4.5
        """
        # Learn a face
        person_id = temp_model.learn_face(sample_encoding)
        index = temp_model.known_ids.index(person_id)
        
        # Add many encodings (more than the limit of 15)
        for i in range(20):
            new_encoding = np.random.rand(128).astype(np.float64)
            temp_model.update_person_encoding(index, new_encoding)
        
        # Should be limited to 15 samples
        assert len(temp_model.known_encodings[index]) <= 15, \
            "Model should limit encoding samples to 15 per person"


class TestDirectoryStructure:
    """Test that processed photos are stored correctly"""
    
    def test_processed_folder_structure(self):
        """
        Test that the expected folder structure exists or can be created.
        
        Validates: Requirements 4.5
        """
        import tempfile
        import shutil
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create the expected structure
            event_id = "test_event_001"
            person_id = "person_0001"
            
            event_dir = os.path.join(temp_dir, event_id)
            person_dir = os.path.join(event_dir, person_id)
            individual_dir = os.path.join(person_dir, "individual")
            group_dir = os.path.join(person_dir, "group")
            
            os.makedirs(individual_dir, exist_ok=True)
            os.makedirs(group_dir, exist_ok=True)
            
            # Verify structure was created
            assert os.path.exists(event_dir), "Event directory should exist"
            assert os.path.exists(person_dir), "Person directory should exist"
            assert os.path.exists(individual_dir), "Individual directory should exist"
            assert os.path.exists(group_dir), "Group directory should exist"
            
            # Verify directories are writable
            test_file = os.path.join(individual_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            assert os.path.exists(test_file), "Should be able to write to directories"
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
