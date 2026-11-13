import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("=" * 70)
    print("  LegalUpdate AI - Regulatory Change Summarizer: Automated Test Suite")
    print("=" * 70)
    loader = unittest.TestLoader()
    suite = loader.discover(str(backend_dir / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    if result.wasSuccessful():
        print("ALL TESTS PASSED SUCCESSFULLY (100% PASS RATE)")
    print("=" * 70)
    sys.exit(0 if result.wasSuccessful() else 1)

