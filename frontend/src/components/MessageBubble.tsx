import React, { useEffect, useRef, type CSSProperties } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Chart, registerables } from 'chart.js';
import * as Babel from '@babel/standalone';

Chart.register(...registerables);

interface TextBlock { block_type: "text"; text: string; }
interface ReactBlock { block_type: "react"; description?: string; code: string; }
interface LLMOutputBlock { blocks: (TextBlock | ReactBlock)[]; }

type ApiMessageContent = TextBlock | LLMOutputBlock; // Content can be a TextBlock or LLMOutputBlock

interface Message {
    msg: {
        content: ApiMessageContent;
        role: 'user' | 'ai'; // Changed from sender to role
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

  // Ensure msg.content is not undefined before proceeding
  if (!msg.content) {
    return null; // Or render a fallback UI
  }

  const codeBlockBackground = msg.role === 'user' ? 'var(--bubble-user)' : 'var(--bg-secondary)'; // Changed from sender to role

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
    if ('blocks' in msg.content) {
      let chartCode = '';
      let reactComponentCode = '';

      for (const block of msg.content.blocks) {
        if (block.block_type === 'react') {
          reactComponentCode = block.code;
          // For now, we'll assume react blocks might contain chart.js code
          // In a more sophisticated setup, you'd parse or have a specific block type for charts
          const jsCodeRegex = /```javascript\n([\s\S]*?)\n```/;
          const match = reactComponentCode.match(jsCodeRegex);
          if (match) {
            chartCode = match[1];
            break; // Assuming only one chart per message for simplicity
          }
        }
      }

      if (chartCode && chartRef.current) {
        const canvas = chartRef.current;
        const ctx = canvas.getContext('2d');

        if (ctx) {
          if (chartInstance.current) {
            chartInstance.current.destroy();
          }

          const originalGetElementById = document.getElementById;
          document.getElementById = (id: string) => {
            if (id === 'myChart') {
              return canvas;
            }
            return originalGetElementById(id);
          };

          try {
            new Function('Chart', chartCode)(Chart);
          } catch (error) {
            console.error("Error executing chart JavaScript:", error);
          } finally {
            document.getElementById = originalGetElementById;
          }
        }
      }
    }
  }, [msg.content]);

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
        className={`message-row ${msg.role}`}
    >
        <div className="message-bubble">
            {'blocks' in msg.content ? (
                msg.content.blocks.map((block, index) => {
                    if (block.block_type === 'text') {
                        return (
                            <ReactMarkdown
                                key={index}
                                remarkPlugins={[remarkGfm]}
                                components={components}
                            >
                                {block.text}
                            </ReactMarkdown>
                        );
                    } else if (block.block_type === 'react') {
                        // Dynamically render React component from code string
                        const DynamicComponent = () => {
                            try {
                                // Transpile JSX to React.createElement calls
                                const transpiledCode = Babel.transform(block.code, {
                                    presets: ['react', 'env']
                                }).code;

                                if (!transpiledCode) {
                                    console.error("Babel transformation failed or returned empty code.");
                                    return <p>Error rendering component: Transformation failed.</p>;
                                }

                                const exports: { default?: React.ComponentType<any> } = {};
                                const func = new Function('React', 'exports', transpiledCode.replace(/export default/, 'exports.default ='));
                                func(React, exports);
                                const Component = exports.default;
                                return Component ? <Component /> : null;
                            } catch (e) {
                                console.error("Error rendering React component:", e);
                                return <p>Error rendering component.</p>;
                            }
                        };
                        return <DynamicComponent key={index} />;
                    }
                    return null;
                })
            ) : (
                // Fallback for old text-only messages or if content is just a TextBlock
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={components}
                >
                    {'text' in msg.content ? msg.content.text : ''}
                </ReactMarkdown>
            )}
            {'blocks' in msg.content && msg.content.blocks.some(block => block.block_type === 'react') && (
                <canvas ref={chartRef} id="myChart" width="800" height="400"></canvas>
            )}
        </div>
    </div>
  );
};

export default MessageBubble;
