import { ArrowRight, Database, MessageSquare, Search, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface LandingPageProps {
  onStartChat: () => void;
}

const features = [
  {
    icon: MessageSquare,
    title: 'AI-Powered Chat',
    description: 'Ask questions in natural language and get accurate answers from your knowledge base.',
  },
  {
    icon: Search,
    title: 'Smart Search',
    description: 'Semantic search powered by embeddings finds the most relevant information.',
  },
  {
    icon: Database,
    title: 'Jira & Confluence',
    description: 'Automatically syncs and indexes your Jira issues and Confluence pages.',
  },
  {
    icon: Sparkles,
    title: 'Source Citations',
    description: 'Every answer includes links to the original documents for verification.',
  },
];

export function LandingPage({ onStartChat }: LandingPageProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
      {/* Hero Section */}
      <div className="text-center space-y-6 mb-12">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          Knowledge Base
          <span className="text-primary"> AI Assistant</span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Your intelligent companion for navigating Jira issues and Confluence documentation.
          Ask questions, get answers with source citations.
        </p>
        <Button size="lg" onClick={onStartChat} className="gap-2">
          Start Chatting
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-6xl">
        {features.map((feature) => (
          <Card key={feature.title} className="bg-card/50 hover:bg-card transition-colors">
            <CardHeader>
              <feature.icon className="h-10 w-10 text-primary mb-2" />
              <CardTitle className="text-lg">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{feature.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
