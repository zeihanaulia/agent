#!/bin/bash

# Quick Integration Test for Phase 4 Code Synthesis
# This script provides a fast way to test Phase 4 improvements
# For detailed testing, use: integration_test_phase4_enhanced.sh

echo "=================================="
echo "🚀 Quick Phase 4 Integration Test"
echo "=================================="
echo ""
echo "Activating venv..."
source .venv/bin/activate

echo ""
echo "Running V3 Agent with Phase 4 focus..."
echo "Feature: Add product management feature with CRUD operations"
echo ""

python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add product management feature with CRUD operations" \
  2>&1 | tee /tmp/phase4_quick_test.log

echo ""
echo "=================================="
echo "✅ Quick Test Complete"
echo "=================================="
echo ""
echo "📋 Log saved to: /tmp/phase4_quick_test.log"
echo ""
echo "🎯 Key improvements to verify:"
echo "  ✅ Data Consumption Summary shows comprehensive data usage"
echo "  ✅ Timeouts increased (60s analysis, 120s implementation)"
echo "  ✅ Explicit file creation guidance in prompts"
echo "  ✅ Reduced 'empty file path' warnings"
echo "  ✅ More code patches generated successfully"
echo ""
echo "📖 For detailed testing with checklist, run:"
echo "    ./scripts/integration_test_phase4_enhanced.sh"
echo ""
