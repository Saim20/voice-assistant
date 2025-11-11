#include "VoiceAssistantService.hpp"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <ctime>
#include <iomanip>
#include <cstdlib>
#include <filesystem>
#include <cmath>
#include <regex>
#include <sys/wait.h>
#include <chrono>

namespace fs = std::filesystem;

namespace VoiceAssistant {

VoiceAssistantService::VoiceAssistantService(sdbus::IConnection& connection, std::string objectPath)
    : m_connection(connection)
    , m_objectPath(std::move(objectPath))
    , m_whisperCtx(nullptr)
    , m_isRunning(false)
    , m_currentMode(Mode::Normal)
    , m_hotword("hey")
    , m_commandThreshold(0.8)
    , m_processingInterval(1.5)
    , m_typingExitPhrases({"stop typing", "exit typing", "normal mode", "go to normal mode"})
    , m_stopAudioThread(false)
    , m_pulseAudio(nullptr)
    , m_lastCommandTime(std::chrono::steady_clock::now())
{
    // Create D-Bus object
    m_object = sdbus::createObject(m_connection, sdbus::ObjectPath(m_objectPath));

    // Register D-Bus methods using vtable API (sdbus-c++ v2.x)
    const char* interfaceName = "com.github.saim.VoiceAssistant";
    
    // Helper lambdas for method callbacks
    auto setModeCallback = [this](sdbus::MethodCall call) {
        std::string mode;
        call >> mode;
        this->SetMode(mode);
        auto reply = call.createReply();
        reply.send();
    };
    
    auto getModeCallback = [this](sdbus::MethodCall call) {
        auto reply = call.createReply();
        reply << this->GetMode();
        reply.send();
    };
    
    auto getStatusCallback = [this](sdbus::MethodCall call) {
        auto reply = call.createReply();
        reply << this->GetStatus();
        reply.send();
    };
    
    auto getConfigCallback = [this](sdbus::MethodCall call) {
        auto reply = call.createReply();
        reply << this->GetConfig();
        reply.send();
    };
    
    auto updateConfigCallback = [this](sdbus::MethodCall call) {
        std::string config;
        call >> config;
        this->UpdateConfig(config);
        auto reply = call.createReply();
        reply.send();
    };
    
    auto setConfigValueCallback = [this](sdbus::MethodCall call) {
        std::string key;
        sdbus::Variant value;
        call >> key >> value;
        this->SetConfigValue(key, value);
        auto reply = call.createReply();
        reply.send();
    };
    
    auto startCallback = [this](sdbus::MethodCall call) {
        this->Start();
        auto reply = call.createReply();
        reply.send();
    };
    
    auto stopCallback = [this](sdbus::MethodCall call) {
        this->Stop();
        auto reply = call.createReply();
        reply.send();
    };
    
    auto restartCallback = [this](sdbus::MethodCall call) {
        this->Restart();
        auto reply = call.createReply();
        reply.send();
    };
    
    auto getBufferCallback = [this](sdbus::MethodCall call) {
        auto reply = call.createReply();
        reply << this->GetBuffer();
        reply.send();
    };
    
    // Register methods using addVTable with MethodVTableItem
    m_object->addVTable(
        sdbus::MethodVTableItem{sdbus::MethodName{"SetMode"}, sdbus::Signature{"s"}, {"mode"}, sdbus::Signature{""}, {}, setModeCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"GetMode"}, sdbus::Signature{""}, {}, sdbus::Signature{"s"}, {"mode"}, getModeCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"GetStatus"}, sdbus::Signature{""}, {}, sdbus::Signature{"a{sv}"}, {"status"}, getStatusCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"GetConfig"}, sdbus::Signature{""}, {}, sdbus::Signature{"s"}, {"config"}, getConfigCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"UpdateConfig"}, sdbus::Signature{"s"}, {"config"}, sdbus::Signature{""}, {}, updateConfigCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"SetConfigValue"}, sdbus::Signature{"sv"}, {"key", "value"}, sdbus::Signature{""}, {}, setConfigValueCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"Start"}, sdbus::Signature{""}, {}, sdbus::Signature{""}, {}, startCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"Stop"}, sdbus::Signature{""}, {}, sdbus::Signature{""}, {}, stopCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"Restart"}, sdbus::Signature{""}, {}, sdbus::Signature{""}, {}, restartCallback, {}},
        sdbus::MethodVTableItem{sdbus::MethodName{"GetBuffer"}, sdbus::Signature{""}, {}, sdbus::Signature{"s"}, {"buffer"}, getBufferCallback, {}},
        
        sdbus::SignalVTableItem{sdbus::SignalName{"ModeChanged"}, sdbus::Signature{"s"}, {"mode"}, {}},
        sdbus::SignalVTableItem{sdbus::SignalName{"StatusChanged"}, sdbus::Signature{"a{sv}"}, {"status"}, {}},
        sdbus::SignalVTableItem{sdbus::SignalName{"BufferChanged"}, sdbus::Signature{"s"}, {"buffer"}, {}},
        sdbus::SignalVTableItem{sdbus::SignalName{"ConfigChanged"}, sdbus::Signature{"s"}, {"config"}, {}}
    ).forInterface(interfaceName);

    // Set config path
    const char* home = std::getenv("HOME");
    m_configPath = std::string(home) + "/.config/nerd-dictation/config.json";
    m_logFile = "/tmp/voice_assistant.log";

    // Load configuration
    loadConfig();

    // Initialize whisper with default model path - use tiny model
    std::string modelPath = std::string(home) + "/.local/share/voice-assistant/models";
    if (!initializeWhisper(modelPath)) {
        log("ERROR", "Failed to initialize Whisper model");
        emitError("Initialization Error", "Failed to load Whisper model from: " + modelPath);
    }

    log("INFO", "Voice Assistant Service initialized");
}

VoiceAssistantService::~VoiceAssistantService() {
    Stop();
    shutdownWhisper();
}

// D-Bus Method Implementations

void VoiceAssistantService::SetMode(const std::string& mode) {
    Mode newMode = stringToMode(mode);
    std::string oldModeStr = modeToString(m_currentMode);
    
    setModeInternal(newMode);
    emitModeChanged(mode, oldModeStr);
    
    log("INFO", "Mode changed from " + oldModeStr + " to " + mode);
}

std::string VoiceAssistantService::GetMode() {
    return modeToString(m_currentMode);
}

std::map<std::string, sdbus::Variant> VoiceAssistantService::GetStatus() {
    std::map<std::string, sdbus::Variant> status;
    
    status["is_running"] = sdbus::Variant(m_isRunning.load());
    status["current_mode"] = sdbus::Variant(modeToString(m_currentMode));
    
    {
        std::lock_guard<std::mutex> lock(m_bufferMutex);
        status["current_buffer"] = sdbus::Variant(m_currentBuffer);
    }
    
    status["command_count"] = sdbus::Variant(static_cast<int32_t>(m_commands.size()));
    status["whisper_loaded"] = sdbus::Variant(m_whisperCtx != nullptr);
    
    return status;
}

std::string VoiceAssistantService::GetConfig() {
    std::lock_guard<std::mutex> lock(m_configMutex);
    Json::StreamWriterBuilder writer;
    return Json::writeString(writer, configToJson());
}

void VoiceAssistantService::UpdateConfig(const std::string& configJson) {
    std::lock_guard<std::mutex> lock(m_configMutex);
    
    Json::CharReaderBuilder reader;
    Json::Value root;
    std::string errs;
    std::istringstream stream(configJson);
    
    if (Json::parseFromStream(reader, stream, &root, &errs)) {
        jsonToConfig(root);
        saveConfig();
        log("INFO", "Configuration updated via D-Bus");
    } else {
        emitError("Configuration Error", "Failed to parse JSON: " + errs);
    }
}

void VoiceAssistantService::SetConfigValue(const std::string& key, const sdbus::Variant& value) {
    std::lock_guard<std::mutex> lock(m_configMutex);
    
    if (key == "hotword") {
        m_hotword = value.get<std::string>();
    } else if (key == "command_threshold") {
        m_commandThreshold = value.get<double>();
    } else if (key == "processing_interval") {
        m_processingInterval = value.get<double>();
    }
    
    saveConfig();
    log("INFO", "Config value updated: " + key);
}

std::string VoiceAssistantService::GetCommands() {
    std::lock_guard<std::mutex> lock(m_commandsMutex);
    
    Json::Value root(Json::arrayValue);
    for (const auto& cmd : m_commands) {
        Json::Value cmdJson;
        cmdJson["name"] = cmd.name;
        cmdJson["command"] = cmd.command;
        
        Json::Value phrases(Json::arrayValue);
        for (const auto& phrase : cmd.phrases) {
            phrases.append(phrase);
        }
        cmdJson["phrases"] = phrases;
        
        root.append(cmdJson);
    }
    
    Json::StreamWriterBuilder writer;
    return Json::writeString(writer, root);
}

void VoiceAssistantService::AddCommand(const std::string& name, const std::string& command,
                                       const std::vector<std::string>& phrases) {
    std::lock_guard<std::mutex> lock(m_commandsMutex);
    
    // Remove existing command with same name
    auto it = std::remove_if(m_commands.begin(), m_commands.end(),
        [&name](const Command& cmd) { return cmd.name == name; });
    m_commands.erase(it, m_commands.end());
    
    // Add new command
    Command newCmd;
    newCmd.name = name;
    newCmd.command = command;
    newCmd.phrases = phrases;
    m_commands.push_back(newCmd);
    
    saveConfig();
    log("INFO", "Command added: " + name);
}

void VoiceAssistantService::RemoveCommand(const std::string& name) {
    std::lock_guard<std::mutex> lock(m_commandsMutex);
    
    auto it = std::remove_if(m_commands.begin(), m_commands.end(),
        [&name](const Command& cmd) { return cmd.name == name; });
    
    if (it != m_commands.end()) {
        m_commands.erase(it, m_commands.end());
        saveConfig();
        log("INFO", "Command removed: " + name);
    }
}

void VoiceAssistantService::Start() {
    if (m_isRunning) {
        log("WARNING", "Service already running");
        return;
    }
    
    if (!m_whisperCtx) {
        emitError("Start Error", "Whisper model not loaded");
        return;
    }
    
    m_isRunning = true;
    m_stopAudioThread = false;
    
    startAudioCapture();
    
    log("INFO", "Voice Assistant started");
    emitNotification("Voice Assistant", "Service started", "normal");
}

void VoiceAssistantService::Stop() {
    if (!m_isRunning) {
        return;
    }
    
    m_isRunning = false;
    m_stopAudioThread = true;
    
    stopAudioCapture();
    
    log("INFO", "Voice Assistant stopped");
    emitNotification("Voice Assistant", "Service stopped", "normal");
}

void VoiceAssistantService::Restart() {
    log("INFO", "Restarting Voice Assistant");
    Stop();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    Start();
}

std::string VoiceAssistantService::GetBuffer() {
    std::lock_guard<std::mutex> lock(m_bufferMutex);
    return m_currentBuffer;
}

// Signal emission methods

void VoiceAssistantService::emitModeChanged(const std::string& newMode, const std::string& oldMode) {
    m_object->emitSignal("ModeChanged").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(newMode, oldMode);
}

void VoiceAssistantService::emitBufferChanged(const std::string& buffer) {
    m_object->emitSignal("BufferChanged").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(buffer);
}

void VoiceAssistantService::emitCommandExecuted(const std::string& command, 
                                                const std::string& phrase, double confidence) {
    m_object->emitSignal("CommandExecuted").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(command, phrase, confidence);
}

void VoiceAssistantService::emitStatusChanged(const std::map<std::string, sdbus::Variant>& status) {
    m_object->emitSignal("StatusChanged").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(status);
}

void VoiceAssistantService::emitError(const std::string& message, const std::string& details) {
    m_object->emitSignal("Error").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(message, details);
}

void VoiceAssistantService::emitNotification(const std::string& title, 
                                             const std::string& message, 
                                             const std::string& urgency) {
    m_object->emitSignal("Notification").onInterface("com.github.saim.VoiceAssistant")
        .withArguments(title, message, urgency);
}

// Whisper integration

bool VoiceAssistantService::initializeWhisper(const std::string& modelPath) {
    m_modelPath = modelPath;
    
    // Use tiny.en model (smallest, ~75MB)
    std::string modelFile = modelPath + "/ggml-tiny.en.bin";
    
    // Initialize whisper context
    whisper_context_params cparams = whisper_context_default_params();
    m_whisperCtx = whisper_init_from_file_with_params(modelFile.c_str(), cparams);
    
    if (!m_whisperCtx) {
        log("ERROR", "Failed to load Whisper model from: " + modelFile);
        return false;
    }
    
    // Setup whisper parameters
    m_whisperParams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    m_whisperParams.print_progress = false;
    m_whisperParams.print_timestamps = false;
    m_whisperParams.print_special = false;
    m_whisperParams.language = "en";
    m_whisperParams.n_threads = 4;
    m_whisperParams.translate = false;
    
    log("INFO", "Whisper model loaded successfully");
    return true;
}

void VoiceAssistantService::shutdownWhisper() {
    if (m_whisperCtx) {
        whisper_free(m_whisperCtx);
        m_whisperCtx = nullptr;
    }
}

std::string VoiceAssistantService::transcribeAudio(const AudioBuffer& audio) {
    if (!m_whisperCtx || audio.samples.empty()) {
        return "";
    }
    
    // Run whisper inference
    if (whisper_full(m_whisperCtx, m_whisperParams, audio.samples.data(), 
                     audio.samples.size()) != 0) {
        log("ERROR", "Whisper transcription failed");
        return "";
    }
    
    // Get transcription result
    const int n_segments = whisper_full_n_segments(m_whisperCtx);
    std::string result;
    
    for (int i = 0; i < n_segments; ++i) {
        const char* text = whisper_full_get_segment_text(m_whisperCtx, i);
        if (text) {
            result += text;
        }
    }
    
    // Clean the transcription
    result = cleanTranscription(result);
    
    return result;
}

std::string VoiceAssistantService::cleanTranscription(const std::string& text) {
    std::string result = text;
    
    // Remove content inside brackets [], braces {}, and parentheses ()
    // This handles [BLANK_AUDIO], [MUSIC], etc.
    std::regex bracketPattern(R"(\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\))");
    result = std::regex_replace(result, bracketPattern, "");
    
    // Remove punctuation (periods, commas, exclamation marks, question marks, etc.)
    std::regex punctPattern(R"([.,!?;:])");
    result = std::regex_replace(result, punctPattern, "");
    
    // Collapse multiple spaces into single space
    std::regex multiSpacePattern(R"(\s+)");
    result = std::regex_replace(result, multiSpacePattern, " ");
    
    // Trim whitespace
    result.erase(0, result.find_first_not_of(" \t\n\r"));
    result.erase(result.find_last_not_of(" \t\n\r") + 1);
    
    // Convert to lowercase for processing
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    
    return result;
}

// Audio capture (using PulseAudio/PipeWire)

void VoiceAssistantService::startAudioCapture() {
    log("INFO", "Starting audio capture");
    
    // Initialize PulseAudio
    pa_sample_spec ss;
    ss.format = PA_SAMPLE_FLOAT32LE;
    ss.channels = 1;  // Mono
    ss.rate = WHISPER_SAMPLE_RATE;  // 16kHz for Whisper
    
    pa_buffer_attr bufattr;
    bufattr.maxlength = (uint32_t) -1;
    bufattr.fragsize = 4096;  // Fragment size
    
    int error;
    m_pulseAudio = pa_simple_new(
        nullptr,                    // Use default server
        "Voice Assistant",          // Application name
        PA_STREAM_RECORD,           // Record stream
        nullptr,                    // Use default source
        "Voice Input",              // Stream description
        &ss,                        // Sample spec
        nullptr,                    // Use default channel map
        &bufattr,                   // Buffer attributes
        &error                      // Error code
    );
    
    if (!m_pulseAudio) {
        std::string errorMsg = "Failed to connect to PulseAudio: " + std::string(pa_strerror(error));
        log("ERROR", errorMsg);
        emitError("Audio Error", errorMsg);
        return;
    }
    
    log("INFO", "PulseAudio connected successfully");
    m_audioThread = std::thread(&VoiceAssistantService::audioProcessingLoop, this);
}

void VoiceAssistantService::stopAudioCapture() {
    log("INFO", "Stopping audio capture");
    
    if (m_audioThread.joinable()) {
        m_stopAudioThread = true;
        m_audioCv.notify_all();
        m_audioThread.join();
    }
    
    if (m_pulseAudio) {
        pa_simple_free(m_pulseAudio);
        m_pulseAudio = nullptr;
    }
}

void VoiceAssistantService::audioProcessingLoop() {
    log("INFO", "Audio processing loop started");
    
    const size_t CHUNK_SIZE = 4096;  // Number of samples per chunk
    const size_t BUFFER_DURATION_SEC = 2;  // Accumulate 2 seconds of audio for faster detection
    const size_t BUFFER_SIZE = WHISPER_SAMPLE_RATE * BUFFER_DURATION_SEC;
    
    std::vector<float> audioBuffer;
    audioBuffer.reserve(BUFFER_SIZE);
    
    std::vector<float> chunk(CHUNK_SIZE);
    int error;
    
    while (!m_stopAudioThread) {
        // Read audio chunk from PulseAudio
        if (pa_simple_read(m_pulseAudio, chunk.data(), 
                          chunk.size() * sizeof(float), &error) < 0) {
            std::string errorMsg = "Failed to read audio: " + std::string(pa_strerror(error));
            log("ERROR", errorMsg);
            emitError("Audio Error", errorMsg);
            break;
        }
        
        // Accumulate audio
        audioBuffer.insert(audioBuffer.end(), chunk.begin(), chunk.end());
        
        // Process when we have enough audio
        if (audioBuffer.size() >= BUFFER_SIZE) {
            log("INFO", "Processing audio buffer of size: " + std::to_string(audioBuffer.size()));
            
            // Create audio buffer for transcription
            AudioBuffer audio;
            audio.samples = audioBuffer;
            audio.sampleRate = WHISPER_SAMPLE_RATE;
            audio.isComplete = true;
            
            // Transcribe audio
            std::string transcription = transcribeAudio(audio);
            
            if (!transcription.empty()) {
                log("INFO", "Transcription: " + transcription);
                processTranscription(transcription);
            }
            
            // Keep the last 1 second of audio for continuity
            const size_t overlap = WHISPER_SAMPLE_RATE;
            if (audioBuffer.size() > overlap) {
                std::vector<float> newBuffer(
                    audioBuffer.end() - overlap, 
                    audioBuffer.end()
                );
                audioBuffer = std::move(newBuffer);
            } else {
                audioBuffer.clear();
            }
        }
        
        // Check if we should stop
        if (m_stopAudioThread) break;
    }
    
    log("INFO", "Audio processing loop stopped");
}

// Command processing

void VoiceAssistantService::processTranscription(const std::string& text) {
    updateBuffer(text);
    
    Mode currentMode = m_currentMode.load();
    
    log("INFO", "Processing in mode: " + modeToString(currentMode) + ", text: '" + text + "'");
    
    if (currentMode == Mode::Normal) {
        // Check for hotword (already lowercase from cleanTranscription)
        if (text.find(m_hotword) != std::string::npos) {
            log("INFO", "Hotword detected: " + m_hotword);
            setModeInternal(Mode::Command);
            emitModeChanged("command", "normal");
            clearBuffer();
        }
    } else if (currentMode == Mode::Command) {
        // Find best matching command
        auto [bestCmd, confidence] = findBestMatch(text);
        
        log("INFO", "Best match confidence: " + std::to_string(confidence) + 
            ", threshold: " + std::to_string(m_commandThreshold));
        
        if (bestCmd) {
            log("INFO", "Best matching command: " + bestCmd->name + 
                " (confidence: " + std::to_string(confidence * 100) + "%)");
        }
        
        if (bestCmd && confidence >= m_commandThreshold) {
            // Check debounce - prevent commands within 0.5 seconds
            {
                std::lock_guard<std::mutex> lock(m_commandTimeMutex);
                auto now = std::chrono::steady_clock::now();
                auto timeSinceLastCommand = std::chrono::duration_cast<std::chrono::milliseconds>(
                    now - m_lastCommandTime).count();
                
                if (timeSinceLastCommand < 500) {
                    log("INFO", "Command ignored due to debounce (only " + 
                        std::to_string(timeSinceLastCommand) + "ms since last command)");
                    return;
                }
                
                m_lastCommandTime = now;
            }
            
            executeCommand(*bestCmd, confidence);
            // Don't clear buffer - keep it visible in the extension
        } else if (bestCmd) {
            log("INFO", "Command match below threshold, not executing");
        } else {
            log("INFO", "No command matched");
        }
    } else if (currentMode == Mode::Typing) {
        // In typing mode, check for exit phrases first
        log("INFO", "Typing mode: checking for exit phrases in text: '" + text + "'");
        bool shouldExit = false;
        for (const auto& exitPhrase : m_typingExitPhrases) {
            log("INFO", "Checking exit phrase: '" + exitPhrase + "'");
            if (text.find(exitPhrase) != std::string::npos) {
                log("INFO", "Typing exit phrase detected: " + exitPhrase);
                shouldExit = true;
                break;
            }
        }
        
        if (shouldExit) {
            setModeInternal(Mode::Normal);
            emitModeChanged("normal", "typing");
            emitNotification("Mode Changed", "Normal Mode", "normal");
            clearBuffer();
        } else {
            // Normal typing mode - emit buffer changes for text input
            emitBufferChanged(text);
        }
    }
}

void VoiceAssistantService::executeCommand(const Command& cmd, double confidence) {
    log("INFO", "Executing command: " + cmd.name + " (confidence: " + 
        std::to_string(confidence) + ")");
    
    // Check if this is the exit command mode command
    if (cmd.command == "exit_command_mode") {
        log("INFO", "Exit command detected, switching to normal mode");
        setModeInternal(Mode::Normal);
        emitModeChanged("normal", "command");
        emitNotification("Mode Changed", "Normal Mode", "normal");
        clearBuffer();
        return;
    }
    
    // Build command with proper environment and background execution
    // Using systemd-run ensures the app gets proper user session environment
    std::string execCmd = "systemd-run --user --scope --slice=app.slice " + cmd.command + " &";
    
    log("INFO", "Executing: " + execCmd);
    
    // Execute the command in background
    int result = std::system(execCmd.c_str());
    
    // systemd-run returns 0 if it successfully started the scope, even if the app fails later
    // So we consider it successful if systemd-run itself succeeded
    if (result == 0 || WIFEXITED(result)) {
        log("INFO", "Command launched successfully");
        emitCommandExecuted(cmd.command, cmd.name, confidence);
        emitNotification("Command Executed", cmd.name, "normal");
    } else {
        log("ERROR", "Command execution failed with result: " + std::to_string(result));
        emitError("Command Execution Failed", cmd.name);
    }
    
    // Stay in command mode - buffer is not cleared to keep it visible in the extension
}

double VoiceAssistantService::matchPhrase(const std::string& text, const std::string& phrase) {
    // Text is already lowercase from cleanTranscription
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

std::pair<const Command*, double> VoiceAssistantService::findBestMatch(const std::string& text) {
    std::lock_guard<std::mutex> lock(m_commandsMutex);
    
    const Command* bestCmd = nullptr;
    double bestConfidence = 0.0;
    
    for (const auto& cmd : m_commands) {
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

// Configuration management

void VoiceAssistantService::loadConfig() {
    std::lock_guard<std::mutex> lock(m_configMutex);
    
    std::ifstream file(m_configPath);
    if (!file.is_open()) {
        log("WARNING", "Config file not found, using defaults");
        return;
    }
    
    Json::CharReaderBuilder reader;
    Json::Value root;
    std::string errs;
    
    if (Json::parseFromStream(reader, file, &root, &errs)) {
        jsonToConfig(root);
        log("INFO", "Configuration loaded from: " + m_configPath);
    } else {
        log("ERROR", "Failed to parse config: " + errs);
    }
}

void VoiceAssistantService::saveConfig() {
    // Note: m_configMutex should already be locked by caller
    
    Json::Value root = configToJson();
    
    // Ensure directory exists
    fs::path configPath(m_configPath);
    fs::create_directories(configPath.parent_path());
    
    std::ofstream file(m_configPath);
    if (file.is_open()) {
        Json::StreamWriterBuilder writer;
        writer["indentation"] = "  ";
        file << Json::writeString(writer, root);
        log("INFO", "Configuration saved");
    } else {
        log("ERROR", "Failed to save config to: " + m_configPath);
    }
}

Json::Value VoiceAssistantService::configToJson() const {
    Json::Value root;
    
    root["hotword"] = m_hotword;
    root["command_threshold"] = m_commandThreshold;
    root["processing_interval"] = m_processingInterval;
    
    Json::Value logging;
    logging["level"] = "INFO";
    logging["file"] = m_logFile;
    root["logging"] = logging;
    
    Json::Value commands(Json::arrayValue);
    for (const auto& cmd : m_commands) {
        Json::Value cmdJson;
        cmdJson["name"] = cmd.name;
        cmdJson["command"] = cmd.command;
        
        Json::Value phrases(Json::arrayValue);
        for (const auto& phrase : cmd.phrases) {
            phrases.append(phrase);
        }
        cmdJson["phrases"] = phrases;
        
        commands.append(cmdJson);
    }
    root["commands"] = commands;
    
    return root;
}

void VoiceAssistantService::jsonToConfig(const Json::Value& json) {
    if (json.isMember("hotword")) {
        m_hotword = json["hotword"].asString();
    }
    
    if (json.isMember("command_threshold")) {
        // Config stores as percentage (0-100), convert to decimal (0.0-1.0)
        m_commandThreshold = json["command_threshold"].asDouble() / 100.0;
    }
    
    if (json.isMember("processing_interval")) {
        m_processingInterval = json["processing_interval"].asDouble();
    }
    
    // Load typing mode exit phrases
    if (json.isMember("typing_mode") && json["typing_mode"].isMember("exit_phrases")) {
        m_typingExitPhrases.clear();
        const auto& exitPhrases = json["typing_mode"]["exit_phrases"];
        if (exitPhrases.isArray()) {
            for (const auto& phrase : exitPhrases) {
                std::string exitPhrase = phrase.asString();
                // Convert to lowercase for matching
                std::transform(exitPhrase.begin(), exitPhrase.end(), exitPhrase.begin(), ::tolower);
                m_typingExitPhrases.push_back(exitPhrase);
            }
            log("INFO", "Loaded " + std::to_string(m_typingExitPhrases.size()) + " typing exit phrases");
        }
    }
    
    if (json.isMember("commands") && json["commands"].isArray()) {
        std::lock_guard<std::mutex> lock(m_commandsMutex);
        m_commands.clear();
        
        for (const auto& cmdJson : json["commands"]) {
            // Skip if this is a comment-only object (all keys start with _)
            bool isCommentOnly = true;
            for (const auto& key : cmdJson.getMemberNames()) {
                if (!key.empty() && key[0] != '_') {
                    isCommentOnly = false;
                    break;
                }
            }
            if (isCommentOnly) {
                continue;
            }
            
            Command cmd;
            cmd.name = cmdJson["name"].asString();
            cmd.command = cmdJson["command"].asString();
            
            if (cmdJson.isMember("phrases") && cmdJson["phrases"].isArray()) {
                for (const auto& phrase : cmdJson["phrases"]) {
                    cmd.phrases.push_back(phrase.asString());
                }
            }
            
            m_commands.push_back(cmd);
            log("INFO", "Loaded command: " + cmd.name + " with " + std::to_string(cmd.phrases.size()) + " phrases");
        }
        
        log("INFO", "Total commands loaded: " + std::to_string(m_commands.size()));
    }
}

// Mode management

void VoiceAssistantService::setModeInternal(Mode mode) {
    m_currentMode = mode;
}

Mode VoiceAssistantService::stringToMode(const std::string& modeStr) const {
    if (modeStr == "command") return Mode::Command;
    if (modeStr == "typing") return Mode::Typing;
    return Mode::Normal;
}

std::string VoiceAssistantService::modeToString(Mode mode) const {
    switch (mode) {
        case Mode::Command: return "command";
        case Mode::Typing: return "typing";
        default: return "normal";
    }
}

// Helper methods

void VoiceAssistantService::log(const std::string& level, const std::string& message) {
    std::lock_guard<std::mutex> lock(m_logMutex);
    
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    
    std::ofstream logFile(m_logFile, std::ios::app);
    if (logFile.is_open()) {
        logFile << std::put_time(&tm, "%Y-%m-%d %H:%M:%S") 
                << " [" << level << "] " << message << std::endl;
    }
}

void VoiceAssistantService::clearBuffer() {
    std::lock_guard<std::mutex> lock(m_bufferMutex);
    m_currentBuffer.clear();
    emitBufferChanged("");
}

void VoiceAssistantService::updateBuffer(const std::string& text) {
    std::lock_guard<std::mutex> lock(m_bufferMutex);
    m_currentBuffer = text;
    emitBufferChanged(text);
}

} // namespace VoiceAssistant
