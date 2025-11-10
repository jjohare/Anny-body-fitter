"""
Integration tests for the Gradio application
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))


class TestGradioApp:
    """Tests for Gradio application"""

    def test_create_demo(self):
        """Test demo creation"""
        from frontend.app import create_demo

        demo = create_demo()
        assert demo is not None

    @pytest.mark.skip(reason="Requires Gradio server running")
    def test_app_launch(self):
        """Test app launch (requires server)"""
        from frontend.app import main

        # This would normally launch the server
        # We skip it in automated tests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
