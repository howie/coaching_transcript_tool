'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient, type SmoothingResponse } from '@/lib/api';

interface TranscriptSmoothingPanelProps {
  assemblyAiTranscript: any;
  onSmoothingComplete: (smoothedResult: SmoothingResponse) => void;
  isVisible: boolean;
  onClose: () => void;
}

interface SmoothingConfig {
  th_short_head_sec: number;
  th_filler_max_sec: number;
  th_gap_sec: number;
  th_max_move_sec: number;
  th_sent_gap_sec: number;
  min_sentence_length: number;
}

export default function TranscriptSmoothingPanel({
  assemblyAiTranscript,
  onSmoothingComplete,
  isVisible,
  onClose
}: TranscriptSmoothingPanelProps) {
  const { t } = useI18n();
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [supportedLanguages, setSupportedLanguages] = useState<any[]>([]);
  const [config, setConfig] = useState<SmoothingConfig | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Load supported languages and default config on mount
  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const languagesData = await apiClient.getSupportedLanguages();
        setSupportedLanguages(languagesData.supported_languages || []);
      } catch (error) {
        console.error('Failed to load supported languages:', error);
      }
    };

    if (isVisible) {
      loadLanguages();
    }
  }, [isVisible]);

  // Load config when language changes
  useEffect(() => {
    const loadConfig = async () => {
      if (selectedLanguage === 'auto') return;
      
      try {
        const defaultConfig = await apiClient.getSmoothingDefaults(selectedLanguage);
        setConfig({
          th_short_head_sec: defaultConfig.smoothing_config.th_short_head_sec,
          th_filler_max_sec: defaultConfig.smoothing_config.th_filler_max_sec,
          th_gap_sec: defaultConfig.smoothing_config.th_gap_sec,
          th_max_move_sec: defaultConfig.smoothing_config.th_max_move_sec,
          th_sent_gap_sec: defaultConfig.punctuation_config.th_sent_gap_sec,
          min_sentence_length: defaultConfig.punctuation_config.min_sentence_length,
        });
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };

    loadConfig();
  }, [selectedLanguage]);

  const handleSmooth = async () => {
    if (!assemblyAiTranscript) return;

    setIsProcessing(true);
    try {
      const result = await apiClient.smoothTranscript(
        assemblyAiTranscript,
        selectedLanguage,
        config
      );
      
      onSmoothingComplete(result);
    } catch (error) {
      console.error('Smoothing failed:', error);
      alert(`${t('sessions.smoothing_error')}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-dashboard-card-bg rounded-lg shadow-dark p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-dashboard-accent">
              {t('sessions.smooth_transcript')}
            </h2>
            <p className="text-dashboard-text-secondary mt-1">
              {t('sessions.smooth_transcript_description')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-dashboard-text-secondary hover:text-dashboard-text"
          >
            ✕
          </button>
        </div>

        {/* Language Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dashboard-text mb-2">
              {t('sessions.select_language')}
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded-lg focus:ring-2 focus:ring-dashboard-accent focus:border-dashboard-accent text-dashboard-text"
            >
              {supportedLanguages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name} {lang.auto_detected && '(Auto-detected)'}
                </option>
              ))}
            </select>
            <p className="text-sm text-dashboard-text-tertiary mt-1">
              {supportedLanguages.find(l => l.code === selectedLanguage)?.description}
            </p>
          </div>

          {/* Advanced Configuration */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center text-dashboard-accent hover:text-dashboard-accent-hover"
            >
              <span className="mr-2">
                {showAdvanced ? '▼' : '▶'}
              </span>
              {t('sessions.advanced_settings')}
            </button>

            {showAdvanced && config && (
              <div className="mt-4 space-y-4 p-4 bg-dashboard-bg border border-dashboard-accent border-opacity-20 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  {/* Boundary Smoothing Settings */}
                  <div>
                    <label className="block text-sm font-medium text-dashboard-text mb-1">
                      {t('sessions.short_head_threshold')} (s)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={config.th_short_head_sec}
                      onChange={(e) => setConfig({
                        ...config,
                        th_short_head_sec: parseFloat(e.target.value)
                      })}
                      className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded text-dashboard-text"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dashboard-text mb-1">
                      {t('sessions.filler_word_threshold')} (s)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={config.th_filler_max_sec}
                      onChange={(e) => setConfig({
                        ...config,
                        th_filler_max_sec: parseFloat(e.target.value)
                      })}
                      className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded text-dashboard-text"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dashboard-text mb-1">
                      {t('sessions.sentence_gap_threshold')} (s)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={config.th_sent_gap_sec}
                      onChange={(e) => setConfig({
                        ...config,
                        th_sent_gap_sec: parseFloat(e.target.value)
                      })}
                      className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded text-dashboard-text"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dashboard-text mb-1">
                      {t('sessions.min_sentence_length')}
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={config.min_sentence_length}
                      onChange={(e) => setConfig({
                        ...config,
                        min_sentence_length: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded text-dashboard-text"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4 pt-4">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isProcessing}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleSmooth}
              disabled={isProcessing || !assemblyAiTranscript}
              className="bg-dashboard-accent text-dashboard-bg hover:bg-dashboard-accent-hover"
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('sessions.smoothing')}...
                </div>
              ) : (
                t('sessions.apply_smoothing')
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}