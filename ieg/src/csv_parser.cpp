#include "ieg/csv_parser.h"
#include <fstream>
#include <regex>
#include <sstream>

namespace fs = std::filesystem;

namespace ieg {

std::string parseToCsv(const fs::path &filePath) {
  std::ifstream ifs(filePath);
  if (!ifs.is_open())
    return "";

  std::string content((std::istreambuf_iterator<char>(ifs)),
                      std::istreambuf_iterator<char>());

  std::ostringstream csv;
  csv << "flowId,sourceAddress,destinationAddress,protocol,sourcePort,"
         "destinationPort,txBytes,rxBytes,txPackets,rxPackets,lostPackets,"
         "timesForwarded,delaySum,jitterSum,lastDelay,"
         "timeFirstTxPacket,timeFirstRxPacket,timeLastTxPacket,"
         "timeLastRxPacket\n";

  // Collect classifier info: flowId => (src, dst, proto, sport, dport)
  std::map<std::string, std::array<std::string, 5>> classifier;
  {
    std::regex flowRe(
        R"re(<Flow\s+flowId="(\d+)"\s+sourceAddress="([^"]+)"\s+destinationAddress="([^"]+)"\s+protocol="(\d+)"\s+sourcePort="(\d+)"\s+destinationPort="(\d+)")re");
    auto begin = std::sregex_iterator(content.begin(), content.end(), flowRe);
    auto end = std::sregex_iterator();
    for (auto it = begin; it != end; ++it) {
      auto &m = *it;
      classifier[m[1].str()] = {m[2].str(), m[3].str(), m[4].str(), m[5].str(),
                                m[6].str()};
    }
  }

  // Parse FlowStats section
  {
    std::regex statsRe(
        R"re(<Flow\s+flowId="(\d+)"\s+timeFirstTxPacket="([^"]+)"\s+timeFirstRxPacket="([^"]+)"\s+timeLastTxPacket="([^"]+)"\s+timeLastRxPacket="([^"]+)"\s+delaySum="([^"]+)"\s+jitterSum="([^"]+)"\s+lastDelay="([^"]+)"\s+txBytes="(\d+)"\s+rxBytes="(\d+)"\s+txPackets="(\d+)"\s+rxPackets="(\d+)"\s+lostPackets="(\d+)"\s+timesForwarded="(\d+)")re");

    auto statsStart = content.find("<FlowStats>");
    auto statsEnd = content.find("</FlowStats>");
    if (statsStart == std::string::npos || statsEnd == std::string::npos) {
      return "";
    }
    std::string statsSection =
        content.substr(statsStart, statsEnd - statsStart);

    auto begin =
        std::sregex_iterator(statsSection.begin(), statsSection.end(), statsRe);
    auto end = std::sregex_iterator();
    for (auto it = begin; it != end; ++it) {
      auto &m = *it;
      std::string fid = m[1].str();

      std::string src, dst, proto, sport, dport;
      if (classifier.count(fid)) {
        auto &c = classifier[fid];
        src = c[0];
        dst = c[1];
        proto = c[2];
        sport = c[3];
        dport = c[4];
      }

      csv << fid << "," << src << "," << dst << "," << proto << "," << sport
          << "," << dport << "," << m[9].str() << "," << m[10].str() << ","
          << m[11].str() << "," << m[12].str() << "," << m[13].str() << ","
          << m[14].str() << "," << m[6].str() << "," << m[7].str() << ","
          << m[8].str() << "," << m[2].str() << "," << m[3].str() << ","
          << m[4].str() << "," << m[5].str() << "\n";
    }
  }

  return csv.str();
}

std::map<std::string, std::string>
parseFilesToCsv(const std::vector<fs::path> &files) {
  std::map<std::string, std::string> result;
  for (auto &f : files) {
    auto csvStr = parseToCsv(f);
    if (!csvStr.empty()) {
      result[fs::canonical(f).string()] = std::move(csvStr);
    }
  }
  return result;
}

} // namespace ieg
