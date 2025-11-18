#pragma once

#include <string>
#include <vector>
#include <mutex>
#include <json/json.h>

namespace VoiceAssistant {

struct Command {
    std::string name;
    std::string command;
    std::vector<std::string> phrases;
};

/**
 * CommandExecutor - Common core for executing commands and simulating keystrokes
 * Shared by all mode workers to avoid duplication
 */
class CommandExecutor {
public:
    CommandExecutor();
    ~CommandExecutor() = default;

    // Command execution
    void executeCommand(const std::string& command);
    
    // Keyboard simulation via ydotool
    void typeText(const std::string& text);
    void pressKey(const std::string& keyCode);
    void pressKeyCombo(const std::vector<std::string>& keyCodes);
    
    // Command matching
    double matchPhrase(const std::string& text, const std::string& phrase);
    std::pair<const Command*, double> findBestMatch(
        const std::string& text,
        const std::vector<Command>& commands,
        double threshold
    );
    
    // Logging
    void log(const std::string& level, const std::string& message);

private:
    std::string m_logFile;
    mutable std::mutex m_logMutex;
    
    // Helper for command execution
    bool executeSystemCommand(const std::string& command);
    
    // Helper for ydotool operations
    bool isYdotoolAvailable();
    std::string escapeForShell(const std::string& str);
};

} // namespace VoiceAssistant
