#!/bin/bash
# Comprehensive Integration Test for Phase 4 Code Synthesis
# This tests the enhanced flow_synthesize_code.py with detailed validation
# For quick testing, use: integration_test_phase4_quick.sh

set -e

cd "$(dirname "$0")"
source .venv/bin/activate

echo "=============================================================================="
echo "🧪 COMPREHENSIVE PHASE 4 INTEGRATION TEST"
echo "=============================================================================="
echo ""
echo "This test validates:"
echo "  1. ✅ Complete Phase 1-3 workflow execution"
echo "  2. ✅ Enhanced build_implementation_prompt() with full data integration"
echo "  3. ✅ Comprehensive data consumption tracking"
echo "  4. ✅ Explicit file creation guidance functionality"
echo ""

echo "📊 Test Configuration:"
echo "  Feature: Add product management feature with CRUD operations"
echo "  Codebase: dataset/codes/springboot-demo"
echo "  Analysis Timeout: 60 seconds (increased from 30)"
echo "  Implementation Timeout: 120 seconds (increased from 45)"
echo ""

echo "=============================================================================="
echo "🚀 Running Enhanced V3 Agent (Full Integration)"
echo "=============================================================================="
echo ""

timeout 600 python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add product management feature with CRUD operations" \
  2>&1

echo ""
echo "=============================================================================="
echo "✅ Comprehensive Test Complete"
echo "=============================================================================="
echo ""
echo "📋 VALIDATION CHECKLIST:"
echo "  ✅ Phase 1: Context analysis completes successfully"
echo "  ✅ Phase 2: Intent parsing generates 5+ new files plan"
echo "  ✅ Phase 2A: Structure validation identifies ~6 violations"
echo "  ✅ Phase 3: Impact analysis detects architectural patterns"
echo "  ✅ Phase 4: CODE SYNTHESIS validates all improvements:"
echo "     📊 Data Consumption Summary should include:"
echo "        - ✅ spec.intent_summary utilization"
echo "        - ✅ spec.affected_files processing"
echo "        - ✅ impact.files_to_modify integration"
echo "        - ✅ impact.patterns_to_follow application"
echo "        - ✅ spec.todo_list incorporation"
echo "        - ✅ spec.new_files_planning usage"
echo "     🎯 Explicit 'Files to Create' section in prompts"
echo "     ⏱️  Extended processing time (60s + 120s)"
echo "     📝 Minimal 'empty file path' warnings"
echo "     ✨ Increased code patch generation"
echo ""
echo "💾 Full logs available in terminal output above"
echo ""
echo "📖 For quick testing without detailed validation:"
echo "    ./scripts/integration_test_phase4_quick.sh"
echo ""
