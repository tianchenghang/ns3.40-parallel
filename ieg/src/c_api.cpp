#include "ieg/c_api.h"
#include "ieg/crypto.h"
#include "ieg/csv_parser.h"
#include "ieg/file_resolver.h"
#include "ieg/validator.h"
#include <cstdlib>
#include <cstring>
#include <sstream>

namespace fs = std::filesystem;

static char *strdup_alloc(const std::string &s) {
  char *p = static_cast<char *>(std::malloc(s.size() + 1));
  if (p) {
    std::memcpy(p, s.c_str(), s.size() + 1);
  }
  return p;
}

static std::string escapeJson(const std::string &s) {
  std::string out;
  out.reserve(s.size() + 16);
  for (char c : s) {
    switch (c) {
    case '"':
      out += "\\\"";
      break;
    case '\\':
      out += "\\\\";
      break;
    case '\n':
      out += "\\n";
      break;
    case '\r':
      out += "\\r";
      break;
    case '\t':
      out += "\\t";
      break;
    default:
      out += c;
      break;
    }
  }
  return out;
}

static fs::path getBaseDir() {
  // Default base: the ieg source directory (parent of build/)
  fs::path cwd = fs::current_path();
  if (fs::exists(cwd / "CMakeLists.txt")) {
    return cwd;
  }
  if (fs::exists(cwd.parent_path() / "CMakeLists.txt")) {
    return cwd.parent_path();
  }
  return cwd;
}

extern "C" {

int ieg_validate(const char *path) {
  try {
    std::string inputPath = path ? path : "";
    auto files = ieg::resolveFiles(inputPath, getBaseDir());
    if (files.empty())
      return -1;
    auto results = ieg::validateFiles(files);
    for (auto &[p, valid] : results) {
      if (!valid)
        return 0;
    }
    return 1;
  } catch (...) {
    return -1;
  }
}

char *ieg_validate_json(const char *path) {
  try {
    std::string inputPath = path ? path : "";
    auto files = ieg::resolveFiles(inputPath, getBaseDir());
    if (files.empty())
      return strdup_alloc("{}");
    auto results = ieg::validateFiles(files);

    std::ostringstream json;
    json << "{";
    bool first = true;
    for (auto &[p, valid] : results) {
      if (!first)
        json << ",";
      json << "\"" << escapeJson(p) << "\":" << (valid ? "true" : "false");
      first = false;
    }
    json << "}";
    return strdup_alloc(json.str());
  } catch (...) {
    return strdup_alloc("{}");
  }
}

char *ieg_encrypt(const char *input, const char *output) {
  try {
    std::string inputPath = input ? input : "";
    std::string outputPath = output ? output : "";
    auto files = ieg::resolveFiles(inputPath, getBaseDir());
    if (files.empty())
      return strdup_alloc("[]");

    std::vector<fs::path> results;
    if (files.size() == 1 && !outputPath.empty()) {
      auto r = ieg::encryptFile(files[0], fs::path(outputPath));
      if (!r.empty())
        results.push_back(r);
    } else {
      fs::path outDir =
          outputPath.empty() ? getBaseDir() / "output" : fs::path(outputPath);
      if (outDir.is_relative())
        outDir = getBaseDir() / outDir;
      results = ieg::encryptFiles(files, outDir);
    }

    std::ostringstream json;
    json << "[";
    for (size_t i = 0; i < results.size(); ++i) {
      if (i > 0)
        json << ",";
      json << "\"" << escapeJson(results[i].string()) << "\"";
    }
    json << "]";
    return strdup_alloc(json.str());
  } catch (...) {
    return strdup_alloc("[]");
  }
}

char *ieg_decrypt(const char *input, const char *output) {
  try {
    std::string inputPath = input ? input : "";
    std::string outputPath = output ? output : "";
    auto files = ieg::resolveFiles(inputPath, getBaseDir());
    if (files.empty())
      return strdup_alloc("[]");

    std::vector<fs::path> results;
    if (files.size() == 1 && !outputPath.empty()) {
      auto r = ieg::decryptFile(files[0], fs::path(outputPath));
      if (!r.empty())
        results.push_back(r);
    } else {
      fs::path outDir =
          outputPath.empty() ? getBaseDir() / "output" : fs::path(outputPath);
      if (outDir.is_relative())
        outDir = getBaseDir() / outDir;
      results = ieg::decryptFiles(files, outDir);
    }

    std::ostringstream json;
    json << "[";
    for (size_t i = 0; i < results.size(); ++i) {
      if (i > 0)
        json << ",";
      json << "\"" << escapeJson(results[i].string()) << "\"";
    }
    json << "]";
    return strdup_alloc(json.str());
  } catch (...) {
    return strdup_alloc("[]");
  }
}

char *ieg_csv(const char *path) {
  try {
    std::string inputPath = path ? path : "";
    auto files = ieg::resolveFiles(inputPath, getBaseDir());
    if (files.empty())
      return strdup_alloc("");

    auto results = ieg::parseFilesToCsv(files);
    if (results.size() == 1) {
      return strdup_alloc(results.begin()->second);
    }

    std::ostringstream json;
    json << "{";
    bool first = true;
    for (auto &[p, csv] : results) {
      if (!first)
        json << ",";
      json << "\"" << escapeJson(p) << "\":\"" << escapeJson(csv) << "\"";
      first = false;
    }
    json << "}";
    return strdup_alloc(json.str());
  } catch (...) {
    return strdup_alloc("");
  }
}

void ieg_free(char *ptr) { std::free(ptr); }

} // extern "C"
