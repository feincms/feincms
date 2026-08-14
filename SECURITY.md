# Security Policy

## Supported Versions

Only the latest stable version of FeinCMS is supported with security updates.
Maintenance branches may receive fixes at the maintainers' discretion.

## Reporting a Vulnerability

Please report security vulnerabilities privately before publishing details.

Please include:

- affected version or commit;
- affected component;
- reproduction steps;
- security impact;

## Scope

This policy applies to the FeinCMS package, including the Django admin
integrations, page module, media library, content types, templates, static files,
and documented default behavior.

Application-specific code built on top of FeinCMS is out of scope unless the
issue is caused by FeinCMS itself.

## Security Expectations

FeinCMS should preserve Django's security guarantees and avoid introducing
unexpected bypasses in authentication, authorization, escaping, file handling,
routing, redirects, previews, and content rendering.

## Out of Scope

The following are generally out of scope:

- issues requiring malicious changes in the host Django application;
- insecure deployment configuration outside FeinCMS defaults;
- vulnerabilities only affecting unsupported dependency versions;
- self-XSS by fully trusted administrators;
- behavior explicitly documented as raw HTML or trusted administrator content.

## Notes

FeinCMS is highly extensible. Reports are strongest when they reproduce using
default FeinCMS modules or documented configuration, without relying on unusual
application-specific code.
