# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Guidelines
- Keep all responses concise - default to bullet points
- Only modify code that needs changing
- Skip explanations unless I ask "why" or "explain"
- When planning: think internally, output minimal summary


## Custom Commands
When I say these phrases, execute the corresponding scripts:
- "wrap it up" or "wrap session" → run `python HOUSEKEEPING/wrap_up.py`
- "update context" → run `python HOUSEKEEPING/update_context.py`
- "status check" or "what's the status" → run `python HOUSEKEEPING/project_status.py`
- "document this" → run `python HOUSEKEEPING/document_changes.py`

## Important to remember
things I want you to remember: 
- Never modify: api_secrets/.env
- use models.yaml as the single source of truth for model names