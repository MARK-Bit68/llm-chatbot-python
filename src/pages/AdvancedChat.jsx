import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Bot, 
  User, 
  Loader, 
  RotateCcw, 
  Brain,
  Zap,
  Target,
  Network,
  BarChart3,
  Sparkles
} from 'lucide-react'
import { useMutation, useQuery } from 'react-query'
import toast from 'react-hot-toast'
import { 
  sendAdvancedChatMessage, 
  resetChatSession, 
  isAdvancedAPIAvailable,
  ANALYTICS_TYPES 
} from '../services/advanced-api'

const advancedQueries = [
  "Analyze product clustering patterns using machine learning",
  "Show me inventory risk analysis with recommendations", 
  "Generate profitability insights for all categories",
  "Detect regional performance patterns",
  "What are the key supply chain optimization opportunities?",
  "Run advanced graph analytics on my portfolio",
  "Identify products with manufacturing constraints using AI",
  "Show me cross-functional planning recommendations"
]

const TypingIndicator = () => (
  <div className="flex items-center space-x-1">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"></div>
      <div className="w-2 h-2 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
      <div className="w-2 h-2 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
    </div>
    <span className="text-sm text-dark-muted ml-2">AI is thinking...</span>
  </div>
)

const MessageBadge = ({ type, isAdvanced }) => {
  if (type === 'user') return null
  
  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-2 ${
      isAdvanced 
        ? 'bg-brand-500/20 text-brand-500' 
        : 'bg-yellow-500/20 text-yellow-500'
    }`}>
      {isAdvanced ? (
        <>
          <Brain className="w-3 h-3 mr-1" />
          Advanced AI
        </>
      ) : (
        <>
          <Zap className="w-3 h-3 mr-1" />
          Fallback Mode
        </>
      )}
    </div>
  )
}

const Message = ({ message, isUser, isLoading, isAdvanced = false }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
  >
    <div className={`p-3 rounded-xl ${
      isUser ? 'bg-brand-500' : isAdvanced ? 'bg-brand-500/10 border border-brand-500/20' : 'bg-surface-2'
    }`}>
      {isUser ? (
        <User className="w-5 h-5 text-white" />
      ) : (
        <Bot className={`w-5 h-5 ${isAdvanced ? 'text-brand-500' : 'text-dark-muted'}`} />
      )}
    </div>
    
    <div className={`max-w-4xl ${isUser ? 'text-right' : ''}`}>
      {!isUser && <MessageBadge type="assistant" isAdvanced={isAdvanced} />}
      
      <div className={`p-4 rounded-xl ${
        isUser 
          ? 'bg-brand-500 text-white ml-12' 
          : isAdvanced
            ? 'bg-surface border border-brand-500/20 mr-12'
            : 'bg-surface border border-white border-opacity-10 mr-12'
      }`}>
        {isLoading ? (
          <TypingIndicator />
        ) : (
          <div className="prose prose-sm max-w-none">
            {typeof message === 'string' ? (
              <div 
                className={`${!isUser ? 'text-dark-text' : 'text-white'}`}
                dangerouslySetInnerHTML={{ 
                  __html: message
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                }} 
              />
            ) : (
              <pre className="whitespace-pre-wrap font-sans text-sm">
                {JSON.stringify(message, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
      
      <div className={`text-xs text-dark-muted mt-1 flex items-center ${isUser ? 'justify-end' : ''}`}>
        <span>{new Date().toLocaleTimeString()}</span>
        {!isUser && isAdvanced && (
          <span className="ml-2 flex items-center">
            <Sparkles className="w-3 h-3 mr-1" />
            Enhanced AI
          </span>
        )}
      </div>
    </div>
  </motion.div>
)

const QuickActions = ({ onActionClick, disabled }) => {
  const actions = [
    { label: "Graph Overview", icon: Network, query: "Show me graph database overview with advanced metrics" },
    { label: "AI Insights", icon: Brain, query: "Generate supply chain insights using machine learning" },
    { label: "Risk Analysis", icon: Target, query: "Analyze inventory risks and provide recommendations" },
    { label: "Performance", icon: BarChart3, query: "Show profitability patterns across all categories" }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {actions.map((action, index) => {
        const Icon = action.icon
        return (
          <button
            key={index}
            onClick={() => onActionClick(action.query)}
            disabled={disabled}
            className="p-3 bg-surface-2 hover:bg-surface-3 rounded-lg transition-all duration-200 
                     disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <Icon className="w-5 h-5 text-brand-500 mx-auto mb-2 group-hover:scale-110 transition-transform" />
            <span className="text-xs text-dark-text">{action.label}</span>
          </button>
        )
      })}
    </div>
  )
}

const AdvancedChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: "Hello! I'm your advanced FMCG supply chain AI assistant powered by graph analytics and machine learning. I can provide:\n\n• **Advanced Analytics**: ML-powered insights and pattern detection\n• **Graph Analysis**: Network analysis of your supply chain\n• **Predictive Insights**: Risk assessment and optimization\n• **Executive Dashboards**: Comprehensive business intelligence\n\nWhat would you like to explore with advanced AI?",
      isUser: false,
      timestamp: new Date(),
      isAdvanced: true
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const [apiAvailable, setApiAvailable] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Check API availability
  const { data: apiStatus } = useQuery(
    'apiAvailability',
    isAdvancedAPIAvailable,
    {
      refetchInterval: 30000,
      onSuccess: (available) => {
        setApiAvailable(available)
        if (!available && messages.length === 1) {
          // Add fallback message
          setMessages(prev => [...prev, {
            id: Date.now(),
            content: "⚠️ **Advanced AI Backend Not Connected**\n\nI'm currently running in fallback mode. To access the full advanced AI capabilities including:\n\n• Machine learning insights\n• Graph analytics\n• Real-time data analysis\n• Advanced recommendations\n\nPlease ensure the advanced backend service is running.\n\nI can still help with general questions using basic functionality!",
            isUser: false,
            timestamp: new Date(),
            isAdvanced: false
          }])
        }
      }
    }
  )

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const chatMutation = useMutation(sendAdvancedChatMessage, {
    onSuccess: (response) => {
      // Remove loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading))
      
      // Add AI response
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: response.response || response,
        isUser: false,
        timestamp: new Date(),
        isAdvanced: response.source === 'advanced_ai'
      }])
      
      // Show success toast for advanced responses
      if (response.source === 'advanced_ai') {
        toast.success('Response generated by Advanced AI', { duration: 2000 })
      }
    },
    onError: (error) => {
      // Remove loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading))
      
      toast.error('Failed to send message')
      console.error('Chat error:', error)
      
      // Add error message
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: "I apologize, but I encountered an error processing your request. This might be due to:\n\n• Backend service connectivity issues\n• Heavy computational load\n• Network timeout\n\nPlease try again or rephrase your question. For complex analytics, please ensure the advanced backend is running.",
        isUser: false,
        timestamp: new Date(),
        isAdvanced: false
      }])
    }
  })

  const handleSendMessage = async (messageText = inputValue) => {
    if (!messageText.trim()) return

    const userMessage = {
      id: Date.now(),
      content: messageText,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    // Add loading message
    const loadingMessage = {
      id: Date.now() + 1,
      content: '',
      isUser: false,
      isLoading: true,
      timestamp: new Date(),
      isAdvanced: apiAvailable
    }
    setMessages(prev => [...prev, loadingMessage])

    // Send to appropriate backend
    if (apiAvailable) {
      chatMutation.mutate({ message: messageText, sessionId })
    } else {
      // Fallback response
      setTimeout(() => {
        setMessages(prev => prev.filter(msg => !msg.isLoading))
        setMessages(prev => [...prev, {
          id: Date.now(),
          content: `I understand you're asking about "${messageText}". \n\n🔌 **Advanced AI Not Available**\n\nTo get sophisticated analysis including:\n• Machine learning insights\n• Graph pattern detection\n• Real-time data analytics\n• Executive dashboards\n\nPlease connect to the advanced backend service.\n\n💡 **Quick Setup**: Ensure your FastAPI server is running on the configured endpoint.`,
          isUser: false,
          timestamp: new Date(),
          isAdvanced: false
        }])
      }, 1500)
    }
  }

  const handleReset = async () => {
    try {
      if (apiAvailable) {
        await resetChatSession(sessionId)
        toast.success('Advanced AI session reset successfully')
      }
      
      setMessages([{
        id: 1,
        content: "Hello! I'm your advanced FMCG supply chain AI assistant. How can I help you today?",
        isUser: false,
        timestamp: new Date(),
        isAdvanced: apiAvailable
      }])
    } catch (error) {
      toast.error('Failed to reset session')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center">
            <Brain className="w-8 h-8 mr-3 text-brand-500" />
            Advanced AI Assistant
          </h1>
          <p className="text-dark-muted mt-1">
            Powered by graph analytics and machine learning
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
            apiAvailable ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              apiAvailable ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}></div>
            <span className="text-sm">
              {apiAvailable ? 'Advanced AI' : 'Fallback Mode'}
            </span>
          </div>
          
          <button onClick={handleReset} className="btn-secondary">
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset Chat
          </button>
        </div>
      </motion.div>

      <div className="flex-1 flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-6 p-6 bg-surface/30 rounded-t-xl">
            <AnimatePresence>
              {messages.map((message) => (
                <Message
                  key={message.id}
                  message={message.content}
                  isUser={message.isUser}
                  isLoading={message.isLoading}
                  isAdvanced={message.isAdvanced}
                />
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="p-4 bg-surface/50">
            <QuickActions 
              onActionClick={handleSendMessage}
              disabled={chatMutation.isLoading}
            />
          </div>

          {/* Input Area */}
          <div className="p-6 bg-surface rounded-b-xl border-t border-white border-opacity-10">
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about advanced analytics, AI insights, or graph analysis..."
                  className="input-field w-full resize-none"
                  rows={3}
                />
              </div>
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || chatMutation.isLoading}
                className="btn-primary px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {chatMutation.isLoading ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Advanced Queries Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-80 ml-6"
        >
          <div className="card">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-brand-500" />
              Advanced Analytics Queries
            </h3>
            
            <div className="space-y-2">
              {advancedQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handleSendMessage(query)}
                  disabled={chatMutation.isLoading}
                  className="w-full text-left p-3 text-sm bg-surface-2 hover:bg-surface-3 rounded-lg 
                           transition-colors text-dark-text disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  "{query}"
                </button>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-brand-500/10 border border-brand-500/20 rounded-lg">
              <h4 className="font-medium text-brand-500 mb-2 flex items-center">
                <Brain className="w-4 h-4 mr-1" />
                AI Capabilities
              </h4>
              <ul className="text-xs text-dark-muted space-y-1">
                <li>• Machine learning pattern detection</li>
                <li>• Graph theory analysis</li>
                <li>• Predictive risk modeling</li>
                <li>• Natural language processing</li>
                <li>• Executive dashboard generation</li>
                <li>• Real-time data insights</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default AdvancedChat