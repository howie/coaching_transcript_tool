'use client'

import { useState, useEffect, useRef } from 'react'
import { 
  UserCircleIcon, 
  CameraIcon,
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  AcademicCapIcon,
  BriefcaseIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline'
import { useI18n } from '@/contexts/i18n-context'
import { useAuth } from '@/contexts/auth-context'
import { apiClient } from '@/lib/api'

export default function ProfilePage() {
  const { t } = useI18n()
  const { user } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [coachProfile, setCoachProfile] = useState<any>(null)
  const [coachingPlans, setCoachingPlans] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [showPlanModal, setShowPlanModal] = useState(false)
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    // 基本資料
    display_name: '',
    profile_photo_url: '',
    public_email: '',
    phone_country_code: '+886',
    phone_number: '',
    country: '',
    city: '',
    timezone: '',
    
    // 語言設定
    coaching_languages: [] as string[],
    
    // 溝通工具
    communication_tools: {
      line: false,
      zoom: false,
      google_meet: false,
      ms_teams: false
    },
    line_id: '',
    
    // 專業資訊
    coach_experience: '',
    training_institution: '',
    certifications: [] as string[],
    linkedin_url: '',
    personal_website: '',
    bio: '',
    specialties: [] as string[],
    
    // 公開設定
    is_public: false
  })
  
  const [newPlan, setNewPlan] = useState({
    plan_type: 'single_session',
    title: '',
    description: '',
    duration_minutes: 60,
    number_of_sessions: 1,
    price: 0,
    currency: 'NTD',
    max_participants: 1,
    is_active: true
  })

  const countryCodes = [
    { code: '+886', name: `🇹🇼 ${t('profile.country.taiwan')}` },
    { code: '+1', name: `🇺🇸 ${t('profile.country.usa')}` },
    { code: '+44', name: `🇬🇧 ${t('profile.country.uk')}` },
    { code: '+86', name: `🇨🇳 ${t('profile.country.china')}` },
    { code: '+81', name: `🇯🇵 ${t('profile.country.japan')}` },
    { code: '+82', name: `🇰🇷 ${t('profile.country.korea')}` }
  ]

  const experienceOptions = [
    { value: 'beginner', label: t('profile.experience.beginner') },
    { value: 'intermediate', label: t('profile.experience.intermediate') },
    { value: 'advanced', label: t('profile.experience.advanced') },
    { value: 'expert', label: t('profile.experience.expert') }
  ]

  const planTypes = [
    { value: 'single_session', label: t('profile.planType.singleSession') },
    { value: 'package', label: t('profile.planType.package') },
    { value: 'group', label: t('profile.planType.group') },
    { value: 'workshop', label: t('profile.planType.workshop') }
  ]

  const timezones = [
    { value: 'Asia/Taipei', label: `${t('profile.timezone.taipei')} (GMT+8)` },
    { value: 'Asia/Tokyo', label: `${t('profile.timezone.tokyo')} (GMT+9)` },
    { value: 'Asia/Shanghai', label: `${t('profile.timezone.shanghai')} (GMT+8)` },
    { value: 'America/New_York', label: `${t('profile.timezone.newyork')} (GMT-5)` },
    { value: 'America/Los_Angeles', label: `${t('profile.timezone.losangeles')} (GMT-8)` },
    { value: 'Europe/London', label: `${t('profile.timezone.london')} (GMT+0)` }
  ]

  // Load coach profile on mount
  useEffect(() => {
    if (user) {
      fetchCoachProfile()
      fetchCoachingPlans()
    }
  }, [user])
  
  const fetchCoachProfile = async () => {
    try {
      const profile = await apiClient.getCoachProfile()
      if (profile) {
        setCoachProfile(profile)
        setFormData({
          display_name: profile.display_name || '',
          profile_photo_url: profile.profile_photo_url || '',
          public_email: profile.public_email || '',
          phone_country_code: profile.phone_country_code || '+886',
          phone_number: profile.phone_number || '',
          country: profile.country || '',
          city: profile.city || '',
          timezone: profile.timezone || '',
          coaching_languages: profile.coaching_languages || [],
          communication_tools: profile.communication_tools || {
            line: false,
            zoom: false,
            google_meet: false,
            ms_teams: false
          },
          line_id: profile.line_id || '',
          coach_experience: profile.coach_experience || '',
          training_institution: profile.training_institution || '',
          certifications: profile.certifications || [],
          linkedin_url: profile.linkedin_url || '',
          personal_website: profile.personal_website || '',
          bio: profile.bio || '',
          specialties: profile.specialties || [],
          is_public: profile.is_public || false
        })
      }
    } catch (error) {
      console.error('Error fetching coach profile:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  const fetchCoachingPlans = async () => {
    try {
      const plans = await apiClient.getCoachingPlans()
      // Ensure plans is always an array
      setCoachingPlans(Array.isArray(plans) ? plans : [])
    } catch (error) {
      console.error('Error fetching coaching plans:', error)
      // Set empty array on error
      setCoachingPlans([])
    }
  }
  
  const handleInputChange = (field: string, value: any) => {
    if (field.startsWith('communication_tools.')) {
      const tool = field.split('.')[1]
      setFormData(prev => ({
        ...prev,
        communication_tools: {
          ...prev.communication_tools,
          [tool]: value
        }
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // For now, we'll just show a placeholder. In a real implementation,
    // you would upload to a service like Cloudinary, AWS S3, etc.
    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result as string
      handleInputChange('profile_photo_url', result)
    }
    reader.readAsDataURL(file)

    // TODO: Implement actual photo upload to storage service
    // const uploadedUrl = await uploadPhotoToStorage(file)
    // handleInputChange('profile_photo_url', uploadedUrl)
  }
  
  const saveCoachProfile = async () => {
    try {
      let savedProfile
      if (coachProfile) {
        savedProfile = await apiClient.updateCoachProfile(formData)
      } else {
        savedProfile = await apiClient.createCoachProfile(formData)
      }
      
      setCoachProfile(savedProfile)
      setIsEditing(false)
      alert(t('profile.saveSuccess'))
    } catch (error) {
      console.error('Error saving coach profile:', error)
      alert(t('profile.saveError'))
    }
  }

  const handleAddCertification = (certification: string) => {
    if (certification.trim() && !formData.certifications.includes(certification.trim())) {
      handleInputChange('certifications', [...formData.certifications, certification.trim()])
    }
  }

  const handleRemoveCertification = (index: number) => {
    const newCertifications = [...formData.certifications]
    newCertifications.splice(index, 1)
    handleInputChange('certifications', newCertifications)
  }

  const handleAddSpecialty = (specialty: string) => {
    if (specialty.trim() && !formData.specialties.includes(specialty.trim())) {
      handleInputChange('specialties', [...formData.specialties, specialty.trim()])
    }
  }

  const handleRemoveSpecialty = (index: number) => {
    const newSpecialties = [...formData.specialties]
    newSpecialties.splice(index, 1)
    handleInputChange('specialties', newSpecialties)
  }

  const handleCreatePlan = async () => {
    try {
      await apiClient.createCoachingPlan(newPlan)
      await fetchCoachingPlans()
      setShowPlanModal(false)
      setNewPlan({
        plan_type: 'single_session',
        title: '',
        description: '',
        duration_minutes: 60,
        number_of_sessions: 1,
        price: 0,
        currency: 'NTD',
        max_participants: 1,
        is_active: true
      })
      alert(t('profile.planCreatedSuccess'))
    } catch (error) {
      console.error('Error creating coaching plan:', error)
      alert('建立方案失敗，請稍後再試。')
    }
  }

  const handleUpdatePlan = async () => {
    if (!editingPlanId) return
    
    try {
      await apiClient.updateCoachingPlan(editingPlanId, newPlan)
      await fetchCoachingPlans()
      setShowPlanModal(false)
      setEditingPlanId(null)
      setNewPlan({
        plan_type: 'single_session',
        title: '',
        description: '',
        duration_minutes: 60,
        number_of_sessions: 1,
        price: 0,
        currency: 'NTD',
        max_participants: 1,
        is_active: true
      })
      alert(t('profile.planUpdatedSuccess'))
    } catch (error) {
      console.error('Error updating coaching plan:', error)
      alert('更新方案失敗，請稍後再試。')
    }
  }

  const handleDeletePlan = async (planId: string) => {
    if (confirm(t('profile.confirmDeletePlan'))) {
      try {
        await apiClient.deleteCoachingPlan(planId)
        await fetchCoachingPlans()
        alert(t('profile.planDeletedSuccess'))
      } catch (error) {
        console.error('Error deleting coaching plan:', error)
        alert('刪除方案失敗，請稍後再試。')
      }
    }
  }

  const openEditPlan = (plan: any) => {
    setEditingPlanId(plan.id)
    setNewPlan({
      plan_type: plan.plan_type,
      title: plan.title,
      description: plan.description,
      duration_minutes: plan.duration_minutes,
      number_of_sessions: plan.number_of_sessions,
      price: plan.price,
      currency: plan.currency,
      max_participants: plan.max_participants,
      is_active: plan.is_active
    })
    setShowPlanModal(true)
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            <div className="h-32 bg-gray-700 rounded"></div>
            <div className="h-32 bg-gray-700 rounded"></div>
            <div className="h-32 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">{t('profile.title')}</h1>
          <p className="text-gray-400">{t('profile.subtitle')}</p>
          
          {!isEditing && (
            <div className="mt-4">
              <button
                onClick={() => setIsEditing(true)}
                className="bg-dashboard-accent text-white px-6 py-2 rounded-lg hover:bg-opacity-80 transition-colors"
              >
                {t('profile.editProfile')}
              </button>
            </div>
          )}
          
          {isEditing && (
            <div className="mt-4 flex space-x-4">
              <button
                onClick={saveCoachProfile}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                {t('common.save')}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false)
                  fetchCoachProfile() // Reset form data
                }}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                {t('common.cancel')}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-8">
          {/* 公開設定 - 移到最上方 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                {formData.is_public ? (
                  <EyeIcon className="h-6 w-6 text-dashboard-accent" />
                ) : (
                  <EyeSlashIcon className="h-6 w-6 text-gray-400" />
                )}
                <h2 className="text-xl font-semibold text-white">{t('profile.publicSettings')}</h2>
                <span className="px-2 py-1 bg-yellow-600 text-yellow-100 text-xs rounded-full">
                  {t('profile.inDevelopment')}
                </span>
              </div>
            </div>
            
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-4">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                🚧 {t('profile.publicProfileComingSoon')}
              </p>
            </div>

            <label className="flex items-center space-x-3 cursor-not-allowed opacity-50">
              <input
                type="checkbox"
                checked={formData.is_public}
                onChange={(e) => handleInputChange('is_public', e.target.checked)}
                disabled={true} // 暫時禁用，直到功能完成
                className="w-4 h-4 text-dashboard-accent bg-gray-100 border-gray-300 rounded focus:ring-dashboard-accent focus:ring-2"
              />
              <span className="text-sm text-gray-300">{t('profile.makeProfilePublic')}</span>
            </label>
          </div>

          {/* 基本資料區塊 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <UserCircleIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold text-white">{t('profile.basicInfo')}</h2>
            </div>
            
            {/* 大頭照 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.profilePhoto')}</label>
              <div className="flex items-center space-x-4">
                <div className="w-20 h-20 bg-gray-600 rounded-full flex items-center justify-center overflow-hidden">
                  {formData.profile_photo_url ? (
                    <img 
                      src={formData.profile_photo_url} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <UserCircleIcon className="h-12 w-12 text-gray-400" />
                  )}
                </div>
                {isEditing && (
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoUpload}
                      className="hidden"
                    />
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center space-x-2 px-4 py-2 bg-dashboard-accent bg-opacity-10 text-dashboard-accent rounded-lg hover:bg-opacity-20 transition-colors"
                    >
                      <CameraIcon className="h-4 w-4" />
                      <span>{t('profile.changePhoto')}</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.displayName')} *</label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => handleInputChange('display_name', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder={t('profile.displayNamePlaceholder')}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.publicEmail')}</label>
                <input
                  type="email"
                  value={formData.public_email}
                  onChange={(e) => handleInputChange('public_email', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder="example@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.phoneNumber')}</label>
                <div className="flex space-x-2">
                  <select
                    value={formData.phone_country_code}
                    onChange={(e) => handleInputChange('phone_country_code', e.target.value)}
                    disabled={!isEditing}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  >
                    {countryCodes.map(country => (
                      <option key={country.code} value={country.code}>
                        {country.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => handleInputChange('phone_number', e.target.value)}
                    disabled={!isEditing}
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                    placeholder={t('profile.phoneNumberPlaceholder')}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.country')}</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => handleInputChange('country', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder={t('profile.countryPlaceholder')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.city')}</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder={t('profile.cityPlaceholder')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.timezone')}</label>
                <select
                  value={formData.timezone}
                  onChange={(e) => handleInputChange('timezone', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                >
                  <option value="">{t('profile.selectTimezone')}</option>
                  {timezones.map(tz => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 語言設定 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <GlobeAltIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold text-white">{t('profile.languageServices')}</h2>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">{t('profile.languageServicesDescription')}</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: 'mandarin', label: t('profile.langMandarin') },
                  { value: 'english', label: 'English' },
                  { value: 'cantonese', label: t('profile.langCantonese') },
                  { value: 'japanese', label: t('profile.langJapanese') },
                  { value: 'korean', label: t('profile.langKorean') },
                  { value: 'spanish', label: 'Español' },
                  { value: 'french', label: 'Français' },
                  { value: 'german', label: 'Deutsch' }
                ].map(lang => (
                  <label key={lang.value} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.coaching_languages.includes(lang.value)}
                      onChange={(e) => {
                        const languages = [...formData.coaching_languages]
                        if (e.target.checked) {
                          languages.push(lang.value)
                        } else {
                          const index = languages.indexOf(lang.value)
                          if (index > -1) {
                            languages.splice(index, 1)
                          }
                        }
                        handleInputChange('coaching_languages', languages)
                      }}
                      disabled={!isEditing}
                      className="w-4 h-4 text-dashboard-accent bg-gray-100 border-gray-300 rounded focus:ring-dashboard-accent focus:ring-2 disabled:opacity-50"
                    />
                    <span className={`text-sm ${!isEditing ? 'text-gray-400' : 'text-gray-300'}`}>
                      {lang.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* 溝通工具 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold text-white">{t('profile.communicationTools')}</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">{t('profile.supportedPlatforms')}</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { key: 'line', label: 'LINE' },
                    { key: 'zoom', label: 'Zoom' },
                    { key: 'google_meet', label: 'Google Meet' },
                    { key: 'ms_teams', label: 'Microsoft Teams' }
                  ].map(tool => (
                    <label key={tool.key} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.communication_tools[tool.key as keyof typeof formData.communication_tools]}
                        onChange={(e) => handleInputChange(`communication_tools.${tool.key}`, e.target.checked)}
                        disabled={!isEditing}
                        className="w-4 h-4 text-dashboard-accent bg-gray-100 border-gray-300 rounded focus:ring-dashboard-accent focus:ring-2 disabled:opacity-50"
                      />
                      <span className={`text-sm ${!isEditing ? 'text-gray-400' : 'text-gray-300'}`}>
                        {tool.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              {formData.communication_tools.line && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">LINE ID</label>
                  <input
                    type="text"
                    value={formData.line_id}
                    onChange={(e) => handleInputChange('line_id', e.target.value)}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                    placeholder={t('profile.lineIdPlaceholder')}
                  />
                </div>
              )}
            </div>
          </div>

          {/* 專業資訊 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <AcademicCapIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold text-white">{t('profile.professionalInfo')}</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.coachingExperience')}</label>
                <select
                  value={formData.coach_experience}
                  onChange={(e) => handleInputChange('coach_experience', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                >
                  <option value="">{t('profile.selectExperience')}</option>
                  {experienceOptions.map(exp => (
                    <option key={exp.value} value={exp.value}>
                      {exp.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.trainingInstitution')}</label>
                <input
                  type="text"
                  value={formData.training_institution}
                  onChange={(e) => handleInputChange('training_institution', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder={t('profile.trainingInstitutionPlaceholder')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">LinkedIn</label>
                <input
                  type="url"
                  value={formData.linkedin_url}
                  onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder="https://linkedin.com/in/yourprofile"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.personalWebsite')}</label>
                <input
                  type="url"
                  value={formData.personal_website}
                  onChange={(e) => handleInputChange('personal_website', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                  placeholder="https://yourwebsite.com"
                />
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.certifications')}</label>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {formData.certifications.map((cert, index) => (
                    <span 
                      key={index}
                      className="bg-dashboard-accent bg-opacity-20 text-dashboard-accent px-3 py-1 rounded-full text-sm flex items-center space-x-2"
                    >
                      <span>{cert}</span>
                      {isEditing && (
                        <button
                          onClick={() => handleRemoveCertification(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <TrashIcon className="h-3 w-3" />
                        </button>
                      )}
                    </span>
                  ))}
                </div>
                {isEditing && (
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder={t('profile.addCertificationPlaceholder')}
                      className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          const input = e.target as HTMLInputElement
                          handleAddCertification(input.value)
                          input.value = ''
                        }
                      }}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.specialties')}</label>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {formData.specialties.map((specialty, index) => (
                    <span 
                      key={index}
                      className="bg-green-600 bg-opacity-20 text-green-300 px-3 py-1 rounded-full text-sm flex items-center space-x-2"
                    >
                      <span>{specialty}</span>
                      {isEditing && (
                        <button
                          onClick={() => handleRemoveSpecialty(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <TrashIcon className="h-3 w-3" />
                        </button>
                      )}
                    </span>
                  ))}
                </div>
                {isEditing && (
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder={t('profile.addSpecialtyPlaceholder')}
                      className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          const input = e.target as HTMLInputElement
                          handleAddSpecialty(input.value)
                          input.value = ''
                        }
                      }}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.bio')}</label>
              <textarea
                value={formData.bio}
                onChange={(e) => handleInputChange('bio', e.target.value)}
                disabled={!isEditing}
                rows={4}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent disabled:opacity-50"
                placeholder={t('profile.bioPlaceholder')}
              />
            </div>
          </div>

          {/* 教練方案 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <BriefcaseIcon className="h-6 w-6 text-dashboard-accent" />
                <h2 className="text-xl font-semibold text-white">{t('profile.coachingPlans')}</h2>
              </div>
              
              <button
                onClick={() => {
                  setEditingPlanId(null)
                  setNewPlan({
                    plan_type: 'single_session',
                    title: '',
                    description: '',
                    duration_minutes: 60,
                    number_of_sessions: 1,
                    price: 0,
                    currency: 'NTD',
                    max_participants: 1,
                    is_active: true
                  })
                  setShowPlanModal(true)
                }}
                className="flex items-center space-x-2 px-4 py-2 bg-dashboard-accent bg-opacity-10 text-dashboard-accent rounded-lg hover:bg-opacity-20 transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                <span>{t('profile.addPlan')}</span>
              </button>
            </div>
            
            <div className="space-y-4">
              {coachingPlans.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <BriefcaseIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>{t('profile.noPlanYet')}</p>
                  <p className="text-sm mt-2">{t('profile.noPlanDescription')}</p>
                </div>
              ) : (
                coachingPlans.map(plan => (
                  <div key={plan.id} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">{plan.title}</h3>
                          <span className="px-2 py-1 bg-blue-600 text-blue-100 text-xs rounded-full">
                            {planTypes.find(t => t.value === plan.plan_type)?.label || plan.plan_type}
                          </span>
                          {!plan.is_active && (
                            <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded-full">
                              {t('profile.planDisabled')}
                            </span>
                          )}
                        </div>
                        {plan.description && (
                          <p className="text-gray-300 text-sm mb-3">{plan.description}</p>
                        )}
                        <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                          {plan.duration_minutes && (
                            <span>{t('profile.planDuration')}: {plan.duration_minutes} {t('profile.minutes')}</span>
                          )}
                          {plan.number_of_sessions > 1 && (
                            <span>{t('profile.planSessions')}: {plan.number_of_sessions}</span>
                          )}
                          <span>{t('profile.planPrice')}: {plan.currency} ${plan.price}</span>
                          {plan.max_participants > 1 && (
                            <span>{t('profile.planMaxParticipants')}: {plan.max_participants} {t('profile.people')}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => openEditPlan(plan)}
                          className="p-2 text-dashboard-accent hover:bg-dashboard-accent hover:bg-opacity-10 rounded transition-colors"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeletePlan(plan.id)}
                          className="p-2 text-red-400 hover:bg-red-400 hover:bg-opacity-10 rounded transition-colors"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 教練方案 Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-dashboard-card rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto m-4">
            <h3 className="text-xl font-semibold text-white mb-4">
              {editingPlanId ? t('profile.editPlan') : t('profile.addPlan')}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.planType')}</label>
                <select
                  value={newPlan.plan_type}
                  onChange={(e) => setNewPlan({...newPlan, plan_type: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                >
                  {planTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.planTitle')} *</label>
                <input
                  type="text"
                  value={newPlan.title}
                  onChange={(e) => setNewPlan({...newPlan, title: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder={t('profile.planTitlePlaceholder')}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.planDescription')}</label>
                <textarea
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({...newPlan, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder={t('profile.planDescriptionPlaceholder')}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.sessionDuration')}</label>
                  <input
                    type="number"
                    value={newPlan.duration_minutes}
                    onChange={(e) => setNewPlan({...newPlan, duration_minutes: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="15"
                    max="480"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.numberOfSessions')}</label>
                  <input
                    type="number"
                    value={newPlan.number_of_sessions}
                    onChange={(e) => setNewPlan({...newPlan, number_of_sessions: parseInt(e.target.value) || 1})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.planPrice')} *</label>
                  <input
                    type="number"
                    value={newPlan.price}
                    onChange={(e) => setNewPlan({...newPlan, price: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="0"
                    step="0.01"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.currency')}</label>
                  <select
                    value={newPlan.currency}
                    onChange={(e) => setNewPlan({...newPlan, currency: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  >
                    <option value="NTD">NTD</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">{t('profile.maxParticipants')}</label>
                <input
                  type="number"
                  value={newPlan.max_participants}
                  onChange={(e) => setNewPlan({...newPlan, max_participants: parseInt(e.target.value) || 1})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  min="1"
                />
              </div>

              <div>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newPlan.is_active}
                    onChange={(e) => setNewPlan({...newPlan, is_active: e.target.checked})}
                    className="w-4 h-4 text-dashboard-accent bg-gray-100 border-gray-300 rounded focus:ring-dashboard-accent focus:ring-2"
                  />
                  <span className="text-sm text-gray-300">{t('profile.enablePlan')}</span>
                </label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => {
                  setShowPlanModal(false)
                  setEditingPlanId(null)
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={editingPlanId ? handleUpdatePlan : handleCreatePlan}
                disabled={!newPlan.title.trim() || newPlan.price < 0}
                className="px-4 py-2 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {editingPlanId ? t('profile.updatePlan') : t('profile.createPlan')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}