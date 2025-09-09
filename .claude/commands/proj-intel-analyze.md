---
description: Analyze codebase using project intelligence data
argument-hint: [analysis-type: complexity|architecture|all]
allowed-tools: Bash, Read, Grep
---

## =Ê Analyze Project with Intelligence

### Complexity Analysis
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action file-elements --format json | \
  jq '[.[] | {path, complexity: (.fn_count + .class_count * 3)}] | \
  sort_by(.complexity) | reverse | .[0:10]'
```

### Architecture Analysis
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action agents --format summary
```

### File Statistics
```bash
python /home/opsvi/master_root/scripts/proj_intel_reader.py \
  --action file-elements --format json | \
  jq '{total_files: length,
      total_functions: [.[].fn_count] | add,
      total_classes: [.[].class_count] | add}'
```
