 LeadShark Codebase Analysis - Major and Minor Files

● 🔥 MAJOR/CORE FILES (Critical System Components)

  1. Entry Points & Orchestration (1,443 lines)

  - run_pipeline.py (358 lines) - PRIMARY ENTRY POINT
    - Main CLI application launcher
    - Handles authentication flow
    - Coordinates all enrichment modes
    - User interaction and command-line argument parsing

  2. Core Enrichment Engines (1,266 lines)

  - compact_enricher.py (572 lines) - COMPACT MODE PROCESSOR
    - Lightweight enrichment using 4-5 columns only
    - Optimized for Google Sheets column limits
    - JSON-based data storage in cells
  - non_destructive_enricher.py (694 lines) - FULL MODE PROCESSOR     
    - Comprehensive enrichment with detailed columns
    - Append-only operations preserving original data
    - Advanced row key matching and deduplication

  3. Core Infrastructure (1,427 lines)

  - enhanced_scraping_pipeline.py (682 lines) - WEB SCRAPING 
  ENGINE
    - Platform-specific scraping optimizations
    - Rate limiting and anti-bot detection
    - LinkedIn, Facebook, Twitter, website scraping
  - google_sheets_auth.py (361 lines) - AUTHENTICATION CORE
    - Google OAuth2 flow implementation
    - Credential management and token refresh
    - Sheet access validation and metadata
  - cli_interface.py (483 lines) - USER INTERFACE ENGINE
    - Rich terminal UI with progress bars
    - Interactive sheet/worksheet selection
    - Real-time processing feedback

  4. Data Processing Core (745 lines)

  - data_enrichment.py (283 lines) - API ENRICHMENT ENGINE
    - Free API integrations (Gender, Email verification, GitHub)      
    - Rate limiting and error handling
    - Response normalization
  - google_sheets_processor.py (462 lines) - LEGACY PROCESSOR
    - Earlier processing implementation
    - Basic sheet operations and data handling

  ⚡ MINOR/SUPPORTING FILES

  5. Specialized Tools (1,443 lines)

  - link_intelligence_orchestrator.py (1,443 lines) - LINK 
  ANALYSIS SPECIALIST
    - Advanced link scanning and intelligence gathering
    - Deep web analysis and content extraction
    - Specialized for link-heavy datasets

  6. Launcher Scripts (599 lines)

  - run_compact.py (128 lines) - Compact mode launcher
  - run_non_destructive.py (213 lines) - Non-destructive mode
  launcher
  - run_link_intelligence.py (258 lines) - Link intelligence
  launcher

  7. Test Suite (929 lines)

  - test_interactive_flow.py (491 lines) - Interactive mode
  testing
  - test_non_destructive.py (397 lines) - Non-destructive enricher    
   tests
  - test_link_intelligence.py (354 lines) - Link intelligence
  tests
  - test_compact.py (59 lines) - Compact enricher tests

  8. Utilities (235 lines)

  - add_enrichment_columns.py (154 lines) - Column management
  utility
  - final_enrichment_summary.py (81 lines) - Report generation        
  utility

  📁 CONFIGURATION & DOCUMENTATION

  9. Configuration Files

  - requirements.txt - Python dependencies specification
  - .env.example - Environment configuration template
  - link_intel_config.json - Link intelligence configuration
  - .claude/settings.local.json - Claude Code IDE settings

  10. Documentation Files

  - README.md - Main project documentation
  - setup_guide.md - Installation and setup instructions
  - README_SETUP.md - Quick setup guide
  - implementation_plan.md - Technical architecture docs
  - INTERACTIVE_FLOW_README.md - Interactive mode documentation       
  - NON_DESTRUCTIVE_README.md - Non-destructive mode docs
  - FINAL_STATUS.md - Project status and capabilities
  - mcp-config.md - MCP configuration documentation

  🔗 DEPENDENCY HIERARCHY

  run_pipeline.py (MAIN ENTRY)
  ├── cli_interface.py
  ├── google_sheets_auth.py
  ├── compact_enricher.py
  │   ├── google_sheets_auth.py
  │   ├── data_enrichment.py
  │   └── enhanced_scraping_pipeline.py
  ├── non_destructive_enricher.py
  │   ├── google_sheets_auth.py
  │   ├── data_enrichment.py
  │   └── enhanced_scraping_pipeline.py
  └── data_enrichment.py (NO DEPENDENCIES)

  link_intelligence_orchestrator.py (STANDALONE)
  ├── google_sheets_auth.py
  └── enhanced_scraping_pipeline.py

  📊 FILE IMPORTANCE RANKING

  🚨 CRITICAL (System won't work without these)

  1. run_pipeline.py - Main entry point
  2. google_sheets_auth.py - Authentication core
  3. compact_enricher.py OR non_destructive_enricher.py -
  Processing engines
  4. enhanced_scraping_pipeline.py - Web scraping engine
  5. data_enrichment.py - API enrichment engine

  ⚠️ IMPORTANT (Core functionality)

  6. cli_interface.py - User experience
  7. requirements.txt - Dependencies
  8. .env.example - Configuration template

  📋 USEFUL (Enhanced features)

  9. link_intelligence_orchestrator.py - Advanced link analysis       
  10. run_*.py scripts - Convenient launchers
  11. Test files - Quality assurance
  12. Documentation - User guidance

  🔧 OPTIONAL (Utilities)

  13. add_enrichment_columns.py - Maintenance utility
  14. final_enrichment_summary.py - Reporting utility
  15. Configuration files - Advanced customization

  The system is architected with clear separation of concerns,        
  making it modular and maintainable while preserving predatory       
  efficiency in lead enrichment operations.