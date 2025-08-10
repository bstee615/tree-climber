#!/usr/bin/env python3
"""Test script to verify the FastAPI /parse endpoint is working correctly."""

import sys

import requests


def test_parse_endpoint():
    """Test the /parse endpoint with sample C code."""
    url = "http://localhost:8001/parse"

    # Test with simple C function
    test_code = """
int foo() {
    return 42;
}
"""

    data = {"source_code": test_code, "language": "c"}

    try:
        print("Testing /parse endpoint...")
        response = requests.post(url, json=data)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")

            if result["success"]:
                cfg = result["cfg"]
                print(f"Function name: {cfg['function_name']}")
                print(f"Number of nodes: {len(cfg['nodes'])}")
                print(f"Entry nodes: {cfg['entry_node_ids']}")
                print(f"Exit nodes: {cfg['exit_node_ids']}")

                # Show first few nodes
                print("\nFirst few nodes:")
                for i, (node_id, node) in enumerate(cfg["nodes"].items()):
                    if i >= 3:  # Show first 3 nodes
                        break
                    print(
                        f"  Node {node_id}: {node['node_type']} - '{node['source_text']}'"
                    )

                return True
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"HTTP Error: {response.text}")
            return False

    except Exception as e:
        print(f"Exception: {e}")
        return False


def test_root_endpoint():
    """Test the root endpoint."""
    url = "http://localhost:8001/"

    try:
        print("Testing root endpoint...")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"API version: {result['version']}")
            print(f"Supported languages: {result['supported_languages']}")
            return True
        else:
            print(f"HTTP Error: {response.text}")
            return False

    except Exception as e:
        print(f"Exception: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Tree Climber CFG API")
    print("=" * 50)

    success = True

    success &= test_root_endpoint()
    print()
    success &= test_parse_endpoint()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
