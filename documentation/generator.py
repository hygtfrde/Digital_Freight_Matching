"""
Main Documentation Generator

Coordinates the generation of all documentation types.
"""

import os
from pathlib import Path
from typing import Dict
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from user_guide import UserGuideGenerator
from technical_docs import TechnicalDocsGenerator
from api_docs import APIDocsGenerator
from deployment_guide import DeploymentGuideGenerator
from examples import ExamplesGenerator


class DocumentationGenerator:
    """Main documentation generator that coordinates all doc types"""
    
    def __init__(self, output_dir: str = "docs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize specialized generators
        self.user_guide = UserGuideGenerator(self.output_dir)
        self.technical_docs = TechnicalDocsGenerator(self.output_dir)
        self.api_docs = APIDocsGenerator(self.output_dir)
        self.deployment_guide = DeploymentGuideGenerator(self.output_dir)
        self.examples = ExamplesGenerator(self.output_dir)
    
    def generate_all_documentation(self) -> Dict[str, str]:
        """Generate all documentation types"""
        generated_docs = {}
        
        try:
            print("Generating user guide...")
            generated_docs["user_guide"] = self.user_guide.generate()
            
            print("Generating technical documentation...")
            generated_docs["technical_docs"] = self.technical_docs.generate()
            
            print("Generating API documentation...")
            generated_docs["api_docs"] = self.api_docs.generate()
            
            print("Generating deployment guide...")
            generated_docs["deployment_guide"] = self.deployment_guide.generate()
            
            print("Generating examples and tutorials...")
            generated_docs["examples"] = self.examples.generate()
            
            print("Generating documentation index...")
            generated_docs["index"] = self._generate_index(generated_docs)
            
            return generated_docs
            
        except Exception as e:
            print(f"Error generating documentation: {e}")
            return {"error": str(e)}
    
    def _generate_index(self, generated_docs: Dict[str, str]) -> str:
        """Generate main documentation index"""
        index_content = f"""# Digital Freight Matching System - Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Documentation Overview

This documentation package provides comprehensive information about the Digital Freight Matching system.

## Available Documentation

"""
        
        doc_descriptions = {
            "user_guide": "Complete user guide with installation and operation instructions",
            "technical_docs": "Technical architecture and design documentation", 
            "api_docs": "REST API reference and examples",
            "deployment_guide": "Production deployment and configuration guide",
            "examples": "Tutorials and real-world usage examples"
        }
        
        for doc_type, file_path in generated_docs.items():
            if doc_type != "index" and doc_type != "error":
                file_name = Path(file_path).name
                description = doc_descriptions.get(doc_type, "System documentation")
                index_content += f"- **[{file_name}]({file_name})** - {description}\n"
        
        index_content += """
## Quick Start

1. **New Users**: Start with the [User Guide](user-guide.md)
2. **Developers**: Review [Technical Documentation](technical-guide.md) and [API Docs](api-documentation.md)
3. **System Admins**: Follow the [Deployment Guide](deployment-guide.md)
4. **Learning**: Try the [Examples and Tutorials](examples-and-tutorials.md)

## System Overview

The Digital Freight Matching system converts unprofitable truck routes into profitable ones by intelligently matching third-party freight orders to available capacity.

**Key Features:**
- Order-to-route matching with constraint validation
- Profitability optimization and analytics
- Real-time performance monitoring
- Comprehensive business rules enforcement

**Business Goal:** Convert -$388.15 daily loss into positive profitability.
"""
        
        index_path = self.output_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return str(index_path)


def main():
    """Generate all documentation"""
    print("=== Digital Freight Matching Documentation Generator ===")
    
    generator = DocumentationGenerator()
    generated_docs = generator.generate_all_documentation()
    
    if "error" in generated_docs:
        print(f"❌ Generation failed: {generated_docs['error']}")
        return
    
    print("\n✅ Documentation generation complete!")
    print(f"📁 Files generated in: {generator.output_dir}")
    
    for doc_type, file_path in generated_docs.items():
        if doc_type != "error":
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            print(f"  📄 {Path(file_path).name}: {file_size:,} bytes")
    
    print("\n📖 Start with: docs/README.md")


if __name__ == "__main__":
    main()