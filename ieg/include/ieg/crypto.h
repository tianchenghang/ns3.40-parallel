#pragma once
#include <filesystem>
#include <string>
#include <vector>

namespace ieg {

// Magic bytes prepended to encrypted files.
inline constexpr const char *MAGIC = "ns3.40";
inline constexpr size_t MAGIC_LEN = 6;

// Encrypt a file. Writes to outputPath (defaults to inputPath + ".enc").
// Returns the output absolute path on success, empty on failure.
std::filesystem::path encryptFile(const std::filesystem::path &inputPath,
                                  const std::filesystem::path &outputPath = "");

// Decrypt a file. Writes to outputPath (defaults to stripping ".enc" suffix).
// Returns the output absolute path on success, empty on failure.
std::filesystem::path decryptFile(const std::filesystem::path &inputPath,
                                  const std::filesystem::path &outputPath = "");

// Batch encrypt/decrypt resolved files into an output directory.
std::vector<std::filesystem::path>
encryptFiles(const std::vector<std::filesystem::path> &files,
             const std::filesystem::path &outDir);
std::vector<std::filesystem::path>
decryptFiles(const std::vector<std::filesystem::path> &files,
             const std::filesystem::path &outDir);

} // namespace ieg
