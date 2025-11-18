#include "CommandExecutor.hpp"
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <sys/wait.h>
#include <cctype>

namespace VoiceAssistant {

CommandExecutor::CommandExecutor()
    : m_logFile("/tmp/willow.log")
{
    // Load context config from default location
    const char* home = std::getenv("HOME");
    if (home) {
        std::string contextPath = std::string(home) + "/.config/willow/context.json";
        loadContextConfig(contextPath);
    }
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

void CommandExecutor::loadContextConfig(const std::string& contextPath) {
    log("INFO", "Loading context config from: " + contextPath);
    
    std::ifstream file(contextPath);
    if (!file.is_open()) {
        log("WARNING", "Could not open context config file, using defaults");
        return;
    }
    
    Json::Value root;
    Json::CharReaderBuilder reader;
    std::string errors;
    
    if (!Json::parseFromStream(reader, file, &root, &errors)) {
        log("ERROR", "Failed to parse context config: " + errors);
        return;
    }
    
    // Load default apps
    if (root.isMember("default_apps") && root["default_apps"].isObject()) {
        for (const auto& key : root["default_apps"].getMemberNames()) {
            m_context.defaultApps[key] = root["default_apps"][key].asString();
        }
    }
    
    // Load search engines
    if (root.isMember("search_engines") && root["search_engines"].isObject()) {
        for (const auto& key : root["search_engines"].getMemberNames()) {
            m_context.searchEngines[key] = root["search_engines"][key].asString();
        }
    }
    
    // Load app aliases
    if (root.isMember("app_aliases") && root["app_aliases"].isObject()) {
        for (const auto& key : root["app_aliases"].getMemberNames()) {
            std::vector<std::string> aliases;
            const Json::Value& aliasArray = root["app_aliases"][key];
            if (aliasArray.isArray()) {
                for (const auto& alias : aliasArray) {
                    aliases.push_back(alias.asString());
                }
            }
            m_context.appAliases[key] = aliases;
        }
    }
    
    log("INFO", "Context config loaded successfully");
}

bool CommandExecutor::isCommandAvailable(const std::string& command) {
    // Extract just the command name (before any arguments)
    std::string cmdName = command;
    size_t spacePos = cmdName.find(' ');
    if (spacePos != std::string::npos) {
        cmdName = cmdName.substr(0, spacePos);
    }
    
    std::string checkCmd = "which " + cmdName + " >/dev/null 2>&1";
    return std::system(checkCmd.c_str()) == 0;
}

std::string CommandExecutor::findApp(const std::string& appName) {
    // Convert to lowercase for matching
    std::string lowerName = appName;
    std::transform(lowerName.begin(), lowerName.end(), lowerName.begin(), ::tolower);
    
    // First check if it's directly available
    if (isCommandAvailable(lowerName)) {
        return lowerName;
    }
    
    // Check in app aliases
    if (m_context.appAliases.count(lowerName)) {
        for (const auto& alias : m_context.appAliases[lowerName]) {
            if (isCommandAvailable(alias)) {
                return alias;
            }
        }
    }
    
    // Check default apps by category
    if (m_context.defaultApps.count(lowerName)) {
        std::string defaultApp = m_context.defaultApps[lowerName];
        if (isCommandAvailable(defaultApp)) {
            return defaultApp;
        }
    }
    
    return "";
}

std::string CommandExecutor::urlEncode(const std::string& str) {
    std::ostringstream encoded;
    encoded.fill('0');
    encoded << std::hex;
    
    for (char c : str) {
        if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            encoded << c;
        } else if (c == ' ') {
            encoded << '+';
        } else {
            encoded << '%' << std::setw(2) << int(static_cast<unsigned char>(c));
        }
    }
    
    return encoded.str();
}

bool CommandExecutor::executeSmartOpen(const std::string& appName) {
    log("INFO", "Smart open requested for: " + appName);
    
    std::string command = findApp(appName);
    
    if (command.empty()) {
        log("WARNING", "Application not found: " + appName);
        return false;
    }
    
    log("INFO", "Opening application: " + command);
    executeCommand(command);
    return true;
}

bool CommandExecutor::executeSmartSearch(const std::string& engine, const std::string& query) {
    log("INFO", "Smart search requested - Engine: " + engine + ", Query: " + query);
    
    // Convert engine name to lowercase
    std::string lowerEngine = engine;
    std::transform(lowerEngine.begin(), lowerEngine.end(), lowerEngine.begin(), ::tolower);
    
    // Find search engine URL
    if (m_context.searchEngines.count(lowerEngine) == 0) {
        log("WARNING", "Unknown search engine: " + engine);
        return false;
    }
    
    std::string baseUrl = m_context.searchEngines[lowerEngine];
    std::string encodedQuery = urlEncode(query);
    std::string url = baseUrl + encodedQuery;
    
    // Get default browser
    std::string browser = "firefox"; // fallback
    if (m_context.defaultApps.count("browser")) {
        browser = m_context.defaultApps["browser"];
    }
    
    std::string command = browser + " '" + url + "'";
    log("INFO", "Opening search URL: " + url);
    executeCommand(command);
    return true;
}

} // namespace VoiceAssistant
