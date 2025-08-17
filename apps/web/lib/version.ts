/**
 * Version information utility for frontend
 * Reads version from root version.json or environment variables
 */

export interface VersionInfo {
  version: string
  displayVersion: string
  description: string
  releaseDate?: string
  releaseNotes?: string
  author?: string
}

/**
 * Get version information from environment variables or fallback
 */
export function getVersionInfo(): VersionInfo {
  // Try to get version from environment variables first (set by Next.js config)
  const envVersion = process.env.NEXT_PUBLIC_APP_VERSION
  const envDisplayVersion = process.env.NEXT_PUBLIC_APP_DISPLAY_VERSION
  const envDescription = process.env.NEXT_PUBLIC_APP_DESCRIPTION
  const envReleaseDate = process.env.NEXT_PUBLIC_APP_RELEASE_DATE
  const envReleaseNotes = process.env.NEXT_PUBLIC_APP_RELEASE_NOTES
  const envAuthor = process.env.NEXT_PUBLIC_APP_AUTHOR

  if (envVersion && envDisplayVersion) {
    return {
      version: envVersion,
      displayVersion: envDisplayVersion,
      description: envDescription || 'Coachly transcription service',
      releaseDate: envReleaseDate,
      releaseNotes: envReleaseNotes,
      author: envAuthor,
    }
  }

  // Fallback version info
  return {
    version: '2.11.0',
    displayVersion: 'v2.11.0',
    description: 'Coachly transcription service',
    releaseDate: '2025-08-17',
    author: 'Coachly Team',
  }
}

/**
 * Get current app version string
 */
export function getAppVersion(): string {
  const versionInfo = getVersionInfo()
  return versionInfo.displayVersion
}