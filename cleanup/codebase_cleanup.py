"""
Codebase Cleanup and Refactoring Engine

This module provides comprehensive analysis and cleanup capabilities for the
Digital Freight Matching codebase including:
- Duplicate code detection across all Python files
- Dead code analyzer to identify unused functions, classes, and imports
- Code quality checker validating naming conventions and standards
- Refactoring suggestions for improved maintainability

Requirements addressed:
- 5.1: No duplicate functionality or redundant implementations
- 5.2: No unused scripts, imports, or dead code
- 5.3: Clear separation of concerns with consistent naming conventions
- 5.4: Follow DRY (Don't Repeat Yourself) principles throughout
"""

import os
import ast
import sys
import re
import math
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DuplicateReport:
    """Report for duplicate code detection"""
    file1: str
    file2: str
    function_name: str
    similarity_score: float
    line_count: int
    duplicate_lines: List[str] = field(default_factory=list)


@dataclass
class DeadCodeReport:
    """Report for dead code analysis"""
    file_path: str
    item_type: str  # 'function', 'class', 'import', 'variable'
    item_name: str
    line_number: int
    reason: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityIssue:
    """Code quality issue"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """Code quality assessment report"""
    file_path: str
    issues: List[QualityIssue]
    complexity_score: float
    maintainability_index: float
    suggestions: List[str] = field(default_factory=list)


@dataclass
class RefactoringRecommendation:
    """Refactoring suggestion"""
    file_path: str
    recommendation_type: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str  # 'small', 'medium', 'large'
    benefits: List[str] = field(default_factory=list)


class CodebaseCleanup:
    """
    Comprehensive codebase cleanup and refactoring engine
    
    Analyzes Python codebase for duplicates, dead code, quality issues,
    and provides refactoring recommendations.
    """
    
    def __init__(self, project_root: str = "."):
        """Initialize the cleanup engine"""
        self.project_root = Path(project_root)
        self.ast_cache: Dict[str, ast.AST] = {}
        
        # Exclude patterns for analysis
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            ".venv",
            "node_modules",
            ".kiro"
        ]
        
        self.python_files = self._find_python_files()
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        
        for file_path in self.project_root.rglob("*.py"):
            # Skip excluded directories
            if any(pattern in str(file_path) for pattern in self.exclude_patterns):
                continue
            python_files.append(file_path)
        
        return python_files
    
    def _parse_file(self, file_path: Path) -> Optional[ast.AST]:
        """Parse Python file into AST"""
        if str(file_path) in self.ast_cache:
            return self.ast_cache[str(file_path)]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            self.ast_cache[str(file_path)] = tree
            return tree
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None
    
    def detect_duplicate_code(self) -> List[DuplicateReport]:
        """
        Detect duplicate code across all Python files
        
        Returns:
            List of DuplicateReport objects
        """
        duplicates = []
        function_signatures = defaultdict(list)
        
        # Extract function signatures from all files
        for file_path in self.python_files:
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    signature = self._get_function_signature(node)
                    function_signatures[signature].append((file_path, node))
        
        # Find duplicates
        for signature, occurrences in function_signatures.items():
            if len(occurrences) > 1:
                for i in range(len(occurrences)):
                    for j in range(i + 1, len(occurrences)):
                        file1, func1 = occurrences[i]
                        file2, func2 = occurrences[j]
                        
                        similarity = self._calculate_similarity(func1, func2)
                        if similarity > 0.8:  # 80% similarity threshold
                            duplicates.append(DuplicateReport(
                                file1=str(file1),
                                file2=str(file2),
                                function_name=func1.name,
                                similarity_score=similarity,
                                line_count=func2.end_lineno - func2.lineno + 1 if hasattr(func2, 'end_lineno') else 0
                            ))
        
        return duplicates
    
    def analyze_dead_code(self) -> List[DeadCodeReport]:
        """
        Analyze codebase for unused functions, classes, and imports
        
        Returns:
            List of DeadCodeReport objects
        """
        dead_code = []
        
        # Build usage map
        all_definitions = {}
        all_usages = set()
        
        # First pass: collect all definitions
        for file_path in self.python_files:
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    all_definitions[node.name] = (file_path, node)
        
        # Second pass: collect all usages
        for file_path in self.python_files:
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    all_usages.add(node.id)
                elif isinstance(node, ast.Attribute):
                    all_usages.add(node.attr)
        
        # Find unused definitions
        for name, (file_path, node) in all_definitions.items():
            if name not in all_usages and not name.startswith('_'):
                # Skip special methods and private functions
                if not (name.startswith('__') and name.endswith('__')):
                    dead_code.append(DeadCodeReport(
                        file_path=str(file_path),
                        item_type='function' if isinstance(node, ast.FunctionDef) else 'class',
                        item_name=name,
                        line_number=node.lineno,
                        reason="No usages found in codebase",
                        suggestions=[
                            f"Remove unused {node.__class__.__name__.lower()} '{name}'",
                            f"Add usage if function is needed",
                            f"Make private with underscore prefix if internal"
                        ]
                    ))
        
        # Analyze unused imports
        dead_code.extend(self._analyze_unused_imports())
        
        return dead_code
    
    def _analyze_unused_imports(self) -> List[DeadCodeReport]:
        """Analyze unused imports in each file"""
        unused_imports = []
        
        for file_path in self.python_files:
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            imports = []
            usages = set()
            
            # Collect imports and usages
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, alias.asname or alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append((alias.name, alias.asname or alias.name, node.lineno))
                elif isinstance(node, ast.Name):
                    usages.add(node.id)
                elif isinstance(node, ast.Attribute):
                    usages.add(node.attr)
            
            # Find unused imports
            for import_name, alias_name, line_no in imports:
                if alias_name not in usages and import_name not in usages:
                    # Skip common imports that might be used implicitly
                    if import_name not in ['sys', 'os', 'logging']:
                        unused_imports.append(DeadCodeReport(
                            file_path=str(file_path),
                            item_type='import',
                            item_name=import_name,
                            line_number=line_no,
                            reason="Import not used in file",
                            suggestions=[f"Remove unused import '{import_name}'"]
                        ))
        
        return unused_imports
    
    def check_code_quality(self) -> List[QualityReport]:
        """
        Check code quality and naming conventions
        
        Returns:
            List of QualityReport objects
        """
        quality_reports = []
        
        for file_path in self.python_files:
            issues = []
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                tree = self._parse_file(file_path)
                if not tree:
                    continue
                
                # Check naming conventions
                issues.extend(self._check_naming_conventions(tree, str(file_path)))
                
                # Check line length
                issues.extend(self._check_line_length(lines, str(file_path)))
                
                # Check complexity
                complexity = self._calculate_complexity(tree)
                
                # Check for code smells
                issues.extend(self._check_code_smells(tree, str(file_path)))
                
                # Calculate maintainability index
                maintainability = self._calculate_maintainability_index(tree, len(lines))
                
                quality_reports.append(QualityReport(
                    file_path=str(file_path),
                    issues=issues,
                    complexity_score=complexity,
                    maintainability_index=maintainability,
                    suggestions=self._generate_quality_suggestions(issues, complexity)
                ))
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
        
        return quality_reports
    
    def suggest_refactoring(self) -> List[RefactoringRecommendation]:
        """
        Generate refactoring recommendations
        
        Returns:
            List of RefactoringRecommendation objects
        """
        recommendations = []
        
        # Analyze for common refactoring opportunities
        for file_path in self.python_files:
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            # Long function detection
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, 'end_lineno'):
                        length = node.end_lineno - node.lineno
                        if length > 50:  # Functions longer than 50 lines
                            recommendations.append(RefactoringRecommendation(
                                file_path=str(file_path),
                                recommendation_type="function_decomposition",
                                description=f"Function '{node.name}' is {length} lines long and should be broken down",
                                priority="medium",
                                estimated_effort="medium",
                                benefits=[
                                    "Improved readability",
                                    "Better testability",
                                    "Easier maintenance"
                                ]
                            ))
            
            # Class with too many methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 15:  # Classes with more than 15 methods
                        recommendations.append(RefactoringRecommendation(
                            file_path=str(file_path),
                            recommendation_type="class_decomposition",
                            description=f"Class '{node.name}' has {len(methods)} methods and may violate SRP",
                            priority="high",
                            estimated_effort="large",
                            benefits=[
                                "Better separation of concerns",
                                "Improved maintainability",
                                "Easier testing"
                            ]
                        ))
        
        return recommendations
    
    def _get_function_signature(self, func_node: ast.FunctionDef) -> str:
        """Generate a signature for function comparison"""
        args = [arg.arg for arg in func_node.args.args]
        return f"{func_node.name}({','.join(args)})"
    
    def _calculate_similarity(self, func1: ast.FunctionDef, func2: ast.FunctionDef) -> float:
        """Calculate similarity between two functions"""
        # Simple similarity based on AST structure
        # In a real implementation, this would be more sophisticated
        
        def count_nodes(node):
            return len(list(ast.walk(node)))
        
        nodes1 = count_nodes(func1)
        nodes2 = count_nodes(func2)
        
        if nodes1 == 0 and nodes2 == 0:
            return 1.0
        
        # Simple similarity metric
        return 1.0 - abs(nodes1 - nodes2) / max(nodes1, nodes2)
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: str) -> List[QualityIssue]:
        """Check Python naming conventions"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        description=f"Function '{node.name}' should use snake_case",
                        severity="warning",
                        suggestion=f"Rename to follow snake_case convention"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        description=f"Class '{node.name}' should use PascalCase",
                        severity="warning",
                        suggestion=f"Rename to follow PascalCase convention"
                    ))
        
        return issues
    
    def _check_line_length(self, lines: List[str], file_path: str) -> List[QualityIssue]:
        """Check for lines that are too long"""
        issues = []
        max_length = 100  # PEP 8 recommends 79, but 100 is more practical
        
        for i, line in enumerate(lines, 1):
            if len(line.rstrip()) > max_length:
                issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="line_length",
                    description=f"Line too long ({len(line.rstrip())} > {max_length} characters)",
                    severity="info",
                    suggestion="Break line into multiple lines"
                ))
        
        return issues
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _check_code_smells(self, tree: ast.AST, file_path: str) -> List[QualityIssue]:
        """Check for common code smells"""
        issues = []
        
        # Check for too many parameters
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="too_many_parameters",
                        description=f"Function '{node.name}' has {param_count} parameters (>5)",
                        severity="warning",
                        suggestion="Consider using a parameter object or breaking down the function"
                    ))
        
        return issues
    
    def _calculate_maintainability_index(self, tree: ast.AST, line_count: int) -> float:
        """Calculate maintainability index (simplified)"""
        complexity = self._calculate_complexity(tree)
        
        # Simplified maintainability index calculation
        # Real calculation would include Halstead metrics
        if line_count == 0:
            return 100.0
        
        mi = max(0, 171 - 5.2 * math.log(complexity) - 0.23 * complexity - 16.2 * math.log(line_count))
        return min(100, mi)
    
    def _generate_quality_suggestions(self, issues: List[QualityIssue], complexity: float) -> List[str]:
        """Generate quality improvement suggestions"""
        suggestions = []
        
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        
        if error_count > 0:
            suggestions.append(f"Fix {error_count} error(s) to improve code quality")
        
        if warning_count > 5:
            suggestions.append(f"Address {warning_count} warning(s) for better maintainability")
        
        if complexity > 20:
            suggestions.append("Consider breaking down complex functions to reduce complexity")
        
        return suggestions
    
    def generate_cleanup_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive cleanup report
        
        Returns:
            Dictionary with all analysis results
        """
        print("🔍 Analyzing codebase for cleanup opportunities...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": len(self.python_files),
            "duplicates": [],
            "dead_code": [],
            "quality_issues": [],
            "refactoring_recommendations": [],
            "summary": {}
        }
        
        try:
            # Run all analyses
            print("  📋 Detecting duplicate code...")
            report["duplicates"] = [
                {
                    "file1": dup.file1,
                    "file2": dup.file2,
                    "function": dup.function_name,
                    "similarity": dup.similarity_score,
                    "lines": dup.line_count
                }
                for dup in self.detect_duplicate_code()
            ]
            
            print("  🗑️  Analyzing dead code...")
            report["dead_code"] = [
                {
                    "file": dead.file_path,
                    "type": dead.item_type,
                    "name": dead.item_name,
                    "line": dead.line_number,
                    "reason": dead.reason,
                    "suggestions": dead.suggestions
                }
                for dead in self.analyze_dead_code()
            ]
            
            print("  ✨ Checking code quality...")
            quality_reports = self.check_code_quality()
            report["quality_issues"] = [
                {
                    "file": qr.file_path,
                    "complexity": qr.complexity_score,
                    "maintainability": qr.maintainability_index,
                    "issues_count": len(qr.issues),
                    "issues": [
                        {
                            "line": issue.line_number,
                            "type": issue.issue_type,
                            "description": issue.description,
                            "severity": issue.severity
                        }
                        for issue in qr.issues
                    ]
                }
                for qr in quality_reports
            ]
            
            print("  🔧 Generating refactoring recommendations...")
            report["refactoring_recommendations"] = [
                {
                    "file": rec.file_path,
                    "type": rec.recommendation_type,
                    "description": rec.description,
                    "priority": rec.priority,
                    "effort": rec.estimated_effort,
                    "benefits": rec.benefits
                }
                for rec in self.suggest_refactoring()
            ]
            
            # Generate summary
            total_issues = sum(len(qr["issues"]) for qr in report["quality_issues"])
            report["summary"] = {
                "duplicate_functions": len(report["duplicates"]),
                "dead_code_items": len(report["dead_code"]),
                "quality_issues": total_issues,
                "refactoring_opportunities": len(report["refactoring_recommendations"]),
                "files_with_issues": len([qr for qr in report["quality_issues"] if qr["issues_count"] > 0])
            }
            
        except Exception as e:
            report["error"] = str(e)
        
        return report


# TODO: This function 'main' is duplicated in db_manager.py

# TODO: This function 'main' is duplicated in db_manager.py

# TODO: This function 'main' is duplicated in db_manager.py

def main():
    """Run codebase cleanup analysis"""
    print("=== Digital Freight Matching Codebase Cleanup ===")
    
    cleanup = CodebaseCleanup()
    report = cleanup.generate_cleanup_report()
    
    if "error" in report:
        print(f"❌ Analysis failed: {report['error']}")
        return
    
    # Display summary
    summary = report["summary"]
    print(f"\n📊 Analysis Summary:")
    print(f"  Files analyzed: {report['files_analyzed']}")
    print(f"  Duplicate functions: {summary['duplicate_functions']}")
    print(f"  Dead code items: {summary['dead_code_items']}")
    print(f"  Quality issues: {summary['quality_issues']}")
    print(f"  Refactoring opportunities: {summary['refactoring_opportunities']}")
    
    # Show top issues
    if report["duplicates"]:
        print(f"\n🔄 Top Duplicate Code:")
        for dup in report["duplicates"][:3]:
            print(f"  - {dup['function']} in {Path(dup['file1']).name} & {Path(dup['file2']).name}")
    
    if report["dead_code"]:
        print(f"\n🗑️  Dead Code Found:")
        for dead in report["dead_code"][:5]:
            print(f"  - {dead['type']} '{dead['name']}' in {Path(dead['file']).name}:{dead['line']}")
    
    if report["refactoring_recommendations"]:
        print(f"\n🔧 Top Refactoring Opportunities:")
        high_priority = [r for r in report["refactoring_recommendations"] if r["priority"] == "high"]
        for rec in high_priority[:3]:
            print(f"  - {rec['description']} ({rec['effort']} effort)")
    
    print(f"\n✅ Cleanup analysis complete!")
    return report


if __name__ == "__main__":
    main()
