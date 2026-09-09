#include "ieg/crypto.h"
#include "ieg/csv_parser.h"
#include "ieg/file_resolver.h"
#include "ieg/validator.h"
#include <iostream>
#include <string>

namespace fs = std::filesystem;

static void printUsage(const char *prog) {
  std::cerr << "Usage:\n"
            << "  " << prog << " validate [path]\n"
            << "  " << prog << " encrypt <input-path> [output-path]\n"
            << "  " << prog << " decrypt <input-path> [output-path]\n"
            << "  " << prog << " csv [path]\n"
            << "\n"
            << "path: .flowmonitor file, .xml file, or directory (default: "
               "../logs)\n";
}

int main(int argc, char *argv[]) {
  if (argc < 2) {
    printUsage(argv[0]);
    return 1;
  }

  std::string command = argv[1];
  fs::path iegDir = fs::canonical(fs::path(argv[0]).parent_path() / "..");
  // When run from build dir, baseDir is the ieg source dir
  fs::path baseDir = fs::current_path();
  if (fs::exists(baseDir / "CMakeLists.txt")) {
    // running from ieg source dir
  } else if (fs::exists(baseDir.parent_path() / "CMakeLists.txt")) {
    baseDir = baseDir.parent_path();
  }

  if (command == "validate") {
    std::string inputPath = argc > 2 ? argv[2] : "";
    auto files = ieg::resolveFiles(inputPath, baseDir);
    if (files.empty()) {
      std::cerr << "No files found.\n";
      return 1;
    }
    auto results = ieg::validateFiles(files);
    bool allValid = true;
    for (auto &[path, valid] : results) {
      std::cout << (valid ? "VALID   " : "INVALID ") << path << "\n";
      if (!valid)
        allValid = false;
    }
    return allValid ? 0 : 1;

  } else if (command == "encrypt" || command == "decrypt") {
    if (argc < 3) {
      std::cerr << "Error: input path required for " << command << "\n";
      return 1;
    }
    std::string inputPath = argv[2];
    std::string outputPath = argc > 3 ? argv[3] : "";

    auto files = ieg::resolveFiles(inputPath, baseDir);
    if (files.empty()) {
      std::cerr << "No files found.\n";
      return 1;
    }

    if (files.size() == 1 && !outputPath.empty()) {
      fs::path result;
      if (command == "encrypt") {
        result = ieg::encryptFile(files[0], fs::path(outputPath));
      } else {
        result = ieg::decryptFile(files[0], fs::path(outputPath));
      }
      if (result.empty()) {
        std::cerr << "Failed: " << files[0] << "\n";
        return 1;
      }
      std::cout << result << "\n";
    } else {
      fs::path outDir =
          outputPath.empty() ? baseDir / "output" : fs::path(outputPath);
      if (outDir.is_relative())
        outDir = baseDir / outDir;

      std::vector<fs::path> results;
      if (command == "encrypt") {
        results = ieg::encryptFiles(files, outDir);
      } else {
        results = ieg::decryptFiles(files, outDir);
      }
      for (auto &r : results) {
        std::cout << r << "\n";
      }
      std::cerr << results.size() << "/" << files.size()
                << " files processed.\n";
    }
    return 0;

  } else if (command == "csv") {
    std::string inputPath = argc > 2 ? argv[2] : "";
    auto files = ieg::resolveFiles(inputPath, baseDir);
    if (files.empty()) {
      std::cerr << "No files found.\n";
      return 1;
    }
    auto results = ieg::parseFilesToCsv(files);
    if (results.size() == 1) {
      std::cout << results.begin()->second;
    } else {
      for (auto &[path, csv] : results) {
        std::cout << "# " << path << "\n" << csv << "\n";
      }
    }
    return 0;

  } else {
    printUsage(argv[0]);
    return 1;
  }
}
