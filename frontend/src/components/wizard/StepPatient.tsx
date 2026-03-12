import { useState } from 'react'
import { Users, Plus, X, Heart, HeartOff } from 'lucide-react'

interface Props {
  patientAlias: string
  setPatientAlias: (v: string) => void
  familyPresent: boolean
  setFamilyPresent: (v: boolean) => void
  surName: string
  setSurName: (v: string) => void
  surRelation: string
  setSurRelation: (v: string) => void
  organSupports: string[]
  setOrganSupports: (v: string[]) => void
}

export default function StepPatient({
  patientAlias, setPatientAlias,
  familyPresent, setFamilyPresent,
  surName, setSurName,
  surRelation, setSurRelation,
  organSupports, setOrganSupports,
}: Props) {
  const [organInput, setOrganInput] = useState('')

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          Patient Identifier
        </label>
        <input
          type="text"
          value={patientAlias}
          onChange={(e) => setPatientAlias(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none transition-all"
          placeholder="e.g. Patient A (de-identified)"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Was the family present for this conversation?
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setFamilyPresent(true)}
            className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
              familyPresent
                ? 'border-clinical bg-clinical/5 shadow-sm'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <Heart className={`w-5 h-5 ${familyPresent ? 'text-clinical' : 'text-gray-400'}`} />
            <div className="text-left">
              <p className={`text-sm font-semibold ${familyPresent ? 'text-clinical' : 'text-gray-600'}`}>
                Yes, present
              </p>
              <p className="text-xs text-gray-400 mt-0.5">Brief summary</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setFamilyPresent(false)}
            className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
              !familyPresent
                ? 'border-navy bg-navy/5 shadow-sm'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <HeartOff className={`w-5 h-5 ${!familyPresent ? 'text-navy' : 'text-gray-400'}`} />
            <div className="text-left">
              <p className={`text-sm font-semibold ${!familyPresent ? 'text-navy' : 'text-gray-600'}`}>
                Not present
              </p>
              <p className="text-xs text-gray-400 mt-0.5">Detailed summary</p>
            </div>
          </button>
        </div>
      </div>

      {familyPresent && (
        <div className="animate-in">
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <Users className="w-4 h-4 text-clinical" />
            Surrogate Decision Maker
          </h3>
          <div className="space-y-2">
            <input
              type="text"
              value={surName}
              onChange={(e) => setSurName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
              placeholder="Name"
            />
            <input
              type="text"
              value={surRelation}
              onChange={(e) => setSurRelation(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
              placeholder="Relationship (e.g., Daughter, healthcare proxy)"
            />
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          Organ Supports
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={organInput}
            onChange={(e) => setOrganInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && organInput.trim()) {
                e.preventDefault()
                setOrganSupports([...organSupports, organInput.trim()])
                setOrganInput('')
              }
            }}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
            placeholder="e.g. Mechanical ventilation"
          />
          <button
            type="button"
            onClick={() => {
              if (organInput.trim()) {
                setOrganSupports([...organSupports, organInput.trim()])
                setOrganInput('')
              }
            }}
            className="px-4 py-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {organSupports.map((os, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg text-xs font-medium">
              {os}
              <button onClick={() => setOrganSupports(organSupports.filter((_, j) => j !== i))}>
                <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
