# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :x:                |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Mox, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send an email to the project maintainer with:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact assessment
4. Suggested fix (if any)

### What to expect

- **Acknowledgment**: within 48 hours
- **Status update**: within 7 days
- **Fix timeline**: depends on severity
  - Critical: 1-3 days
  - High: 7 days
  - Medium: 14 days
  - Low: 30 days

## Security Considerations

Mox is a security testing platform designed for **authorized red teaming and research**. Users must:

1. **Only test systems you own or have explicit permission to test**
2. **Follow responsible disclosure practices** for any vulnerabilities found
3. **Comply with all applicable laws and regulations** in your jurisdiction
4. **Not use Mox for unauthorized access** to any system or service

## Built-in Security Measures

- JWT-based authentication for API access
- Rate limiting on API endpoints
- Input validation and sanitization
- Audit logging for all operations
- Configurable safety thresholds for attack evaluations

## Scope

This security policy covers the Mox codebase and its official deployments. Third-party integrations, plugins, or modified versions are outside the scope of this policy.
