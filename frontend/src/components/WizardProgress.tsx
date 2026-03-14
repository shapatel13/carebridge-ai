import { Check } from 'lucide-react'

const STEPS = [
  { num: 1, label: 'Patient & People' },
  { num: 2, label: 'Conversation' },
  { num: 3, label: 'Clinician Notes' },
  { num: 4, label: 'Review' },
]

interface Props {
  currentStep: number
  onStepClick: (step: number) => void
  canAdvanceTo: number
}

export default function WizardProgress({ currentStep, onStepClick, canAdvanceTo }: Props) {
  return (
    <div className="bg-white dark:bg-slate-800 border-b border-gray-100 dark:border-slate-700 transition-colors">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {STEPS.map((step, i) => {
            const isCompleted = currentStep > step.num
            const isCurrent = currentStep === step.num
            const isClickable = step.num <= canAdvanceTo

            return (
              <div key={step.num} className="flex items-center flex-1">
                <button
                  onClick={() => isClickable && onStepClick(step.num)}
                  disabled={!isClickable}
                  className={`flex items-center gap-2 group ${
                    isClickable ? 'cursor-pointer' : 'cursor-not-allowed'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                      isCompleted
                        ? 'bg-success text-white'
                        : isCurrent
                        ? 'bg-navy text-white shadow-md'
                        : isClickable
                        ? 'bg-gray-200 text-gray-600 group-hover:bg-gray-300 dark:bg-slate-600 dark:text-slate-300'
                        : 'bg-gray-100 text-gray-400 dark:bg-slate-700 dark:text-slate-500'
                    }`}
                  >
                    {isCompleted ? <Check className="w-4 h-4" /> : step.num}
                  </div>
                  <span
                    className={`text-sm font-medium hidden sm:block ${
                      isCurrent ? 'text-navy dark:text-clinical' : isCompleted ? 'text-success' : 'text-gray-400 dark:text-slate-500'
                    }`}
                  >
                    {step.label}
                  </span>
                </button>
                {i < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-3 rounded ${
                      currentStep > step.num ? 'bg-success' : 'bg-gray-200 dark:bg-slate-600'
                    }`}
                  />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
