#pragma once

#include <sdbus-c++/sdbus-c++.h>
#include <json/json.h>
#include <pulse/simple.h>
#include <pulse/error.h>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <queue>

#include "CommandExecutor.hpp"
#include "SpeechSegmenter.hpp"
#include "ModeWorkers.hpp"

namespace VoiceAssistant {

enum class Mode {
    Normal,
    Command,
    Typing
};

class VoiceAssistantService {
public:
    VoiceAssistantService(sdbus::IConnection& connection, std::string objectPath);
    ~VoiceAssistantService();

    // D-Bus Methods
    void SetMode(const std::string& mode);
    std::string GetMode();
    std::map<std::string, sdbus::Variant> GetStatus();
    std::string GetConfig();
    void UpdateConfig(const std::string& configJson);
    void SetConfigValue(const std::string& key, const sdbus::Variant& value);
    std::string GetCommands();
    void AddCommand(const std::string& name, const std::string& command, 
                    const std::vector<std::string>& phrases);
    void RemoveCommand(const std::string& name);
    void Start();
    void Stop();
    void Restart();
    std::string GetBuffer();

    // D-Bus Signals
    void emitModeChanged(const std::string& newMode, const std::string& oldMode);
    void emitBufferChanged(const std::string& buffer);
    void emitCommandExecuted(const std::string& command, const std::string& phrase, double confidence);
    void emitStatusChanged(const std::map<std::string, sdbus::Variant>& status);
    void emitError(const std::string& message, const std::string& details);
    void emitNotification(const std::string& title, const std::string& message, const std::string& urgency);
    void emitConfigChanged(const std::string& config);

    // D-Bus Properties
    bool IsRunning() const { return m_isRunning; }
    std::string CurrentMode() const { return modeToString(m_currentMode); }
    std::string CurrentBuffer() const;
    std::string Version() const { return "2.0.0"; }

private:
    // Audio capture
    void startAudioCapture();
    void stopAudioCapture();
    void audioProcessingLoop();

    // Transcription handling
    void handleTranscription(const std::string& text);

    // Configuration management
    void loadConfig();
    void saveConfig();
    Json::Value configToJson() const;
    void jsonToConfig(const Json::Value& json);

    // Mode management
    void setModeInternal(Mode mode);
    Mode stringToMode(const std::string& modeStr) const;
    std::string modeToString(Mode mode) const;

    // Helper methods
    void log(const std::string& level, const std::string& message);
    void updateModeWorkers();

    // Member variables
    sdbus::IConnection& m_connection;
    std::string m_objectPath;
    std::unique_ptr<sdbus::IObject> m_object;

    // Core components (shared by all workers)
    std::shared_ptr<CommandExecutor> m_executor;
    std::shared_ptr<SpeechSegmenter> m_segmenter;
    
    // Mode workers
    std::unique_ptr<NormalModeWorker> m_normalWorker;
    std::unique_ptr<CommandModeWorker> m_commandWorker;
    std::unique_ptr<TypingModeWorker> m_typingWorker;
    ModeWorker* m_currentWorker;

    // State
    std::atomic<bool> m_isRunning;
    std::atomic<Mode> m_currentMode;
    mutable std::mutex m_modeMutex;
    
    // Commands
    std::vector<Command> m_commands;
    mutable std::mutex m_commandsMutex;

    // Configuration
    std::string m_hotword;
    double m_commandThreshold;
    double m_processingInterval;
    std::string m_whisperModel;
    bool m_gpuAcceleration;
    std::vector<std::string> m_typingExitPhrases;
    std::string m_configPath;
    std::string m_modelPath;
    mutable std::mutex m_configMutex;

    // Audio processing
    std::thread m_audioThread;
    std::atomic<bool> m_stopAudioThread;
    
    // PulseAudio
    pa_simple* m_pulseAudio;

    // Logging
    std::string m_logFile;
    mutable std::mutex m_logMutex;
};

} // namespace VoiceAssistant
