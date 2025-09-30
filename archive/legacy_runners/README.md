# Legacy Runner Scripts - Archived

**Date Archived**: September 30, 2025  
**Reason**: Consolidated into unified `leadshark.py` entry point

---

## ⚠️ These Files Are Deprecated

All functionality from these scripts has been consolidated into the new unified entry point: **`leadshark.py`**

### Migration Guide

**Old Way** → **New Way**

```bash
# Compact enrichment
python run_compact.py
→ python leadshark.py compact --sheet-id YOUR_ID

# Non-destructive enrichment
python run_non_destructive.py
→ python leadshark.py full --sheet-id YOUR_ID

# Link intelligence
python run_link_intelligence.py
→ python leadshark.py link-intel --sheet-id YOUR_ID

# AI enrichment
python ai_powered_enricher.py --sheet-id YOUR_ID
→ python leadshark.py ai --sheet-id YOUR_ID

# Enhanced enrichment
python run_enhanced_enrichment.py
→ python leadshark.py full --sheet-id YOUR_ID

# Live enrichment
python run_live_enrichment.py
→ python leadshark.py compact --sheet-id YOUR_ID --all
```

---

## Why Consolidate?

**Before**: 10+ separate runner scripts, each with slightly different interfaces
**After**: 1 unified command with consistent interface

**Benefits**:
- ✅ Single command to learn
- ✅ Consistent interface across all modes
- ✅ Better error handling
- ✅ Easier maintenance
- ✅ Interactive + CLI modes

---

## Archived Files

1. `run_compact.py` - Compact enrichment runner
2. `run_non_destructive.py` - Full enrichment runner
3. `run_link_intelligence.py` - Link intel runner
4. `run_link_intel_auto.py` - Automated link intel
5. `run_leadshark.py` - Simplified entry point
6. `run_leadshark_demo.py` - Demo script
7. `run_live_enrichment.py` - Live processing
8. `run_enhanced_enrichment.py` - Enhanced enrichment
9. `run_expanded_enrichment.py` - Expanded enrichment

---

## New Unified Interface

```bash
# Get help
python leadshark.py --help

# Interactive mode (guided)
python leadshark.py

# AI enrichment (OpenAI)
python leadshark.py ai --provider openai --sheet-id YOUR_ID --test

# Compact enrichment (production)
python leadshark.py compact --sheet-id YOUR_ID --all

# Link intelligence
python leadshark.py link-intel --sheet-id YOUR_ID --limit 100

# Smart auto-detect
python leadshark.py smart --sheet-id YOUR_ID
```

---

For questions, see main README.md or run: `python leadshark.py --help`
