"use client";

import React, { useState, useRef } from "react";
import { Send, Menu } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface Message {
  type: "user" | "assistant" | "status";
  content: string;
  timestamp: string;
}

interface CustomerInfo {
  customer_id: string;
  name: string;
  status?: string;
}

const AuditInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      type: "assistant",
      content: "Welcome to Global Trust Bank! \nGenerate comprehensive audit reports for any loan application — just enter a customer name to begin.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerInfo | null>(null);
  const [searchResults, setSearchResults] = useState<CustomerInfo[]>([]);
  const backendUrl = process.env.NEXT_PUBLIC_AUDIT_BACKEND_URL || "http://localhost:8001";

  const formatTimestamp = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const addMessage = (type: "user" | "assistant" | "status", content: string) => {
    const newMessage: Message = {
      type,
      content,
      timestamp: formatTimestamp()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const sendAuditRequest = async (customerName: string) => {
    try {
      setIsLoading(true);
      addMessage("user", `Generate audit summary for: ${customerName}`);
      addMessage("status", "🔍 Searching for customer and retrieving audit records...");

      const response = await fetch(`${backendUrl}/api/audit/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ customer_name: customerName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add the audit summary response
      addMessage("assistant", data.message || data.audit_summary || "Audit summary generated successfully.");

    } catch (error) {
      console.error("Failed to generate audit summary:", error);
      addMessage("status", `❌ Error: ${error instanceof Error ? error.message : "Failed to generate audit summary"}`);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (currentMessage.trim() && !isLoading) {
      const customerName = currentMessage.trim();
      setCurrentMessage("");
      await sendAuditRequest(customerName);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      sendMessage();
    }
  };

  const renderTable = (tableContent: string) => {
    console.log("Processing table content:", tableContent);
    
    const lines = tableContent.split('\n');
    
    // Find table boundaries more precisely
    let tableStart = -1;
    let tableEnd = -1;
    
    // Look for table header - find line with Stage No. or similar table headers
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.includes('|') && (
        line.toLowerCase().includes('stage') || 
        line.toLowerCase().includes('audit checkpoint') ||
        line.toLowerCase().includes('status') ||
        line.toLowerCase().includes('auditor') ||
        line.toLowerCase().includes('timestamp')
      )) {
        tableStart = i;
        break;
      }
    }
    
    // If no proper header found, look for any line that looks like a table header
    if (tableStart === -1) {
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.includes('|') && line.split('|').length >= 4) {
          // Check if it's not a separator line
          if (!line.includes('---') && !line.includes('===')) {
            tableStart = i;
            break;
          }
        }
      }
    }
    
    if (tableStart === -1) {
      console.log("No table header found");
      return null;
    }
    
    // Find table end
    tableEnd = lines.length;
    for (let i = tableStart + 1; i < lines.length; i++) {
      const line = lines[i].trim();
      // Stop if we hit a line that doesn't contain | or is clearly not part of the table
      if (!line.includes('|') && line !== '') {
        // Unless it's the next line after the header (could be a separator)
        if (i !== tableStart + 1) {
          tableEnd = i;
          break;
        }
      }
    }
    
    const tableLines = lines.slice(tableStart, tableEnd);
    console.log("Extracted table lines:", tableLines);
    
    if (tableLines.length === 0) return null;
    
    // Process table lines - remove separator lines
    const processedLines = tableLines
      .map(line => line.trim())
      .filter(line => line.includes('|') && !line.includes('---') && !line.includes('===') && line !== '');
    
    if (processedLines.length < 2) {
      console.log("Not enough table data");
      return null;
    }
    
    const headerRow = processedLines[0];
    const dataRows = processedLines.slice(1);
    
    // Parse header - clean up the cells
    const headerCells = headerRow
      .split('|')
      .map(cell => cell.trim())
      .filter(cell => cell !== '' && cell !== ' ');
    
    console.log("Final header cells:", headerCells);
    console.log("Data rows count:", dataRows.length);
    
    if (headerCells.length === 0) {
      console.log("No valid header cells");
      return null;
    }
    
    return (
      <div className="overflow-x-auto mt-4">
        <table className="min-w-full border border-gray-200 text-sm">
          <thead>
            <tr className="bg-blue-50">
              {headerCells.map((cell, cellIndex) => (
                <th key={cellIndex} className="px-3 py-2 border border-gray-200 font-bold text-blue-800 text-left">
                  {cell}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((line, rowIndex) => {
              const cells = line
                .split('|')
                .map(cell => cell.trim())
                .filter(cell => cell !== '' && cell !== ' ');
              
              // Pad cells if needed
              while (cells.length < headerCells.length) {
                cells.push('');
              }
              
              return (
                <tr key={rowIndex} className={rowIndex % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  {cells.slice(0, headerCells.length).map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-3 py-2 border border-gray-200 align-top">
                      <div className="whitespace-pre-wrap">{cell}</div>
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  const formatRegularContent = (content: string) => {
    let formattedContent = content;
    
    // Make headers bold
    formattedContent = formattedContent.replace(/(\*\*.*?\*\*)/g, '<strong>$1</strong>');
    formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert ### headers to HTML h3
    formattedContent = formattedContent.replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold text-purple-800 mb-2">$1</h3>');
    
    // Make section headers bold (lines that end with colons)
    formattedContent = formattedContent.replace(/^([^:\n]+:)$/gm, '<strong>$1</strong>');
    
    // Make customer information lines bold
    formattedContent = formattedContent.replace(/^(Customer ID:|Customer Name:|Loan Type:|Requested Amount:|Application Date:|Total Processing Duration:|Application Status:)(.*)$/gm, '<strong>$1</strong>$2');
    
    // Make emoji lines bold
    formattedContent = formattedContent.replace(/^(🧾.*|🧍.*|🔍.*)$/gm, '<strong>$1</strong>');
    
    return formattedContent;
  };

  const renderMessageContent = (content: string) => {
    console.log("Rendering message content:", content.substring(0, 200));
    
    // Check if this is an audit summary report
    const hasAuditMarkers = content.includes('🧾') || content.includes('🧍') || content.includes('🔍');
    const hasAuditKeywords = content.includes('Customer Information') || 
                            content.includes('Detailed Audit Trail') || 
                            content.includes('Overview Summary') ||
                            content.includes('Customer ID:') ||
                            content.includes('Stage No.');
    
    console.log("Has audit markers:", hasAuditMarkers);
    console.log("Has audit keywords:", hasAuditKeywords);
    
    if (hasAuditMarkers || hasAuditKeywords) {
      return renderAuditSummary(content);
    }
    
    // Check for table content even in regular messages
    const hasTableContent = content.includes('|') && (
      content.includes('Stage No.') || 
      content.includes('Audit Checkpoint') ||
      content.includes('---')
    );
    
    if (hasTableContent) {
      console.log("Found table content in regular message");
      // Try to render as table
      const tableMatch = content.match(/(.*?)((?:\|.*\n?)+)(.*)/);
      if (tableMatch) {
        const [, beforeTable, tableContent, afterTable] = tableMatch;
        
        return (
          <div className="space-y-4">
            {beforeTable && (
              <div 
                className="whitespace-pre-line" 
                dangerouslySetInnerHTML={{ __html: formatRegularContent(beforeTable) }}
              />
            )}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              {renderTable(tableContent)}
            </div>
            {afterTable && (
              <div 
                className="whitespace-pre-line" 
                dangerouslySetInnerHTML={{ __html: formatRegularContent(afterTable) }}
              />
            )}
          </div>
        );
      }
    }
    
    return (
      <div 
        className="whitespace-pre-line" 
        dangerouslySetInnerHTML={{ __html: formatRegularContent(content) }}
      />
    );
  };

  const renderAuditSummary = (content: string) => {
    console.log("Full content received:", content);
    
    // Parse the content more robustly
    let titleSection = '';
    let customerSection = '';
    let auditTrailSection = '';
    let overviewSection = '';
    
    // Extract title section (everything before first real section marker)
    const titleMatch = content.match(/^([\s\S]*?)(?=\*\*Customer Information\*\*|🧍|Customer ID:|Customer Name:)/);
    if (titleMatch) {
      titleSection = titleMatch[1].trim();
    }
    
    // Extract customer information section
    const customerPatterns = [
      /(\*\*Customer Information\*\*[\s\S]*?)(?=\*\*Detailed Audit Trail\*\*|🔍|$)/,
      /(🧍[\s\S]*?)(?=🔍|$)/,
      /(Customer ID:[\s\S]*?)(?=\*\*Detailed Audit Trail\*\*|🔍|Stage No\.|$)/
    ];
    
    for (const pattern of customerPatterns) {
      const match = content.match(pattern);
      if (match && match[1]) {
        customerSection = match[1].trim();
        break;
      }
    }
    
    // Extract audit trail section (includes table)
    const auditPatterns = [
      /(\*\*Detailed Audit Trail\*\*[\s\S]*?\|[\s\S]*?)(?=\*\*Overview|Overview Summary|$)/,
      /(🔍[\s\S]*?\|[\s\S]*?)(?=\*\*Overview|Overview Summary|$)/,
      /(\| Stage No\.[\s\S]*?)(?=\*\*Overview|Overview Summary|$)/
    ];
    
    for (const pattern of auditPatterns) {
      const match = content.match(pattern);
      if (match && match[1]) {
        auditTrailSection = match[1].trim();
        break;
      }
    }
    
    // Extract overview section
    const overviewPatterns = [
      /(\*\*Overview Summary\*\*[\s\S]*?)(?=\n\n\n|\n\*\*|$)/,
      /(Overview Summary[\s\S]*?)(?=\n\n\n|\n\*\*|$)/,
      /(\*\*Overview\*\*[\s\S]*?)(?=\n\n\n|\n\*\*|$)/
    ];
    
    for (const pattern of overviewPatterns) {
      const match = content.match(pattern);
      if (match && match[1]) {
        overviewSection = match[1].trim();
        break;
      }
    }
    
    console.log("Sections identified:");
    console.log("- Title:", !!titleSection, titleSection.substring(0, 50));
    console.log("- Customer:", !!customerSection, customerSection.substring(0, 50));
    console.log("- Audit Trail:", !!auditTrailSection, auditTrailSection.substring(0, 50));
    console.log("- Overview:", !!overviewSection, overviewSection.substring(0, 50));

    const formatSection = (sectionContent: string) => {
      let formatted = sectionContent;
      
      // Make headers bold
      formatted = formatted.replace(/(\*\*.*?\*\*)/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      // Convert ### headers to HTML h3
      formatted = formatted.replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold text-blue-800 mb-2">$1</h3>');
      
      // Make customer information lines bold
      formatted = formatted.replace(/^(Customer ID:|Customer Name:|Loan Type:|Requested Amount:|Application Date:|Total Processing Duration:|Application Status:)(.*)$/gm, '<strong>$1</strong>$2');
      
      // Make emoji lines bold
      formatted = formatted.replace(/^(🧾.*|🧍.*|🔍.*)$/gm, '<strong>$1</strong>');
      
      return formatted;
    };

    return (
      <div className="space-y-4">
        {/* Title */}
        {titleSection && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div 
              className="whitespace-pre-line text-center font-bold text-blue-900" 
              dangerouslySetInnerHTML={{ __html: formatSection(titleSection) }}
            />
          </div>
        )}

        {/* Customer Information */}
        {customerSection && (
          <div className="bg-white border border-blue-200 rounded-lg p-4 shadow-sm">
            <div 
              className="whitespace-pre-line" 
              dangerouslySetInnerHTML={{ __html: formatSection(customerSection) }}
            />
          </div>
        )}

        {/* Audit Trail */}
        {auditTrailSection && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            {/* Extract and render the text part before the table */}
            <div>
              {(() => {
                const textBeforeTable = auditTrailSection.split('|')[0].trim();
                return (
                  <div 
                    className="whitespace-pre-line mb-4" 
                    dangerouslySetInnerHTML={{ __html: formatSection(textBeforeTable) }}
                  />
                );
              })()}
            </div>
            
            {/* Render the table if present */}
            {auditTrailSection.includes('|') && (
              <div>
                {renderTable(auditTrailSection)}
              </div>
            )}
          </div>
        )}

        {/* Overview Summary */}
        {overviewSection && (
          <div className="bg-white border border-blue-200 rounded-lg p-4 shadow-sm">
            <div 
              className="whitespace-pre-line" 
              dangerouslySetInnerHTML={{ __html: formatSection(overviewSection) }}
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 text-white shadow-lg">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🏦</div>
            <div>
              <h1 className="text-xl font-bold">Global Trust Bank</h1>
              <p className="text-blue-200 text-sm">AI First Bank</p>
              <p className="text-blue-200 text-sm">AI driven,customer focused</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="text-white hover:bg-blue-800">
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Audit Agent Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
            📊
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">Audit Insight Generation System</h2>
          </div>
          <div className="ml-auto">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="text-xs text-gray-500">Connected</span>
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
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                    {message.content}
                  </span>
                </div>
              )}
              {message.type === "assistant" && (
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                    📊
                  </div>
                  <div className="bg-white rounded-lg p-4 shadow-sm border max-w-4xl">
                    {renderMessageContent(message.content)}
                    <p className="text-xs text-gray-500 mt-2">{message.timestamp}</p>
                  </div>
                </div>
              )}
              {message.type === "user" && (
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white rounded-lg p-4 shadow-sm max-w-md">
                    <p className="whitespace-pre-line">{message.content}</p>
                    <p className="text-xs text-blue-200 mt-2">{message.timestamp}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex items-center justify-center space-x-2 text-gray-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm">Generating audit summary...</span>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center space-x-2 bg-gray-50 rounded-lg border">
            <Input
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Enter customer name to generate audit summary..."
              className="flex-1 border-0 bg-transparent focus:ring-0 text-sm"
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />
            <div className="flex items-center space-x-1 pr-2">
              <Button
                onClick={sendMessage}
                size="icon"
                className="h-8 w-8 bg-blue-600 hover:bg-blue-700"
                disabled={isLoading || !currentMessage.trim()}
              >
                {isLoading ? (
                  <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Enter a customer name to generate their loan application audit summary
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuditInterface;
