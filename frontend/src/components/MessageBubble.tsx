import React, { useEffect, useRef, type CSSProperties } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface Message {
    msg: {
        text: string;
        sender: string;
    };
}

interface CodeComponentProps {
    inline?: boolean;
    className?: string;
    children?: React.ReactNode;
}

const MessageBubble: React.FC<Message> = ({ msg }) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  const codeBlockBackground = msg.sender === 'user' ? 'var(--bubble-user)' : 'var(--bg-secondary)';

  const codeBlockStyle: { [key: string]: CSSProperties } = {
    ...atomDark,
    'code[class*="language-"]': {
      ...(atomDark['code[class*="language-"]'] as CSSProperties),
      background: codeBlockBackground,
      border: 'none',
    },
    'pre[class*="language-"]': {
      ...(atomDark['pre[class*="language-"]'] as CSSProperties),
      background: codeBlockBackground,
      border: 'none',
    },
  };

  useEffect(() => {
    if (msg.text) {
      const jsCodeRegex = /```javascript\n([\s\S]*?)\n```/;
      const match = msg.text.match(jsCodeRegex);

      if (match && chartRef.current) {
        const jsCode = match[1];
        const canvas = chartRef.current;
        const ctx = canvas.getContext('2d');

        if (ctx) {
          // Destroy existing chart instance if it exists
          if (chartInstance.current) {
            chartInstance.current.destroy();
          }

          // Temporarily replace document.getElementById to target our specific canvas
          const originalGetElementById = document.getElementById;
          document.getElementById = (id: string) => {
            if (id === 'myChart') {
              return canvas;
            }
            return originalGetElementById(id);
          };

          try {
            // Execute the JavaScript code
            new Function('Chart', jsCode)(Chart);
          } catch (error) {
            console.error("Error executing chart JavaScript:", error);
          } finally {
            // Restore original document.getElementById
            document.getElementById = originalGetElementById;
          }
        }
      }
    }
  }, [msg.text]);

  const components: Components = {
    code({ inline, className, children }: CodeComponentProps) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={codeBlockStyle as any}
          language={match[1]}
          PreTag="p"
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className}>
          {children}
        </code>
      );
    },
  };

  return (
    <div
        className={`message-row ${msg.sender}`}
    >
        <div className="message-bubble">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={components}
            >
                {msg.text}
            </ReactMarkdown>
            {msg.text.includes('```javascript') && (
                <canvas ref={chartRef} id="myChart" width="800" height="400"></canvas>
            )}
        </div>
    </div>
  );
};

export default MessageBubble;
