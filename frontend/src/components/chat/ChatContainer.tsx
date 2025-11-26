import { useEffect, useRef } from 'react';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useChatStore } from '@/store/chatStore';
import { sendMessage } from '@/services/api';

interface ChatContainerProps {
  onBack: () => void;
}

export function ChatContainer({ onBack }: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const {
    currentSession,
    isLoading,
    error,
    createSession,
    addMessage,
    setLoading,
    setError,
    clearCurrentSession,
  } = useChatStore();

  // Create session if none exists
  useEffect(() => {
    if (!currentSession) {
      createSession();
    }
  }, [currentSession, createSession]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentSession?.messages]);

  const handleSend = async (content: string) => {
    if (!currentSession) return;

    // Add user message
    addMessage('user', content);
    setLoading(true);
    setError(null);

    try {
      const response = await sendMessage({
        query: content,
        session_id: currentSession.id,
      });

      // Add assistant message with sources
      addMessage('assistant', response.response, response.sources);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      addMessage('assistant', `Sorry, I encountered an error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Chat header */}
      <div className="flex items-center justify-between pb-4 border-b">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h2 className="font-semibold">Chat Session</h2>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={clearCurrentSession}
          title="Clear chat"
        >
          <Trash2 className="h-5 w-5" />
        </Button>
      </div>

      {/* Messages area */}
      <ScrollArea className="flex-1 py-4">
        <div className="space-y-4 pr-4">
          {currentSession?.messages.length === 0 && (
            <div className="text-center text-muted-foreground py-12">
              <p className="text-lg mb-2">Start a conversation</p>
              <p className="text-sm">
                Ask questions about your Jira issues and Confluence pages
              </p>
            </div>
          )}

          {currentSession?.messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {error && (
            <div className="text-destructive text-sm text-center py-2">
              {error}
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="pt-4 border-t">
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  );
}
