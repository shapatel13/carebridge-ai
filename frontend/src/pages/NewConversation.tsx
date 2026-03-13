import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useConversation } from '../hooks/useConversation'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import AppHeader from '../components/AppHeader'
import WizardProgress from '../components/WizardProgress'
import StepPatient from '../components/wizard/StepPatient'
import StepConversation from '../components/wizard/StepConversation'
import StepClinician from '../components/wizard/StepClinician'
import StepReview from '../components/wizard/StepReview'

export default function NewConversation() {
  const navigate = useNavigate()
  const { createConversation, addSegment, generateOutput, generating, reset } =
    useConversation()

  // Wizard navigation
  const [currentStep, setCurrentStep] = useState(1)
  const [direction, setDirection] = useState<'left' | 'right'>('left')

  // Step 1: Patient & People
  const [patientAlias, setPatientAlias] = useState('Patient A')
  const [familyPresent, setFamilyPresent] = useState(false)
  const [language, setLanguage] = useState('english')
  const [surName, setSurName] = useState('')
  const [surRelation, setSurRelation] = useState('')
  const [organSupports, setOrganSupports] = useState<string[]>([])

  // Step 2: Conversation
  const [segments, setSegments] = useState<string[]>([])

  // Step 3: Clinician Notes
  const [tone, setTone] = useState('neutral')
  const [codeDiscussed, setCodeDiscussed] = useState(false)
  const [annotations, setAnnotations] = useState<string[]>([])
  const [familyQuestions, setFamilyQuestions] = useState<string[]>([])

  // Error
  const [error, setError] = useState('')

  useEffect(() => {
    reset()
  }, [])

  // Navigation logic
  const hasTranscript = segments.length > 0
  const canAdvanceTo = hasTranscript ? 4 : 2 // Can always go to step 2, but 3+ requires transcript

  const goToStep = (step: number) => {
    if (step < 1 || step > 4) return
    if (step > canAdvanceTo) return
    setDirection(step > currentStep ? 'left' : 'right')
    setCurrentStep(step)
    setError('')
  }

  const handleNext = () => {
    if (currentStep === 2 && !hasTranscript) {
      setError('Please add at least one conversation segment before continuing.')
      return
    }
    goToStep(currentStep + 1)
  }

  const handleBack = () => {
    goToStep(currentStep - 1)
  }

  const handleGenerate = async () => {
    if (segments.length === 0) {
      setError('No transcript segments. Go back and add conversation text.')
      return
    }
    setError('')

    try {
      const id = await createConversation({
        patient_alias: patientAlias,
        tone_setting: tone,
        organ_supports: organSupports.length > 0 ? organSupports : null,
        code_status_discussed: codeDiscussed,
        family_present: familyPresent,
        language: language,
        surrogate_name: surName || null,
        surrogate_relationship: surRelation || null,
        family_questions: familyQuestions.length > 0 ? familyQuestions : null,
        clinician_annotations: annotations.length > 0 ? annotations : null,
      } as any)

      for (const text of segments) {
        await addSegment(id, text)
      }

      await generateOutput(id)
      navigate(`/conversations/${id}/review`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to generate. Please try again.')
    }
  }

  const slideClass = direction === 'left' ? 'wizard-slide-left' : 'wizard-slide-right'

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />
      <WizardProgress
        currentStep={currentStep}
        onStepClick={goToStep}
        canAdvanceTo={canAdvanceTo}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Step Content */}
        <div key={currentStep} className={slideClass}>
          {currentStep === 1 && (
            <StepPatient
              patientAlias={patientAlias}
              setPatientAlias={setPatientAlias}
              familyPresent={familyPresent}
              setFamilyPresent={setFamilyPresent}
              language={language}
              setLanguage={setLanguage}
              surName={surName}
              setSurName={setSurName}
              surRelation={surRelation}
              setSurRelation={setSurRelation}
              organSupports={organSupports}
              setOrganSupports={setOrganSupports}
            />
          )}
          {currentStep === 2 && (
            <StepConversation
              segments={segments}
              setSegments={setSegments}
            />
          )}
          {currentStep === 3 && (
            <StepClinician
              tone={tone}
              setTone={setTone}
              codeDiscussed={codeDiscussed}
              setCodeDiscussed={setCodeDiscussed}
              annotations={annotations}
              setAnnotations={setAnnotations}
              familyQuestions={familyQuestions}
              setFamilyQuestions={setFamilyQuestions}
            />
          )}
          {currentStep === 4 && (
            <StepReview
              patientAlias={patientAlias}
              familyPresent={familyPresent}
              language={language}
              surName={surName}
              surRelation={surRelation}
              organSupports={organSupports}
              segments={segments}
              tone={tone}
              codeDiscussed={codeDiscussed}
              annotations={annotations}
              familyQuestions={familyQuestions}
              onStepClick={goToStep}
              onGenerate={handleGenerate}
              generating={generating}
            />
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 text-sm text-danger bg-red-50 rounded-lg px-4 py-3 max-w-lg mx-auto">
            {error}
          </div>
        )}

        {/* Navigation Buttons (not shown on Step 4 — it has its own Generate button) */}
        {currentStep < 4 && (
          <div className="mt-8 flex justify-between max-w-lg mx-auto">
            <button
              onClick={handleBack}
              disabled={currentStep === 1}
              className="px-6 py-3 border border-gray-200 rounded-xl text-sm font-medium text-muted hover:bg-gray-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={handleNext}
              className="px-6 py-3 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors flex items-center gap-1 shadow-sm"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
