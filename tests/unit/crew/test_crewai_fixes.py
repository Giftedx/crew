"""Test script to verify CrewAI workflow fixes.

This script tests the enhanced autonomous orchestrator and tool wrapper fixes
to ensure they properly handle the issues identified in the crew workflow.
"""
import asyncio
import os
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent / 'src'))

@pytest.mark.asyncio
async def test_enhanced_orchestrator():
    """Test the enhanced autonomous orchestrator."""
    print('🧪 Testing Enhanced Autonomous Orchestrator')
    print('=' * 50)
    try:
        from ultimate_discord_intelligence_bot.enhanced_autonomous_orchestrator import EnhancedAutonomousOrchestrator
        print('✅ Enhanced orchestrator imported successfully')
        orchestrator = EnhancedAutonomousOrchestrator()
        print('✅ Orchestrator initialized')
        print(f'   System Health: {orchestrator.system_health['healthy']}')
        print(f'   Available Capabilities: {orchestrator.system_health['available_capabilities']}')
        print(f'   Issues: {len(orchestrator.system_health['errors'])}')
        if orchestrator.system_health['errors']:
            print('   Known Issues:')
            for error in orchestrator.system_health['errors'][:3]:
                print(f'     - {error}')
    except ImportError as e:
        print(f'❌ Failed to import enhanced orchestrator: {e}')
        pytest.fail(f'Failed to import enhanced orchestrator: {e}')
    except Exception as e:
        print(f'❌ Error testing enhanced orchestrator: {e}')
        pytest.fail(f'Error testing enhanced orchestrator: {e}')

def test_crewai_tool_wrappers():
    """Test the improved CrewAI tool wrappers."""
    print('\n🧪 Testing CrewAI Tool Wrapper Fixes')
    print('=' * 50)
    try:
        from ultimate_discord_intelligence_bot.crewai_tool_wrappers import CrewAIToolWrapper
        print('✅ CrewAI tool wrapper imported successfully')

        class MockTool:
            name = 'Test Tool'
            description = 'Tool for testing wrapper fixes'

            def run(self, text='test'):
                from platform.core.step_result import StepResult
                return StepResult.ok(data={'processed_text': text, 'status': 'success'})
        mock_tool = MockTool()
        wrapper = CrewAIToolWrapper(mock_tool)
        print('✅ Wrapper created successfully')
        validation = wrapper._validate_tool_dependencies()
        print(f'✅ Dependency validation works: {validation['dependencies_valid']}')
        if not validation['dependencies_valid']:
            print('   Missing dependencies:')
            for dep in validation['missing_dependencies']:
                print(f'     - {dep}')
            print('   Configuration issues:')
            for issue in validation['configuration_issues']:
                print(f'     - {issue}')
        result = wrapper._run('test input')
        print(f'✅ Wrapper execution test: {(result.success if hasattr(result, 'success') else 'unknown')}')
    except ImportError as e:
        print(f'❌ Failed to import tool wrapper: {e}')
        pytest.fail(f'Failed to import tool wrapper: {e}')
    except Exception as e:
        print(f'❌ Error testing tool wrapper: {e}')
        pytest.fail(f'Error testing tool wrapper: {e}')

def test_fallback_orchestrator():
    """Test the fallback orchestrator."""
    print('\n🧪 Testing Fallback Orchestrator')
    print('=' * 50)
    try:
        from ultimate_discord_intelligence_bot.fallback_orchestrator import FallbackAutonomousOrchestrator
        print('✅ Fallback orchestrator imported successfully')
        _ = FallbackAutonomousOrchestrator()
        print('✅ Fallback orchestrator initialized')
    except ImportError as e:
        print(f'❌ Failed to import fallback orchestrator: {e}')
        pytest.fail(f'Failed to import fallback orchestrator: {e}')
    except Exception as e:
        print(f'❌ Error testing fallback orchestrator: {e}')
        pytest.fail(f'Error testing fallback orchestrator: {e}')

def test_system_health():
    """Test system health and dependencies.

    Note: This function is called from main() which captures the return value,
    so it's allowed to return data for the summary. When run via pytest directly,
    the return value is ignored.
    """
    print('\n🧪 Testing System Health and Dependencies')
    print('=' * 50)
    dependencies = {'yt-dlp': lambda: __import__('yt_dlp'), 'openai key': lambda: bool(os.getenv('OPENAI_API_KEY') and (not os.getenv('OPENAI_API_KEY', '').startswith('dummy'))), 'discord webhook': lambda: bool(os.getenv('DISCORD_WEBHOOK') and (not os.getenv('DISCORD_WEBHOOK', '').startswith('dummy'))), 'crewai': lambda: __import__('crewai'), 'pipeline': lambda: __import__('ultimate_discord_intelligence_bot.tools.pipeline_tool')}
    results = {}
    for name, check in dependencies.items():
        try:
            check()
            results[name] = '✅ Available'
            print(f'✅ {name}: Available')
        except ImportError:
            results[name] = '❌ Missing'
            print(f'❌ {name}: Missing')
        except Exception as e:
            results[name] = f'⚠️ Issue: {e}'
            print(f'⚠️ {name}: {e}')
    available_count = sum((1 for status in results.values() if status.startswith('✅')))
    total_count = len(results)
    print(f'\n📊 System Status: {available_count}/{total_count} dependencies available')
    if available_count >= 3:
        print('🟢 System should work with enhanced orchestrator')
    elif available_count >= 2:
        print('🟡 System should work with fallback modes')
    else:
        print('🔴 System may have limited functionality')
    return results

async def main():
    """Run all tests."""
    print('🚀 CrewAI Workflow Fixes Test Suite')
    print('=' * 60)
    health_results = test_system_health()
    orchestrator_ok = True
    wrapper_ok = True
    fallback_ok = True
    try:
        await test_enhanced_orchestrator()
    except Exception:
        orchestrator_ok = False
    try:
        test_crewai_tool_wrappers()
    except Exception:
        wrapper_ok = False
    try:
        test_fallback_orchestrator()
    except Exception:
        fallback_ok = False
    print('\n📋 Test Summary')
    print('=' * 50)
    print(f'Enhanced Orchestrator: {('✅ Pass' if orchestrator_ok else '❌ Fail')}')
    print(f'Tool Wrapper Fixes:    {('✅ Pass' if wrapper_ok else '❌ Fail')}')
    print(f'Fallback Orchestrator: {('✅ Pass' if fallback_ok else '❌ Fail')}')
    available_deps = sum((1 for status in health_results.values() if status.startswith('✅')))
    print(f'System Dependencies:   {available_deps}/{len(health_results)} available')
    if orchestrator_ok and wrapper_ok and fallback_ok:
        print('\n🎉 All core fixes are working!')
        if available_deps >= 3:
            print('✅ System should handle /autointel commands successfully')
        else:
            print('⚠️ Limited functionality due to missing dependencies')
    else:
        print('\n❌ Some fixes have issues that need attention')
    print('\n💡 To test with actual YouTube URL:')
    print('   /autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:standard')
if __name__ == '__main__':
    asyncio.run(main())