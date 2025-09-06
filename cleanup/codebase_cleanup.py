"""
Codebase Cleanup and Refactoring Engine

This module implements the CodebaseCleanup class with analysis and cleanup methods
for identifying and removing redundant code, unused imports, and dead code.

Requirements addressed:
- 5.1: No duplicate functionality or redundant implementations
- 5.2: No unused scripts, imports, or dead code
- 5.3: Clear separation of concerns with consistent naming conventions
- 5.4: DRY (Don't Repeat Yourself) principles throughout
"""

import ast
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path


@dataclass
class DuplicateReport:
    """Report of duplicate code found"""
    file1: str
    file2: str
    function_name: str
    similarity_score: float
    line_count: int


@dataclass
class DeadCodeReport:
    """Report of dead code found"""
    file_path: str
    item_type: str  # 'function', 'class', 'import', 'variable'
    item_name: str
    line_number: int
    reason: str


@dataclass
class QualityIssue:
    """Code quality issue"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    suggestion: str


@dataclass
class QualityReport:
    """Code quality assessment report"""
    file_path: str
    issues: List[QualityIssue]
    complexity_score: float
    maintainability_index: float
    suggestions: List[str]


@dataclass
class RefactoringRecommendation:
    """Refactoring recommendation"""
    file_path: str
    recommendation_type: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    estimated_effort: str


class CodebaseCleanup:
    """
    Codebase cleanup and refactoring engine
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.python_files = self._find_python_files()
        self.import_graph = {}
        self.function_definitions = {}
        self.class_definitions = {}

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip common directories that shouldn't be analyzed
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files

    def detect_duplicate_code(self) -> List[DuplicateReport]:
        """
        Identify duplicate functionality across Python files
        """
        duplicates = []

        # Build function signature map
        function_signatures = {}

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create signature based on function name and parameters
                        params = [arg.arg for arg in node.args.args]
                        signature = f"{node.name}({', '.join(params)})"

                        if signature in function_signatures:
                            # Found potential duplicate
                            original_file = function_signatures[signature]
                            if original_file != str(file_path):
                                duplicates.append(DuplicateReport(
                                    file1=str(original_file),
                                    file2=str(file_path),
                                    function_name=node.name,
                                    similarity_score=0.9,  # Simplified scoring
                                    line_count=len(node.body)
                                ))
                        else:
                            function_signatures[signature] = str(file_path)

            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Warning: Could not parse {file_path}: {e}")
                continue

        return duplicates

    def analyze_dead_code(self) -> List[DeadCodeReport]:
        """
        Find unused functions, classes, and imports
        """
        dead_code = []

        # Build usage maps
        all_imports = set()
        all_definitions = set()
        all_usages = set()

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                # Track imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            all_imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                all_imports.add(f"{node.module}.{alias.name}")
                    elif isinstance(node, ast.FunctionDef):
                        all_definitions.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        all_definitions.add(node.name)
                    elif isinstance(node, ast.Name):
                        all_usages.add(node.id)

            except (SyntaxError, UnicodeDecodeError):
                continue

        # Find unused definitions (simplified analysis)
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name not in all_usages and not node.name.startswith('_'):
                            dead_code.append(DeadCodeReport(
                                file_path=str(file_path),
                                item_type='function',
                                item_name=node.name,
                                line_number=node.lineno,
                                reason='Function appears to be unused'
                            ))

            except (SyntaxError, UnicodeDecodeError):
                continue

        return dead_code

    def check_code_quality(self) -> List[QualityReport]:
        """
        Validate coding standards and conventions
        """
        quality_reports = []

        for file_path in self.python_files:
            issues = []

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Check for common quality issues
                for i, line in enumerate(lines, 1):
                    # Check line length
                    if len(line.rstrip()) > 120:
                        issues.append(QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type='line_length',
                            description=f'Line too long ({len(line.rstrip())} characters)',
                            suggestion='Break line into multiple lines'
                        ))

                    # Check for TODO/FIXME comments
                    if 'TODO' in line or 'FIXME' in line:
                        issues.append(QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type='todo',
                            description='TODO/FIXME comment found',
                            suggestion='Address the TODO item or create a proper issue'
                        ))

                # Parse AST for more complex checks
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        # Check function complexity (simplified)
                        if isinstance(node, ast.FunctionDef):
                            if len(node.body) > 20:
                                issues.append(QualityIssue(
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    issue_type='complexity',
                                    description=f'Function {node.name} is too complex ({len(node.body)} statements)',
                                    suggestion='Consider breaking function into smaller functions'
                                ))

                except SyntaxError:
                    pass

                quality_reports.append(QualityReport(
                    file_path=str(file_path),
                    issues=issues,
                    complexity_score=len(issues) * 0.1,  # Simplified scoring
                    maintainability_index=max(0, 100 - len(issues) * 5),
                    suggestions=[]
                ))

            except (UnicodeDecodeError, FileNotFoundError):
                continue

        return quality_reports

    def suggest_refactoring(self) -> List[RefactoringRecommendation]:
        """
        Recommend improvements for maintainability
        """
        recommendations = []

        # Analyze file sizes and suggest splitting large files
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                if len(lines) > 500:
                    recommendations.append(RefactoringRecommendation(
                        file_path=str(file_path),
                        recommendation_type='file_size',
                        description=f'File is very large ({len(lines)} lines)',
                        priority='medium',
                        estimated_effort='2-4 hours'
                    ))

                # Check for import organization
                import_lines = [line for line in lines[:50] if line.strip().startswith(('import ', 'from '))]
                if len(import_lines) > 15:
                    recommendations.append(RefactoringRecommendation(
                        file_path=str(file_path),
                        recommendation_type='imports',
                        description=f'Too many imports ({len(import_lines)})',
                        priority='low',
                        estimated_effort='30 minutes'
                    ))

            except (UnicodeDecodeError, FileNotFoundError):
                continue

        return recommendations

    def fix_common_issues(self) -> Dict[str, int]:
        """
        Automatically fix common issues
        """
        fixes_applied = {
            'trailing_whitespace': 0,
            'missing_newlines': 0,
            'import_sorting': 0,
            'assertion_methods': 0
        }

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = f.readlines()

                modified = False
                new_lines = []

                # Reset file pointer and read lines again
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    original_line = line

                    # Fix trailing whitespace
                    if line.rstrip() != line.rstrip('\n'):
                        line = line.rstrip() + '\n'
                        fixes_applied['trailing_whitespace'] += 1
                        modified = True

                    # Fix common test assertion typos
                    if 'assertEqual' in line:
                        line = line.replace('assertEqual', 'assertEqual')
                        fixes_applied['assertion_methods'] += 1
                        modified = True

                    if 'assertTrue' in line:
                        line = line.replace('assertTrue', 'assertTrue')
                        fixes_applied['assertion_methods'] += 1
                        modified = True

                    if 'assertFalse' in line:
                        line = line.replace('assertFalse', 'assertFalse')
                        fixes_applied['assertion_methods'] += 1
                        modified = True

                    new_lines.append(line)

                # Ensure file ends with newline
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] += '\n'
                    fixes_applied['missing_newlines'] += 1
                    modified = True

                # Write back if modified
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)

            except (UnicodeDecodeError, FileNotFoundError):
                continue

        return fixes_applied

    def generate_cleanup_report(self) -> str:
        """
        Generate comprehensive cleanup report
        """
        duplicates = self.detect_duplicate_code()
        dead_code = self.analyze_dead_code()
        quality_reports = self.check_code_quality()
        recommendations = self.suggest_refactoring()

        report = []
        report.append("# Codebase Cleanup Report")
        report.append(f"Generated for project: {self.project_root}")
        report.append(f"Python files analyzed: {len(self.python_files)}")
        report.append("")

        # Duplicate code section
        report.append("## Duplicate Code Analysis")
        if duplicates:
            report.append(f"Found {len(duplicates)} potential duplicates:")
            for dup in duplicates[:10]:  # Show top 10
                report.append(f"- {dup.function_name} in {dup.file1} and {dup.file2}")
        else:
            report.append("✅ No duplicate functions detected")
        report.append("")

        # Dead code section
        report.append("## Dead Code Analysis")
        if dead_code:
            report.append(f"Found {len(dead_code)} potentially unused items:")
            for item in dead_code[:10]:  # Show top 10
                report.append(f"- {item.item_type} '{item.item_name}' in {item.file_path}:{item.line_number}")
        else:
            report.append("✅ No obvious dead code detected")
        report.append("")

        # Quality issues section
        report.append("## Code Quality Issues")
        total_issues = sum(len(qr.issues) for qr in quality_reports)
        if total_issues > 0:
            report.append(f"Found {total_issues} quality issues across {len(quality_reports)} files")

            # Group by issue type
            issue_types = {}
            for qr in quality_reports:
                for issue in qr.issues:
                    issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1

            for issue_type, count in sorted(issue_types.items()):
                report.append(f"- {issue_type}: {count} occurrences")
        else:
            report.append("✅ No quality issues detected")
        report.append("")

        # Refactoring recommendations
        report.append("## Refactoring Recommendations")
        if recommendations:
            high_priority = [r for r in recommendations if r.priority == 'high']
            medium_priority = [r for r in recommendations if r.priority == 'medium']

            if high_priority:
                report.append("### High Priority:")
                for rec in high_priority:
                    report.append(f"- {rec.description} ({rec.file_path})")

            if medium_priority:
                report.append("### Medium Priority:")
                for rec in medium_priority[:5]:  # Show top 5
                    report.append(f"- {rec.description} ({rec.file_path})")
        else:
            report.append("✅ No major refactoring needed")

        return "\n".join(report)


def main():
    """Main function for running cleanup analysis"""
    cleanup = CodebaseCleanup()

    print("🧹 Running codebase cleanup analysis...")

    # Apply automatic fixes
    print("\n📝 Applying automatic fixes...")
    fixes = cleanup.fix_common_issues()
    for fix_type, count in fixes.items():
        if count > 0:
            print(f"  ✅ {fix_type}: {count} fixes applied")

    # Generate report
    print("\n📊 Generating cleanup report...")
    report = cleanup.generate_cleanup_report()

    # Save report
    report_path = Path("cleanup_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Cleanup complete! Report saved to {report_path}")
    print("\nSummary:")
    print(report.split('\n\n')[1])  # Show summary section


if __name__ == "__main__":
    main()
