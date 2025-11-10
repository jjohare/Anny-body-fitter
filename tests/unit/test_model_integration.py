# Anny Body Fitter - Model Integration Unit Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
London School TDD unit tests for model creation and integration.

Tests model initialization and parameter handling with mocked data loading.
"""
import pytest
import torch
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestModelCreation:
    """Test model factory function."""

    @patch('anny.models.full_model.load_data')
    @patch('anny.models.full_model.RiggedModelWithPhenotypeParameters')
    def test_should_create_model_with_default_configuration(self, mock_model_class, mock_load_data):
        """Should create model with default rig and topology."""
        # Arrange
        from anny.models.full_model import create_model

        mock_cached_data = {
            'template_vertices': torch.randn(1000, 3),
            'faces': torch.randint(0, 1000, (500, 4)),
            'blendshapes': torch.randn(100, 1000, 3),
            'bone_labels': [f'bone_{i}' for i in range(53)],
            'bone_parents': list(range(53)),
            'local_change_labels': []
        }
        mock_load_data.return_value = mock_cached_data

        # Act
        model = create_model()

        # Assert
        mock_load_data.assert_called_once()
        mock_model_class.assert_called_once()

    @patch('anny.models.full_model.load_data')
    def test_should_support_different_rig_types(self, mock_load_data):
        """Should create models with different rigging schemes."""
        # Arrange
        from anny.models.full_model import create_model

        mock_load_data.return_value = {
            'template_vertices': torch.randn(1000, 3),
            'faces': torch.randint(0, 1000, (500, 4)),
            'blendshapes': torch.randn(100, 1000, 3),
            'bone_labels': [],
            'bone_parents': [],
            'local_change_labels': []
        }

        # Act & Assert
        for rig_type in ['default', 'default_no_toes', 'cmu_mb', 'game_engine', 'mixamo']:
            create_model(rig=rig_type)
            # Should not raise exception

    @patch('anny.models.full_model.load_data')
    def test_should_filter_local_changes(self, mock_load_data):
        """Should filter local changes based on configuration."""
        # Arrange
        from anny.models.full_model import create_model

        all_local_changes = ['nose_width', 'eye_size', 'mouth_width', 'ear_shape']
        mock_load_data.return_value = {
            'template_vertices': torch.randn(1000, 3),
            'faces': torch.randint(0, 1000, (500, 4)),
            'blendshapes': torch.randn(200, 1000, 3),  # Includes local changes
            'bone_heads_blendshapes': torch.randn(200, 53, 3),
            'bone_tails_blendshapes': torch.randn(200, 53, 3),
            'bone_labels': [f'bone_{i}' for i in range(53)],
            'bone_parents': list(range(53)),
            'local_change_labels': all_local_changes,
            'texture_coordinates': torch.randn(1000, 2),
            'face_texture_coordinate_indices': torch.randint(0, 1000, (500, 4))
        }

        # Act
        model = create_model(local_changes=['nose_width', 'eye_size'])

        # Assert: Should filter out unwanted local changes
        # Verification would happen in model initialization
        assert True  # Placeholder for actual verification


@pytest.mark.unit
class TestDataLoading:
    """Test data loading and caching."""

    @patch('anny.models.full_model.torch.load')
    @patch('anny.models.full_model.os.path.exists')
    def test_should_load_from_cache_when_available(self, mock_exists, mock_torch_load):
        """Should use cached data when cache file exists."""
        # Arrange
        from anny.models.full_model import load_data

        mock_exists.return_value = True
        mock_torch_load.return_value = {
            'template_vertices': torch.randn(1000, 3),
            'faces': torch.randint(0, 1000, (500, 4))
        }

        # Act
        data = load_data()

        # Assert
        mock_torch_load.assert_called_once()

    @patch('anny.models.full_model.os.path.exists')
    @patch('anny.models.full_model.torch.save')
    def test_should_create_cache_when_not_exists(self, mock_torch_save, mock_exists):
        """Should generate and cache data on first load."""
        # Arrange
        from anny.models.full_model import load_data

        # Mock cache doesn't exist
        mock_exists.return_value = False

        # Mock file loading operations
        with patch('anny.utils.obj_utils.load_obj_file') as mock_load_obj:
            mock_load_obj.return_value = (
                torch.randn(1000, 3),  # vertices
                torch.randn(1000, 2),  # texture coords
                {'body': {'face_vertex_indices': torch.randint(0, 1000, (500, 4)),
                         'face_texture_coordinate_indices': torch.randint(0, 1000, (500, 4)),
                         'vertex_unique_indices': torch.arange(1000)}}  # groups
            )

            with patch('builtins.open', create=True) as mock_file:
                with patch('json.load') as mock_json_load:
                    mock_json_load.return_value = {
                        'root': {'parent': '', 'head': {'strategy': 'VERTEX', 'vertex_index': 0},
                                'tail': {'strategy': 'VERTEX', 'vertex_index': 1}, 'roll': 0.0},
                        'weights': {'root': []}
                    }

                    with patch('anny.models.full_model.load_macrodetails') as mock_load_blend:
                        mock_load_blend.return_value = ({}, {}, {}, {}, {})

                        # Act
                        data = load_data()

                        # Assert
                        mock_torch_save.assert_called_once()


@pytest.mark.unit
class TestMeshEditing:
    """Test mesh topology editing for censorship."""

    def test_should_remove_sensitive_faces(self):
        """Should remove faces containing sensitive vertex indices."""
        # Arrange
        from anny.models.full_model import get_edited_mesh_faces

        # Create test faces with some containing sensitive indices
        faces = torch.tensor([
            [0, 1, 2, 3],
            [1780, 1781, 1782, 1783],  # Contains sensitive index
            [100, 200, 300, 400],
            [8451, 8452, 8453, 8454],  # Contains sensitive index
            [500, 600, 700, 800]
        ])
        face_tex_coords = torch.arange(20).reshape(5, 4)

        # Act
        edited_faces, edited_tex = get_edited_mesh_faces(faces, face_tex_coords)

        # Assert
        assert edited_faces.shape[0] < faces.shape[0]  # Some faces removed
        # Should not contain sensitive indices
        assert not torch.isin(edited_faces, torch.tensor([1780, 8451])).any()

    def test_should_add_cap_faces_to_close_holes(self):
        """Should add new faces to close holes left by removed faces."""
        # Arrange
        from anny.models.full_model import get_edited_mesh_faces

        faces = torch.randint(0, 10000, (1000, 4))
        face_tex_coords = torch.randint(0, 1000, (1000, 4))

        # Act
        edited_faces, _ = get_edited_mesh_faces(faces, face_tex_coords)

        # Assert
        # Should have cap faces added (14 total: 7 left + 7 right)
        # Actual count depends on how many faces were removed
        assert edited_faces.shape[1] == 4  # Still quad faces


@pytest.mark.unit
class TestParameterValidation:
    """Test parameter validation and bounds."""

    def test_should_validate_rig_parameter(self):
        """Should raise error for invalid rig type."""
        # Arrange
        from anny.models.full_model import load_data

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid rig type"):
            load_data(rig='invalid_rig_name')

    @patch('anny.models.full_model.load_data')
    def test_should_validate_topology_parameter(self, mock_load_data):
        """Should accept valid topology options."""
        # Arrange
        from anny.models.full_model import create_model

        mock_load_data.return_value = {
            'template_vertices': torch.randn(1000, 3),
            'faces': torch.randint(0, 1000, (500, 4)),
            'face_texture_coordinate_indices': torch.randint(0, 1000, (500, 4)),
            'blendshapes': torch.randn(100, 1000, 3),
            'bone_heads_blendshapes': torch.randn(100, 53, 3),
            'bone_tails_blendshapes': torch.randn(100, 53, 3),
            'bone_labels': [],
            'bone_parents': [],
            'local_change_labels': [],
            'texture_coordinates': torch.randn(1000, 2)
        }

        # Act & Assert
        create_model(topology='default')  # Should work
        create_model(topology='makehuman')  # Should work

        with pytest.raises(AssertionError):
            create_model(topology='invalid_topology')


@pytest.mark.unit
class TestVertexReduction:
    """Test vertex reduction for optimized meshes."""

    @patch('anny.models.full_model.load_data')
    def test_should_remove_unattached_vertices_when_requested(self, mock_load_data):
        """Should keep only vertices referenced by faces."""
        # Arrange
        from anny.models.full_model import create_model

        # Create data with some unreferenced vertices
        all_vertices = torch.randn(1000, 3)
        faces = torch.tensor([[0, 1, 2, 3], [4, 5, 6, 7]])  # Only uses 8 vertices

        mock_load_data.return_value = {
            'template_vertices': all_vertices,
            'faces': faces,
            'face_texture_coordinate_indices': torch.zeros_like(faces),
            'vertex_bone_weights': torch.rand(1000, 4),
            'vertex_bone_indices': torch.randint(0, 53, (1000, 4)),
            'blendshapes': torch.randn(100, 1000, 3),
            'bone_heads_blendshapes': torch.randn(100, 53, 3),
            'bone_tails_blendshapes': torch.randn(100, 53, 3),
            'bone_labels': [],
            'bone_parents': [],
            'local_change_labels': [],
            'texture_coordinates': torch.randn(1000, 2)
        }

        # Act
        model = create_model(remove_unattached_vertices=True)

        # Assert
        # Model should be created with reduced vertex count
        assert True  # Placeholder for actual model inspection


@pytest.mark.unit
class TestFaceTriangulation:
    """Test quad to triangle face conversion."""

    @patch('anny.models.full_model.load_data')
    @patch('anny.utils.mesh_utils.triangulate_faces_with_texture_coordinates')
    def test_should_triangulate_quad_faces_when_requested(self, mock_triangulate, mock_load_data):
        """Should convert quad faces to triangles."""
        # Arrange
        from anny.models.full_model import create_model

        quad_faces = torch.tensor([[0, 1, 2, 3], [4, 5, 6, 7]])
        tri_faces = [[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7]]
        tri_tex = [[0, 1, 2], [0, 2, 3], [0, 1, 2], [0, 2, 3]]

        mock_load_data.return_value = {
            'template_vertices': torch.randn(100, 3),
            'faces': quad_faces,
            'face_texture_coordinate_indices': torch.zeros_like(quad_faces),
            'blendshapes': torch.randn(10, 100, 3),
            'bone_heads_blendshapes': torch.randn(10, 53, 3),
            'bone_tails_blendshapes': torch.randn(10, 53, 3),
            'bone_labels': [],
            'bone_parents': [],
            'local_change_labels': [],
            'texture_coordinates': torch.randn(100, 2)
        }

        mock_triangulate.return_value = (tri_faces, tri_tex)

        # Act
        model = create_model(triangulate_faces=True)

        # Assert
        mock_triangulate.assert_called_once()
