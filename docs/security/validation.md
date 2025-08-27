# Input Validation

The `src.security.validate` module provides helpers to reject unsafe inputs
before they reach sensitive parts of the system.

## URL checks
Use `validate_url` to ensure a URL uses HTTP(S) and resolves to a public host.

## File names and paths
`validate_filename` rejects names containing path separators or traversal
components. Combine it with `validate_path` to keep file operations confined to
an expected base directory.

## MIME consistency
`validate_mime` verifies the provided MIME type matches what the filename
suggests. This guards against disguised executables.
