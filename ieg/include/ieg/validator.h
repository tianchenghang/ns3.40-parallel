#pragma once
#include <filesystem>
#include <map>
#include <string>

namespace ieg {

// Validate XML well-formedness of a single file.
bool validateXml(const std::filesystem::path &filePath);

// Validate multiple files, returns absolutePath => isValid map.
std::map<std::string, bool>
validateFiles(const std::vector<std::filesystem::path> &files);

} // namespace ieg
