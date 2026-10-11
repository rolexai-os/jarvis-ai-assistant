# JARVIS plugin system

The 0.4 foundation uses a data-only allowlist for built-in skills. It does not import or execute third-party Python files. This is deliberate: plugin code otherwise runs with the same permissions as your Windows account.

To add a skill, implement a narrowly scoped action in reviewed application code, add metadata to the built-in registry, and write tests. Do not install untrusted plugin scripts.
