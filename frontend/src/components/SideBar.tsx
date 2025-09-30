import React from 'react';
import { MenuIcon, MessageSquareTextIcon, Plus } from 'lucide-react';

interface TextBlock { block_type: "text"; text: string; }
interface ReactBlock { block_type: "react"; description?: string; code: string; }
interface LLMOutputBlock { blocks: (TextBlock | ReactBlock)[]; }

type ApiMessageContent = TextBlock | LLMOutputBlock; // Content can be a TextBlock or LLMOutputBlock

interface ApiMessage {
    id: number;
    chat_session_id: string;
    role: 'user' | 'ai'; // Role can be 'user' or 'ai'
    content: ApiMessageContent;
    created_at: string;
}

interface ChatSession {
    id: string;
    user_id: number;
    title: string;
    created_at: string;
    updated_at: string | null;
    messages: ApiMessage[]; // Messages are now ApiMessage objects
}

interface SideBarProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
    chatHistory: { [key: string]: ChatSession };
    selectedChatId: string | null;
    handleChatSelection: (chatId: string) => void;
    handleNewChat: () => void;
}

const SideBar: React.FC<SideBarProps> = ({ isSidebarOpen, setIsSidebarOpen, chatHistory, selectedChatId, handleChatSelection, handleNewChat }) => {
    const getChatTitle = (chatId: string) => {
        const session = chatHistory[chatId];
        if (session && session.title) {
            const title = session.title;
            return title.length > 20 ? title.substring(0, 20) + '...' : title;
        }
        return 'New Chat';
    };

    return (
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
    );
};

export default SideBar;