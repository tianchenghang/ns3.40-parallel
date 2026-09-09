#pragma once
#include <filesystem>
#include <string>
#include <vector>

namespace ieg {

// Resolve input path (file or directory) to a list of absolute file paths.
// Accepts .flowmonitor files, .xml files, or directories (scans recursively).
// Default base directory is ieg/../logs when path is empty.
std::vector<std::filesystem::path>
resolveFiles(const std::string &inputPath,
             const std::filesystem::path &baseDir = "");

} // namespace ieg
