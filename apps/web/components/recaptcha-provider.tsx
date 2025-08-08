'use client';

import React, { createContext, useContext, ReactNode, useCallback } from 'react';
import { GoogleReCaptchaProvider, useGoogleReCaptcha } from 'react-google-recaptcha-v3';

interface ReCaptchaContextType {
  getReCaptchaToken: (action: string) => Promise<string | undefined>;
}

const ReCaptchaContext = createContext<ReCaptchaContextType | null>(null);

export const useReCaptcha = () => {
  const context = useContext(ReCaptchaContext);
  if (!context) {
    throw new Error('useReCaptcha must be used within a ReCaptchaProvider');
  }
  return context;
};

const ReCaptchaComponent = ({ children }: { children: ReactNode }) => {
  const { executeRecaptcha } = useGoogleReCaptcha();

  const getReCaptchaToken = useCallback(async (action: string) => {
    if (!executeRecaptcha) {
      console.error('ReCaptcha not available');
      return undefined;
    }
    return await executeRecaptcha(action);
  }, [executeRecaptcha]);

  return (
    <ReCaptchaContext.Provider value={{ getReCaptchaToken }}>
      {children}
    </ReCaptchaContext.Provider>
  );
};

// Fallback component when reCAPTCHA is disabled
const ReCaptchaFallback = ({ children }: { children: ReactNode }) => {
  const getReCaptchaToken = useCallback(async (action: string) => {
    console.warn('reCAPTCHA is disabled - returning undefined token');
    return undefined;
  }, []);

  return (
    <ReCaptchaContext.Provider value={{ getReCaptchaToken }}>
      {children}
    </ReCaptchaContext.Provider>
  );
};

export const ReCaptchaProvider = ({ children }: { children: ReactNode }) => {
  const siteKey = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;

  if (!siteKey) {
    console.warn('reCAPTCHA site key not found. reCAPTCHA will be disabled.');
    // Return fallback provider that returns undefined tokens
    return <ReCaptchaFallback>{children}</ReCaptchaFallback>;
  }

  return (
    <GoogleReCaptchaProvider reCaptchaKey={siteKey}>
      <ReCaptchaComponent>{children}</ReCaptchaComponent>
    </GoogleReCaptchaProvider>
  );
};
