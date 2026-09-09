#pragma once
#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace ieg {

// Parse a single .flowmonitor/.xml file to CSV string.
// Returns empty string on failure.
std::string parseToCsv(const std::filesystem::path &filePath);

// Parse multiple files, returns absolutePath => csvString map.
std::map<std::string, std::string>
parseFilesToCsv(const std::vector<std::filesystem::path> &files);

} // namespace ieg
