#pragma once

#include "CommandExecutor.hpp"
#include "SpeechSegmenter.hpp"
#include <string>
#include <memory>
#include <atomic>
#include <functional>

namespace VoiceAssistant {

/**
 * Base class for mode workers
 */
class ModeWorker {
public:
    using ModeChangeCallback = std::function<void(const std::string&)>;
    
    virtual ~ModeWorker() = default;
    
    // Lifecycle
    virtual void start() = 0;
    virtual void stop() = 0;
    virtual bool isRunning() const = 0;
    
    // Process transcribed text
    virtual void processTranscription(const std::string& text) = 0;
    
    // Set mode change callback
    void setModeChangeCallback(ModeChangeCallback callback) {
        m_modeChangeCallback = callback;
    }
    
    // Get current buffer (for display)
    virtual std::string getBuffer() const = 0;

protected:
    ModeChangeCallback m_modeChangeCallback;
    std::shared_ptr<CommandExecutor> m_executor;
    
    void requestModeChange(const std::string& newMode) {
        if (m_modeChangeCallback) {
            m_modeChangeCallback(newMode);
        }
    }
};

/**
 * NormalModeWorker - Power-efficient hotword detection
 * 
 * Uses a lightweight approach:
 * - Smaller audio buffers (500ms instead of 2s)
 * - Simple energy-based pre-filtering before whisper
 * - Only transcribes when energy suggests speech
 */
class NormalModeWorker : public ModeWorker {
public:
    NormalModeWorker(std::shared_ptr<CommandExecutor> executor,
                     std::shared_ptr<SpeechSegmenter> segmenter);
    ~NormalModeWorker() override = default;
    
    void start() override;
    void stop() override;
    bool isRunning() const override { return m_isRunning; }
    
    void processTranscription(const std::string& text) override;
    
    void setHotword(const std::string& hotword) { m_hotword = hotword; }
    
    std::string getBuffer() const override { return ""; }  // No buffer in normal mode

private:
    std::atomic<bool> m_isRunning;
    std::string m_hotword;
    std::shared_ptr<SpeechSegmenter> m_segmenter;
};

/**
 * CommandModeWorker - Command matching and execution
 */
class CommandModeWorker : public ModeWorker {
public:
    CommandModeWorker(std::shared_ptr<CommandExecutor> executor,
                      std::shared_ptr<SpeechSegmenter> segmenter);
    ~CommandModeWorker() override = default;
    
    void start() override;
    void stop() override;
    bool isRunning() const override { return m_isRunning; }
    
    void processTranscription(const std::string& text) override;
    
    void setCommands(const std::vector<Command>& commands);
    void setThreshold(double threshold) { m_threshold = threshold; }
    
    std::string getBuffer() const override;

private:
    std::atomic<bool> m_isRunning;
    std::shared_ptr<SpeechSegmenter> m_segmenter;
    
    std::vector<Command> m_commands;
    mutable std::mutex m_commandsMutex;
    
    double m_threshold;
    
    std::string m_buffer;
    mutable std::mutex m_bufferMutex;
    
    // Duplicate prevention
    struct ExecutionRecord {
        std::string commandName;
        std::chrono::steady_clock::time_point timestamp;
    };
    std::vector<ExecutionRecord> m_executionHistory;
    std::mutex m_historyMutex;
    
    bool isDuplicate(const std::string& commandName);
    void recordExecution(const std::string& commandName);
    void cleanHistory();
};

/**
 * TypingModeWorker - Speech-to-text typing
 */
class TypingModeWorker : public ModeWorker {
public:
    TypingModeWorker(std::shared_ptr<CommandExecutor> executor,
                     std::shared_ptr<SpeechSegmenter> segmenter);
    ~TypingModeWorker() override = default;
    
    void start() override;
    void stop() override;
    bool isRunning() const override { return m_isRunning; }
    
    void processTranscription(const std::string& text) override;
    
    void setExitPhrases(const std::vector<std::string>& phrases) {
        m_exitPhrases = phrases;
    }
    
    std::string getBuffer() const override;

private:
    std::atomic<bool> m_isRunning;
    std::shared_ptr<SpeechSegmenter> m_segmenter;
    
    std::vector<std::string> m_exitPhrases;
    
    std::string m_buffer;
    mutable std::mutex m_bufferMutex;
    
    bool checkExitPhrases(const std::string& text);
};

} // namespace VoiceAssistant
