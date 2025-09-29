import React from 'react';
import { MenuIcon, MessageSquareTextIcon, Plus } from 'lucide-react';

interface SideBarProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
    chatHistory: { [key: string]: { query: string; response: string; }[] };
    selectedChatId: string | null;
    handleChatSelection: (chatId: string) => void;
    handleNewChat: () => void;
}

const SideBar: React.FC<SideBarProps> = ({ isSidebarOpen, setIsSidebarOpen, chatHistory, selectedChatId, handleChatSelection, handleNewChat }) => {
    const getChatTitle = (chatId: string) => {
        const chat = chatHistory[chatId];
        if (chat && chat[0] && chat[0].query) {
            const title = chat[0].query;
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