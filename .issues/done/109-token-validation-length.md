# Issue #109: Fix Token Validation Minimum Length

## Description

The SecretManager validates GitHub Personal Access Tokens with a minimum length of 20 characters, but actual GitHub PATs are typically 40+ characters (starting with ghp_, gho_, ghs_, ghu_, ghsa_). This may cause valid tokens to be rejected.

## Requirements

- Update token validation to accept 40+ character GitHub PATs
- Adjust the TOKEN_PATTERN regex to allow correct token lengths
- Ensure all GitHub token prefixes (ghp, gho, ghs, ghu, ghsa, ghsr) are supported
- Test with actual GitHub token format

## Technical Details

### Current Implementation
```python
# In secret_manager.py
TOKEN_PATTERN = re.compile(r"^gh(p|o|s|u|sa|sr)_[A-Za-z0-9_]{20,251}$")
```

### Token Format Examples
- Classic PAT: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40 chars after prefix)
- OAuth: `gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40 chars)
- Server-to-server: `ghs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40 chars)
- User-to-server: `ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40 chars)
- App: `ghsa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40 chars)

### Issue
The current regex allows `{20,251}` characters after the prefix. This should be:
- Minimum: 40 characters (actual PAT length)
- Maximum: 251 (current limit is fine)

### Fix
```python
TOKEN_PATTERN = re.compile(r"^gh(p|o|s|u|sa|sr)_[A-Za-z0-9_]{36,251}$")
# Changed minimum from 20 to 36 to match real GitHub PAT format
```

### Also Update
The `_validate_token_format` method should also use 36 instead of 20:
```python
def _validate_token_format(self, token: str) -> bool:
    if not token or len(token) < 36:  # Changed from 20
        return False
    return bool(self.TOKEN_PATTERN.match(token))
```

## Business Value

- Prevents rejection of valid GitHub tokens
- Better user experience when configuring credentials
- Accurate validation matches real GitHub token format

## Status: COMPLETED