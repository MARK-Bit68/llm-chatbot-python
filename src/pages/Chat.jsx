import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader, RotateCcw } from 'lucide-react'
import { useMutation } from 'react-query'
import toast from 'react-hot-toast'
import { sendChatMessage } from '../services/api'

const exampleQueries = [
  "List the distinct product categories",
  "What is the category of SKU001?",
  "Which SKU has the highest gross profit per unit?",
  "Show me excess inventory for promotions",
  "Analyze regional demand variations",
  "Which SKUs have manufacturing constraints?",
]

const Message = ({ message, isUser, isLoading }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
  >
    <div className={`p-2 rounded-lg ${
      isUser ? 'bg-brand-500' : 'bg-surface-2'
    }`}>
      {isUser ? (
        <User className="w-5 h-5 text-white" />
      ) : (
        <Bot className="w-5 h-5 text-brand-500" />
      )}
    </div>
    
    <div className={`max-w-3xl ${isUser ? 'text-right' : ''}`}>
      <div className={`p-4 rounded-xl ${
        isUser 
          ? 'bg-brand-500 text-white ml-12' 
          : 'bg-surface border border-white border-opacity-10 mr-12'
      }`}>
        {isLoading ? (
          <div className="flex items-center space-x-2">
            <Loader className="w-4 h-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        ) : (
          <div className="prose prose-sm max-w-none">
            {typeof message === 'string' ? (
              <div dangerouslySetInnerHTML={{ __html: message.replace(/\n/g, '<br>') }} />
            ) : (
              <pre className="whitespace-pre-wrap font-sans">{JSON.stringify(message, null, 2)}</pre>
            )}
          </div>
        )}
      </div>
      <div className={`text-xs text-dark-muted mt-1 ${isUser ? 'text-right' : ''}`}>
        {new Date().toLocaleTimeString()}
      </div>
    </div>
  </motion.div>
)

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: "Hello! I'm your FMCG supply chain assistant. I can help you analyze SKU data, supply chain metrics, and answer questions about your inventory and operations. What would you like to explore?",
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const chatMutation = useMutation(sendChatMessage, {
    onSuccess: (response) => {
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: response.response || response,
        isUser: false,
        timestamp: new Date()
      }])
    },
    onError: (error) => {
      toast.error('Failed to send message')
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: "I'm sorry, I encountered an error processing your request. Please try again.",
        isUser: false,
        timestamp: new Date()
      }])
    }
  })

  const handleSendMessage = (messageText = inputValue) => {
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
      timestamp: new Date()
    }
    setMessages(prev => [...prev, loadingMessage])

    chatMutation.mutate({ message: messageText })
  }

  const handleReset = () => {
    setMessages([{
      id: 1,
      content: "Hello! I'm your FMCG supply chain assistant. I can help you analyze SKU data, supply chain metrics, and answer questions about your inventory and operations. What would you like to explore?",
      isUser: false,
      timestamp: new Date()
    }])
    toast.success('Chat reset successfully')
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
          <h1 className="text-3xl font-bold text-white">Chat Assistant</h1>
          <p className="text-dark-muted mt-1">Ask questions about your supply chain data</p>
        </div>
        <button
          onClick={handleReset}
          className="btn-secondary"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset Chat
        </button>
      </motion.div>

      <div className="flex-1 flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-6 p-6 bg-surface/50 rounded-t-xl">
            <AnimatePresence>
              {messages.map((message) => (
                <Message
                  key={message.id}
                  message={message.content}
                  isUser={message.isUser}
                  isLoading={message.isLoading}
                />
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
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
                  placeholder="Ask about your FMCG supply chain data..."
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

        {/* Example Queries Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-80 ml-6"
        >
          <div className="card">
            <h3 className="text-lg font-semibold text-white mb-4">Example Queries</h3>
            <div className="space-y-2">
              {exampleQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handleSendMessage(query)}
                  className="w-full text-left p-3 text-sm bg-surface-2 hover:bg-surface-3 rounded-lg transition-colors text-dark-text"
                >
                  "{query}"
                </button>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-brand-500/10 border border-brand-500/20 rounded-lg">
              <h4 className="font-medium text-brand-500 mb-2">💡 Pro Tips</h4>
              <ul className="text-xs text-dark-muted space-y-1">
                <li>• Be specific with SKU IDs (e.g., SKU001)</li>
                <li>• Ask for comparisons and analysis</li>
                <li>• Request dashboard visualizations</li>
                <li>• Explore supply chain metrics</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Chat