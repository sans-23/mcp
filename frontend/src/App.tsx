import { useState, useRef, useEffect } from 'react';
import { SendHorizonalIcon } from 'lucide-react';
import MessageBubble from './components/MessageBubble';
import SideBar from './components/SideBar';
import './App.css';

function App() {
    type ChatMessage = { text: string; sender: string; }; // This is for the UI display

    type ApiMessageContent = { text: string; }; // Content is an object with a text property

    type ApiMessage = {
        id: number;
        chat_session_id: string;
        role: 'user' | 'ai'; // Role can be 'user' or 'ai'
        content: ApiMessageContent;
        created_at: string;
    };

    type ChatSession = {
        id: string;
        user_id: number;
        title: string;
        created_at: string;
        updated_at: string | null;
        messages: ApiMessage[]; // Messages are now ApiMessage objects
    };

    type ChatHistory = {
        [key: string]: ChatSession;
    };
    
    const [chatHistory, setChatHistory] = useState<ChatHistory>({});
    const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]); // Use ChatMessage for display
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch chat sessions from the backend to populate the sidebar
    useEffect(() => {
        const fetchChatSessions = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/v1/sessions/user/2'); // Assuming user_id is 1
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                const sessions: ChatSession[] = data.sessions;

                console.log('Fetched sessions:', sessions);

                const formattedChatHistory: ChatHistory = {};
                sessions.forEach((session: ChatSession) => {
                    // Initialize messages as empty, they will be fetched on selection
                    formattedChatHistory[session.id] = { ...session, messages: [] }; 
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

    // Fetch and display messages for the selected chat session
    useEffect(() => {
        const fetchAndDisplaySessionMessages = async () => {
            if (!selectedChatId) {
                setMessages([]);
                return;
            }

            setIsLoading(true);
            try {
                // Check if messages are already loaded in chatHistory for this session
                const currentSession = chatHistory[selectedChatId];
                if (currentSession && currentSession.messages && currentSession.messages.length > 0) {
                    const formattedMessages = currentSession.messages.map(apiMsg => ({
                        text: apiMsg.content.text,
                        sender: apiMsg.role
                    }));
                    setMessages(formattedMessages);
                    setIsLoading(false);
                    return;
                }

                // If not loaded, fetch from /api/v1/sessions/{session_id}
                const response = await fetch(`http://localhost:8000/api/v1/sessions/${selectedChatId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const sessionDetail: ChatSession = await response.json(); // The response is now a ChatSession

                // Update chatHistory with the fetched messages for this specific session
                setChatHistory(prev => ({
                    ...prev,
                    [selectedChatId]: {
                        ...prev[selectedChatId],
                        messages: sessionDetail.messages, // Store the raw API messages
                    } as ChatSession,
                }));

                const formattedMessages = sessionDetail.messages.map(apiMsg => ({
                    text: apiMsg.content.text,
                    sender: apiMsg.role
                }));
                setMessages(formattedMessages);

            } catch (error) {
                console.error('Error fetching session messages:', error);
                setMessages([{ text: 'Error: Could not load messages for this session.', sender: 'ai' }]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchAndDisplaySessionMessages();
    }, [selectedChatId]); // Removed chatHistory from dependency array

    // Update chat history in state on message send
    const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedChatId) return;

        setIsLoading(true);
        
        const newUserApiMessage: ApiMessage = { 
            id: Date.now(), // Temporary ID
            chat_session_id: selectedChatId,
            role: 'user',
            content: { text: input },
            created_at: new Date().toISOString()
        };

        const currentSession = chatHistory[selectedChatId];
        const updatedMessagesForSend = [...(currentSession?.messages || []), newUserApiMessage];
        
        setChatHistory(prev => ({
            ...prev,
            [selectedChatId]: {
                ...currentSession,
                messages: updatedMessagesForSend,
            } as ChatSession,
        }));
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
            const aiResponseContent = data.response; // Assuming data.response is the AI's text response
            const aiApiMessage: ApiMessage = { 
                id: Date.now(), // Temporary ID
                chat_session_id: selectedChatId,
                role: 'ai',
                content: { text: aiResponseContent },
                created_at: new Date().toISOString()
            };
            
            setChatHistory(prev => {
                const updatedSession = { ...prev[selectedChatId] };
                if (updatedSession.messages) {
                    updatedSession.messages.push(aiApiMessage);
                }
                return { ...prev, [selectedChatId]: updatedSession as ChatSession };
            });
        } catch (error) {
            console.error('Error sending message:', error);
            setChatHistory(prev => {
                const updatedSession = { ...prev[selectedChatId] };
                if (updatedSession.messages) {
                    // Find the last user message and update its content to show an error
                    let lastUserMessage: ApiMessage | undefined;
                    for (let i = updatedSession.messages.length - 1; i >= 0; i--) {
                        if (updatedSession.messages[i].role === 'user') {
                            lastUserMessage = updatedSession.messages[i];
                            break;
                        }
                    }
                    if (lastUserMessage) {
                        lastUserMessage.content.text = 'Error: Could not get a response.';
                    }
                }
                return { ...prev, [selectedChatId]: updatedSession as ChatSession };
            });
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
            const response = await fetch('http://localhost:8000/api/v1/sessions/user/2', { // Assuming user_id is 2
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: "New Chat" }), // Provide a default title
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const newSession: ChatSession = await response.json();
            setChatHistory(prev => ({ ...prev, [newSession.id]: { ...newSession, messages: [] } })); // Initialize messages as empty
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
