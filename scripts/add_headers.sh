#!/bin/bash
# add_headers.sh - Pre-commit hook to add SPDX license headers
# Receives files as arguments from pre-commit

COMPANY="The Culture List, Inc."
YEAR=$(date +%Y)
MODIFIED=0

add_python_header() {
  local file="$1"
  # Check for shebang and insert header after it
  if head -1 "$file" | grep -q "^#!"; then
    head -1 "$file" > temp
    echo "# Copyright (C) $YEAR $COMPANY" >> temp
    echo "# SPDX-License-Identifier: GPL-3.0-or-later" >> temp
    echo "" >> temp
    tail -n +2 "$file" >> temp
  else
    echo "# Copyright (C) $YEAR $COMPANY" > temp
    echo "# SPDX-License-Identifier: GPL-3.0-or-later" >> temp
    echo "" >> temp
    cat "$file" >> temp
  fi
  mv temp "$file"
}

add_c_style_header() {
  local file="$1"
  echo "// Copyright (C) $YEAR $COMPANY" > temp
  echo "// SPDX-License-Identifier: GPL-3.0-or-later" >> temp
  echo "" >> temp
  cat "$file" >> temp
  mv temp "$file"
}

for file in "$@"; do
  # Skip if file doesn't exist
  [[ -f "$file" ]] || continue

  # Skip if already has SPDX identifier
  if grep -q "SPDX-License-Identifier" "$file" 2>/dev/null; then
    continue
  fi

  echo "Adding license header to: $file"

  case "$file" in
    *.py)
      add_python_header "$file"
      ;;
    *.qml|*.frag|*.vert|*.geom|*.comp|*.tesc|*.tese)
      add_c_style_header "$file"
      ;;
    *)
      # Unknown file type, skip
      continue
      ;;
  esac

  # Re-stage the file so the commit includes the header
  git add "$file"
done

# Always exit successfully so commit proceeds with headers added
exit 0
