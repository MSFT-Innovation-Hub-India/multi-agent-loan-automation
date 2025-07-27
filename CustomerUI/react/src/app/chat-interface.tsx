"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Upload, Menu, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Modality,
  RTClient,
  RTInputAudioItem,
  RTResponse,
  TurnDetection,
} from "rt-client";
import { AudioHandler } from "@/lib/audio";

interface Message {
  type: "user" | "assistant" | "status";
  content: string;
}

interface DocumentDetails {
  filename: string;
  customer_id: string | null;
  uploaded_at: string;
  document_type: string;
  size: number;
}

interface UploadResponse {
  message: string;
  status: string;
  document_details: DocumentDetails;
}

interface ToolDeclaration {
  name: string;
  parameters: string;
  returnValue: string;
}

interface LoanAction {
  id: string;
  label: string;
  message: string;
}

const loanActions: LoanAction[] = [
  {
    id: "eligibility",
    label: "Check Eligibility",
    message: "I would like to check my early eligibility for a applying a loan",
  },
  {
    id: "application",
    label: "Apply Loan",
    message: "I would like to start a new loan application",
  },
  {
    id: "status",
    label: "Track Application",
    message: "I would like to check the status of my loan application",
  },

];

const ChatInterface = () => {
  // NOTE: In production, store secrets securely (Azure Key Vault etc)
  const [isAzure] = useState(true);
  const [apiKey] = useState(
    process.env.NEXT_PUBLIC_AZURE_OPENAI_API_KEY || ""
  );
  const [endpoint] = useState(
    process.env.NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT || ""
  );
  const [deployment] = useState(process.env.NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT || "gpt-4o-mini-realtime-preview");
  const [useVAD] = useState(true);
  const [instructions] = useState(`You are an experienced loan processing agent. Your responsibilities include:
- Evaluating loan applications based on credit score, income, and debt-to-income ratio
- Approving or rejecting loan applications based on established criteria
- Assisting clients with loan application process
- Explaining loan terms, rates, and conditions
- Handling loan modification requests
- Processing loan disbursements
- Managing loan documentation

Please maintain a professional and helpful demeanor while assisting clients with their loan-related inquiries.`);
  const [temperature] = useState(0.6);
  const [modality] = useState("audio");
  const [tools] = useState<ToolDeclaration[]>([]);
  const [messages, setMessages] = useState<Message[]>([
  {
  type: "assistant",
  content: "Welcome to Global Trust Bank! I’m Tria, your Trusted AI assistant here to help you."
},
{
  type: "assistant",
  content: "Welcome to Global Trust Bank! I can assist you with all your loan needs. Here are some quick links ⬇️"
}
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [interactionCount, setInteractionCount] = useState(0);
  const clientRef = useRef<RTClient | null>(null);
  const audioHandlerRef = useRef<AudioHandler | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

  const handleConnect = async () => {
    if (!isConnected) {
      try {
        setIsConnecting(true);
        clientRef.current = isAzure
          ? new RTClient(new URL(endpoint), { key: apiKey }, { deployment })
          : new RTClient(
              { key: apiKey },
              { model: "gpt-4o-realtime-preview-2024-10-01" }
            );
        const modalities: Modality[] =
          modality === "audio" ? ["text", "audio"] : ["text"];
        const turnDetection: TurnDetection = useVAD
          ? { type: "server_vad" }
          : null;
        clientRef.current.configure({
          instructions: instructions?.length > 0 ? instructions : undefined,
          input_audio_transcription: { model: "whisper-1" },
          turn_detection: turnDetection,
          tools,
          temperature,
          modalities,
        });
        startResponseListener();

        setIsConnected(true);
      } catch (error) {
        console.error("Connection failed:", error);
      } finally {
        setIsConnecting(false);
      }
    } else {
      await disconnect();
    }
  };

  const disconnect = async () => {
    if (clientRef.current) {
      try {
        await clientRef.current.close();
        clientRef.current = null;
        setIsConnected(false);
      } catch (error) {
        console.error("Disconnect failed:", error);
      }
    }
  };

  const handleResponse = async (response: RTResponse) => {
    for await (const item of response) {
      if (item.type === "message" && item.role === "assistant") {
        const message: Message = {
          type: item.role,
          content: "",
        };
        setMessages((prevMessages) => [...prevMessages, message]);
        for await (const content of item) {
          if (content.type === "text") {
            for await (const text of content.textChunks()) {
              message.content += text;
              setMessages((prevMessages) => {
                prevMessages[prevMessages.length - 1].content = message.content;
                return [...prevMessages];
              });
            }
          } else if (content.type === "audio") {
            const textTask = async () => {
              for await (const text of content.transcriptChunks()) {
                message.content += text;
                setMessages((prevMessages) => {
                  prevMessages[prevMessages.length - 1].content =
                    message.content;
                  return [...prevMessages];
                });
              }
            };
            const audioTask = async () => {
              audioHandlerRef.current?.startStreamingPlayback();
              for await (const audio of content.audioChunks()) {
                audioHandlerRef.current?.playChunk(audio);
              }
            };
            await Promise.all([textTask(), audioTask()]);
          }
        }
      }
    }
  };

  const handleInputAudio = async (item: RTInputAudioItem) => {
    audioHandlerRef.current?.stopStreamingPlayback();
    await item.waitForCompletion();
    const transcription = item.transcription || "";

    // Add user's transcribed message to chat
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        type: "user",
        content: transcription,
      },
    ]);

    // Send transcribed text to FastAPI backend
    try {
      const response = await fetch(
        `${backendUrl}/agent/message`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: transcription }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add assistant's response to messages using the message field
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          type: "assistant",
          content: data.message, // Changed from data.response to data.message
        },
      ]);


    } catch (error) {
      console.error("Failed to get response from server:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          type: "status",
          content: "Error: Failed to get response from server",
        },
      ]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      await uploadFile(selectedFile);
    }
  };

  const uploadFile = async (selectedFile: File) => {
    if (!selectedFile) return;
    setUploading(true);

    try {
      // Step 1: Upload document
      const formData = new FormData();
      formData.append("file", selectedFile);

      const uploadResponse = await fetch(
        "https://applicationagent.azurewebsites.net/upload-document",
        {
          method: "POST",
          body: formData,
        }
      );

      const uploadData: UploadResponse = await uploadResponse.json();
      if (uploadResponse.ok) {
        // Add upload success message to chat
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "user",
            content: `📎 Uploaded: ${selectedFile.name}`,
          },
        ]);

        // Step 2: Notify agent about successful upload - only send the success message
        const response = await fetch(`${backendUrl}/agent/message`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: uploadData.message, // Just send "Document uploaded successfully"
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Add agent's response to messages
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "assistant",
            content: data.message,
          },
        ]);
      } else {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "status",
            content: `Upload failed: ${uploadData?.message || "Unknown error"}`,
          },
        ]);
      }
    } catch (err) {
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          type: "status",
          content: `Upload error: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ]);
    }

    setUploading(false);
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const startResponseListener = async () => {
    if (!clientRef.current) return;

    try {
      for await (const serverEvent of clientRef.current.events()) {
        if (serverEvent.type === "input_audio") {
          await handleInputAudio(serverEvent);
        }
      }
    } catch (error) {
      if (clientRef.current) {
        console.error("Response iteration error:", error);
      }
    }
  };

  const sendMessage = async () => {
    if (currentMessage.trim()) {
      try {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "user",
            content: currentMessage,
          },
        ]);

        // Send message to FastAPI backend with thread in URL
        const response = await fetch(
          `${backendUrl}/agent/message`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: currentMessage }),
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Add assistant's response to messages
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "assistant",
            content: data.message, // Using the message field from API response
          },
        ]);

        setCurrentMessage("");

      } catch (error) {
        console.error("Failed to send message:", error);
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            type: "status",
            content: "Error: Failed to get response from server",
          },
        ]);
      }
    }
  };

  const toggleRecording = async () => {
    if (!isRecording && clientRef.current) {
      try {
        if (!audioHandlerRef.current) {
          audioHandlerRef.current = new AudioHandler();
          await audioHandlerRef.current.initialize();
        }
        await audioHandlerRef.current.startRecording(async (chunk) => {
          await clientRef.current?.sendAudio(chunk);
        });
        setIsRecording(true);
      } catch (error) {
        console.error("Failed to start recording:", error);
      }
    } else if (audioHandlerRef.current) {
      try {
        audioHandlerRef.current.stopRecording();
        if (!useVAD) {
          const inputAudio = await clientRef.current?.commitAudio();
          await handleInputAudio(inputAudio!);
          await clientRef.current?.generateResponse();
        }
        setIsRecording(false);
      } catch (error) {
        console.error("Failed to stop recording:", error);
      }
    }
  };

  const handleLoanAction = async (actionId: string) => {
    const action = loanActions.find((a) => a.id === actionId);
    if (!action) return;
    
    setSelectedAction(actionId);
    // Hide quick actions immediately when any button is clicked
    setShowQuickActions(false);
    
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        type: "user",
        content: action.message,
      },
    ]);
    
    try {
      const response = await fetch(`${backendUrl}/agent/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: action.message }),
      });
      if (!response.ok) {
        throw new Error("Failed to send message");
      }
      const data = await response.json();
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          type: "assistant",
          content: data.message || "(No response from agent)",
        },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          type: "status",
          content: "Error sending message. Please try again.",
        },
      ]);
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  useEffect(() => {
    const initAndConnect = async () => {
      // Initialize audio handler
      const handler = new AudioHandler();
      await handler.initialize();
      audioHandlerRef.current = handler;

      // Auto-connect to the service
      try {
        setIsConnecting(true);
        clientRef.current = new RTClient(
          new URL(endpoint),
          { key: apiKey },
          { deployment }
        );

        const modalities: Modality[] = ["text", "audio"];
        const turnDetection: TurnDetection = { type: "server_vad" };

        clientRef.current.configure({
          instructions: instructions?.length > 0 ? instructions : undefined,
          input_audio_transcription: { model: "whisper-1" },
          turn_detection: turnDetection,
          tools,
          temperature,
          modalities,
        });

        startResponseListener();
        setIsConnected(true);
      } catch (error) {
        console.error("Auto-connection failed:", error);
      } finally {
        setIsConnecting(false);
      }
    };

    initAndConnect().catch(console.error);

    return () => {
      disconnect();
      audioHandlerRef.current?.close().catch(console.error);
    };
  }, []);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 text-white shadow-lg">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🏦</div>
            <div>
              <h1 className="text-xl font-bold">Global Trust Bank</h1>
              <p className="text-blue-200 text-sm">AI-First Bank</p>
              <p className="text-blue-200 text-sm">AI driven Customer Focused</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="text-white hover:bg-blue-800">
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Tria Assistant Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
            T
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">NEED HELP? ASK TRIA</h2>
            <p className="text-sm text-gray-600">Your Trusted AI Assistant</p>
          </div>
          <div className="ml-auto">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-xs text-gray-500">
                {isConnecting ? 'Connecting...' : isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-4xl mx-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div key={index}>
              {message.type === "status" && (
                <div className="text-center my-2">
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
                    {message.content}
                  </span>
                </div>
              )}
              {message.type === "assistant" && (
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                    T
                  </div>
                  <div className="bg-white rounded-lg p-4 shadow-sm border max-w-md">
                    <p className="text-gray-800 whitespace-pre-line">{message.content}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              )}
              {message.type === "user" && (
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white rounded-lg p-4 shadow-sm max-w-md">
                    <p className="whitespace-pre-line">{message.content}</p>
                    <p className="text-xs text-blue-200 mt-2">
                      {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Action Buttons */}
      {showQuickActions && (
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {loanActions.map((action) => (
                <Button
                  key={action.id}
                  variant="outline"
                  size="sm"
                  onClick={() => handleLoanAction(action.id)}
                  className="text-blue-600 border-blue-200 hover:bg-blue-50 text-xs px-3 py-2 h-auto whitespace-nowrap"
                  disabled={!isConnected}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center space-x-2 bg-gray-50 rounded-lg border">
            <Input
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Type your message here..."
              className="flex-1 border-0 bg-transparent focus:ring-0 text-sm"
              onKeyPress={(e) => e.key === "Enter" && sendMessage()}
              disabled={!isConnected}
            />
            <div className="flex items-center space-x-1 pr-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleFileUpload}
                className="h-8 w-8 text-gray-500 hover:text-blue-600"
                disabled={!isConnected || uploading}
              >
                {uploading ? (
                  <div className="w-4 h-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleRecording}
                className={`h-8 w-8 ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-blue-600'}`}
                disabled={!isConnected}
              >
                {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
              <Button
                onClick={sendMessage}
                size="icon"
                className="h-8 w-8 bg-blue-600 hover:bg-blue-700"
                disabled={!isConnected}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};

export default ChatInterface;