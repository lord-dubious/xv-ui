"""
Unit tests for the shared environment utilities module.
Tests the get_env_value function and environment settings caching.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.webui.utils.env_utils import (
    get_env_value,
    invalidate_env_cache,
    load_env_settings_with_cache,
)


class TestEnvUtils(unittest.TestCase):
    """Test cases for environment utilities."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock webui_manager
        self.mock_webui_manager = Mock()
        self.mock_webui_manager.env_file_path = None

        # Clear any existing cache
        invalidate_env_cache(self.mock_webui_manager)

    def tearDown(self):
        """Clean up after tests."""
        invalidate_env_cache(self.mock_webui_manager)

    def test_get_env_value_basic(self):
        """Test basic get_env_value functionality."""
        env_settings = {"TEST_KEY": "test_value"}

        # Test string value
        result = get_env_value(env_settings, "TEST_KEY", "default")
        self.assertEqual(result, "test_value")

        # Test default value
        result = get_env_value(env_settings, "MISSING_KEY", "default")
        self.assertEqual(result, "default")

    def test_get_env_value_type_casting(self):
        """Test type casting functionality."""
        env_settings = {
            "BOOL_TRUE": "true",
            "BOOL_FALSE": "false",
            "INT_VALUE": "42",
            "FLOAT_VALUE": "3.14",
            "INVALID_INT": "not_a_number",
        }

        # Test boolean casting
        self.assertTrue(get_env_value(env_settings, "BOOL_TRUE", False, bool))
        self.assertFalse(get_env_value(env_settings, "BOOL_FALSE", True, bool))

        # Test integer casting
        self.assertEqual(get_env_value(env_settings, "INT_VALUE", 0, int), 42)

        # Test float casting
        self.assertEqual(get_env_value(env_settings, "FLOAT_VALUE", 0.0, float), 3.14)

        # Test invalid casting falls back to default
        self.assertEqual(get_env_value(env_settings, "INVALID_INT", 999, int), 999)

    def test_get_env_value_boolean_variations(self):
        """Test various boolean string representations."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("yes", False),  # Only "true" should be True
            ("1", False),  # Only "true" should be True
        ]

        for value, expected in test_cases:
            env_settings = {"BOOL_KEY": value}
            result = get_env_value(env_settings, "BOOL_KEY", False, bool)
            self.assertEqual(result, expected, f"Failed for value: {value}")

    def test_load_env_settings_with_cache(self):
        """Test environment settings caching."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("ANOTHER_VAR=another_value\n")
            temp_env_path = f.name

        try:
            self.mock_webui_manager.env_file_path = temp_env_path

            # First call should read from file
            with patch("src.webui.utils.env_utils.logger") as mock_logger:
                result1 = load_env_settings_with_cache(self.mock_webui_manager)
                mock_logger.debug.assert_called()

            # Second call should use cache
            with patch("src.webui.utils.env_utils.logger") as mock_logger:
                result2 = load_env_settings_with_cache(self.mock_webui_manager)
                # Should not call debug for file reading
                self.assertEqual(result1, result2)

            # Verify content
            self.assertEqual(result1["TEST_VAR"], "test_value")
            self.assertEqual(result1["ANOTHER_VAR"], "another_value")

        finally:
            os.unlink(temp_env_path)

    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("CACHE_TEST=original_value\n")
            temp_env_path = f.name

        try:
            self.mock_webui_manager.env_file_path = temp_env_path

            # Load initial cache
            result1 = load_env_settings_with_cache(self.mock_webui_manager)
            self.assertEqual(result1["CACHE_TEST"], "original_value")

            # Modify the file
            with open(temp_env_path, "w") as f:
                f.write("CACHE_TEST=updated_value\n")

            # Should still return cached value
            result2 = load_env_settings_with_cache(self.mock_webui_manager)
            self.assertEqual(result2["CACHE_TEST"], "original_value")

            # Invalidate cache
            invalidate_env_cache(self.mock_webui_manager)

            # Should now return updated value
            result3 = load_env_settings_with_cache(self.mock_webui_manager)
            self.assertEqual(result3["CACHE_TEST"], "updated_value")

        finally:
            os.unlink(temp_env_path)

    def test_missing_env_file(self):
        """Test behavior when .env file doesn't exist."""
        self.mock_webui_manager.env_file_path = "/nonexistent/path/.env"

        result = load_env_settings_with_cache(self.mock_webui_manager)
        self.assertEqual(result, {})

    def test_none_env_file_path(self):
        """Test behavior when env_file_path is None."""
        self.mock_webui_manager.env_file_path = None

        result = load_env_settings_with_cache(self.mock_webui_manager)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
