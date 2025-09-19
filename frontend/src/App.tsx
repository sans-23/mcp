import { useState, useRef, useEffect } from 'react';
import { SendHorizonalIcon, Sparkles, MenuIcon, MessageSquareTextIcon, Plus } from 'lucide-react';
import MessageBubble from './components/MessageBubble';

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
        "373f5b763cc76da3": [{ "query": "hi", "response": "Hi! How can I help you with GitHub today?" }],
        "cd1cf0a6a41b215a": [{ "query": "what are the tool you have, list prominent five", "response": "Here are five prominent tools from the available API..." }],
        "3ccfce796e57ffdd": [{ "query": "get file content for .env in mcp repo", "response": "Who is the owner of the mcp repository?" }],
        "1bd5cc3694c9ea06": [{ "query": "sans-23", "response": "I can help you with that, but I need more information..." }],
        "5a193b6a85da3309": [{ "query": "get file content for .env in mcp repo owner is sans-23", "response": "" }],
        "786318468f6868f5": [{ "query": "hey", "response": "How can I help?" }],
        "6bff23bdc68082a7": [{ "query": "hi", "response": "Hi there! How can I help you with GitHub today?" }],
        "d9f9210286bc0a25": [{ "query": "hi", "response": "Hi! How can I help you with GitHub today?" }],
        "20205d41dfa97f1a": [{ "query": "hi", "response": "Hi there! How can I help you today?" }],
        "95e5091f9c28c3ec": [{ "query": "ho", "response": "How can I help?" }],
        "4c4f574df60d03b6": [{ "query": "dd", "response": "I am designed to help with GitHub related tasks. Can you please provide more details on what you would like to do?" }],
        "e351578cdfb3573e": [{ "query": "d", "response": "I am sorry, I cannot fulfill this request. The input 'd' is too short..." }],
        "eeb748f0ae87af12": [{ "query": "hi", "response": "Hi! How can I help you with GitHub today?" }],
        "fca943c848b389b8": [{ "query": "ask me my name", "response": "I do not have access to your name..." }],
        "8fad6a7949b27ac2": [{ "query": "naruto ", "response": "Could you please provide more details? I need the owner and repository name to proceed..." }],
        "afaa6c70d7557194": [{ "query": "my profile details sans-23", "response": "" }],
        "88718b88544fb0a3": [{ "query": "what happened", "response": "I am ready to help. What happened, and how can I help with it?" }],
        "3b03e555f5957078": [{ "query": "kuch nhi", "response": "I am sorry, I cannot fulfill this request..." }],
        "01ba9e963a01c338": [{ "query": "hi", "response": "Hi! How can I help you with GitHub today?" }],
        "3b548de44f837722": [{ "query": "hi", "response": "Hi there! How can I help you with GitHub today?" }],
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
            <style>
                {`
                :root {
                    --bg-primary: #171618;
                    --bg-secondary: #2C2D30;
                    --text-primary: #ECECEC;
                    --text-secondary: #B0B0B0;
                    --bubble-user: #1f3760;
                    --input-bg: #2C2D30;
                    --border-color: #3B3B3B;
                    --sidebar-width-open: 280px;
                    --sidebar-width-closed: 64px;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: var(--bg-primary);
                    color: var(--text-primary);
                    margin: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                }
                
                .app-wrapper {
                    display: flex;
                    width: 100vw;
                    height: 100vh;
                    overflow: hidden;
                }

                .sidebar {
                    width: var(--sidebar-width-open);
                    background-color: var(--bg-primary);
                    color: var(--text-secondary);
                    transition: width 0.3s ease-in-out;
                    flex-shrink: 0;
                    display: flex;
                    flex-direction: column;
                    padding: 1rem;
                    border-right: 1px solid var(--border-color);
                }

                .sidebar.closed {
                    width: var(--sidebar-width-closed);
                    align-items: center;
                }

                .sidebar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                    color: var(--text-primary);
                }

                .sidebar-header.closed {
                    justify-content: center;
                }

                .new-chat-button {
                    display: flex;
                    align-items: center;
                    background-color: var(--input-bg);
                    color: var(--text-primary);
                    padding: 0.75rem 1rem;
                    border-radius: 9999px;
                    border: none;
                    cursor: pointer;
                    font-size: 0.875rem;
                    transition: background-color 0.2s;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .new-chat-button:hover {
                    background-color: #3b3b3b;
                }
                
                .chat-history-list {
                    flex: 1;
                    overflow-y: auto;
                    transition: opacity 0.3s ease-in-out;
                    opacity: 1;
                    padding: 0;
                    margin: 0;
                }
                
                .chat-history-list.hidden {
                    opacity: 0;
                    pointer-events: none;
                }

                .chat-history-item {
                    display: flex;
                    align-items: center;
                    padding: 0.75rem 0.5rem;
                    border-radius: 0.5rem;
                    margin-bottom: 0.5rem;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                
                .chat-history-item.selected {
                    background-color: var(--bg-secondary);
                }

                .chat-history-item:hover {
                    background-color: var(--bg-secondary);
                }

                .chat-history-item-text {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    margin-left: 0.5rem;
                }

                .chat-container-main {
                    display: flex;
                    flex-direction: column;
                    flex-grow: 1;
                    height: 100vh;
                    background-color: var(--bg-primary);
                    transition: width 0.3s ease-in-out;
                }

                .chat-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem;
                    background-color: var(--bg-primary);
                    max-width: 960px;
                    width: 100%;
                    margin: 0 auto;
                    border-bottom: 1px solid var(--border-color);
                    position: sticky;
                    top: 0;
                    z-index: 1;
                }

                .header-title {
                    font-size: 1.2rem;
                    font-weight: 500;
                    color: var(--text-primary);
                }

                .messages-list {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1rem 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    scroll-behavior: smooth;
                    max-width: 960px;
                    width: 100%;
                    margin: 0 auto;
                }

                .empty-chat-message {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    height: 100%;
                    text-align: center;
                    color: var(--text-secondary);
                }

                .empty-chat-message h2 {
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                }

                .empty-chat-message p {
                    font-size: 0.875rem;
                    padding: 0 2rem;
                    max-width: 28rem;
                }

                .message-row {
                    display: flex;
                }

                .message-row.user {
                    justify-content: flex-end;
                }

                .message-bubble {
                    max-width: 85%;
                    min-width: 8rem;
                    padding: 0.05rem 1rem;
                    border-radius: 1rem;
                    transition: all 0.3s ease-in-out;
                    font-size: 0.875rem;
                    line-height: 1.5;
                }

                .message-row.user .message-bubble {
                    background-color: var(--bubble-user);
                    color: var(--text-primary);
                }

                .message-row.ai .message-bubble {
                    background-color: var(--bg-secondary);
                    color: var(--text-secondary);
                }

                .input-form {
                    flex-shrink: 0;
                    padding: 1rem;
                    position: sticky;
                    bottom: 0;
                    background-color: var(--bg-primary);
                    max-width: 960px;
                    width: 100%;
                    margin: 0 auto;
                }

                .input-wrapper {
                    position: relative;
                    display: flex;
                    align-items: center;
                    width: 100%;
                    background-color: var(--input-bg);
                    border-radius: 9999px;
                    border: 1px solid var(--border-color);
                }

                .input-field {
                    width: 100%;
                    padding: 0.75rem 3.5rem 0.75rem 1.5rem;
                    font-size: 0.875rem;
                    color: var(--text-primary);
                    background-color: transparent;
                    outline: none;
                    border: none;
                }

                .input-field::placeholder {
                    color: var(--text-secondary);
                    transition: color 0.2s;
                }

                .input-field:focus::placeholder {
                    color: rgba(156, 163, 175, 0.8);
                }

                .send-button {
                    position: absolute;
                    right: 0.625rem;
                    padding: 0.5rem;
                    border-radius: 9999px;
                    transition: background-color 0.2s;
                    background-color: transparent;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .send-button:hover:not(:disabled) {
                    background-color: #3b3b3b;
                }

                .send-button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .send-icon {
                    width: 1.25rem;
                    height: 1.25rem;
                    color: var(--text-secondary);
                }

                @media (max-width: 768px) {
                    .sidebar {
                        position: fixed;
                        top: 0;
                        left: 0;
                        height: 100vh;
                        z-index: 10;
                    }
                }
                `}
            </style>
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
                        <Sparkles size={24} style={{ color: '#d3e3fd' }} />
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
