#!/usr/bin/env python3

class SimpleTest:
    def test_method(self):
        raise Exception("This should always raise!")
        return "This should never be reached"

if __name__ == "__main__":
    test = SimpleTest()
    try:
        result = test.test_method()
        print(f"ERROR: Got result: {result}")
    except Exception as e:
        print(f"SUCCESS: Got exception: {e}")