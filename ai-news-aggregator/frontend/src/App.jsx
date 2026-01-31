import { useState, useEffect } from 'react'
import { Mail, User, Youtube, Sparkles, Check, ChevronRight, ChevronLeft, Clock, Loader2 } from 'lucide-react'

const API_BASE = '/api'

function App() {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [interests, setInterests] = useState([])
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    interest_ids: [],
    youtube_urls: [''],
    hours_window: 24,
  })

  useEffect(() => {
    fetchInterests()
  }, [])

  const fetchInterests = async () => {
    try {
      const res = await fetch(`${API_BASE}/interests`)
      if (res.ok) {
        const data = await res.json()
        setInterests(data)
      }
    } catch (err) {
      console.error('Failed to fetch interests:', err)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setError('')
  }

  const handleInterestToggle = (id) => {
    setFormData(prev => {
      const current = prev.interest_ids
      if (current.includes(id)) {
        return { ...prev, interest_ids: current.filter(i => i !== id) }
      }
      if (current.length >= 7) {
        setError('Maximum 7 interests allowed')
        return prev
      }
      return { ...prev, interest_ids: [...current, id] }
    })
    setError('')
  }

  const handleYoutubeChange = (index, value) => {
    setFormData(prev => {
      const urls = [...prev.youtube_urls]
      urls[index] = value
      return { ...prev, youtube_urls: urls }
    })
    setError('')
  }

  const addYoutubeUrl = () => {
    setFormData(prev => ({
      ...prev,
      youtube_urls: [...prev.youtube_urls, '']
    }))
  }

  const removeYoutubeUrl = (index) => {
    if (formData.youtube_urls.length > 1) {
      setFormData(prev => ({
        ...prev,
        youtube_urls: prev.youtube_urls.filter((_, i) => i !== index)
      }))
    }
  }

  const validateStep = () => {
    switch (step) {
      case 1:
        if (!formData.name.trim()) {
          setError('Name is required')
          return false
        }
        if (!formData.email.trim() || !formData.email.includes('@')) {
          setError('Valid email is required')
          return false
        }
        return true
      case 2:
        if (formData.interest_ids.length === 0) {
          setError('Select at least 1 interest')
          return false
        }
        if (formData.interest_ids.length > 7) {
          setError('Maximum 7 interests allowed')
          return false
        }
        return true
      case 3:
        const validUrls = formData.youtube_urls.filter(url => url.trim())
        if (validUrls.length === 0) {
          setError('At least 1 YouTube URL is required')
          return false
        }
        for (const url of validUrls) {
          if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
            setError('Please enter valid YouTube URLs')
            return false
          }
        }
        return true
      default:
        return true
    }
  }

  const nextStep = () => {
    if (validateStep()) {
      setStep(prev => Math.min(prev + 1, 4))
      setError('')
    }
  }

  const prevStep = () => {
    setStep(prev => Math.max(prev - 1, 1))
    setError('')
  }

  const handleSubmit = async () => {
    if (!validateStep()) return

    setLoading(true)
    setError('')

    try {
      const payload = {
        ...formData,
        youtube_urls: formData.youtube_urls.filter(url => url.trim()),
      }

      const res = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json()

      if (res.ok && data.success) {
        setSuccess(true)
        setStep(5)
      } else {
        setError(data.detail || data.message || 'Registration failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {[1, 2, 3, 4].map((s) => (
        <div key={s} className="flex items-center">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
              step >= s
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            {step > s ? <Check size={20} /> : s}
          </div>
          {s < 4 && (
            <div
              className={`w-12 h-1 mx-1 transition-all ${
                step > s ? 'bg-gradient-to-r from-indigo-500 to-purple-600' : 'bg-gray-200'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  )

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100 mb-4">
          <User className="w-8 h-8 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Your Details</h2>
        <p className="text-gray-500 mt-2">Let's start with your basic information</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleInputChange}
          placeholder="John Doe"
          className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            placeholder="john@example.com"
            className="w-full pl-11 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
          />
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-4">
          <Sparkles className="w-8 h-8 text-purple-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Your Interests</h2>
        <p className="text-gray-500 mt-2">
          Select up to 7 topics ({formData.interest_ids.length}/7 selected)
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-2">
        {interests.map((interest) => (
          <button
            key={interest.id}
            onClick={() => handleInterestToggle(interest.id)}
            className={`p-3 rounded-lg border-2 text-left transition-all ${
              formData.interest_ids.includes(interest.id)
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{interest.display_name}</span>
              {formData.interest_ids.includes(interest.id) && (
                <Check className="w-4 h-4 text-indigo-600" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
          <Youtube className="w-8 h-8 text-red-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">YouTube Channels</h2>
        <p className="text-gray-500 mt-2">Add YouTube video or channel URLs to follow</p>
      </div>

      <div className="space-y-3">
        {formData.youtube_urls.map((url, index) => (
          <div key={index} className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => handleYoutubeChange(index, e.target.value)}
              placeholder="https://youtube.com/watch?v=... or @channel"
              className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
            />
            {formData.youtube_urls.length > 1 && (
              <button
                onClick={() => removeYoutubeUrl(index)}
                className="px-3 py-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={addYoutubeUrl}
        className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-indigo-400 hover:text-indigo-500 transition-colors"
      >
        + Add another URL
      </button>
    </div>
  )

  const renderStep4 = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
          <Clock className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Preferences</h2>
        <p className="text-gray-500 mt-2">Customize your newsletter delivery</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-4">
          Time Window: <span className="text-indigo-600 font-bold">{formData.hours_window} hours</span>
        </label>
        <input
          type="range"
          min="18"
          max="36"
          value={formData.hours_window}
          onChange={(e) => setFormData(prev => ({ ...prev, hours_window: parseInt(e.target.value) }))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>18h</span>
          <span>24h</span>
          <span>30h</span>
          <span>36h</span>
        </div>
        <p className="text-sm text-gray-500 mt-4">
          You'll receive the top 5 articles from the last {formData.hours_window} hours.
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 mt-6">
        <h3 className="font-semibold text-gray-900 mb-3">Summary</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li><strong>Name:</strong> {formData.name}</li>
          <li><strong>Email:</strong> {formData.email}</li>
          <li><strong>Interests:</strong> {formData.interest_ids.length} selected</li>
          <li><strong>YouTube:</strong> {formData.youtube_urls.filter(u => u.trim()).length} channel(s)</li>
          <li><strong>Window:</strong> {formData.hours_window} hours</li>
          <li><strong>Trial:</strong> 3 days free</li>
        </ul>
      </div>
    </div>
  )

  const renderSuccess = () => (
    <div className="text-center py-8">
      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6">
        <Check className="w-10 h-10 text-green-600" />
      </div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">You're Almost There!</h2>
      <p className="text-gray-600 text-lg mb-6">
        We've sent a confirmation email to <strong>{formData.email}</strong>
      </p>
      <div className="bg-indigo-50 rounded-lg p-6 text-left">
        <h3 className="font-semibold text-indigo-900 mb-2">Next Steps:</h3>
        <ol className="list-decimal list-inside space-y-2 text-indigo-800">
          <li>Check your inbox (and spam folder)</li>
          <li>Click the confirmation link</li>
          <li>Start receiving personalized AI news!</li>
        </ol>
      </div>
      <p className="text-sm text-gray-500 mt-6">
        Your 3-day free trial begins after confirmation.
      </p>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🤖 AI News Digest</h1>
          <p className="text-white/80">Personalized AI news delivered to your inbox</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {!success && renderStepIndicator()}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
          {step === 5 && renderSuccess()}

          {!success && (
            <div className="flex gap-3 mt-8">
              {step > 1 && (
                <button
                  onClick={prevStep}
                  className="flex-1 py-3 px-4 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                >
                  <ChevronLeft size={20} /> Back
                </button>
              )}
              {step < 4 ? (
                <button
                  onClick={nextStep}
                  className="flex-1 py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-600 hover:to-purple-700 transition-all flex items-center justify-center gap-2"
                >
                  Continue <ChevronRight size={20} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-medium hover:from-green-600 hover:to-emerald-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={20} /> Submitting...
                    </>
                  ) : (
                    <>
                      Subscribe <Check size={20} />
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>

        <p className="text-center text-white/60 text-sm mt-6">
          By subscribing, you agree to receive emails. Unsubscribe anytime.
        </p>
      </div>
    </div>
  )
}

export default App
