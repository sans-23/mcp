import React from 'react';
import { MenuIcon, MessageSquareTextIcon, Plus } from 'lucide-react';

interface SideBarProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
    chatHistory: string[];
}

const SideBar: React.FC<SideBarProps> = ({ isSidebarOpen, setIsSidebarOpen, chatHistory }) => {
    return (
        <aside className={`sidebar ${isSidebarOpen ? '' : 'closed'}`}>
                    <div className={`sidebar-header ${isSidebarOpen ? '' : 'closed'}`}>
                        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.5rem' }}>
                            <MenuIcon size={24} color="var(--text-primary)" />
                        </button>
                        {isSidebarOpen && (
                            <button className="new-chat-button" onClick={() => {}}>
                                <Plus size={20} />
                                <span style={{ marginLeft: '0.5rem' }}>New Chat</span>
                            </button>
                        )}
                    </div>
                    <div className={`chat-history-list ${isSidebarOpen ? '' : 'hidden'}`}>
                        {chatHistory.map((chat, index) => (
                            <div key={index} className="chat-history-item">
                                <MessageSquareTextIcon size={16} />
                                <span className="chat-history-item-text">{chat}</span>
                            </div>
                        ))}
                    </div>
                </aside>
    );
};

export default SideBar;