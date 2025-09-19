import React from 'react'

interface Message {
    msg: {

        text: string;

        sender: string;

    };
}

const MessageBubble: React.FC<Message> = ({ msg }) => {
  return (
    <div
        className={`message-row ${msg.sender}`}
    >
        <div className="message-bubble">
            <p>{msg.text}</p>
        </div>
    </div>
  )
}

export default MessageBubble
