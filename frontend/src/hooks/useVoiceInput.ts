import { useState, useCallback, useRef, useEffect } from 'react'

export interface UseVoiceInputOptions {
  language?: string
  continuous?: boolean
  interimResults?: boolean
  onResult?: (transcript: string, isFinal: boolean) => void
  onError?: (error: string) => void
  onStart?: () => void
  onEnd?: () => void
}

export interface VoiceInputState {
  isListening: boolean
  isSupported: boolean
  transcript: string
  interimTranscript: string
  error: string | null
}

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: 'no-speech' | 'audio-capture' | 'not-allowed' | 'network' | 'aborted' | 'language-not-supported' | 'service-not-allowed'
}

interface SpeechRecognitionClass {
  new (): SpeechRecognitionInstance
}

interface SpeechRecognitionInstance extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  onstart: ((this: SpeechRecognitionInstance, ev: Event) => void) | null
  onresult: ((this: SpeechRecognitionInstance, ev: SpeechRecognitionEvent) => void) | null
  onerror: ((this: SpeechRecognitionInstance, ev: SpeechRecognitionErrorEvent) => void) | null
  onend: ((this: SpeechRecognitionInstance, ev: Event) => void) | null
  start(): void
  stop(): void
  abort(): void
}

// Extend window for SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionClass
    webkitSpeechRecognition: SpeechRecognitionClass
  }
}

/**
 * Hook for voice input using Web Speech API.
 * 
 * Features:
 * - Continuous or one-shot recognition
 * - Interim results for real-time feedback
 * - Error handling
 * - Browser compatibility check
 */
export function useVoiceInput({
  language = 'en-US',
  continuous = false,
  interimResults = true,
  onResult,
  onError,
  onStart,
  onEnd,
}: UseVoiceInputOptions = {}): VoiceInputState & {
  startListening: () => void
  stopListening: () => void
  toggleListening: () => void
  clearTranscript: () => void
} {
  const [state, setState] = useState<VoiceInputState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    error: null,
  })

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)

  // Check browser support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    setState(prev => ({ ...prev, isSupported: !!SpeechRecognition }))
  }, [])

  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      setState(prev => ({
        ...prev,
        error: 'Speech recognition is not supported in this browser',
      }))
      onError?.('Speech recognition is not supported in this browser')
      return
    }

    // Stop any existing recognition
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }

    const recognition = new SpeechRecognition()
    recognitionRef.current = recognition

    recognition.lang = language
    recognition.continuous = continuous
    recognition.interimResults = interimResults

    recognition.onstart = () => {
      setState(prev => ({
        ...prev,
        isListening: true,
        error: null,
        interimTranscript: '',
      }))
      onStart?.()
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }

      if (finalTranscript) {
        setState(prev => ({
          ...prev,
          transcript: prev.transcript + finalTranscript,
          interimTranscript: '',
        }))
        onResult?.(finalTranscript, true)
      }

      if (interim) {
        setState(prev => ({ ...prev, interimTranscript: interim }))
        onResult?.(interim, false)
      }
    }

    recognition.onerror = (event) => {
      let errorMessage = 'Speech recognition error'
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech was detected'
          break
        case 'audio-capture':
          errorMessage = 'No microphone was found'
          break
        case 'not-allowed':
          errorMessage = 'Microphone permission denied'
          break
        case 'network':
          errorMessage = 'Network error occurred'
          break
        case 'aborted':
          errorMessage = 'Recognition was aborted'
          break
        case 'language-not-supported':
          errorMessage = 'Language not supported'
          break
        case 'service-not-allowed':
          errorMessage = 'Service not allowed'
          break
      }

      setState(prev => ({
        ...prev,
        isListening: false,
        error: errorMessage,
      }))
      onError?.(errorMessage)
    }

    recognition.onend = () => {
      setState(prev => ({
        ...prev,
        isListening: false,
        interimTranscript: '',
      }))
      onEnd?.()
    }

    try {
      recognition.start()
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to start recognition',
      }))
      onError?.('Failed to start recognition')
    }
  }, [language, continuous, interimResults, onResult, onError, onStart, onEnd])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setState(prev => ({
      ...prev,
      isListening: false,
      interimTranscript: '',
    }))
  }, [])

  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [state.isListening, startListening, stopListening])

  const clearTranscript = useCallback(() => {
    setState(prev => ({
      ...prev,
      transcript: '',
      interimTranscript: '',
    }))
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [])

  return {
    ...state,
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
  }
}

/**
 * Hook for text-to-speech synthesis.
 */
export function useTextToSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const speak = useCallback((text: string, options?: {
    lang?: string
    rate?: number
    pitch?: number
    volume?: number
  }) => {
    if (!window.speechSynthesis) {
      console.warn('Speech synthesis not supported')
      return
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utteranceRef.current = utterance

    utterance.lang = options?.lang || 'en-US'
    utterance.rate = options?.rate || 1
    utterance.pitch = options?.pitch || 1
    utterance.volume = options?.volume || 1

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }, [])

  const stop = useCallback(() => {
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }, [])

  return {
    speak,
    stop,
    isSpeaking,
    isSupported: typeof window !== 'undefined' && 'speechSynthesis' in window,
  }
}

export default useVoiceInput

