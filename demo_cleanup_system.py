"""
Demo Cleanup System

Demonstrates the codebase cleanup and refactoring capabilities without
making actual changes to the codebase.
"""

import sys
import os
from pathlib import Path

# Add cleanup directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cleanup'))

from cleanup.codebase_cleanup import CodebaseCleanup


def demo_cleanup_analysis():
    """Demonstrate cleanup analysis capabilities"""
    print("=== Digital Freight Matching Codebase Cleanup Demo ===")
    print("This demo analyzes the codebase for cleanup opportunities without making changes.\n")

    # Initialize cleanup analyzer
    cleanup = CodebaseCleanup()

    print("🔍 Analyzing codebase structure...")
    print(f"  📁 Project root: {cleanup.project_root}")
    print(f"  📄 Python files found: {len(cleanup.python_files)}")

    # Show file distribution
    file_types = {}
    for file_path in cleanup.python_files:
        if 'test' in str(file_path):
            file_types['test_files'] = file_types.get('test_files', 0) + 1
        elif 'demo' in str(file_path):
            file_types['demo_files'] = file_types.get('demo_files', 0) + 1
        elif 'app' in str(file_path):
            file_types['app_files'] = file_types.get('app_files', 0) + 1
        else:
            file_types['other_files'] = file_types.get('other_files', 0) + 1

    print("  📊 File distribution:")
    for file_type, count in file_types.items():
        print(f"    {file_type}: {count}")

    print("\n" + "="*60)

    # Run comprehensive analysis
    report = cleanup.generate_cleanup_report()

    if "error" in report:
        print(f"❌ Analysis failed: {report['error']}")
        return

    # Display detailed results
    print("\n📋 DETAILED ANALYSIS RESULTS")
    print("="*60)

    # Duplicate code analysis
    print(f"\n🔄 DUPLICATE CODE ANALYSIS")
    print(f"Found {len(report['duplicates'])} potential duplicates:")

    if report['duplicates']:
        print("\n_Top duplicates:")
        for i, dup in enumerate(report['duplicates'][:5], 1):
            file1_name = Path(dup['file1']).name
            file2_name = Path(dup['file2']).name
            print(f"  {i}. Function '{dup['function']}' ({dup['similarity']:.1%} similar)")
            print(f"     📁 {file1_name} ↔️ {file2_name}")
            print(f"     📏 {dup['lines']} lines")
    else:
        print("  ✅ No significant duplicates found!")

    # Dead code analysis
    print(f"\n🗑️  DEAD CODE ANALYSIS")
    print(f"Found {len(report['dead_code'])} potentially unused items:")

    if report['dead_code']:
        # Group by type
        by_type = {}
        for item in report['dead_code']:
            item_type = item['type']
            by_type[item_type] = by_type.get(item_type, 0) + 1

        print("\n_Breakdown by type:")
        for item_type, count in by_type.items():
            print(f"  📦 {item_type}: {count} items")

        print("\n_Top unused items:")
        for i, item in enumerate(report['dead_code'][:8], 1):
            file_name = Path(item['file']).name
            print(f"  {i}. {item['type']} '{item['name']}' in {file_name}:{item['line']}")
            print(f"     💡 {item['reason']}")
    else:
        print("  ✅ No dead code found!")

    # Quality issues analysis
    print(f"\n✨ CODE QUALITY ANALYSIS")
    total_issues = sum(qr['issues_count'] for qr in report['quality_issues'])
    print(f"Found {total_issues} quality issues across {len(report['quality_issues'])} files:")

    if report['quality_issues']:
        # Show files with most issues
        files_by_issues = sorted(report['quality_issues'],
                               key=lambda x: x['issues_count'], reverse=True)

        print("\n_Files needing attention:")
        for i, file_report in enumerate(files_by_issues[:5], 1):
            file_name = Path(file_report['file']).name
            print(f"  {i}. {file_name}: {file_report['issues_count']} issues")
            print(f"     🔧 Complexity: {file_report['complexity']:.1f}")
            print(f"     📊 Maintainability: {file_report['maintainability']:.1f}")

            # Show top issues for this file
            if file_report['issues']:
                top_issue = file_report['issues'][0]
                print(f"     ⚠️  {top_issue['type']}: {top_issue['description']}")
    else:
        print("  ✅ No quality issues found!")

    # Refactoring recommendations
    print(f"\n🔧 REFACTORING RECOMMENDATIONS")
    print(f"Found {len(report['refactoring_recommendations'])} opportunities:")

    if report['refactoring_recommendations']:
        # Group by priority
        by_priority = {}
        for rec in report['refactoring_recommendations']:
            priority = rec['priority']
            by_priority[priority] = by_priority.get(priority, 0) + 1

        print("\n_By priority:")
        for priority in ['high', 'medium', 'low']:
            count = by_priority.get(priority, 0)
            if count > 0:
                print(f"  🔥 {priority}: {count} recommendations")

        print("\n_Top recommendations:")
        high_priority = [r for r in report['refactoring_recommendations'] if r['priority'] == 'high']
        for i, rec in enumerate(high_priority[:3], 1):
            file_name = Path(rec['file']).name
            print(f"  {i}. {rec['description']}")
            print(f"     📁 File: {file_name}")
            print(f"     ⏱️  Effort: {rec['effort']}")
            print(f"     💡 Benefits: {', '.join(rec['benefits'][:2])}")
    else:
        print("  ✅ No refactoring opportunities identified!")

    # Summary and recommendations
    print(f"\n📊 CLEANUP SUMMARY")
    print("="*60)

    summary = report['summary']
    print(f"📈 Overall Assessment:")
    print(f"  • Files analyzed: {report['files_analyzed']}")
    print(f"  • Files with issues: {summary['files_with_issues']}")
    print(f"  • Total cleanup opportunities: {summary['duplicate_functions'] + summary['dead_code_items']}")

    # Calculate cleanup priority
    total_issues = (summary['duplicate_functions'] +
                   summary['dead_code_items'] +
                   summary['quality_issues'])

    if total_issues > 100:
        priority = "🔴 HIGH"
        message = "Significant cleanup needed"
    elif total_issues > 50:
        priority = "🟡 MEDIUM"
        message = "Moderate cleanup recommended"
    else:
        priority = "🟢 LOW"
        message = "Codebase is in good shape"

    print(f"\n🎯 Cleanup Priority: {priority}")
    print(f"💬 Recommendation: {message}")

    # Next steps
    print(f"\n🚀 RECOMMENDED NEXT STEPS")
    print("="*60)

    if summary['dead_code_items'] > 20:
        print("1. 🗑️  Remove unused imports and obvious dead code")

    if summary['duplicate_functions'] > 10:
        print("2. 🔄 Consolidate duplicate functions")

    if summary['quality_issues'] > 50:
        print("3. ✨ Address code quality issues")

    if summary['refactoring_opportunities'] > 5:
        print("4. 🔧 Implement high-priority refactoring recommendations")

    print("5. 📝 Update documentation to reflect changes")
    print("6. 🧪 Run comprehensive tests after cleanup")

    print(f"\n⚠️  SAFETY NOTE: Always backup code before running automated cleanup!")
    print(f"💾 The cleanup executor creates automatic backups in 'cleanup_backups/' directory")

    print(f"\n✅ Analysis complete! Use 'python cleanup/cleanup_executor.py' to execute cleanup.")

    return report


if __name__ == "__main__":
    demo_cleanup_analysis()
