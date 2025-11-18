#include "CommandExecutor.hpp"
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <sys/wait.h>

namespace VoiceAssistant {

CommandExecutor::CommandExecutor()
    : m_logFile("/tmp/willow.log")
{
}

void CommandExecutor::executeCommand(const std::string& command) {
    log("INFO", "Executing command: " + command);
    
    // Build command with proper environment and background execution
    // Using systemd-run ensures the app gets proper user session environment
    std::string execCmd = "systemd-run --user --scope --slice=app.slice " + command + " &";
    
    log("INFO", "Full command: " + execCmd);
    
    // Execute the command in background
    int result = std::system(execCmd.c_str());
    
    // systemd-run returns 0 if it successfully started the scope
    if (result == 0 || WIFEXITED(result)) {
        log("INFO", "Command executed successfully");
    } else {
        log("ERROR", "Command execution failed with code: " + std::to_string(result));
    }
}

void CommandExecutor::typeText(const std::string& text) {
    if (text.empty()) return;
    
    if (!isYdotoolAvailable()) {
        log("ERROR", "ydotool is not available");
        return;
    }
    
    log("INFO", "Typing text: " + text);
    
    // Use ydotool to type the text
    std::string command = "ydotool type '" + escapeForShell(text) + "'";
    
    int result = std::system(command.c_str());
    if (result != 0) {
        log("ERROR", "Failed to type text via ydotool");
    }
}

void CommandExecutor::pressKey(const std::string& keyCode) {
    if (!isYdotoolAvailable()) {
        log("ERROR", "ydotool is not available");
        return;
    }
    
    std::string command = "ydotool key " + keyCode;
    std::system(command.c_str());
}

void CommandExecutor::pressKeyCombo(const std::vector<std::string>& keyCodes) {
    if (!isYdotoolAvailable()) {
        log("ERROR", "ydotool is not available");
        return;
    }
    
    std::string command = "ydotool key";
    for (const auto& keyCode : keyCodes) {
        command += " " + keyCode;
    }
    std::system(command.c_str());
}

double CommandExecutor::matchPhrase(const std::string& text, const std::string& phrase) {
    // Convert phrase to lowercase for matching
    std::string lowerPhrase = phrase;
    std::transform(lowerPhrase.begin(), lowerPhrase.end(), lowerPhrase.begin(), ::tolower);
    
    // Simple substring match
    if (text.find(lowerPhrase) != std::string::npos) {
        return 1.0;
    }
    
    // TODO: Implement proper fuzzy matching algorithm for partial matches
    return 0.0;
}

std::pair<const Command*, double> CommandExecutor::findBestMatch(
    const std::string& text,
    const std::vector<Command>& commands,
    double threshold
) {
    const Command* bestCmd = nullptr;
    double bestConfidence = 0.0;
    
    for (const auto& cmd : commands) {
        for (const auto& phrase : cmd.phrases) {
            double confidence = matchPhrase(text, phrase);
            if (confidence > bestConfidence) {
                bestConfidence = confidence;
                bestCmd = &cmd;
            }
        }
    }
    
    return {bestCmd, bestConfidence};
}

void CommandExecutor::log(const std::string& level, const std::string& message) {
    std::lock_guard<std::mutex> lock(m_logMutex);
    
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    
    std::ofstream logFile(m_logFile, std::ios::app);
    if (logFile.is_open()) {
        logFile << std::put_time(&tm, "%Y-%m-%d %H:%M:%S") 
                << " [" << level << "] " << message << std::endl;
    }
    
    // Also log to console
    std::cout << "[" << level << "] " << message << std::endl;
}

bool CommandExecutor::executeSystemCommand(const std::string& command) {
    int result = std::system(command.c_str());
    return (result == 0 || WIFEXITED(result));
}

bool CommandExecutor::isYdotoolAvailable() {
    int result = std::system("which ydotool >/dev/null 2>&1");
    return result == 0;
}

std::string CommandExecutor::escapeForShell(const std::string& str) {
    std::string escaped;
    for (char c : str) {
        if (c == '\'') {
            escaped += "'\\''";
        } else {
            escaped += c;
        }
    }
    return escaped;
}

} // namespace VoiceAssistant
