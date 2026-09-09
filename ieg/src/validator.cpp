#include "ieg/validator.h"
#include <fstream>
#include <stack>
#include <vector>

namespace ieg {

// Minimal XML well-formedness checker:
// - checks XML declaration
// - checks balanced tags (handles self-closing />)
// - checks attribute quoting
// - does NOT validate schema/DTD
bool validateXml(const std::filesystem::path &filePath) {
  std::ifstream ifs(filePath, std::ios::binary);
  if (!ifs.is_open()) {
    return false;
  }

  std::string content((std::istreambuf_iterator<char>(ifs)),
                      std::istreambuf_iterator<char>());

  if (content.empty()) {
    return false;
  }

  // Must start with XML declaration
  if (content.rfind("<?xml", 0) != 0) {
    return false;
  }

  enum class State {
    Text,
    TagOpen,
    TagName,
    AttrName,
    AttrEq,
    AttrValue,
    Comment,
    PI
  };
  State state = State::Text;
  std::stack<std::string> tagStack;
  std::string current;
  char quoteChar = 0;
  bool inClosingTag = false;

  for (size_t i = 0; i < content.size(); ++i) {
    char c = content[i];

    switch (state) {
    case State::Text:
      if (c == '<') {
        if (i + 1 < content.size() && content[i + 1] == '?') {
          state = State::PI;
          current.clear();
          ++i;
        } else if (i + 3 < content.size() && content.substr(i, 4) == "<!--") {
          state = State::Comment;
          i += 3;
        } else {
          state = State::TagOpen;
          current.clear();
          inClosingTag = false;
        }
      }
      break;

    case State::PI:
      if (c == '?' && i + 1 < content.size() && content[i + 1] == '>') {
        state = State::Text;
        ++i;
      }
      break;

    case State::Comment:
      if (c == '-' && i + 2 < content.size() && content.substr(i, 3) == "-->") {
        state = State::Text;
        i += 2;
      }
      break;

    case State::TagOpen:
      if (c == '/') {
        inClosingTag = true;
        state = State::TagName;
        current.clear();
      } else if (std::isalpha(c) || c == '_') {
        state = State::TagName;
        current = c;
      } else {
        return false;
      }
      break;

    case State::TagName:
      if (std::isalnum(c) || c == '_' || c == '-' || c == ':' || c == '.') {
        current += c;
      } else if (c == '>') {
        if (inClosingTag) {
          if (tagStack.empty() || tagStack.top() != current) {
            return false;
          }
          tagStack.pop();
        } else {
          tagStack.push(current);
        }
        state = State::Text;
      } else if (c == '/' && i + 1 < content.size() && content[i + 1] == '>') {
        if (inClosingTag) {
          return false;
        }
        ++i;
        state = State::Text;
      } else if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
        if (inClosingTag) {
          // skip whitespace before >
        } else {
          state = State::AttrName;
          current += '\0'; // separator: tag name is before \0
        }
      } else {
        return false;
      }
      break;

    case State::AttrName:
      if (c == '>') {
        std::string tagName = current.substr(0, current.find('\0'));
        if (inClosingTag) {
          if (tagStack.empty() || tagStack.top() != tagName) {
            return false;
          }
          tagStack.pop();
        } else {
          tagStack.push(tagName);
        }
        state = State::Text;
      } else if (c == '/' && i + 1 < content.size() && content[i + 1] == '>') {
        ++i;
        state = State::Text;
      } else if (c == '=') {
        state = State::AttrEq;
      } else if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
        // skip
      } else if (std::isalnum(c) || c == '_' || c == '-' || c == ':' ||
                 c == '.') {
        // continue attr name
      } else {
        return false;
      }
      break;

    case State::AttrEq:
      if (c == '"' || c == '\'') {
        quoteChar = c;
        state = State::AttrValue;
      } else if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
        // skip
      } else {
        return false;
      }
      break;

    case State::AttrValue:
      if (c == quoteChar) {
        state = State::AttrName;
      }
      break;
    }
  }

  return tagStack.empty() && state == State::Text;
}

std::map<std::string, bool>
validateFiles(const std::vector<std::filesystem::path> &files) {
  std::map<std::string, bool> result;
  for (auto &f : files) {
    result[std::filesystem::canonical(f).string()] = validateXml(f);
  }
  return result;
}

} // namespace ieg
