#!/bin/bash
# Organize Test Files
# Author: Hoseyn Doulabi (@hoseynd-ai)
# Date: 2025-10-25

echo "============================================================"
echo "📁 Organizing Test Files"
echo "============================================================"
echo ""

cd ~/Desktop/gold-price-analyzer/backend

# Create directories
echo "📂 Creating test directories..."
mkdir -p tests/integration
mkdir -p tests/analysis
mkdir -p tests/visualization
mkdir -p tests/scripts

# Create __init__.py files
touch tests/__init__.py
touch tests/integration/__init__.py
touch tests/analysis/__init__.py
touch tests/visualization/__init__.py
touch tests/scripts/__init__.py

echo "✅ Directories created"
echo ""

# Move integration tests
echo "📦 Moving integration tests..."
mv -f test_alpha_vantage.py tests/integration/ 2>/dev/null
mv -f test_real_gold_service.py tests/integration/ 2>/dev/null
mv -f test_converter.py tests/integration/ 2>/dev/null
echo "✅ Integration tests moved"
echo ""

# Move analysis tests
echo "📊 Moving analysis tests..."
mv -f test_data_range.py tests/analysis/ 2>/dev/null
mv -f test_gld_conversion.py tests/analysis/ 2>/dev/null
mv -f test_final_data.py tests/analysis/ 2>/dev/null
echo "✅ Analysis tests moved"
echo ""

# Move visualization
echo "📈 Moving visualization scripts..."
mv -f visualize_gold_data.py tests/visualization/ 2>/dev/null
mv -f simple_chart.py tests/visualization/ 2>/dev/null
echo "✅ Visualization scripts moved"
echo ""

# Move utility scripts
echo "🔧 Moving utility scripts..."
mv -f fetch_full_history.py tests/scripts/ 2>/dev/null
mv -f test_converter_debug.py tests/scripts/ 2>/dev/null
echo "✅ Utility scripts moved"
echo ""

# Show final structure
echo "============================================================"
echo "📊 Final Structure:"
echo "============================================================"
tree tests/ -L 2 2>/dev/null || find tests/ -type f -name "*.py" | sort

echo ""
echo "============================================================"
echo "🎉 Organization Complete!"
echo "============================================================"
echo ""
echo "📝 Update imports in files:"
echo "   Old: python test_alpha_vantage.py"
echo "   New: python -m tests.integration.test_alpha_vantage"
echo ""
echo "Or run from tests directory:"
echo "   cd tests/integration && python test_alpha_vantage.py"
echo ""
