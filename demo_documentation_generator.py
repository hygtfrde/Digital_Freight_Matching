#!/usr/bin/env python3
"""
Demo script for the Documentation Generation System

This script demonstrates the comprehensive documentation generation capabilities
of the Digital Freight Matching system.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main demo function"""
    print("🚀 Digital Freight Matching - Documentation Generator Demo")
    print("=" * 60)
    
    try:
        # Import and run the documentation generator
        from documentation.documentation_generator import demo_documentation_generation
        
        # Run the demo
        result = demo_documentation_generation()
        
        if "error" not in result:
            print("\n📋 Documentation Summary:")
            print("  • User Guide: Complete installation and operation guide")
            print("  • Technical Guide: Architecture and algorithms documentation")
            print("  • API Documentation: REST API reference with examples")
            print("  • Deployment Guide: Production deployment instructions")
            print("  • Examples & Tutorials: Step-by-step usage examples")
            print("  • Troubleshooting Guide: Common issues and solutions")
            
            print("\n🎯 Next Steps:")
            print("  1. Review generated documentation in docs/ directory")
            print("  2. Start with docs/README.md for overview")
            print("  3. Use docs/user-guide.md for getting started")
            print("  4. Reference docs/api-documentation.md for development")
            
            print("\n✨ Documentation generation completed successfully!")
            return True
        else:
            print(f"\n❌ Error: {result['error']}")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("💡 Make sure you're in the project root directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)