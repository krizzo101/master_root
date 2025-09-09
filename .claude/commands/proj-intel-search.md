---
description: Search for code elements using project intelligence
argument-hint: [search-term]
allowed-tools: Bash, Read, Grep
---

## =
 Search Project Intelligence

Searching for: $ARGUMENTS

### Search Classes/Agents
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action agents --format json | \
  jq -r --arg s "$ARGUMENTS" \
  '.[] | .data | select(.name | ascii_downcase | contains($s | ascii_downcase))'
```

### Search File Paths
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action file-elements --format json | \
  jq -r --arg s "$ARGUMENTS" \
  '.[] | select(.path | contains($s))'
```

### Get File Details
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action read-by-path --path "$ARGUMENTS"
```
