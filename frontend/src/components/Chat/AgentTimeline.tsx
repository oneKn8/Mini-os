import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle,
  Clock,
  AlertCircle,
  Zap,
  Brain,
  Code,
  Database,
  TrendingUp,
  Info,
} from 'lucide-react';

interface AgentEvent {
  type: string;
  timestamp?: string;
  content?: string;
  step?: string;
  tool?: string;
  status?: string;
  progress_percent?: number;
  current_step?: number;
  total_steps?: number;
  percent_complete?: number;
  capabilities?: string[];
  data_type?: string;
  count?: number;
  question?: string;
  choice?: string;
  [key: string]: any;
}

interface AgentTimelineProps {
  events: AgentEvent[];
  maxEvents?: number;
}

const EventIcon: React.FC<{ type: string; status?: string }> = ({ type, status }) => {
  const iconClass = "w-4 h-4";

  if (type === 'reasoning') {
    return <Brain className={iconClass} />;
  } else if (type.startsWith('tool')) {
    if (status === 'completed') {
      return <CheckCircle className={`${iconClass} text-green-500`} />;
    } else if (status === 'failed') {
      return <AlertCircle className={`${iconClass} text-red-500`} />;
    }
    return <Code className={iconClass} />;
  } else if (type === 'progress') {
    return <TrendingUp className={iconClass} />;
  } else if (type === 'data') {
    return <Database className={iconClass} />;
  } else if (type === 'agent_status') {
    return <Zap className={iconClass} />;
  } else if (type === 'decision') {
    return <Brain className={iconClass} />;
  }

  return <Info className={iconClass} />;
};

const EventCard: React.FC<{ event: AgentEvent; index: number }> = ({ event, index }) => {
  const getEventColor = () => {
    if (event.type === 'reasoning') return 'from-blue-500/10 to-blue-600/5';
    if (event.type.startsWith('tool')) {
      if (event.status === 'completed') return 'from-green-500/10 to-green-600/5';
      if (event.status === 'failed') return 'from-red-500/10 to-red-600/5';
      return 'from-purple-500/10 to-purple-600/5';
    }
    if (event.type === 'progress') return 'from-yellow-500/10 to-yellow-600/5';
    if (event.type === 'agent_status') return 'from-indigo-500/10 to-indigo-600/5';
    if (event.type === 'data') return 'from-cyan-500/10 to-cyan-600/5';
    return 'from-gray-500/10 to-gray-600/5';
  };

  const getEventTitle = () => {
    if (event.type === 'reasoning') {
      return event.step || 'Thinking';
    } else if (event.type === 'tool_execution' || event.type === 'tool_start') {
      return `Tool: ${event.tool || 'Unknown'}`;
    } else if (event.type === 'progress') {
      return `Progress: ${event.percent_complete || 0}%`;
    } else if (event.type === 'agent_status') {
      return `Agent: ${event.status || 'Active'}`;
    } else if (event.type === 'data') {
      return `Data: ${event.data_type || 'Retrieved'} (${event.count || 0})`;
    } else if (event.type === 'decision') {
      return 'Decision Point';
    }
    return event.type;
  };

  const getEventContent = () => {
    if (event.content) return event.content;
    if (event.question) return event.question;
    if (event.choice) return `Choice: ${event.choice}`;
    if (event.current_step && event.total_steps) {
      return `Step ${event.current_step} of ${event.total_steps}`;
    }
    if (event.capabilities && event.capabilities.length > 0) {
      return `Capabilities: ${event.capabilities.join(', ')}`;
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
        delay: index * 0.05, // Staggered animation
      }}
      className={`relative pl-8 pb-4 border-l-2 border-gray-700/50 last:border-transparent`}
    >
      <motion.div
        className="absolute left-0 top-0 -translate-x-1/2 w-6 h-6 rounded-full bg-gray-800 border-2 border-gray-700 flex items-center justify-center"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: index * 0.05 + 0.1 }}
      >
        <EventIcon type={event.type} status={event.status} />
      </motion.div>

      <div
        className={`rounded-lg p-3 bg-gradient-to-br ${getEventColor()} border border-gray-700/30 backdrop-blur-sm`}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-200">
            {getEventTitle()}
          </span>
          {event.progress_percent !== undefined && (
            <span className="text-xs text-gray-400">{event.progress_percent}%</span>
          )}
        </div>

        {getEventContent() && (
          <p className="text-sm text-gray-300 leading-relaxed">{getEventContent()}</p>
        )}

        {event.type === 'progress' && event.percent_complete !== undefined && (
          <div className="mt-2">
            <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                initial={{ width: 0 }}
                animate={{ width: `${event.percent_complete}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ events, maxEvents = 50 }) => {
  const displayEvents = events.slice(-maxEvents);

  if (displayEvents.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-2xl mx-auto py-4">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 flex items-center gap-2"
      >
        <Clock className="w-5 h-5 text-blue-400" />
        <h3 className="text-lg font-semibold text-gray-200">Agent Activity</h3>
        <span className="text-sm text-gray-400">({displayEvents.length} events)</span>
      </motion.div>

      <div className="space-y-0">
        <AnimatePresence mode="popLayout">
          {displayEvents.map((event, index) => (
            <EventCard
              key={`${event.timestamp || index}-${event.type}`}
              event={event}
              index={index}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AgentTimeline;
