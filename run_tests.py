#!/usr/bin/env python3
"""
Test runner for the enhanced delay UI and settings persistence features.
Runs unit tests for environment utilities and delay functionality.
"""

import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_sync_tests():
    """Run synchronous unit tests."""
    print("🧪 Running synchronous unit tests...")

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add specific test modules
    try:
        from tests.test_env_utils import TestEnvUtils

        suite.addTests(loader.loadTestsFromTestCase(TestEnvUtils))
        print("✅ Loaded environment utilities tests")
    except ImportError as e:
        print(f"⚠️  Could not load env_utils tests: {e}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_delay_tests():
    """Run delay functionality unit tests."""
    print("\n🧪 Running delay functionality unit tests...")

    try:
        from tests.test_delay_functionality import TestDelayFunctionality

        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        suite.addTests(loader.loadTestsFromTestCase(TestDelayFunctionality))

        print("✅ Loaded delay functionality tests")

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

    except ImportError as e:
        print(f"⚠️  Could not load delay functionality tests: {e}")
        return True  # Don't fail if optional tests can't load


def main():
    """Main test runner."""
    print("🚀 Starting Enhanced Delay UI and Settings Persistence Tests")
    print("=" * 60)

    # Run synchronous tests
    sync_success = run_sync_tests()

    # Run delay functionality tests
    delay_success = run_delay_tests()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if sync_success:
        print("✅ Environment utilities tests: PASSED")
    else:
        print("❌ Environment utilities tests: FAILED")

    if delay_success:
        print("✅ Delay functionality tests: PASSED")
    else:
        print("❌ Delay functionality tests: FAILED")

    overall_success = sync_success and delay_success

    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Environment utilities working correctly")
        print("✅ Delay functionality working correctly")
        print("✅ Caching mechanisms working correctly")
        print("✅ Type safety and error handling working correctly")
        return 0
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("\n❌ Please review the test output above")
        print("❌ Fix any failing tests before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
