#!/usr/bin/env node

/**
 * 本地端 HTTPS 轉換測試腳本
 * 驗證 API URL 的 HTTPS 強制轉換邏輯
 */

console.log('🧪 HTTPS Enforcement Test Script\n');

// 模擬生產環境的測試 URLs
const testURLs = [
  'http://api.doxa.com.tw/api/health',
  'http://api.doxa.com.tw/api/health/',
  'http://api.doxa.com.tw/api/webhooks/health',
  'http://api.doxa.com.tw/api/webhooks/health/',
  'http://api.doxa.com.tw/api/v1/user/profile',
  'https://api.doxa.com.tw/api/v1/clients',  // Already HTTPS
  'http://localhost:8000/api/health',        // Should not be changed
];

// 模擬 createSecureFetcher 中的 HTTPS 轉換邏輯
function enforceHTTPS(url, isSecureContext = true) {
  if (!isSecureContext) return url;
  
  const originalUrl = url;
  
  // 1. Aggressively force HTTPS for doxa.com.tw domains
  if (url.includes('api.doxa.com.tw')) {
    url = url.replace(/^https?:\/\/api\.doxa\.com\.tw/, 'https://api.doxa.com.tw');
  }
  
  // 2. Simulate trailing slash logic for specific endpoints
  const needsTrailingSlash = [
    '/api/health',
    '/api/webhooks/health'
  ];
  
  const [path, query] = url.split('?');
  let pathWithSlash = path;
  for (const endpoint of needsTrailingSlash) {
    if (path.endsWith(endpoint) && !path.endsWith(endpoint + '/')) {
      pathWithSlash = path + '/';
      break;
    }
  }
  url = query ? `${pathWithSlash}?${query}` : pathWithSlash;
  
  return { originalUrl, transformedUrl: url, wasTransformed: originalUrl !== url };
}

// 執行測試
let passedTests = 0;
let totalTests = testURLs.length;

console.log('🔍 Testing URL transformations:\n');

testURLs.forEach((testUrl, index) => {
  const result = enforceHTTPS(testUrl, true);
  const isCorrect = result.transformedUrl.startsWith('https://') || 
                   result.transformedUrl.startsWith('http://localhost');
  
  console.log(`Test ${index + 1}:`);
  console.log(`  Original:    ${result.originalUrl}`);
  console.log(`  Transformed: ${result.transformedUrl}`);
  console.log(`  Changed:     ${result.wasTransformed}`);
  console.log(`  Status:      ${isCorrect ? '✅ PASS' : '❌ FAIL'}\n`);
  
  if (isCorrect) passedTests++;
});

// 測試結果
console.log(`\n📊 Test Results: ${passedTests}/${totalTests} tests passed`);

if (passedTests === totalTests) {
  console.log('🎉 All tests passed! HTTPS enforcement logic is working correctly.');
  process.exit(0);
} else {
  console.log('⚠️  Some tests failed. Please check the HTTPS enforcement logic.');
  process.exit(1);
}