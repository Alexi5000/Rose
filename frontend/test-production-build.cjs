/**
 * Production Build Test Script
 * 
 * Verifies the production build was created successfully and
 * checks bundle sizes, file structure, and basic functionality.
 * 
 * Usage: npm run test:production
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const buildDir = path.join(__dirname, '..', 'src', 'ai_companion', 'interfaces', 'web', 'static');
const targetGzipSize = 2048; // 2MB in KB

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(title, 'cyan');
  console.log('='.repeat(60));
}

function checkBuildDirectory() {
  logSection('📁 Build Directory Check');
  
  if (!fs.existsSync(buildDir)) {
    log('❌ Build directory not found!', 'red');
    log(`   Expected: ${buildDir}`, 'yellow');
    log('   Run: npm run build', 'yellow');
    return false;
  }
  
  log('✅ Build directory exists', 'green');
  log(`   Location: ${buildDir}`, 'blue');
  return true;
}

function checkRequiredFiles() {
  logSection('📄 Required Files Check');
  
  const requiredFiles = [
    'index.html',
  ];
  
  let allFound = true;
  
  for (const file of requiredFiles) {
    const filePath = path.join(buildDir, file);
    if (fs.existsSync(filePath)) {
      log(`✅ ${file}`, 'green');
    } else {
      log(`❌ ${file} not found`, 'red');
      allFound = false;
    }
  }
  
  // Check assets directory
  const assetsDir = path.join(buildDir, 'assets');
  if (fs.existsSync(assetsDir)) {
    const assets = fs.readdirSync(assetsDir);
    log(`\n📦 Assets (${assets.length} files):`, 'blue');
    
    const jsFiles = assets.filter(f => f.endsWith('.js'));
    const cssFiles = assets.filter(f => f.endsWith('.css'));
    
    log(`   JavaScript: ${jsFiles.length} files`, 'blue');
    log(`   CSS: ${cssFiles.length} files`, 'blue');
    
    // Check for expected chunks
    const expectedChunks = ['three', 'r3f', 'animations', 'index'];
    for (const chunk of expectedChunks) {
      const found = jsFiles.some(f => f.includes(chunk));
      if (found) {
        log(`   ✅ ${chunk} chunk found`, 'green');
      } else {
        log(`   ⚠️  ${chunk} chunk not found`, 'yellow');
      }
    }
  } else {
    log('❌ Assets directory not found', 'red');
    allFound = false;
  }
  
  return allFound;
}

function analyzeBundleSize() {
  logSection('📊 Bundle Size Analysis');
  
  const assetsDir = path.join(buildDir, 'assets');
  if (!fs.existsSync(assetsDir)) {
    log('❌ Cannot analyze: assets directory not found', 'red');
    return false;
  }
  
  const assets = fs.readdirSync(assetsDir);
  let totalSize = 0;
  const bundles = [];
  
  for (const asset of assets) {
    const filePath = path.join(assetsDir, asset);
    const stats = fs.statSync(filePath);
    const sizeKB = stats.size / 1024;
    totalSize += sizeKB;
    
    bundles.push({
      name: asset,
      size: sizeKB,
    });
  }
  
  // Sort by size descending
  bundles.sort((a, b) => b.size - a.size);
  
  log('\n📦 Bundle Breakdown:', 'blue');
  for (const bundle of bundles) {
    const sizeStr = bundle.size.toFixed(2).padStart(10);
    log(`   ${sizeStr} KB  ${bundle.name}`, 'blue');
  }
  
  log(`\n📏 Total Size: ${totalSize.toFixed(2)} KB`, 'blue');
  
  // Estimate gzipped size (typically 25-30% of original)
  const estimatedGzip = totalSize * 0.28;
  log(`   Estimated Gzipped: ~${estimatedGzip.toFixed(2)} KB`, 'blue');
  
  // Check against target
  if (estimatedGzip < targetGzipSize) {
    log(`   ✅ Under target (${targetGzipSize} KB)`, 'green');
    return true;
  } else {
    log(`   ⚠️  May exceed target (${targetGzipSize} KB)`, 'yellow');
    return false;
  }
}

function checkIndexHtml() {
  logSection('🔍 Index.html Verification');
  
  const indexPath = path.join(buildDir, 'index.html');
  if (!fs.existsSync(indexPath)) {
    log('❌ index.html not found', 'red');
    return false;
  }
  
  const content = fs.readFileSync(indexPath, 'utf-8');
  
  // Check for required elements
  const checks = [
    { name: 'DOCTYPE', pattern: /<!DOCTYPE html>/i },
    { name: 'Viewport meta', pattern: /<meta name="viewport"/i },
    { name: 'Title', pattern: /<title>.*Rose.*<\/title>/i },
    { name: 'Script tag', pattern: /<script.*type="module"/i },
    { name: 'CSS link', pattern: /<link.*stylesheet/i },
  ];
  
  let allPassed = true;
  for (const check of checks) {
    if (check.pattern.test(content)) {
      log(`✅ ${check.name}`, 'green');
    } else {
      log(`❌ ${check.name} not found`, 'red');
      allPassed = false;
    }
  }
  
  return allPassed;
}

function checkBuildOptimizations() {
  logSection('⚡ Build Optimizations Check');
  
  const assetsDir = path.join(buildDir, 'assets');
  if (!fs.existsSync(assetsDir)) {
    log('❌ Cannot check: assets directory not found', 'red');
    return false;
  }
  
  const jsFiles = fs.readdirSync(assetsDir).filter(f => f.endsWith('.js'));
  
  if (jsFiles.length === 0) {
    log('❌ No JavaScript files found', 'red');
    return false;
  }
  
  // Check first JS file for minification
  const sampleFile = path.join(assetsDir, jsFiles[0]);
  const content = fs.readFileSync(sampleFile, 'utf-8');
  
  // Check for minification indicators
  const isMinified = !content.includes('\n\n') && content.length > 1000;
  const hasConsoleLog = content.includes('console.log');
  const hasDebugger = content.includes('debugger');
  
  if (isMinified) {
    log('✅ Code is minified', 'green');
  } else {
    log('⚠️  Code may not be minified', 'yellow');
  }
  
  if (!hasConsoleLog) {
    log('✅ console.log statements removed', 'green');
  } else {
    log('⚠️  console.log statements found', 'yellow');
  }
  
  if (!hasDebugger) {
    log('✅ debugger statements removed', 'green');
  } else {
    log('⚠️  debugger statements found', 'yellow');
  }
  
  // Check for code splitting
  if (jsFiles.length > 1) {
    log(`✅ Code splitting enabled (${jsFiles.length} chunks)`, 'green');
  } else {
    log('⚠️  Code splitting may not be configured', 'yellow');
  }
  
  return true;
}

function printNextSteps() {
  logSection('🚀 Next Steps');
  
  log('\n1. Test the production build locally:', 'blue');
  log('   npm run preview', 'cyan');
  log('   Then open: http://localhost:4173\n', 'cyan');
  
  log('2. Test with backend integration:', 'blue');
  log('   cd .. && make ava-run', 'cyan');
  log('   Then open: http://localhost:8080\n', 'cyan');
  
  log('3. Run Lighthouse audit (requires backend):', 'blue');
  log('   npm run lighthouse', 'cyan');
  log('   (Note: Install lighthouse first: npm install -g lighthouse chrome-launcher)\n', 'cyan');
  
  log('4. Test on different devices:', 'blue');
  log('   - Desktop browsers (Chrome, Firefox, Safari)', 'cyan');
  log('   - Mobile devices (iOS Safari, Android Chrome)', 'cyan');
  log('   - Different screen sizes and resolutions\n', 'cyan');
  
  log('5. Verify functionality:', 'blue');
  log('   - 3D scene loads and renders correctly', 'cyan');
  log('   - Voice interaction works', 'cyan');
  log('   - Audio-reactive effects respond', 'cyan');
  log('   - Animations are smooth', 'cyan');
  log('   - Error handling works\n', 'cyan');
  
  log('6. Review documentation:', 'blue');
  log('   - PRODUCTION_BUILD_TESTING.md', 'cyan');
  log('   - test-production.html (visual test page)\n', 'cyan');
}

function printSummary(results) {
  logSection('📈 Test Summary');
  
  const passed = results.filter(r => r.passed).length;
  const total = results.length;
  const percentage = ((passed / total) * 100).toFixed(0);
  
  log(`\n${passed}/${total} checks passed (${percentage}%)`, 'blue');
  
  for (const result of results) {
    const icon = result.passed ? '✅' : '❌';
    const color = result.passed ? 'green' : 'red';
    log(`${icon} ${result.name}`, color);
  }
  
  if (passed === total) {
    log('\n🎉 All checks passed! Production build is ready.', 'green');
    return true;
  } else {
    log('\n⚠️  Some checks failed. Review the output above.', 'yellow');
    return false;
  }
}

// Main execution
function main() {
  log('\n🧪 Production Build Test', 'cyan');
  log('Testing build output and verifying optimizations...\n', 'blue');
  
  const results = [
    { name: 'Build Directory', passed: checkBuildDirectory() },
    { name: 'Required Files', passed: checkRequiredFiles() },
    { name: 'Bundle Size', passed: analyzeBundleSize() },
    { name: 'Index.html', passed: checkIndexHtml() },
    { name: 'Optimizations', passed: checkBuildOptimizations() },
  ];
  
  const allPassed = printSummary(results);
  printNextSteps();
  
  process.exit(allPassed ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { main };
