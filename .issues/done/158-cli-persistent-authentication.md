# Issue #162: CLI Persistent Authentication

## Description
Store credentials locally after first login to improve CLI UX, eliminating the need to re-enter credentials for every session.

## Expected Behavior
After successful authentication, credentials should be stored locally and reused in subsequent CLI sessions.

## Actual Behavior
Credentials must be provided every time a CLI command is executed, requiring environment variables or repeated flag input.

## Status: DONE ✓ (duplicate of #150)

## Resolution
- Already implemented in issue #150: tasker login/logout commands
- Credentials stored in ~/.tasker/credentials

## Steps to Reproduce
1. Run a CLI command with credentials
2. Close the terminal
3. Run another CLI command
4. Observe that credentials must be provided again

## Status: PENDING

## Priority: MEDIUM

## Recommendations
- Implement secure local credential storage (consider using keyring libraries)
- Add `tasker login` and `tasker logout` commands
- Store encrypted credentials in platform-specific secure storage
- Implement credential expiration and refresh mechanisms
- Ensure proper security warnings about credential storage
- Support both environment variables and persistent storage as methods
- Add configuration option to disable persistent storage for security-conscious users

## Technical Notes
- Related to Issue #01 (CLI Authentication UX) but focused on CLI specifically
- Can reuse similar storage mechanisms from Issue #01