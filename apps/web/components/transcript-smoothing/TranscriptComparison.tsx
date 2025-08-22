'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/contexts/i18n-context';
import { type ProcessedSegment, type ProcessingStats } from '@/lib/api';

interface TranscriptComparisonProps {
  originalTranscript: any;
  smoothedSegments: ProcessedSegment[];
  processingStats: ProcessingStats;
  isVisible: boolean;
  onClose: () => void;
  onAccept: () => void;
}

export default function TranscriptComparison({
  originalTranscript,
  smoothedSegments,
  processingStats,
  isVisible,
  onClose,
  onAccept
}: TranscriptComparisonProps) {
  const { t } = useI18n();
  const [viewMode, setViewMode] = useState<'original' | 'smoothed' | 'side-by-side'>('side-by-side');

  if (!isVisible) return null;

  const renderSegment = (segment: any, isSmoothed: boolean = false) => (
    <div 
      key={isSmoothed ? `smoothed-${segment.speaker}-${segment.start_ms}` : `original-${segment.speaker}-${segment.start}`}
      className="mb-4 p-3 border border-dashboard-accent border-opacity-20 rounded-lg"
    >
      <div className="flex justify-between items-center mb-2">
        <span className={`font-semibold ${
          segment.speaker === 'A' || segment.speaker === '1' ? 'text-blue-600' : 'text-green-600'
        }`}>
          {isSmoothed ? segment.speaker : (segment.speaker || 'Unknown')}
        </span>
        <span className="text-sm text-dashboard-text-secondary">
          {isSmoothed 
            ? `${(segment.start_ms / 1000).toFixed(1)}s - ${(segment.end_ms / 1000).toFixed(1)}s`
            : `${(segment.start / 1000).toFixed(1)}s - ${(segment.end / 1000).toFixed(1)}s`
          }
        </span>
      </div>
      <p className="text-dashboard-text">
        {isSmoothed ? segment.text : (segment.words?.map((w: any) => w.text).join('') || segment.text)}
      </p>
      {isSmoothed && segment.note && (
        <div className="mt-2 text-sm text-dashboard-accent">
          <span className="opacity-75">Note: </span>
          {segment.note}
        </div>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-dashboard-card-bg rounded-lg shadow-dark p-6 max-w-7xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-dashboard-accent">
              {t('sessions.transcript_comparison')}
            </h2>
            <p className="text-dashboard-text-secondary mt-1">
              {t('sessions.review_smoothed_transcript')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-dashboard-text-secondary hover:text-dashboard-text"
          >
            ✕
          </button>
        </div>

        {/* Processing Stats */}
        <div className="mb-6 p-4 bg-dashboard-bg border border-dashboard-accent border-opacity-20 rounded-lg">
          <h3 className="text-lg font-semibold text-dashboard-accent mb-3">
            {t('sessions.processing_statistics')}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-dashboard-text-secondary">{t('sessions.language_detected')}:</span>
              <div className="font-medium text-dashboard-text">{processingStats.language_detected}</div>
            </div>
            <div>
              <span className="text-dashboard-text-secondary">{t('sessions.words_moved')}:</span>
              <div className="font-medium text-dashboard-text">{processingStats.moved_word_count}</div>
            </div>
            <div>
              <span className="text-dashboard-text-secondary">{t('sessions.segments_merged')}:</span>
              <div className="font-medium text-dashboard-text">{processingStats.merged_segments}</div>
            </div>
            <div>
              <span className="text-dashboard-text-secondary">{t('sessions.processing_time')}:</span>
              <div className="font-medium text-dashboard-text">{processingStats.processing_time_ms}ms</div>
            </div>
          </div>

          {/* Heuristic Stats */}
          <div className="mt-4">
            <h4 className="text-sm font-medium text-dashboard-text mb-2">
              {t('sessions.heuristic_applications')}:
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
              <div className="text-dashboard-text-secondary">
                {t('sessions.short_segments')}: {processingStats.heuristic_hits.short_first_segment}
              </div>
              <div className="text-dashboard-text-secondary">
                {t('sessions.filler_words')}: {processingStats.heuristic_hits.filler_words}
              </div>
              <div className="text-dashboard-text-secondary">
                {t('sessions.echo_backfill')}: {processingStats.heuristic_hits.echo_backfill}
              </div>
              <div className="text-dashboard-text-secondary">
                {t('sessions.no_terminal_punct')}: {processingStats.heuristic_hits.no_terminal_punct}
              </div>
            </div>
          </div>
        </div>

        {/* View Mode Selector */}
        <div className="mb-4">
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-dashboard-accent text-dashboard-bg'
                  : 'bg-dashboard-bg text-dashboard-text border border-dashboard-accent border-opacity-30'
              }`}
            >
              {t('sessions.side_by_side')}
            </button>
            <button
              onClick={() => setViewMode('original')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'original'
                  ? 'bg-dashboard-accent text-dashboard-bg'
                  : 'bg-dashboard-bg text-dashboard-text border border-dashboard-accent border-opacity-30'
              }`}
            >
              {t('sessions.original_only')}
            </button>
            <button
              onClick={() => setViewMode('smoothed')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'smoothed'
                  ? 'bg-dashboard-accent text-dashboard-bg'
                  : 'bg-dashboard-bg text-dashboard-text border border-dashboard-accent border-opacity-30'
              }`}
            >
              {t('sessions.smoothed_only')}
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto">
          {viewMode === 'side-by-side' && (
            <div className="grid grid-cols-2 gap-4 h-full">
              <div>
                <h3 className="text-lg font-semibold text-dashboard-text mb-4">
                  {t('sessions.original_transcript')}
                </h3>
                <div className="space-y-2">
                  {originalTranscript?.utterances?.map((segment: any, index: number) => 
                    renderSegment(segment, false)
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-dashboard-text mb-4">
                  {t('sessions.smoothed_transcript')}
                </h3>
                <div className="space-y-2">
                  {smoothedSegments.map((segment) => 
                    renderSegment(segment, true)
                  )}
                </div>
              </div>
            </div>
          )}

          {viewMode === 'original' && (
            <div>
              <h3 className="text-lg font-semibold text-dashboard-text mb-4">
                {t('sessions.original_transcript')}
              </h3>
              <div className="space-y-2">
                {originalTranscript?.utterances?.map((segment: any, index: number) => 
                  renderSegment(segment, false)
                )}
              </div>
            </div>
          )}

          {viewMode === 'smoothed' && (
            <div>
              <h3 className="text-lg font-semibold text-dashboard-text mb-4">
                {t('sessions.smoothed_transcript')}
              </h3>
              <div className="space-y-2">
                {smoothedSegments.map((segment) => 
                  renderSegment(segment, true)
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-4 border-t border-dashboard-accent border-opacity-20">
          <Button
            variant="outline"
            onClick={onClose}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={onAccept}
            className="bg-dashboard-accent text-dashboard-bg hover:bg-dashboard-accent-hover"
          >
            {t('sessions.accept_smoothed_version')}
          </Button>
        </div>
      </div>
    </div>
  );
}