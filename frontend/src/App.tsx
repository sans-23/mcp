import { useState, useRef, useEffect } from 'react';
import { SendHorizonalIcon, MenuIcon, MessageSquareTextIcon, Plus } from 'lucide-react';
import MessageBubble from './components/MessageBubble';
import './App.css';

function App() {
    const chatData = {
        "d97690fc37545ac0": [
            { "query": "Who are you and what tools do you have access to?", "response": "I am Gemini, a large language model built by Google..." },
            { "query": "I am sanskar, is sans-23 the owner?", "response": "I do not have enough information to answer the question. Could you please provide the repository name?" },
            { "query": "intellilearn", "response": "OK. Is `sans-23` the owner of the `intellilearn` repository?" },
            { "query": "intellilearn", "response": "Sorry, I am still a little confused. Is `sans-23` the owner of the `intellilearn` repository, or are you asking me to find out?" }
        ],
        "da4712dcff5f76e0": [
            { "query": "intellilearn", "response": "What would you like to do with intellilearn? For example, are you looking for a repository or trying to create one?" },
            { "query": "intellilearn2 create repo", "response": "I can help with that. What would you like the repository to be named?" },
            { "query": "intellilearn2 is repo name, it should be public, basic readme.md, in my personal account", "response": "" },
            { "query": "unstar intellilearn, owner sans-23", "response": "" },
            { "query": "is it done? unstar intellilearn, owner sans-23", "response": "" },
            { "query": "is it done?", "response": "Yes, unstarring intellilearn from sans-23 is done." }
        ],
        "e99622536ea9a039": [{ "query": "hi", "response": "Hi! How can I help you with GitHub today?" }]
    };

    type ChatHistory = {
        [key: string]: { query: string; response: string; }[];
    };
    
    const [chatHistory, setChatHistory] = useState<ChatHistory>(chatData);
    const [selectedChatId, setSelectedChatId] = useState(Object.keys(chatData)[0]);
    const [messages, setMessages] = useState<{ text: string; sender: string; }[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Update displayed messages when selectedChatId changes
    useEffect(() => {
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
    }, [selectedChatId, chatHistory]);

    // Update chat history in state on message send
    const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

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
    
    const handleNewChat = () => {
        const newChatId = Date.now().toString();
        setChatHistory(prev => ({ ...prev, [newChatId]: [] }));
        setSelectedChatId(newChatId);
        setIsSidebarOpen(false); // Close sidebar on new chat
    };

    const getChatTitle = (chatId: string) => {
      const chat = chatHistory[chatId];
      if (chat && chat[0] && chat[0].query) {
        const title = chat[0].query;
        return title.length > 20 ? title.substring(0, 20) + '...' : title;
      }
      return 'New Chat';
    };

    return (
        <>
            <div className="app-wrapper">
                {/* Sidebar */}
                <aside className={`sidebar ${isSidebarOpen ? '' : 'closed'}`}>
                    <div className={`sidebar-header ${isSidebarOpen ? '' : 'closed'}`}>
                        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.5rem' }}>
                            <MenuIcon size={24} color="var(--text-primary)" />
                        </button>
                        {isSidebarOpen && (
                            <button className="new-chat-button" onClick={handleNewChat}>
                                <Plus size={20} />
                                <span style={{ marginLeft: '0.5rem' }}>New Chat</span>
                            </button>
                        )}
                    </div>
                    <div className={`chat-history-list ${isSidebarOpen ? '' : 'hidden'}`}>
                        {Object.keys(chatHistory).map((chatId) => (
                            <div key={chatId} className={`chat-history-item ${selectedChatId === chatId ? 'selected' : ''}`} onClick={() => handleChatSelection(chatId)}>
                                <MessageSquareTextIcon size={16} />
                                <span className="chat-history-item-text">{getChatTitle(chatId)}</span>
                            </div>
                        ))}
                    </div>
                </aside>

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
