import { useState, useRef, useEffect } from 'react';
import { SendHorizonalIcon } from 'lucide-react';
import './App.css';
import SideBar from './components/SideBar';
import MessageBubble from './components/MessageBubble';

function App() {
    const [messages, setMessages] = useState<{ text: string; sender: string; }[]>([]);
    const [input, setInput] = useState('');
    const [chatId, setChatId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Mock chat history for the sidebar
    const chatHistory = [
        "What are the benefits of React?",
        "How to center a div in CSS?",
        "Explain machine learning concepts.",
        "Write a Python function for a linked list.",
        "Summarize the plot of Inception.",
    ];

    const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        setIsLoading(true);
        const userMessage = { text: input, sender: 'user' };
        setMessages(prev => [...prev, userMessage]);
        setInput('');

        try {
            const payload = { query: input, chatId };
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const aiResponse = { text: data.response, sender: 'ai' };
            setMessages(prev => [...prev, aiResponse]);
            setChatId(data.chat_id);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { text: 'Error: Could not get a response.', sender: 'ai' }]);
        } finally {
            setIsLoading(false);
        }
    };

    // Auto-scroll to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <>
            <div className="app-wrapper">
                {/* Sidebar */}
                <SideBar
                   isSidebarOpen={isSidebarOpen}
                   setIsSidebarOpen={setIsSidebarOpen}
                   chatHistory={chatHistory}
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