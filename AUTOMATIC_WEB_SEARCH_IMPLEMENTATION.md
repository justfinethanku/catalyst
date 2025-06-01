# Automatic Web Search Implementation

**Implementation Date:** 2025-05-31  
**Author:** Claude Code  
**Objective:** Enable automatic web search tools for OpenAI GPT-4.1 models and live data steps

## Overview

This implementation adds automatic web search tool enablement to the Catalyst intelligence system. Web search is now automatically enabled based on model type and step requirements, eliminating the need for manual configuration while ensuring live data access for research steps.

## Key Features

### 1. Automatic Model-Based Enablement
- **All GPT-4.1 variants** automatically get web search tools
  - `gpt-4.1` → Auto-enabled
  - `gpt-4.1-nano` → Auto-enabled
  - Future GPT-4.1 variants → Auto-enabled

### 2. Automatic Step-Based Enablement  
- **Live data steps** automatically get web search tools:
  - `discovery` - Company research requires current information
  - `market_position` - Market trends need live data
  - `competitive_landscape` - Competitor analysis needs current data
  - `audience_insights` - Customer insights benefit from recent data

### 3. Manual Override Support
- Explicit `enable_web_search: false` disables automatic enablement
- Explicit `enable_web_search: true` forces enablement regardless of model/step
- Legacy `web_search_queries` config still triggers enablement

### 4. Fail-Fast Error Handling
- Web search tool failures immediately raise exceptions
- No silent degradation or fallback to non-web search
- Clear error messages indicate auto-enablement reason

## Files Modified

### 1. `/src/core/llm_providers.py`

**Lines 137-163:** Modified web search enablement logic
```python
# BEFORE: Manual config-based enablement
if config.get("enable_web_search", False):

# AFTER: Automatic intelligent enablement  
should_enable_web_search = self._should_enable_web_search(model_key, model_name, config)
if should_enable_web_search:
```

**Lines 231-276:** Added `_should_enable_web_search()` method
```python
def _should_enable_web_search(self, model_key: str, model_name: str, config: Dict[str, Any]) -> bool:
    """
    Determine if web search should be automatically enabled.
    
    Auto-enables web search for:
    1. All GPT-4.1 model variants (gpt-4.1, gpt-4.1-nano)
    2. Any step that requires live data (discovery, market_position, competitive_landscape)
    3. Manual override via config (enable_web_search: true)
    """
```

**Lines 216-221:** Updated error handling for auto-enabled web search
```python
# BEFORE: Generic web search error handling
if config.get("enable_web_search", False) and ("tool" in str(e).lower() or "web_search" in str(e).lower()):

# AFTER: Context-aware error handling
if should_enable_web_search and ("tool" in str(e).lower() or "web_search" in str(e).lower()):
    error_msg = f"Web-search tool failed (auto-enabled for {model_key}) - FAILING FAST: {str(e)}"
```

### 2. `/src/core/pipeline/engine.py`

**Line 359:** Added step_id to LLM config
```python
# BEFORE: Basic config merge
llm_config = {**config.settings, **step.config}

# AFTER: Include step identification
llm_config = {**config.settings, **step.config, "step_id": step.id}
```

## Logic Flow

### Enablement Decision Tree

```
1. Check for manual override
   ├─ enable_web_search: true → ENABLE
   ├─ enable_web_search: false → DISABLE
   └─ No override → Continue to auto-detection

2. Check model type
   ├─ Contains "gpt-4.1" → ENABLE
   └─ Other models → Continue to step check

3. Check step requirements
   ├─ Step in [discovery, market_position, competitive_landscape, audience_insights] → ENABLE
   └─ Other steps → Continue to legacy check

4. Check legacy config
   ├─ web_search_queries present → ENABLE
   └─ No queries → DISABLE
```

### API Call Flow

```
1. Pipeline Engine calls LLM provider
   ├─ Includes step_id in config
   └─ Passes combined settings + step config

2. OpenAI Provider processes request
   ├─ Calls _should_enable_web_search()
   ├─ Adds tools array if enabled
   └─ Sets tool_choice: "auto"

3. OpenAI API Response
   ├─ Success → Extract content + tool_calls
   ├─ Tool Error → Fail fast with context
   └─ Other Error → Standard error handling
```

## Testing Results

Comprehensive testing validated the implementation:

✅ **GPT-4.1 Auto-Enablement**
- GPT-4.1 model: 1 web search call made
- GPT-4.1-nano model: 2 web search calls made

✅ **Step-Based Auto-Enablement**  
- Discovery step: Web search enabled
- Market position step: Web search enabled

✅ **Manual Override**
- `enable_web_search: false` properly disabled web search on GPT-4.1

✅ **No Auto-Enable Conditions**
- Strategic synthesis step: No web search (correct)

✅ **Fail-Fast Behavior**
- GPT-4o + web search: Failed fast (GPT-4o doesn't support tools)

## Configuration Impact

### Pipeline Config (`company_intelligence.yaml`)
- **No changes required** - automatic enablement works with existing config
- `enable_web_search: true` in pipeline settings becomes legacy fallback
- Step-specific `web_search_queries` still supported for compatibility

### Model Config (`models.yaml`)  
- **No changes required** - logic is in provider layer as requested
- Model names remain clean and focused on model mapping
- No web search configuration polluting model definitions

## Usage Examples

### Automatic Enablement (No Config Changes)
```python
# GPT-4.1 automatically gets web search
config = {"model": "gpt-4.1"}  # Web search auto-enabled

# Discovery step automatically gets web search  
config = {"model": "gpt-4o", "step_id": "discovery"}  # Web search auto-enabled

# Combined conditions
config = {"model": "gpt-4.1", "step_id": "discovery"}  # Web search auto-enabled
```

### Manual Control
```python
# Force disable on auto-enable model
config = {"model": "gpt-4.1", "enable_web_search": False}  # Disabled

# Force enable on non-auto model
config = {"model": "gpt-4o", "step_id": "synthesis", "enable_web_search": True}  # Enabled
```

## Benefits Achieved

1. **Zero Configuration Required** - Web search automatically enabled where needed
2. **Intelligent Defaults** - GPT-4.1 and live data steps get web search by default  
3. **Manual Override** - Explicit control when automatic behavior isn't desired
4. **Fail-Fast Safety** - No silent degradation when web search fails
5. **Provider-Layer Logic** - Implementation in API layer, not configuration files
6. **Backward Compatibility** - Existing configurations continue to work

## Future Considerations

1. **New Models** - Add new models to auto-enablement list as they support tools
2. **New Steps** - Add steps requiring live data to the auto-enablement list
3. **Tool Evolution** - Update tool definitions as OpenAI API evolves
4. **Performance** - Monitor token usage impact of automatic web search enablement

## Summary

This implementation successfully enables automatic web search for all GPT-4.1 API calls and live data research steps, moving the logic to the provider layer as requested. The system now intelligently determines when web search is needed without requiring manual configuration, while maintaining full manual override capabilities and fail-fast error handling.