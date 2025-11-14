#pragma once

#include <sdbus-c++/sdbus-c++.h>
#include <whisper.h>
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

namespace VoiceAssistant {

enum class Mode {
    Normal,
    Command,
    Typing
};

struct Command {
    std::string name;
    std::string command;
    std::vector<std::string> phrases;
};

struct AudioBuffer {
    std::vector<float> samples;
    int sampleRate;
    bool isComplete;
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

    // D-Bus Properties
    bool IsRunning() const { return m_isRunning; }
    std::string CurrentMode() const { return modeToString(m_currentMode); }
    std::string CurrentBuffer() const { return m_currentBuffer; }
    std::string Version() const { return "2.0.0"; }

private:
    // Whisper.cpp integration
    bool initializeWhisper(const std::string& modelPath);
    void shutdownWhisper();
    std::string transcribeAudio(const AudioBuffer& audio);
    std::string cleanTranscription(const std::string& text);

    // Audio capture
    void startAudioCapture();
    void stopAudioCapture();
    void audioProcessingLoop();

    // Command processing
    void processTranscription(const std::string& text);
    void executeCommand(const Command& cmd, double confidence);
    double matchPhrase(const std::string& text, const std::string& phrase);
    std::pair<const Command*, double> findBestMatch(const std::string& text);

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
    void clearBuffer();
    void updateBuffer(const std::string& text);

    // Member variables
    sdbus::IConnection& m_connection;
    std::string m_objectPath;
    std::unique_ptr<sdbus::IObject> m_object;

    // Whisper
    whisper_context* m_whisperCtx;
    whisper_full_params m_whisperParams;
    std::string m_modelPath;

    // State
    std::atomic<bool> m_isRunning;
    std::atomic<Mode> m_currentMode;
    std::string m_currentBuffer;
    mutable std::mutex m_bufferMutex;
    
    // Commands
    std::vector<Command> m_commands;
    mutable std::mutex m_commandsMutex;

    // Configuration
    std::string m_hotword;
    double m_commandThreshold;
    double m_processingInterval;
    std::string m_whisperModel;
    std::vector<std::string> m_typingExitPhrases;
    std::string m_configPath;
    mutable std::mutex m_configMutex;

    // Audio processing
    std::thread m_audioThread;
    std::atomic<bool> m_stopAudioThread;
    std::queue<AudioBuffer> m_audioQueue;
    std::mutex m_audioMutex;
    std::condition_variable m_audioCv;
    
    // PulseAudio
    pa_simple* m_pulseAudio;

    // Logging
    std::string m_logFile;
    mutable std::mutex m_logMutex;
    
    // Command debouncing
    std::chrono::steady_clock::time_point m_lastCommandTime;
    std::mutex m_commandTimeMutex;
    
    // Transcription deduplication
    struct TranscriptionRecord {
        std::string text;
        std::chrono::steady_clock::time_point timestamp;
    };
    std::vector<TranscriptionRecord> m_recentTranscriptions;
    std::mutex m_transcriptionMutex;
    bool isDuplicateTranscription(const std::string& text);
    void addTranscriptionRecord(const std::string& text);
    void cleanOldTranscriptions();
};

} // namespace VoiceAssistant
