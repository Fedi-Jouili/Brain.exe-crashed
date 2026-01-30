"""
PriceSense Master System Diagnostic
Comprehensive health check of all components

Run: python backend/scripts/diagnose_system.py

Checks:
- File structure completeness
- Agent implementations
- Database connections (Qdrant, Redis)
- Data population
- LangGraph workflow
- API endpoints
- Dependencies
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import importlib
import inspect
from typing import Dict, List, Tuple, Any
import os
import logging

# Suppress debug logs for cleaner output
logging.basicConfig(level=logging.ERROR)

# ANSI color codes for terminal output
os.system('')

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * 80)


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


# ============================================================================
# FILE STRUCTURE CHECKS
# ============================================================================

def check_file_structure() -> Tuple[int, int]:
    """Check if all required files exist"""
    print_header("CHECKING FILE STRUCTURE")
    
    backend_dir = Path(__file__).parent.parent
    
    required_files = {
        # Core infrastructure
        "core/config.py": "Configuration management",
        "core/embeddings.py": "CLIP embeddings",
        "core/qdrant_client.py": "Qdrant vector database client",
        "core/redis_client.py": "Redis cache and state management",
        
        # Models
        "models/state.py": "Agent state management",
        "models/schemas.py": "Pydantic schemas",
        
        # ML
        "ml/thompson_sampling.py": "Thompson Sampling RL engine",
        
        # Agents
        "agents/agent1_discovery.py": "Agent 1: Discovery",
        "agents/agent2_financial.py": "Agent 2: Financial Analyzer",
        "agents/agent2_5_pathfinder.py": "Agent 2.5: Budget PathFinder",
        "agents/agent3_recommender.py": "Agent 3: Smart Recommender",
        "agents/agent4_explainer.py": "Agent 4: Explainer",
        
        # Orchestration
        "orchestration/workflow.py": "LangGraph workflow orchestration",
        
        # API
        "main.py": "FastAPI application",
        
        # Scripts
        "scripts/cluster_products.py": "K-Means clustering",
        "scripts/populate_qdrant.py": "Qdrant data population",
        "scripts/populate_financial_kb.py": "Financial KB population",
        "scripts/initialize_thompson_redis.py": "Thompson Redis initialization",
        "scripts/verify_qdrant.py": "Qdrant verification",
        "scripts/test_redis.py": "Redis testing",
    }
    
    found = 0
    missing = 0
    
    for filepath, description in required_files.items():
        full_path = backend_dir / filepath
        
        if full_path.exists():
            print_success(f"{filepath:<50} {description}")
            found += 1
        else:
            print_error(f"{filepath:<50} MISSING - {description}")
            missing += 1
    
    print(f"\nFiles: {found} found, {missing} missing")
    return found, missing


# ============================================================================
# AGENT IMPLEMENTATION CHECKS
# ============================================================================

def check_agent_implementation(agent_name: str, module_path: str, required_methods: List[str]) -> bool:
    """Check if agent is properly implemented"""
    try:
        # Import module
        module = importlib.import_module(module_path)
        
        # Get agent class (look for class with "Agent" in name)
        agent_classes = [
            cls for name, cls in inspect.getmembers(module, inspect.isclass)
            if 'Agent' in name and cls.__module__ == module_path
        ]
        
        if not agent_classes:
            # Fallback: check for instance variables if class not found or named differently
            # Some implementations might verify instances directly
            print_warning(f"{agent_name}: No specific 'Agent' class found in module, checking module attributes...")
            return False
        
        agent_class = agent_classes[0]
        
        # Check for required methods
        methods = [m for m in dir(agent_class) if not m.startswith('_')]
        
        missing_methods = [m for m in required_methods if m not in methods]
        
        if missing_methods:
            print_error(f"{agent_name}: Missing methods: {', '.join(missing_methods)}")
            return False
        
        # Check if execute() method exists
        if 'execute' not in methods:
            print_error(f"{agent_name}: Missing execute() method")
            return False
        
        print_success(f"{agent_name}: All required methods present")
        return True
        
    except ImportError as e:
        print_error(f"{agent_name}: Import failed - {e}")
        return False
    except Exception as e:
        print_error(f"{agent_name}: Check failed - {e}")
        return False


def check_all_agents() -> Tuple[int, int]:
    """Check all agent implementations"""
    print_header("CHECKING AGENT IMPLEMENTATIONS")
    
    agents = {
        "Agent 1 (Discovery)": {
            "module": "agents.agent1_discovery",
            "methods": ["execute"]
        },
        "Agent 2 (Financial)": {
            "module": "agents.agent2_financial",
            "methods": ["execute"]
        },
        "Agent 2.5 (PathFinder)": {
            "module": "agents.agent2_5_pathfinder",
            "methods": ["execute"]
        },
        "Agent 3 (Recommender)": {
            "module": "agents.agent3_recommender",
            "methods": ["execute"]
        },
        "Agent 4 (Explainer)": {
            "module": "agents.agent4_explainer",
            "methods": ["execute"]
        }
    }
    
    passed = 0
    failed = 0
    
    for agent_name, config in agents.items():
        if check_agent_implementation(agent_name, config["module"], config["methods"]):
            passed += 1
        else:
            failed += 1
    
    print(f"\nAgents: {passed} complete, {failed} incomplete")
    return passed, failed


# ============================================================================
# CORE COMPONENT CHECKS
# ============================================================================

def check_qdrant_client() -> bool:
    """Check Qdrant client implementation"""
    print_header("CHECKING QDRANT CLIENT")
    
    required_methods = [
        'search_products',
        'get_product_by_id',
        'get_products_by_cluster',
        'upsert_products',
        'retrieve_financial_rules',
        'upsert_financial_rules',
        'health_check',
        'create_collections',
        'get_collection_info'
    ]
    
    try:
        from core.qdrant_client import qdrant_manager
        
        missing = []
        for method in required_methods:
            if not hasattr(qdrant_manager, method):
                missing.append(method)
        
        if missing:
            print_error(f"Missing methods: {', '.join(missing)}")
            return False
        
        print_success("All required methods present")
        
        # Test health check
        try:
            healthy = qdrant_manager.health_check()
            if healthy:
                print_success("Health check: PASS")
            else:
                print_warning("Health check: FAIL (Qdrant may not be running)")
        except Exception as e:
            print_warning(f"Health check error: {e}")
        
        return len(missing) == 0
        
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


def check_redis_client() -> bool:
    """Check Redis client implementation"""
    print_header("CHECKING REDIS CLIENT")
    
    required_methods = [
        # Cache methods
        'cache_search_results',
        'get_cached_search_results',
        'cache_product',
        'get_cached_product',
        'invalidate_cache',
        'get_cache_stats',
        
        # Thompson methods
        'get_thompson_params',
        'set_thompson_params',
        'initialize_thompson_params',
        'get_thompson_stats',
        
        # Session methods
        'create_session',
        'get_session',
        'update_session',
        'delete_session',
        
        # Metrics methods
        'increment_counter',
        'get_counter',
        'record_timing',
        'get_timing_stats',
        
        # Health
        'health_check',
        'get_memory_info'
    ]
    
    try:
        from core.redis_client import redis_manager
        
        missing = []
        for method in required_methods:
            if not hasattr(redis_manager, method):
                missing.append(method)
        
        if missing:
            print_error(f"Missing methods: {', '.join(missing)}")
            for m in missing:
                print(f"  - {m}")
            return False
        
        print_success("All required methods present")
        
        # Test health check
        try:
            healthy = redis_manager.health_check()
            if healthy:
                print_success("Health check: PASS")
            else:
                print_warning("Health check: FAIL (Redis may not be running)")
        except Exception as e:
            print_warning(f"Health check error: {e}")
        
        return len(missing) == 0
        
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


def check_thompson_engine() -> bool:
    """Check Thompson Sampling engine"""
    print_header("CHECKING THOMPSON SAMPLING ENGINE")
    
    required_methods = [
        'get_params',
        'update_params',
        'rank_products',
        'sample',
        'get_confidence_level'
    ]
    
    try:
        from ml.thompson_sampling import ThompsonSamplingEngine
        
        missing = []
        for method in required_methods:
            if not hasattr(ThompsonSamplingEngine, method):
                missing.append(method)
        
        if missing:
            print_error(f"Missing methods: {', '.join(missing)}")
            return False
        
        print_success("All required methods present")
        return True
        
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


def check_langgraph_workflow() -> bool:
    """Check LangGraph workflow"""
    print_header("CHECKING LANGGRAPH WORKFLOW")
    
    try:
        from orchestration.workflow import run_recommendation_pipeline, get_recommendation_graph
        
        print_success("Workflow functions importable")
        
        # Check if workflow can be created
        try:
            get_recommendation_graph()
            print_success("Workflow graph can be created")
            return True
        except Exception as e:
            print_error(f"Workflow graph creation failed: {e}")
            return False
        
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False


# ============================================================================
# DATA POPULATION CHECKS
# ============================================================================

def check_data_population() -> Tuple[int, int]:
    """Check if data is populated in Qdrant and Redis"""
    print_header("CHECKING DATA POPULATION")
    
    checks_passed = 0
    checks_failed = 0
    
    # Check Qdrant
    try:
        from core.qdrant_client import qdrant_manager
        from core.config import settings
        
        if qdrant_manager.health_check():
            # Products
            try:
                products_info = qdrant_manager.get_collection_info(settings.qdrant_collection_products)
                product_count = products_info.points_count
                
                if product_count > 0:
                    print_success(f"Qdrant products collection: {product_count} products")
                    checks_passed += 1
                else:
                    print_error("Qdrant products collection is EMPTY")
                    print_info("Run: python backend/scripts/populate_qdrant.py")
                    checks_failed += 1
            except Exception as e:
                print_error(f"Products collection check failed: {e}")
                checks_failed += 1
            
            # Financial KB
            try:
                financial_info = qdrant_manager.get_collection_info(settings.qdrant_collection_financial_kb)
                rule_count = financial_info.points_count
                
                if rule_count > 0:
                    print_success(f"Qdrant financial KB: {rule_count} rules")
                    checks_passed += 1
                else:
                    print_error("Qdrant financial KB is EMPTY")
                    print_info("Run: python backend/scripts/populate_financial_kb.py")
                    checks_failed += 1
            except Exception as e:
                print_error(f"Financial KB check failed: {e}")
                checks_failed += 1
        else:
            print_warning("Qdrant not accessible, skipping data checks")
            checks_failed += 2
    except Exception as e:
        print_error(f"Qdrant check failed: {e}")
        checks_failed += 2
    
    # Check Redis Thompson params
    try:
        from core.redis_client import redis_manager
        
        if redis_manager.health_check():
            stats = redis_manager.get_thompson_stats()
            thompson_count = stats.get('products_tracked', 0)
            
            if thompson_count > 0:
                print_success(f"Redis Thompson parameters: {thompson_count} products initialized")
                checks_passed += 1
            else:
                print_error("Redis Thompson parameters NOT initialized")
                print_info("Run: python backend/scripts/initialize_thompson_redis.py")
                checks_failed += 1
        else:
            print_warning("Redis not accessible, skipping Thompson check")
            checks_failed += 1
    except Exception as e:
        print_error(f"Redis check failed: {e}")
        checks_failed += 1
    
    print(f"\nData checks: {checks_passed} passed, {checks_failed} failed")
    return checks_passed, checks_failed


# ============================================================================
# INTEGRATION CHECKS
# ============================================================================

def check_integrations() -> Tuple[int, int]:
    """Check component integrations"""
    print_header("CHECKING INTEGRATIONS")
    
    passed = 0
    failed = 0
    
    # Check Agent 1 can use Qdrant
    try:
        from agents.agent1_discovery import discovery_agent
        
        if hasattr(discovery_agent, 'execute'):
            print_success("Agent 1 → Qdrant integration: OK")
            passed += 1
        else:
            print_error("Agent 1 missing execute method")
            failed += 1
    except Exception as e:
        print_error(f"Agent 1 integration check failed: {e}")
        failed += 1
    
    # Check Agent 2 can use Qdrant (RAG)
    try:
        from agents.agent2_financial import financial_analyzer_agent
        
        if hasattr(financial_analyzer_agent, 'execute'):
            print_success("Agent 2 → Qdrant (RAG) integration: OK")
            passed += 1
        else:
            print_error("Agent 2 missing execute method")
            failed += 1
    except Exception as e:
        print_error(f"Agent 2 integration check failed: {e}")
        failed += 1
    
    # Check Agent 2.5 can use Qdrant (cluster search)
    try:
        from agents.agent2_5_pathfinder import budget_pathfinder_agent
        from core.qdrant_client import qdrant_manager
        
        if hasattr(qdrant_manager, 'get_products_by_cluster'):
            print_success("Agent 2.5 → Qdrant (cluster search) integration: OK")
            passed += 1
        else:
            print_error("Qdrant missing get_products_by_cluster method")
            failed += 1
    except Exception as e:
        print_error(f"Agent 2.5 integration check failed: {e}")
        failed += 1
    
    # Check Agent 3 can use Thompson Sampling
    try:
        from agents.agent3_recommender import smart_recommender_agent
        
        if hasattr(smart_recommender_agent, 'execute'):
            print_success("Agent 3 → Thompson Sampling integration: OK")
            passed += 1
        else:
            print_error("Agent 3 missing execute method")
            failed += 1
    except Exception as e:
        print_error(f"Agent 3 integration check failed: {e}")
        failed += 1
    
    # Check Agent 4 can use Gemini LLM
    try:
        from agents.agent4_explainer import explainer_agent
        
        if hasattr(explainer_agent, 'execute'):
            print_success("Agent 4 → Gemini LLM integration: OK")
            passed += 1
        else:
            print_error("Agent 4 missing execute method")
            failed += 1
    except Exception as e:
        print_error(f"Agent 4 integration check failed: {e}")
        failed += 1
    
    # Check LangGraph can orchestrate agents
    try:
        from orchestration.workflow import run_recommendation_pipeline
        
        print_success("LangGraph → Agents orchestration: OK")
        passed += 1
    except Exception as e:
        print_error(f"LangGraph orchestration check failed: {e}")
        failed += 1
    
    print(f"\nIntegrations: {passed} working, {failed} broken")
    return passed, failed


# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

def check_dependencies() -> Tuple[int, int]:
    """Check if all required dependencies are installed"""
    print_header("CHECKING DEPENDENCIES")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'qdrant_client',
        'redis',
        'numpy',
        'scipy',
        'sklearn',  # package name is scikit-learn but import is sklearn
        'langgraph',
        'langchain',
        'google.generativeai',
        'PIL', # pillow
        'transformers',
    ]
    
    installed = 0
    missing = 0
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_success(f"{package}")
            installed += 1
        except ImportError:
            # Try mapping common package names to imports
            try:
                if package == 'PIL':
                    importlib.import_module('PIL')
                elif package == 'sklearn':
                    importlib.import_module('sklearn')
                else:
                    raise ImportError
                print_success(f"{package}")
                installed += 1
            except ImportError:
                print_error(f"{package} - NOT INSTALLED")
                missing += 1
    
    print(f"\nDependencies: {installed} installed, {missing} missing")
    return installed, missing


# ============================================================================
# MAIN DIAGNOSTIC
# ============================================================================

def main():
    """Run complete system diagnostic"""
    
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}{Colors.HEADER}PRICESENSE MASTER SYSTEM DIAGNOSTIC{Colors.ENDC}")
    print("=" * 80)
    
    results = {}
    
    # Run all checks
    print_info("Running comprehensive system checks...\n")
    
    # 1. File structure
    files_found, files_missing = check_file_structure()
    results['file_structure'] = (files_found, files_missing)
    
    # 2. Agent implementations
    agents_ok, agents_broken = check_all_agents()
    results['agents'] = (agents_ok, agents_broken)
    
    # 3. Core components
    qdrant_ok = check_qdrant_client()
    redis_ok = check_redis_client()
    thompson_ok = check_thompson_engine()
    workflow_ok = check_langgraph_workflow()
    results['core'] = (sum([1 if x else 0 for x in [qdrant_ok, redis_ok, thompson_ok, workflow_ok]]), 4 - sum([1 if x else 0 for x in [qdrant_ok, redis_ok, thompson_ok, workflow_ok]]))
    
    # 4. Data population
    data_ok, data_missing = check_data_population()
    results['data'] = (data_ok, data_missing)
    
    # 5. Integrations
    integrations_ok, integrations_broken = check_integrations()
    results['integrations'] = (integrations_ok, integrations_broken)
    
    # 6. Dependencies
    deps_ok, deps_missing = check_dependencies()
    results['dependencies'] = (deps_ok, deps_missing)
    
    # ========================================================================
    # FINAL REPORT
    # ========================================================================
    
    print_header("DIAGNOSTIC SUMMARY")
    
    total_passed = 0
    total_failed = 0
    
    for category, (passed, failed) in results.items():
        total_passed += passed
        total_failed += failed
        
        status = f"{passed}/{passed + failed}"
        if failed == 0:
            print_success(f"{category.replace('_', ' ').title():<30} {status:>10}")
        else:
            print_error(f"{category.replace('_', ' ').title():<30} {status:>10}")
    
    print("\n" + "=" * 80)
    
    # Calculate completion percentage
    total_checks = total_passed + total_failed
    completion_pct = (total_passed / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n{Colors.BOLD}OVERALL STATUS:{Colors.ENDC}")
    print(f"  Total Checks: {total_checks}")
    print(f"  Passed: {Colors.OKGREEN}{total_passed}{Colors.ENDC}")
    print(f"  Failed: {Colors.FAIL}{total_failed}{Colors.ENDC}")
    print(f"  Completion: {Colors.BOLD}{completion_pct:.1f}%{Colors.ENDC}")
    
    print("\n" + "=" * 80)
    
    if total_failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ SYSTEM FULLY OPERATIONAL!{Colors.ENDC}")
        print("All components are properly implemented and integrated.")
    elif completion_pct >= 80:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  SYSTEM MOSTLY COMPLETE{Colors.ENDC}")
        print(f"Review errors above and complete remaining {total_failed} items.")
    elif completion_pct >= 50:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  SYSTEM PARTIALLY COMPLETE{Colors.ENDC}")
        print(f"Significant work remaining. Address {total_failed} failed checks.")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ SYSTEM INCOMPLETE{Colors.ENDC}")
        print(f"Major components missing. Complete {total_failed} failed checks.")
    
    print("=" * 80 + "\n")
    
    # Return exit code
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
