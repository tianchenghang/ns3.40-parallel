#include "ieg/crypto.h"
#include <cstring>
#include <fstream>

namespace fs = std::filesystem;

namespace ieg {

static std::vector<uint8_t> readFileBytes(const fs::path &p) {
  std::ifstream ifs(p, std::ios::binary);
  if (!ifs.is_open())
    return {};
  return {std::istreambuf_iterator<char>(ifs),
          std::istreambuf_iterator<char>()};
}

static bool writeFileBytes(const fs::path &p,
                           const std::vector<uint8_t> &data) {
  fs::create_directories(p.parent_path());
  std::ofstream ofs(p, std::ios::binary);
  if (!ofs.is_open())
    return false;
  ofs.write(reinterpret_cast<const char *>(data.data()),
            static_cast<std::streamsize>(data.size()));
  return ofs.good();
}

static void xorTransform(std::vector<uint8_t> &data) {
  const auto *key = reinterpret_cast<const uint8_t *>(MAGIC);
  for (size_t i = 0; i < data.size(); ++i) {
    data[i] ^= key[i % MAGIC_LEN];
  }
}

fs::path encryptFile(const fs::path &inputPath, const fs::path &outputPath) {
  auto data = readFileBytes(inputPath);
  if (data.empty() && !fs::exists(inputPath))
    return {};

  // Check not already encrypted
  if (data.size() >= MAGIC_LEN &&
      std::memcmp(data.data(), MAGIC, MAGIC_LEN) == 0) {
    return {};
  }

  xorTransform(data);

  std::vector<uint8_t> out;
  out.reserve(MAGIC_LEN + data.size());
  out.insert(out.end(), MAGIC, MAGIC + MAGIC_LEN);
  out.insert(out.end(), data.begin(), data.end());

  fs::path outPath =
      outputPath.empty() ? fs::path(inputPath.string() + ".enc") : outputPath;
  if (outPath.is_relative()) {
    outPath = fs::current_path() / outPath;
  }

  if (!writeFileBytes(outPath, out))
    return {};
  return fs::canonical(outPath);
}

fs::path decryptFile(const fs::path &inputPath, const fs::path &outputPath) {
  auto data = readFileBytes(inputPath);
  if (data.size() < MAGIC_LEN)
    return {};

  if (std::memcmp(data.data(), MAGIC, MAGIC_LEN) != 0) {
    return {};
  }

  std::vector<uint8_t> payload(data.begin() + MAGIC_LEN, data.end());
  xorTransform(payload);

  fs::path outPath;
  if (outputPath.empty()) {
    auto s = inputPath.string();
    if (s.size() > 4 && s.substr(s.size() - 4) == ".enc") {
      outPath = fs::path(s.substr(0, s.size() - 4));
    } else {
      outPath = fs::path(s + ".dec");
    }
  } else {
    outPath = outputPath;
  }
  if (outPath.is_relative()) {
    outPath = fs::current_path() / outPath;
  }

  if (!writeFileBytes(outPath, payload))
    return {};
  return fs::canonical(outPath);
}

std::vector<fs::path> encryptFiles(const std::vector<fs::path> &files,
                                   const fs::path &outDir) {
  std::vector<fs::path> results;
  for (auto &f : files) {
    fs::path out = outDir / (f.filename().string() + ".enc");
    auto r = encryptFile(f, out);
    if (!r.empty())
      results.push_back(r);
  }
  return results;
}

std::vector<fs::path> decryptFiles(const std::vector<fs::path> &files,
                                   const fs::path &outDir) {
  std::vector<fs::path> results;
  for (auto &f : files) {
    auto name = f.filename().string();
    if (name.size() > 4 && name.substr(name.size() - 4) == ".enc") {
      name = name.substr(0, name.size() - 4);
    }
    fs::path out = outDir / name;
    auto r = decryptFile(f, out);
    if (!r.empty())
      results.push_back(r);
  }
  return results;
}

} // namespace ieg
