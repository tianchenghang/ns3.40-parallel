#include "ieg/file_resolver.h"
#include <algorithm>

namespace fs = std::filesystem;

namespace ieg {

static bool isTargetFile(const fs::path &p) {
  auto ext = p.extension().string();
  std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
  return ext == ".flowmonitor" || ext == ".xml";
}

std::vector<fs::path> resolveFiles(const std::string &inputPath,
                                   const fs::path &baseDir) {
  fs::path base = baseDir.empty() ? fs::current_path() : baseDir;
  fs::path target =
      inputPath.empty() ? base / ".." / "logs" : fs::path(inputPath);

  if (target.is_relative()) {
    target = base / target;
  }
  target = fs::canonical(target);

  std::vector<fs::path> result;

  if (fs::is_directory(target)) {
    for (auto &entry : fs::recursive_directory_iterator(target)) {
      if (entry.is_regular_file() && isTargetFile(entry.path())) {
        result.push_back(fs::canonical(entry.path()));
      }
    }
    std::sort(result.begin(), result.end());
  } else if (fs::is_regular_file(target)) {
    result.push_back(target);
  }

  return result;
}

} // namespace ieg
