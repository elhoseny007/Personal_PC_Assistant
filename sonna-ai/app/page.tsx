'use client'

import { ChangeEvent, FormEvent, useMemo, useRef, useState } from 'react'
import {
  Activity,
  ArrowLeft,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Globe2,
  LockKeyhole,
  Mic,
  MicOff,
  MonitorDot,
  Paperclip,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X,
} from 'lucide-react'

type Section = {
  id: string
  name: string
  description: string
  icon: typeof MonitorDot
  accent: string
  status: string
}

type Message = { id: number; role: 'user' | 'assistant'; text: string; time: string }

const sections: Section[] = [
  { id: 'pc', name: 'PC Search', description: 'Find files on your computer', icon: MonitorDot, accent: 'emerald', status: 'Local' },
  { id: 'web', name: 'Google Search', description: 'Search the web using AI', icon: Globe2, accent: 'blue', status: 'Explore' },
  { id: 'tools', name: 'AI Tools', description: 'Use intelligent services and tools', icon: Sparkles, accent: 'violet', status: 'Ready' },
  { id: 'docs', name: 'Document Analysis', description: 'Ask questions about your files', icon: FileText, accent: 'amber', status: 'RAG' },
  { id: 'monitoring', name: 'AI Monitoring', description: 'Track model health and observability', icon: Activity, accent: 'rose', status: 'Protected' },
]

const starterMessages: Record<string, Message[]> = {
  pc: [{ id: 1, role: 'assistant', text: 'PC Search is ready. Tell me what you want to find on your computer.', time: 'Now' }],
  web: [{ id: 1, role: 'assistant', text: 'Google Search is ready. What should I research for you?', time: 'Now' }],
  tools: [{ id: 1, role: 'assistant', text: 'AI Tools are ready. Choose a task and I will help you get it done.', time: 'Now' }],
  docs: [{ id: 1, role: 'assistant', text: 'Document Analysis is ready. Upload a document or ask about your indexed files.', time: 'Now' }],
}

const accentClasses: Record<string, string> = {
  emerald: 'icon-emerald', blue: 'icon-blue', violet: 'icon-violet', amber: 'icon-amber', rose: 'icon-rose',
}

export default function Page() {
  const [activeSection, setActiveSection] = useState<Section | null>(null)
  const [messages, setMessages] = useState<Record<string, Message[]>>(starterMessages)
  const [draft, setDraft] = useState('')
  const [monitoringAuthed, setMonitoringAuthed] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [attachmentStatus, setAttachmentStatus] = useState('')
  const recorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const activeMessages = useMemo(() => activeSection ? messages[activeSection.id] || [] : [], [activeSection, messages])

  function openSection(section: Section) {
    setActiveSection(section)
    setDraft('')
    setLoginError('')
  }

  function sendMessage(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || !activeSection) return
    const current = messages[activeSection.id] || []
    const userMessage: Message = { id: Date.now(), role: 'user', text, time: 'Now' }
    const reply: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      text: `I received your request in ${activeSection.name}. The connected assistant will process it here.`,
      time: 'Now',
    }
    setMessages({ ...messages, [activeSection.id]: [...current, userMessage, reply] })
    setDraft('')
  }

  function login(event: FormEvent) {
    event.preventDefault()
    if (email.trim().toLowerCase() === 'elhosenyhassan007@gamil.com' && password === 'Elhoseny@007') {
      setMonitoringAuthed(true)
      setLoginError('')
    } else {
      setLoginError('Incorrect email or password. Please try again.')
    }
  }

  async function uploadFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files
    if (!files?.length) return
    setIsUploading(true)
    setAttachmentStatus(`Uploading ${files.length} file${files.length === 1 ? '' : 's'}...`)
    const formData = new FormData()
    Array.from(files).forEach((file) => formData.append('files', file))
    try {
      const response = await fetch('/api/rag/upload', { method: 'POST', body: formData })
      if (!response.ok) throw new Error('Upload failed')
      setAttachmentStatus(`${files.length} file${files.length === 1 ? '' : 's'} attached`)
    } catch {
      setAttachmentStatus('Upload unavailable. Start main.py on port 8000 first.')
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  async function toggleRecording() {
    if (isRecording && recorderRef.current) {
      recorderRef.current.stop()
      setIsRecording(false)
      return
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setAttachmentStatus('Voice recording is not supported in this browser.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []
      recorder.ondataavailable = (event) => audioChunksRef.current.push(event.data)
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop())
        const audio = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        const formData = new FormData()
        formData.append('audio', audio, 'voice.webm')
        formData.append('language', 'ar')
        setAttachmentStatus('Transcribing voice...')
        try {
          const response = await fetch('/api/voice', { method: 'POST', body: formData })
          const result = await response.json()
          if (!response.ok || !result.ok) throw new Error(result.error || 'Voice failed')
          setDraft(`${draft}${draft ? ' ' : ''}${result.text}`)
          setAttachmentStatus('Voice added to message')
        } catch {
          setAttachmentStatus('Voice service unavailable. Start main.py on port 8000 first.')
        }
      }
      recorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
      setAttachmentStatus('Recording voice... click the mic to stop')
    } catch {
      setAttachmentStatus('Microphone permission was not granted.')
    }
  }

  return (
    <main className="workspace-shell" dir="ltr">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><Bot size={22} /></div>
          <div><strong>SONNA AI</strong><span>Workspace</span></div>
        </div>
        <div className="sidebar-label">Your workspace</div>
        <nav className="section-nav" aria-label="AI sections">
          {sections.map((section) => {
            const Icon = section.icon
            return <button key={section.id} className={`nav-item ${activeSection?.id === section.id ? 'selected' : ''}`} onClick={() => openSection(section)}>
              <span className={`nav-icon ${accentClasses[section.accent]}`}><Icon size={18} /></span>
              <span className="nav-copy"><b>{section.name}</b><small>{section.description}</small></span>
              <ChevronRight size={16} className="nav-chevron" />
            </button>
          })}
        </nav>
        <div className="sidebar-foot"><ShieldCheck size={16} /><span>Private workspace</span></div>
      </aside>

      <section className="content-area">
        <header className="topbar">
          <div><span className="eyebrow">AI WORKSPACE</span><h1>{activeSection ? activeSection.name : 'Your AI Workspace'}</h1></div>
          <div className="online-pill"><span /> All systems online</div>
        </header>

        {!activeSection ? <Home sections={sections} onOpen={openSection} /> : activeSection.id === 'monitoring' && !monitoringAuthed ? <LoginCard email={email} password={password} setEmail={setEmail} setPassword={setPassword} error={loginError} onSubmit={login} /> : <ChatPanel section={activeSection} messages={activeMessages} draft={draft} setDraft={setDraft} onSubmit={sendMessage} onBack={() => setActiveSection(null)} monitoringAuthed={activeSection.id === 'monitoring'} onUpload={uploadFiles} onToggleRecording={toggleRecording} isRecording={isRecording} isUploading={isUploading} attachmentStatus={attachmentStatus} />}
      </section>
    </main>
  )
}

function Home({ sections, onOpen }: { sections: Section[]; onOpen: (section: Section) => void }) {
  return <div className="home-view"><div className="hero-copy"><div className="hero-orb"><Sparkles size={24} /></div><p className="eyebrow">WELCOME BACK</p><h2>One assistant.<br /><em>Multiple capabilities.</em></h2><p className="hero-description">Choose a section to start a focused conversation with your AI workspace.</p></div><div className="section-grid">{sections.map((section) => { const Icon = section.icon; return <button key={section.id} className={`section-card card-${section.accent}`} onClick={() => onOpen(section)}><div className="section-card-top"><span className={`card-icon ${accentClasses[section.accent]}`}><Icon size={21} /></span><span className="card-status">{section.status}</span></div><div><h3>{section.name}</h3><p>{section.description}</p></div><span className="open-link">Open section <ArrowLeft size={14} className="flip-icon" /></span></button> })}</div></div>
}

function LoginCard({ email, password, setEmail, setPassword, error, onSubmit }: { email: string; password: string; setEmail: (v: string) => void; setPassword: (v: string) => void; error: string; onSubmit: (e: FormEvent) => void }) {
  return <div className="login-wrap"><div className="login-card"><div className="login-icon"><LockKeyhole size={22} /></div><p className="eyebrow">PROTECTED AREA</p><h2>AI Monitoring</h2><p className="login-copy">Sign in to access monitoring backend metrics, traces, and model health.</p><form onSubmit={onSubmit} className="login-form"><label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="username" required /></label><label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" required /></label>{error && <p className="error-text" role="alert">{error}</p>}<button className="primary-button" type="submit">Continue to monitoring <ChevronRight size={16} /></button></form><div className="secure-note"><ShieldCheck size={15} /> Secure access for monitoring backend</div></div></div>
}

function ChatPanel({ section, messages, draft, setDraft, onSubmit, onBack, monitoringAuthed, onUpload, onToggleRecording, isRecording, isUploading, attachmentStatus }: { section: Section; messages: Message[]; draft: string; setDraft: (v: string) => void; onSubmit: (e: FormEvent) => void; onBack: () => void; monitoringAuthed: boolean; onUpload: (event: ChangeEvent<HTMLInputElement>) => void; onToggleRecording: () => void; isRecording: boolean; isUploading: boolean; attachmentStatus: string }) {
  const Icon = section.icon
  return <div className="chat-view"><button className="back-button" onClick={onBack}><ArrowLeft size={16} /> All sections</button><div className="chat-heading"><div className={`large-icon ${accentClasses[section.accent]}`}><Icon size={25} /></div><div><p className="eyebrow">FOCUSED ASSISTANT</p><h2>{section.name}</h2><p>{monitoringAuthed ? 'Monitoring backend connected · traces.jsonl ready' : section.description}</p></div><span className="connected-badge"><CheckCircle2 size={14} /> Connected</span></div>{monitoringAuthed && <div className="monitor-strip"><div><TrendingUp size={17} /><span><b>99.8%</b> uptime</span></div><div><Activity size={17} /><span><b>24</b> active traces</span></div><div><Clock3 size={17} /><span><b>182ms</b> avg latency</span></div></div>}<div className="messages-panel">{messages.map((message) => <div key={message.id} className={`message-row ${message.role}`}><div className={`avatar ${message.role}`}>{message.role === 'assistant' ? <Bot size={15} /> : 'Y'}</div><div><div className="message-bubble">{message.text}</div><small>{message.time}</small></div></div>)}</div><form className="chat-composer" onSubmit={onSubmit}><div className="composer-tools"><label className="tool-button" title="Attach files"><Paperclip size={17} /><span className="sr-only">Attach files</span><input type="file" multiple onChange={onUpload} /></label><button type="button" className={`tool-button ${isRecording ? 'recording' : ''}`} onClick={onToggleRecording} aria-label={isRecording ? 'Stop recording' : 'Record voice'} title={isRecording ? 'Stop recording' : 'Record voice'}>{isRecording ? <MicOff size={17} /> : <Mic size={17} />}</button></div><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={`Ask ${section.name}...`} aria-label={`Message ${section.name}`} /><button type="submit" aria-label="Send message"><Send size={17} /></button></form>{attachmentStatus && <p className="attachment-status" role="status">{isUploading ? '...' : attachmentStatus}</p>}</div>
}
<div
  className="message-bubble"
  dangerouslySetInnerHTML={renderMarkdown(message.text)}
/>
