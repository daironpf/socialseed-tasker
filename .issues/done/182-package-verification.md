# Issue #182 - Add Package Verification to Release Process

## Description

There's no automated verification that the package includes all required assets before publishing to PyPI. This led to the frontend compiled assets not being included in v0.8.0.

## Problem

After building the package, there's no check to verify:
- Frontend compiled assets are included
- Template files are present
- Package size is within expected range

## Root Cause

The release workflow builds the package but doesn't verify its contents before uploading.

## Expected Behavior

The release workflow should include a verification step:

```yaml
- name: Verify package contents
  run: |
    pip install dist/*.whl --target /tmp/verify
    ls /tmp/verify/socialseed_tasker/assets/frontend/
    # Should show: index.html, assets/
    
    FRONTEND_SIZE=$(du -sh /tmp/verify/socialseed_tasker/assets/frontend/ | cut -f1)
    if [ "$FRONTEND_SIZE" -lt 100 ]; then
      echo "ERROR: Frontend assets too small, missing compiled files"
      exit 1
    fi
```

## Implementation Steps

### Step 1: Update release.yml workflow

Add verification step after building:

```yaml
- name: Verify package contents
  run: |
    python -m pip install dist/*.whl --target /tmp/verify-package
    
    # Check frontend assets exist
    if [ ! -d "/tmp/verify-package/socialseed_tasker/assets/frontend/assets" ]; then
      echo "ERROR: Frontend compiled assets not found in package"
      exit 1
    fi
    
    # Check frontend assets have content
    FRONTEND_SIZE=$(du -sm /tmp/verify-package/socialseed_tasker/assets/frontend/ | cut -f1)
    if [ "$FRONTEND_SIZE" -lt 100 ]; then
      echo "WARNING: Frontend assets are smaller than expected (${FRONTEND_SIZE}KB)"
    else
      echo "Frontend assets verified: ${FRONTEND_SIZE}KB"
    fi
```

### Step 2: Add template verification

```yaml
    # Check template files exist
    TEMPLATE_FILES=(
      "socialseed_tasker/assets/templates/docker-compose.yml"
      "socialseed_tasker/assets/templates/skills/task_skill.py"
      "socialseed_tasker/assets/templates/project_readme.md"
    )
    
    for file in "${TEMPLATE_FILES[@]}"; do
      if [ ! -f "/tmp/verify-package/$file" ]; then
        echo "ERROR: Template file not found: $file"
        exit 1
      fi
    done
    echo "All template files verified"
```

### Step 3: Document verification

Add documentation about the verification process in CONTRIBUTING.md or a new RELEASE_CHECKLIST.md.

## Affected Files

- `.github/workflows/release.yml`

## Verification

After the workflow runs, check that:
1. The build passes verification
2. Package size is appropriate (wheel should be ~350KB+)
3. All required assets are included

## Status: COMPLETED