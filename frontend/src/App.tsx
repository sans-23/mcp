import { useState, useRef, useEffect } from 'react';
import { SendHorizonalIcon } from 'lucide-react';
import MessageBubble from './components/MessageBubble';
import SideBar from './components/SideBar';
import './App.css';

function App() {
    type ChatHistory = {
        [key: string]: { query: string; response: string; }[];
    };
    
    const [chatHistory, setChatHistory] = useState<ChatHistory>({});
    const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
    const [messages, setMessages] = useState<{ text: string; sender: string; }[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch chat sessions from the backend
    useEffect(() => {
        const fetchChatSessions = async () => {
            try {
                const response = await fetch('http://localhost:8000/sessions/user/2'); // Assuming user_id is 2
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                const sessions = data.sessions;

                console.log('Fetched sessions:', sessions);

                const formattedChatHistory: ChatHistory = {};
                sessions.forEach((session: any) => {
                    formattedChatHistory[session.id] = session.messages.map((msg: any) => ({
                        query: msg.query,
                        response: msg.response
                    }));
                });
                setChatHistory(formattedChatHistory);
                if (sessions.length > 0) {
                    setSelectedChatId(sessions[0].id);
                }
            } catch (error) {
                console.error('Error fetching chat sessions:', error);
            }
        };

        fetchChatSessions();
    }, []);

    // Update displayed messages when selectedChatId changes
    useEffect(() => {
        if (selectedChatId) {
            const conversation = chatHistory[selectedChatId];
            if (conversation) {
                const formattedMessages = conversation.flatMap(entry => [
                    { text: entry.query, sender: 'user' },
                    { text: entry.response, sender: 'ai' }
                ]);
                setMessages(formattedMessages);
            } else {
                setMessages([]);
            }
        } else {
            setMessages([]);
        }
    }, [selectedChatId, chatHistory]);

    // Update chat history in state on message send
    const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedChatId) return;

        setIsLoading(true);
        const userMessage = { query: input, response: '' };
        const newMessages = [...(chatHistory[selectedChatId] || []), userMessage];
        setChatHistory(prev => ({ ...prev, [selectedChatId]: newMessages }));
        setInput('');

        try {
            const payload = { query: input, chatId: selectedChatId };
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const aiResponse = { query: input, response: data.response };
            const updatedMessages = [...(chatHistory[selectedChatId] || [])];
            updatedMessages[updatedMessages.length - 1] = aiResponse;
            setChatHistory(prev => ({ ...prev, [selectedChatId]: updatedMessages }));
        } catch (error) {
            console.error('Error sending message:', error);
            const updatedMessages = [...(chatHistory[selectedChatId] || [])];
            updatedMessages[updatedMessages.length - 1].response = 'Error: Could not get a response.';
            setChatHistory(prev => ({ ...prev, [selectedChatId]: updatedMessages }));
        } finally {
            setIsLoading(false);
        }
    };

    // Auto-scroll to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleChatSelection = (chatId: string) => {
        setSelectedChatId(chatId);
    };
    
    const handleNewChat = async () => {
        try {
            const response = await fetch('http://localhost:8000/sessions/user/2', { // Assuming user_id is 2
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: "New Chat" }), // Provide a default title
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const newSession = await response.json();
            setChatHistory(prev => ({ ...prev, [newSession.id]: [] }));
            setSelectedChatId(newSession.id);
            setIsSidebarOpen(false); // Close sidebar on new chat
        } catch (error) {
            console.error('Error creating new chat session:', error);
        }
    };

    return (
        <>
            <div className="app-wrapper">
                <SideBar
                    isSidebarOpen={isSidebarOpen}
                    setIsSidebarOpen={setIsSidebarOpen}
                    chatHistory={chatHistory}
                    selectedChatId={selectedChatId}
                    handleChatSelection={handleChatSelection}
                    handleNewChat={handleNewChat}
                />

                {/* Main Chat Container */}
                <div className="chat-container-main">
                    {/* Header */}
                    <header className="chat-header">
                        <h1 className="header-title">MCP workbench</h1>
                    </header>

                    {/* Messages List */}
                    <div className="messages-list">
                        {messages.length === 0 ? (
                            <div className="empty-chat-message">
                                <h2>Welcome to your Chatbot</h2>
                                <p>This is a minimalistic chat interface inspired by the Gemini UI. Feel free to ask me anything!</p>
                            </div>
                        ) : (
                            messages.map((msg, index) => (
                                <MessageBubble key={index} msg={msg} />
                            ))
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input Form */}
                    <form
                        className="input-form"
                        onSubmit={handleSendMessage}
                    >
                        <div className="input-wrapper">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask me anything..."
                                disabled={isLoading}
                                className="input-field"
                            />
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="send-button"
                            >
                                <SendHorizonalIcon className="send-icon" />
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    );
}

export default App;
