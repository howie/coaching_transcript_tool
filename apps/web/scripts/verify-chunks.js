#!/usr/bin/env node

/**
 * Chunk Verification Script
 *
 * Verifies that all JavaScript chunks from Next.js build are present in OpenNext output
 * This prevents 404 errors in production due to missing chunks
 */

const fs = require('fs');
const path = require('path');

const COLORS = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, icon, message) {
  console.log(`${COLORS[color]}${icon} ${message}${COLORS.reset}`);
}

function getAllFiles(dir, fileList = []) {
  if (!fs.existsSync(dir)) {
    return fileList;
  }

  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      getAllFiles(filePath, fileList);
    } else {
      fileList.push(filePath);
    }
  });

  return fileList;
}

function extractChunkNames(files, baseDir) {
  return files
    .filter(f => f.endsWith('.js') || f.endsWith('.css'))
    .map(f => path.relative(baseDir, f))
    .sort();
}

function main() {
  log('blue', '🔍', 'Starting chunk verification...\n');

  const nextStaticDir = path.join(process.cwd(), '.next', 'static');
  const openNextAssetsDir = path.join(process.cwd(), '.open-next', 'assets', '_next', 'static');

  // Check if directories exist
  if (!fs.existsSync(nextStaticDir)) {
    log('red', '❌', 'Next.js build directory not found: .next/static');
    log('yellow', '⚠️', 'Please run "npm run build" first');
    process.exit(1);
  }

  if (!fs.existsSync(openNextAssetsDir)) {
    log('red', '❌', 'OpenNext assets directory not found: .open-next/assets/_next/static');
    log('yellow', '⚠️', 'Please run "npm run build:cf" first');
    process.exit(1);
  }

  // Get all chunks from both directories
  const nextChunks = extractChunkNames(
    getAllFiles(nextStaticDir),
    nextStaticDir
  );

  const openNextChunks = extractChunkNames(
    getAllFiles(openNextAssetsDir),
    openNextAssetsDir
  );

  log('blue', 'ℹ️', `Found ${nextChunks.length} chunks in Next.js build`);
  log('blue', 'ℹ️', `Found ${openNextChunks.length} chunks in OpenNext output\n`);

  // Check for missing chunks
  const missingChunks = nextChunks.filter(chunk => !openNextChunks.includes(chunk));

  if (missingChunks.length > 0) {
    log('red', '❌', `VERIFICATION FAILED: ${missingChunks.length} chunks are missing in OpenNext output!\n`);

    console.log('Missing chunks:');
    missingChunks.slice(0, 20).forEach(chunk => {
      console.log(`  - ${chunk}`);
    });

    if (missingChunks.length > 20) {
      console.log(`  ... and ${missingChunks.length - 20} more\n`);
    }

    log('yellow', '💡', 'Recommended actions:');
    console.log('  1. Clean build: npm run clean && npm run build && npm run build:cf');
    console.log('  2. Check OpenNext version compatibility');
    console.log('  3. Review .open-next build logs for errors\n');

    process.exit(1);
  }

  // Check for extra chunks (informational only)
  const extraChunks = openNextChunks.filter(chunk => !nextChunks.includes(chunk));

  if (extraChunks.length > 0) {
    log('yellow', '⚠️', `Info: ${extraChunks.length} extra chunks found in OpenNext (this is usually OK)\n`);
  }

  // Check BUILD_ID consistency
  const nextBuildId = fs.readFileSync(path.join(process.cwd(), '.next', 'BUILD_ID'), 'utf-8').trim();
  const openNextBuildIdPath = path.join(process.cwd(), '.open-next', 'assets', '_next', 'BUILD_ID');

  if (fs.existsSync(openNextBuildIdPath)) {
    const openNextBuildId = fs.readFileSync(openNextBuildIdPath, 'utf-8').trim();

    if (nextBuildId !== openNextBuildId) {
      log('red', '❌', 'BUILD_ID mismatch detected!');
      console.log(`  Next.js BUILD_ID:  ${nextBuildId}`);
      console.log(`  OpenNext BUILD_ID: ${openNextBuildId}\n`);
      log('yellow', '💡', 'This will cause 404 errors. Rebuild with consistent BUILD_ID.\n');
      process.exit(1);
    }

    log('green', '✅', `BUILD_ID verified: ${nextBuildId}`);
  }

  // Success
  log('green', '✅', 'All chunks verified successfully!');
  log('green', '✅', 'Deployment package is ready\n');

  // Print summary
  console.log('Deployment Summary:');
  console.log(`  • BUILD_ID: ${nextBuildId}`);
  console.log(`  • Total chunks: ${nextChunks.length}`);
  console.log(`  • Ready for deployment: YES\n`);
}

// Run verification
try {
  main();
} catch (error) {
  log('red', '❌', `Verification failed with error: ${error.message}`);
  console.error(error);
  process.exit(1);
}
