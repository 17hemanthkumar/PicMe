"""
Property-based test for face recognition model loading.

**Feature: docker-deployment, Property 6: Face recognition model loading**

Property: For any container startup, if the shape_predictor_68_face_landmarks.dat 
file exists in the application directory, the face recognition system should 
successfully load the model without errors.

**Validates: Requirements 4.5**

This test uses property-based testing to verify that the face recognition model
loads correctly under various conditions.
"""

import pytest
import os
import sys
import tempfile
import shutil
from hypothesis import given, strategies as st, settings, assume
import dlib

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from face_model import FaceRecognitionModel


class TestFaceRecognitionModelLoadingProperty:
    """
    Property-based tests for face recognition model loading.
    
    **Feature: docker-deployment, Property 6: Face recognition model loading**
    **Validates: Requirements 4.5**
    """
    
    @settings(max_examples=100)
    @given(
        data_file_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=50
        ).map(lambda x: x + '.dat')
    )
    def test_face_recognition_model_initializes_with_any_valid_filename(self, data_file_name):
        """
        Property: For any valid filename, FaceRecognitionModel should initialize successfully.
        
        This tests that the model can be created with various valid filenames,
        which is important for container startup scenarios where file paths may vary.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create full path
            data_file_path = os.path.join(temp_dir, data_file_name)
            
            # Initialize model
            model = FaceRecognitionModel(data_file=data_file_path)
            
            # Verify model initialized correctly
            assert model is not None, "Model should initialize"
            assert hasattr(model, 'known_encodings'), "Model should have known_encodings"
            assert hasattr(model, 'known_ids'), "Model should have known_ids"
            assert isinstance(model.known_encodings, list), "known_encodings should be a list"
            assert isinstance(model.known_ids, list), "known_ids should be a list"
            assert model.data_file == data_file_path, "Model should store correct data file path"
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_dlib_shape_predictor_loads_successfully_on_startup(self):
        """
        Property: If shape_predictor_68_face_landmarks.dat exists, dlib should load it successfully.
        
        This is the core property: the face recognition system must be able to load
        the dlib model file when it exists in the application directory.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(base_dir, "shape_predictor_68_face_landmarks.dat")
        
        # Verify the file exists (precondition)
        assert os.path.exists(predictor_path), \
            "shape_predictor_68_face_landmarks.dat must exist for this test"
        
        # Property: If the file exists, dlib should load it without errors
        try:
            predictor = dlib.shape_predictor(predictor_path)
            
            # Verify predictor loaded successfully
            assert predictor is not None, \
                "dlib predictor should load successfully when file exists"
            
            # Verify predictor is functional (can be called)
            assert callable(predictor), \
                "Loaded predictor should be callable"
        
        except Exception as e:
            pytest.fail(f"Failed to load dlib predictor: {e}")
    
    @settings(max_examples=100)
    @given(
        num_startups=st.integers(min_value=1, max_value=10)
    )
    def test_model_loads_successfully_on_multiple_container_startups(self, num_startups):
        """
        Property: For any number of container startups, the model should load successfully each time.
        
        This simulates multiple container restarts and verifies that the model
        loads correctly every time, which is critical for container orchestration.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            data_file_path = os.path.join(temp_dir, 'known_faces.dat')
            
            # Simulate multiple container startups
            for startup_num in range(num_startups):
                # Create a new model instance (simulating container startup)
                model = FaceRecognitionModel(data_file=data_file_path)
                
                # Verify model loaded successfully
                assert model is not None, \
                    f"Model should load successfully on startup {startup_num + 1}"
                assert hasattr(model, 'known_encodings'), \
                    f"Model should have known_encodings on startup {startup_num + 1}"
                assert hasattr(model, 'known_ids'), \
                    f"Model should have known_ids on startup {startup_num + 1}"
                
                # If this is not the first startup, verify data persisted
                if startup_num > 0:
                    # Data should be loaded from file
                    assert isinstance(model.known_encodings, list), \
                        "Loaded model should have encodings list"
                    assert isinstance(model.known_ids, list), \
                        "Loaded model should have ids list"
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @settings(max_examples=100)
    @given(
        directory_depth=st.integers(min_value=1, max_value=5)
    )
    def test_model_loads_from_nested_directories(self, directory_depth):
        """
        Property: For any directory depth, if the data file exists, the model should load.
        
        This tests that the model can load from various directory structures,
        which is important for different container filesystem layouts.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create nested directory structure
            nested_path = temp_dir
            for i in range(directory_depth):
                nested_path = os.path.join(nested_path, f'level_{i}')
            
            os.makedirs(nested_path, exist_ok=True)
            
            data_file_path = os.path.join(nested_path, 'known_faces.dat')
            
            # Initialize model
            model = FaceRecognitionModel(data_file=data_file_path)
            
            # Verify model initialized correctly
            assert model is not None, \
                f"Model should initialize at directory depth {directory_depth}"
            assert model.data_file == data_file_path, \
                "Model should store correct nested path"
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_face_utils_module_imports_successfully(self):
        """
        Property: The face_utils module should import successfully when dlib model exists.
        
        This verifies that the face_utils module, which depends on the dlib model,
        can be imported without errors during container startup.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        try:
            # This import should succeed if dlib model is available
            import face_utils
            
            # Verify key functions are available
            assert hasattr(face_utils, 'align_face'), \
                "face_utils should have align_face function"
            assert hasattr(face_utils, 'compute_frame_quality'), \
                "face_utils should have compute_frame_quality function"
            assert hasattr(face_utils, 'aggregate_face_encoding_from_bgr_frames'), \
                "face_utils should have aggregate_face_encoding_from_bgr_frames function"
            assert hasattr(face_utils, 'verify_liveness_from_bgr_frames'), \
                "face_utils should have verify_liveness_from_bgr_frames function"
            
            # Verify predictor is loaded
            assert hasattr(face_utils, 'predictor'), \
                "face_utils should have predictor loaded"
            assert face_utils.predictor is not None, \
                "face_utils predictor should not be None"
        
        except ImportError as e:
            pytest.fail(f"Failed to import face_utils: {e}")
        except Exception as e:
            pytest.fail(f"Error during face_utils verification: {e}")
    
    @settings(max_examples=100)
    @given(
        file_exists=st.booleans()
    )
    def test_model_handles_missing_data_file_gracefully(self, file_exists):
        """
        Property: Model should handle both existing and non-existing data files gracefully.
        
        This tests that the model initializes correctly whether the data file
        exists or not, which is important for first-time container startups.
        
        **Feature: docker-deployment, Property 6: Face recognition model loading**
        **Validates: Requirements 4.5**
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            data_file_path = os.path.join(temp_dir, 'known_faces.dat')
            
            if file_exists:
                # Create an empty data file
                import pickle
                with open(data_file_path, 'wb') as f:
                    pickle.dump(([], []), f)
            
            # Initialize model (should work whether file exists or not)
            model = FaceRecognitionModel(data_file=data_file_path)
            
            # Verify model initialized correctly
            assert model is not None, \
                "Model should initialize regardless of file existence"
            assert isinstance(model.known_encodings, list), \
                "Model should have encodings list"
            assert isinstance(model.known_ids, list), \
                "Model should have ids list"
            
            if file_exists:
                # If file existed, it should have been loaded
                assert len(model.known_encodings) == 0, \
                    "Empty file should result in empty encodings"
                assert len(model.known_ids) == 0, \
                    "Empty file should result in empty ids"
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
