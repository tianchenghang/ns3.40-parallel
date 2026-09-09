#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
#define IEG_API __declspec(dllexport)
#else
#define IEG_API __attribute__((visibility("default")))
#endif

// Validate XML files. path: file or directory (NULL/"" = default ../logs).
// Returns 1 if all valid, 0 if any invalid, -1 on error.
IEG_API int ieg_validate(const char *path);

// Validate and return JSON: {"absPath": true/false, ...}
// Caller must free with ieg_free.
IEG_API char *ieg_validate_json(const char *path);

// Encrypt file(s). input: file or directory. output: file or directory (NULL =
// default). Returns JSON array of output paths. Caller must free with ieg_free.
IEG_API char *ieg_encrypt(const char *input, const char *output);

// Decrypt file(s). Same semantics as ieg_encrypt.
IEG_API char *ieg_decrypt(const char *input, const char *output);

// Parse file(s) to CSV. Returns CSV string (single file) or
// JSON {"absPath": "csv...", ...} (multiple files).
// Caller must free with ieg_free.
IEG_API char *ieg_csv(const char *path);

// Free a string returned by ieg_* functions.
IEG_API void ieg_free(char *ptr);

#ifdef __cplusplus
}
#endif
