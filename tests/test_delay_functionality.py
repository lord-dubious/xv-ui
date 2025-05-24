"""
Unit tests for the delay functionality in BrowserUseAgent.
Tests delay caching, application, and cache invalidation.
"""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch


class MockAgent:
    """Mock agent class for testing delay functionality."""

    def __init__(self):
        self._delay_settings_cache = {}
        self._cache_delay_settings()

    def _cache_delay_settings(self):
        """Cache delay settings from environment variables to avoid repeated file reads."""
        delay_types = ["STEP", "ACTION", "TASK"]

        for delay_type in delay_types:
            # Cache random interval settings
            enable_random_str = os.environ.get(
                f"{delay_type}_ENABLE_RANDOM_INTERVAL", "false"
            )
            enable_random = enable_random_str.lower() == "true"

            # Cache fixed delay settings
            delay_minutes_str = os.environ.get(f"{delay_type}_DELAY_MINUTES", "0.0")
            if not delay_minutes_str:
                delay_minutes_str = "0.0"

            # Cache random delay range settings
            min_delay_str = os.environ.get(f"{delay_type}_MIN_DELAY_MINUTES", "0.0")
            if not min_delay_str:
                min_delay_str = "0.0"

            max_delay_str = os.environ.get(f"{delay_type}_MAX_DELAY_MINUTES", "0.0")
            if not max_delay_str:
                max_delay_str = "0.0"

            self._delay_settings_cache[delay_type] = {
                "enable_random": enable_random,
                "delay_minutes": delay_minutes_str,
                "min_delay_minutes": min_delay_str,
                "max_delay_minutes": max_delay_str,
            }

    def invalidate_delay_cache(self):
        """Invalidate and refresh the delay settings cache."""
        self._cache_delay_settings()

    async def _apply_delay(self, delay_type: str) -> None:
        """Apply a delay based on the delay type (STEP, ACTION, or TASK)."""
        import random

        # Get cached settings for this delay type
        settings = self._delay_settings_cache.get(delay_type)
        if not settings:
            return

        enable_random_delay = settings["enable_random"]

        if enable_random_delay:
            # Use cached random delay settings
            min_delay_minutes_str = settings["min_delay_minutes"]
            max_delay_minutes_str = settings["max_delay_minutes"]

            try:
                min_delay_minutes_raw = float(min_delay_minutes_str)
                max_delay_minutes_raw = float(max_delay_minutes_str)

                min_seconds_raw = min_delay_minutes_raw * 60
                max_seconds_raw = max_delay_minutes_raw * 60

                actual_min_seconds = min(min_seconds_raw, max_seconds_raw)
                actual_max_seconds = max(min_seconds_raw, max_seconds_raw)

                if actual_max_seconds > 0.0:
                    random_delay_seconds = random.uniform(
                        actual_min_seconds, actual_max_seconds
                    )
                    await asyncio.sleep(random_delay_seconds)

            except ValueError:
                pass
        else:
            # Use cached fixed delay settings
            delay_minutes_str = settings["delay_minutes"]

            try:
                delay_minutes = float(delay_minutes_str)
                if delay_minutes > 0.0:
                    delay_seconds = delay_minutes * 60
                    await asyncio.sleep(delay_seconds)
            except ValueError:
                pass


class TestDelayFunctionality(unittest.TestCase):
    """Test cases for delay functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = MockAgent()

    def test_delay_cache_initialization(self):
        """Test that delay settings are cached on initialization."""
        # Mock environment variables
        env_vars = {
            "STEP_ENABLE_RANDOM_INTERVAL": "false",
            "STEP_DELAY_MINUTES": "1.0",
            "STEP_MIN_DELAY_MINUTES": "0.5",
            "STEP_MAX_DELAY_MINUTES": "2.0",
            "ACTION_ENABLE_RANDOM_INTERVAL": "true",
            "ACTION_DELAY_MINUTES": "0.5",
            "ACTION_MIN_DELAY_MINUTES": "0.1",
            "ACTION_MAX_DELAY_MINUTES": "1.0",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Create new agent to test initialization
            agent = MockAgent()

        # Verify cache was populated
        self.assertIn("STEP", agent._delay_settings_cache)
        self.assertIn("ACTION", agent._delay_settings_cache)
        self.assertIn("TASK", agent._delay_settings_cache)

        # Verify STEP settings
        step_settings = agent._delay_settings_cache["STEP"]
        self.assertFalse(step_settings["enable_random"])
        self.assertEqual(step_settings["delay_minutes"], "1.0")

        # Verify ACTION settings
        action_settings = agent._delay_settings_cache["ACTION"]
        self.assertTrue(action_settings["enable_random"])
        self.assertEqual(action_settings["min_delay_minutes"], "0.1")
        self.assertEqual(action_settings["max_delay_minutes"], "1.0")

    def test_cache_invalidation(self):
        """Test delay cache invalidation and refresh."""
        # Initial cache
        original_cache = self.agent._delay_settings_cache.copy()

        # Mock new environment variables
        new_env_vars = {
            "STEP_DELAY_MINUTES": "5.0",
            "ACTION_ENABLE_RANDOM_INTERVAL": "false",
        }

        with patch.dict(os.environ, new_env_vars, clear=False):
            # Invalidate cache
            self.agent.invalidate_delay_cache()

        # Verify cache was updated
        new_cache = self.agent._delay_settings_cache
        self.assertNotEqual(original_cache, new_cache)
        self.assertEqual(new_cache["STEP"]["delay_minutes"], "5.0")

    async def test_apply_fixed_delay(self):
        """Test applying fixed delay."""
        # Set up cache for fixed delay
        self.agent._delay_settings_cache = {
            "TEST": {
                "enable_random": False,
                "delay_minutes": "0.01",  # 0.6 seconds for quick test
                "min_delay_minutes": "0.0",
                "max_delay_minutes": "0.0",
            }
        }

        # Mock asyncio.sleep to track calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await self.agent._apply_delay("TEST")

            # Verify sleep was called with correct duration
            mock_sleep.assert_called_once()
            call_args = mock_sleep.call_args[0]
            self.assertAlmostEqual(call_args[0], 0.6, places=1)  # 0.01 * 60 = 0.6

    async def test_apply_random_delay(self):
        """Test applying random delay."""
        # Set up cache for random delay
        self.agent._delay_settings_cache = {
            "TEST": {
                "enable_random": True,
                "delay_minutes": "0.0",
                "min_delay_minutes": "0.01",  # 0.6 seconds
                "max_delay_minutes": "0.02",  # 1.2 seconds
            }
        }

        # Mock asyncio.sleep to track calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await self.agent._apply_delay("TEST")

            # Verify sleep was called
            mock_sleep.assert_called_once()
            call_args = mock_sleep.call_args[0]

            # Verify delay is within expected range
            self.assertGreaterEqual(call_args[0], 0.6)  # min: 0.01 * 60
            self.assertLessEqual(call_args[0], 1.2)  # max: 0.02 * 60

    async def test_apply_zero_delay(self):
        """Test that zero delays don't call sleep."""
        # Set up cache for zero delay
        self.agent._delay_settings_cache = {
            "TEST": {
                "enable_random": False,
                "delay_minutes": "0.0",
                "min_delay_minutes": "0.0",
                "max_delay_minutes": "0.0",
            }
        }

        # Mock asyncio.sleep to track calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await self.agent._apply_delay("TEST")

            # Verify sleep was not called
            mock_sleep.assert_not_called()

    async def test_apply_delay_invalid_type(self):
        """Test behavior with invalid delay type."""
        # Mock asyncio.sleep to track calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await self.agent._apply_delay("INVALID_TYPE")

            # Verify sleep was not called
            mock_sleep.assert_not_called()

    async def test_apply_delay_invalid_values(self):
        """Test behavior with invalid cached values."""
        # Set up cache with invalid values
        self.agent._delay_settings_cache = {
            "TEST": {
                "enable_random": False,
                "delay_minutes": "invalid_number",
                "min_delay_minutes": "0.0",
                "max_delay_minutes": "0.0",
            }
        }

        # Mock asyncio.sleep to track calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await self.agent._apply_delay("TEST")

            # Verify sleep was not called due to invalid value
            mock_sleep.assert_not_called()

    def test_delay_types_coverage(self):
        """Test that all expected delay types are cached."""
        expected_types = ["STEP", "ACTION", "TASK"]

        for delay_type in expected_types:
            self.assertIn(delay_type, self.agent._delay_settings_cache)

            # Verify all required keys are present
            settings = self.agent._delay_settings_cache[delay_type]
            required_keys = [
                "enable_random",
                "delay_minutes",
                "min_delay_minutes",
                "max_delay_minutes",
            ]

            for key in required_keys:
                self.assertIn(key, settings)


if __name__ == "__main__":
    unittest.main()
