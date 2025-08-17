import { useState, useCallback } from 'react';
import planService, { ValidationResult } from '@/lib/services/plan.service';
import { toast } from 'react-hot-toast';

interface PlanLimitOptions {
  showError?: boolean;
  showUpgradePrompt?: boolean;
  silent?: boolean;
}

export function usePlanLimits() {
  const [validating, setValidating] = useState(false);
  const [lastValidation, setLastValidation] = useState<ValidationResult | null>(null);

  const validateAction = useCallback(async (
    action: string,
    params?: any,
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    const { 
      showError = true, 
      showUpgradePrompt = true,
      silent = false 
    } = options;

    setValidating(true);
    try {
      const result: ValidationResult = await planService.validateAction(action, params);
      setLastValidation(result);
      
      if (!result.allowed && !silent) {
        if (showError) {
          // Show error toast with custom action
          const toastId = toast.error(
            <div>
              <p className="font-medium">{result.message}</p>
              {result.limit_info && (
                <p className="text-sm mt-1 opacity-90">
                  Current: {result.limit_info.current} / Limit: {result.limit_info.limit}
                </p>
              )}
              {showUpgradePrompt && result.upgrade_suggestion && (
                <button
                  onClick={() => {
                    toast.dismiss(toastId);
                    window.location.href = '/dashboard/billing?tab=plans';
                  }}
                  className="mt-2 px-3 py-1 bg-white bg-opacity-20 rounded text-sm font-medium hover:bg-opacity-30 transition-colors"
                >
                  Upgrade to {result.upgrade_suggestion.display_name}
                </button>
              )}
            </div>,
            {
              duration: 6000,
              position: 'top-center',
              style: {
                background: '#1f2937',
                color: '#fff',
                border: '1px solid #ef4444',
              },
            }
          );
        }
      }
      
      return result.allowed;
    } catch (error) {
      console.error('Failed to validate action:', error);
      // Fail open - allow action on error
      if (!silent) {
        toast.error('Unable to validate plan limits. Proceeding anyway.');
      }
      return true;
    } finally {
      setValidating(false);
    }
  }, []);

  const checkBeforeAction = useCallback(async (
    action: string,
    callback: () => void | Promise<void>,
    params?: any
  ) => {
    const allowed = await validateAction(action, params, {
      showError: true,
      showUpgradePrompt: true
    });
    
    if (allowed) {
      await callback();
    }
  }, [validateAction]);

  const validateFile = useCallback(async (
    file: File,
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    const fileSizeMb = file.size / (1024 * 1024);
    return validateAction('upload_file', { file_size_mb: fileSizeMb }, options);
  }, [validateAction]);

  const validateExport = useCallback(async (
    format: string,
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    return validateAction('export_transcript', { format }, options);
  }, [validateAction]);

  const canCreateSession = useCallback(async (
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    return validateAction('create_session', {}, options);
  }, [validateAction]);

  const canTranscribe = useCallback(async (
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    return validateAction('transcribe', {}, options);
  }, [validateAction]);

  // Check multiple actions at once
  const validateMultiple = useCallback(async (
    actions: Array<{ action: string; params?: any }>,
    options: PlanLimitOptions = {}
  ): Promise<boolean> => {
    for (const { action, params } of actions) {
      const allowed = await validateAction(action, params, { 
        ...options, 
        showError: false // Only show error for the last failed action
      });
      if (!allowed) {
        if (options.showError !== false) {
          await validateAction(action, params, options); // Re-run to show error
        }
        return false;
      }
    }
    return true;
  }, [validateAction]);

  return {
    validateAction,
    checkBeforeAction,
    validateFile,
    validateExport,
    canCreateSession,
    canTranscribe,
    validateMultiple,
    validating,
    lastValidation
  };
}