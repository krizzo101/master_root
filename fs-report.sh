#!/usr/bin/env bash
# fs-report.sh — size report and directory map for a given path
# Usage:
#   ./fs-report.sh /path/to/scan
#   ./fs-report.sh /path/to/scan --top 50 --depth 3 --no-excludes
#
# Outputs:
#   - Largest files (TOP)
#   - Largest directories (TOP)
#   - Directory map (DEPTH)
#
# Notes:
#   - Stays on the same filesystem (du -x)
#   - Excludes common dev junk by default (node_modules, venv/.venv, __pycache__, .cache)
#   - Requires GNU coreutils (Linux). macOS users: install coreutils or adapt flags.

set -euo pipefail

# ---------- defaults ----------
PATH_IN="${1:-}"
TOP_N=30
DEPTH=2
EXCLUDES=1  # 1 = exclude common junk; 0 = include everything

# ---------- parse optional flags ----------
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --top)    TOP_N="${2:-}"; shift 2 ;;
    --depth)  DEPTH="${2:-}"; shift 2 ;;
    --no-excludes) EXCLUDES=0; shift ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

if [[ -z "$PATH_IN" || ! -d "$PATH_IN" ]]; then
  echo "Usage: $0 /path/to/scan [--top N] [--depth D] [--no-excludes]"
  exit 1
fi

# ---------- build find/du exclude args ----------
readarray -t EX_PATTERNS < <(cat <<'EOF'
*/node_modules/*
*/.venv/*
*/venv/*
*/__pycache__/*
*/.cache/*
EOF
)

FIND_PRUNE=()
DU_EXCLUDE=()
if [[ $EXCLUDES -eq 1 ]]; then
  for pat in "${EX_PATTERNS[@]}"; do
    FIND_PRUNE+=(-path "$pat" -prune -o)
    DU_EXCLUDE+=("--exclude=$pat")
  done
fi

# Helper: pretty heading
h() { echo; printf '=== %s ===\n' "$*"; }

# ---------- Largest FILES ----------
h "Largest files (top $TOP_N) in $PATH_IN"
# Use null delimiters to be safe with spaces/newlines in names
# Print bytes\tpath, sort numerically, take top N, then humanize sizes
# shellcheck disable=SC2016
eval find \"\$PATH_IN\" -xdev -type f ${FIND_PRUNE[@]+"${FIND_PRUNE[@]}"} -print0 \
  \| xargs -0 -I{} du --bytes -x {} 2>/dev/null \
  \| sort -nrk1,1 \
  \| head -n "$TOP_N" \
  \| awk '{
      # Humanize bytes (B,KB,MB,GB,TB)
      split("B KB MB GB TB PB", u);
      s=$1; i=1;
      while (s>=1024 && i<6){s/=1024;i++}
      printf "%7.2f %2s  %s\n", s, u[i], substr($0, index($0,$2))
    }'

# ---------- Largest DIRECTORIES ----------
h "Largest directories (top $TOP_N) at depth 1 under $PATH_IN"
# du -x keeps to one filesystem; --bytes for raw size; -d 1 = one level down
du -x --bytes -d 1 "${DU_EXCLUDE[@]}" "$PATH_IN" 2>/dev/null \
  | sort -nr \
  | head -n "$TOP_N" \
  | awk '{
      split("B KB MB GB TB PB", u);
      s=$1; i=1;
      while (s>=1024 && i<6){s/=1024;i++}
      printf "%7.2f %2s  %s\n", s, u[i], $2
    }'

# ---------- Directory MAP (tree) ----------
h "Directory map (depth $DEPTH) for $PATH_IN"
if command -v tree >/dev/null 2>&1; then
  # tree output with sizes; -d for directories only; -L depth limit
  # Use --prune to respect our exclude patterns by piping through grep -v (portable)
  EX_GREP=''
  if [[ $EXCLUDES -eq 1 ]]; then
    # join patterns into a single egrep alternation
    PAT_RE='(node_modules|\.venv|\/venv\/|__pycache__|\.cache)'
    EX_GREP="| egrep -v '$PAT_RE'"
  fi
  # shellcheck disable=SC2086
  bash -c "tree -h -d -L $DEPTH \"$PATH_IN\" $EX_GREP || true"
else
  echo "(tip) Install 'tree' for a nicer map: sudo apt-get install -y tree"
  echo "Fallback map:"
  # Fallback: print indented directory list to depth with sizes
  # We compute dir sizes at max depth, then print an indented map.
  # Get dirs up to DEPTH
  IFS=$'\n' read -r -d '' -a DIRS < <(
    find "$PATH_IN" -xdev -type d ${FIND_PRUNE[@]+"${FIND_PRUNE[@]}"} -printf '%d\t%p\n' 2>/dev/null \
      | awk -v base="$PATH_IN" -v maxd="$DEPTH" '{
          # depth relative to base
          rel=$1; full=$2;
          # compute relative depth from base path
          # count slashes difference
          gsub(/\/+$/,"",base); gsub(/\/+$/,"",full);
          n1=split(base,a,"/"); n2=split(full,b,"/");
          depth=n2-n1;
          if (depth<=maxd && depth>=0) print depth "\t" full;
        }' \
      | sort -n -k1,1 -k2,2 \
      | tr -d '\r' \
      | sed -e 's/\t/ /' \
      && printf '\0'
  )
  for entry in "${DIRS[@]}"; do
    depth="${entry%% *}"
    path="${entry#* }"
    # size of this dir (not recursive beyond itself to keep it cheap)
    sz_bytes=$(du --bytes -s -x "${DU_EXCLUDE[@]}" "$path" 2>/dev/null | awk '{print $1}')
    # humanize
    unit=(B KB MB GB TB PB); i=0; s="$sz_bytes"
    while [[ "$s" -ge 1024 && $i -lt 5 ]]; do s=$((s/1024)); ((i++)); done
    indent=""
    for ((k=0;k<depth;k++)); do indent+="  "; done
    printf "%s%6s %2s  %s\n" "$indent" "$s" "${unit[$i]}" "$path"
  done
fi

echo
echo "Done."

