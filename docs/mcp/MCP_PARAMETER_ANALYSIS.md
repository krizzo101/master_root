# MCP Parameter Analysis for Thinking Server

## Parameter Type Analysis

### Required Parameters (Always Present)
| Parameter | Expected Type | Function Signature | Coercion Needed | Notes |
|-----------|--------------|-------------------|-----------------|-------|
| thought | str | str | No | Direct string, no coercion needed |
| triggerContext | str | str | No | Direct string, no coercion needed |
| thoughtNumber | int | Any | Yes | MCP sends as string, needs int() |
| totalThoughts | int | Any | Yes | MCP sends as string, needs int() |
| nextThoughtNeeded | bool | bool | Maybe | Check if MCP sends as string "true"/"false" |

### Optional Parameters - Simple Types
| Parameter | Expected Type | Function Signature | Coercion Needed | Notes |
|-----------|--------------|-------------------|-----------------|-------|
| intendedAction | Optional[str] | Optional[str] | No | String or None |
| assumptions | Optional[str] | Optional[str] | No | String or None |
| workPhase | Optional[str] | Optional[str] | No | String or None, default "auto" |
| isRevision | Optional[bool] | Optional[bool] | Maybe | Check if sent as string |
| revisesThought | Optional[int] | Any | Yes | Could be string or None |
| branchFromThought | Optional[int] | Any | Yes | Could be string or None |
| branchId | Optional[str] | Optional[str] | No | String or None |
| needsMoreThoughts | Optional[bool] | Optional[bool] | Maybe | Check if sent as string |
| metaObservation | Optional[str] | Optional[str] | No | String or None |
| questionAssumption | Optional[str] | Optional[str] | No | String or None |
| patternRecognized | Optional[str] | Optional[str] | No | String or None |
| improvementIdentified | Optional[str] | Optional[str] | No | String or None |
| redundancyDetected | Optional[str] | Optional[str] | No | String or None |
| metacognitiveType | Optional[str] | Optional[str] | No | String or None |

### Enhanced Context Parameters
| Parameter | Expected Type | Function Signature | Coercion Needed | Notes |
|-----------|--------------|-------------------|-----------------|-------|
| userRequest | Optional[str] | Optional[str] | No | String or None |
| confidenceLevel | Optional[int] | Any | Yes | 0-100, could be string |
| attemptNumber | Optional[int] | Any | Yes | >= 1, could be string, default 1 |
| previousFailures | Optional[List[str]] | Any | Yes | JSON string to list |
| currentBlocker | Optional[str] | Optional[str] | No | String or None |
| evidenceGathered | Optional[List[str]] | Any | Yes | JSON string to list |

## MCP Transport Behavior

MCP converts parameters as follows:
1. **Integers** → Sent as strings (e.g., 42 → "42")
2. **Booleans** → Sent as booleans (true/false) 
3. **Lists** → Sent as JSON strings (e.g., ["a", "b"] → '["a", "b"]')
4. **None/null** → Sometimes sent as string "None" or omitted
5. **Strings** → Sent as strings (no change)

## Required Coercion Logic

### Current Issues
1. ✅ Integer coercion implemented for most fields
2. ❌ Boolean coercion NOT implemented (isRevision, needsMoreThoughts, nextThoughtNeeded)
3. ✅ List coercion implemented for previousFailures and evidenceGathered
4. ❌ Need to handle empty strings that should be None
5. ❌ Need to handle string "null" or "undefined" as None

### Complete Coercion Requirements

```python
# Integer fields that need coercion
- thoughtNumber (required, >= 1)
- totalThoughts (required, >= 1)  
- confidenceLevel (optional, 0-100)
- attemptNumber (optional, >= 1, default 1)
- revisesThought (optional)
- branchFromThought (optional)

# Boolean fields that need coercion
- nextThoughtNeeded (required)
- isRevision (optional)
- needsMoreThoughts (optional)

# List fields that need JSON parsing
- previousFailures (optional, default [])
- evidenceGathered (optional, default [])

# String fields (no coercion needed)
- All other fields remain as strings or None
```

## Validation After Coercion

The ThoughtData model expects:
- thoughtNumber: int with ge=1 (>= 1)
- totalThoughts: int with ge=1 (>= 1)
- confidenceLevel: Optional[int] with ge=0, le=100 (0-100 range)
- attemptNumber: Optional[int] with ge=1, default=1
- previousFailures: Optional[List[str]], default_factory=list
- evidenceGathered: Optional[List[str]], default_factory=list