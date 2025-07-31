# Modern Password Hashing - 2025 Best Practices

This document explains the modern password hashing implementations available in this FastAPI application and how to choose between them.

## Overview

We've implemented three security modules following 2025 best practices:

1. **Direct bcrypt** (`src/core/security.py`) - Modern bcrypt without passlib
2. **Argon2** (`src/core/security_argon2.py`) - State-of-the-art password hashing
3. **Unified** (`src/core/security_unified.py`) - Configurable with auto-detection

## Why We Moved Away from passlib

The traditional approach using `passlib` had compatibility issues with newer bcrypt versions, causing warning messages like:

```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

Instead of patching these compatibility issues, we adopted modern approaches that are more maintainable and secure.

## Implementation 1: Direct bcrypt

**File**: `src/core/security.py`

```python
import bcrypt

def get_password_hash(password: str) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)
```

### Advantages:
- ✅ Zero compatibility warnings
- ✅ Direct dependency on `python-bcrypt`
- ✅ Mature, battle-tested algorithm
- ✅ Wide ecosystem support
- ✅ Suitable for most applications

### Configuration:
```toml
# pyproject.toml
"bcrypt>=4.1.0,<5.0.0"
```

## Implementation 2: Argon2 (Recommended for new projects)

**File**: `src/core/security_argon2.py`

```python
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=1,      # Number of parallel threads
    hash_len=32,        # Length of hash in bytes
    salt_len=16,        # Length of salt in bytes
)

def get_password_hash(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
```

### Advantages:
- 🚀 **Winner of Password Hashing Competition (PHC)**
- 🛡️ **Best resistance to specialized hardware attacks**
- 🔒 **Built-in protection against side-channel attacks**
- ⚡ **Configurable memory/time trade-offs**
- 🔄 **Automatic parameter upgrade detection**
- 📈 **Future-proof algorithm**

### Configuration:
```toml
# pyproject.toml
"argon2-cffi>=23.1.0,<24.0.0"
```

### Environment variables:
```bash
PASSWORD_HASH_ALGORITHM=argon2
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=1
```

## Implementation 3: Unified (Best of both worlds)

**File**: `src/core/security_unified.py`

This implementation provides:
- 🔄 **Configurable algorithm selection**
- 🔍 **Automatic hash format detection**
- ⬆️ **Seamless algorithm migration**
- 🔧 **Runtime parameter upgrades**

```python
# Automatically detects and verifies both bcrypt and Argon2 hashes
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
        return bcrypt_verify(plain_password, hashed_password)
    elif hashed_password.startswith('$argon2'):
        return argon2_verify(plain_password, hashed_password)
    # ... fallback logic
```

## Performance Comparison

| Algorithm | Time (ms) | Memory (MB) | Security Level | Year Introduced |
|-----------|-----------|-------------|----------------|-----------------|
| bcrypt    | ~100      | <1          | Good           | 1999            |
| Argon2id  | ~150      | 64          | Excellent      | 2015            |

## Configuration Options

### Environment Variables

```bash
# Choose algorithm
PASSWORD_HASH_ALGORITHM=argon2  # or "bcrypt"

# bcrypt settings
BCRYPT_ROUNDS=12

# Argon2 settings (production-tuned)
ARGON2_TIME_COST=3      # Higher = slower but more secure
ARGON2_MEMORY_COST=65536 # 64MB memory usage
ARGON2_PARALLELISM=1    # Number of threads
```

### Production Tuning

For production environments, tune parameters based on your hardware:

```python
# Low-end servers
ARGON2_TIME_COST=2
ARGON2_MEMORY_COST=32768  # 32MB

# High-end servers
ARGON2_TIME_COST=4
ARGON2_MEMORY_COST=131072  # 128MB
```

## Migration Strategy

### 1. Gradual Migration (Recommended)

```python
# During login, check if hash needs upgrade
def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if verify_password(password, user.hashed_password):
        # Check if we need to upgrade the hash
        new_hash = upgrade_password_hash(password, user.hashed_password)
        if new_hash:
            user.hashed_password = new_hash
            save_user(user)
        return user
```

### 2. Immediate Migration

For immediate migration, create a script to rehash all passwords:

```python
# This requires users to reset passwords
def migrate_all_hashes():
    # Disable login
    # Send password reset emails to all users
    # Users will get new Argon2 hashes on reset
```

## CLI Commands

The `db_manage.py` script automatically uses the configured algorithm:

```bash
# Create users with current algorithm
python scripts/db_manage.py createuser user@example.com --password "SecurePass123!"
python scripts/db_manage.py createsuperuser admin@example.com --password "AdminPass123!"

# Check security info
python -c "from src.core.security_unified import get_security_info; print(get_security_info())"
```

## Recommendations

### For New Projects (2025+)
- 🚀 **Use Argon2** - Best security, future-proof
- ⚙️ **Start with default parameters** - Tune for your hardware later
- 📊 **Monitor performance** - Adjust based on user experience

### For Existing Projects
- 🔄 **Gradual migration** - Upgrade hashes during login
- 📈 **A/B testing** - Test performance impact
- 🛡️ **Security audit** - Review current hash strength

### For High-Security Applications
- 🔒 **Always use Argon2** with higher parameters
- 🔄 **Regular parameter updates** 
- 📝 **Security monitoring** and logging

## Code Examples

### Basic Usage
```python
from src.core.security_unified import get_password_hash, verify_password

# Hash a password
hashed = get_password_hash("my_secure_password")

# Verify a password
is_valid = verify_password("my_secure_password", hashed)
```

### Advanced Usage
```python
from src.core.security_unified import upgrade_password_hash, get_security_info

# Check if hash needs upgrading
new_hash = upgrade_password_hash("password", old_hash)
if new_hash:
    # Update user's hash in database
    update_user_hash(user_id, new_hash)

# Get current configuration
config = get_security_info()
print(f"Using {config['algorithm']} algorithm")
```

## Security Benefits Summary

| Feature | bcrypt | Argon2 | Unified |
|---------|--------|--------|---------|
| No warnings | ✅ | ✅ | ✅ |
| Memory-hard | ❌ | ✅ | ✅ |
| Side-channel protection | ❌ | ✅ | ✅ |
| Algorithm migration | ❌ | ❌ | ✅ |
| Auto-detection | ❌ | ❌ | ✅ |
| Parameter upgrades | ❌ | ✅ | ✅ |
| Future-proof | ⚠️ | ✅ | ✅ |

## Conclusion

The move to modern password hashing eliminates compatibility issues while providing state-of-the-art security. The unified approach offers the best developer experience with automatic hash detection and seamless migration capabilities.

Choose **Argon2** for new projects requiring maximum security, or **bcrypt** for existing projects with broad compatibility requirements. The **unified** approach allows you to have both and migrate gradually.
