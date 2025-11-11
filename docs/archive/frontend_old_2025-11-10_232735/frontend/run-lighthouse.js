/**
 * Lighthouse Audit Script
 * 
 * Runs Lighthouse performance audit on the production build
 * and generates a detailed report.
 * 
 * Usage:
 *   node run-lighthouse.js [url]
 * 
 * Default URL: http://localhost:8080
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

// Configuration
const url = process.argv[2] || 'http://localhost:8080';
const outputDir = path.join(__dirname, 'lighthouse-reports');

// Lighthouse configuration
const lighthouseConfig = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
    screenEmulation: {
      mobile: false,
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
      disabled: false,
    },
  },
};

// Mobile configuration
const mobileConfig = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    formFactor: 'mobile',
    throttling: {
      rttMs: 150,
      throughputKbps: 1638.4,
      cpuSlowdownMultiplier: 4,
    },
    screenEmulation: {
      mobile: true,
      width: 375,
      height: 667,
      deviceScaleFactor: 2,
      disabled: false,
    },
  },
};

async function runLighthouse(url, config, label) {
  console.log(`\n🔍 Running Lighthouse audit for ${label}...`);
  console.log(`   URL: ${url}`);
  
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  const options = {
    logLevel: 'info',
    output: ['html', 'json'],
    port: chrome.port,
  };

  try {
    const runnerResult = await lighthouse(url, options, config);

    // Extract scores
    const { lhr } = runnerResult;
    const scores = {
      performance: lhr.categories.performance.score * 100,
      accessibility: lhr.categories.accessibility.score * 100,
      bestPractices: lhr.categories['best-practices'].score * 100,
      seo: lhr.categories.seo.score * 100,
    };

    // Print scores
    console.log(`\n📊 ${label} Scores:`);
    console.log(`   Performance:     ${scores.performance.toFixed(0)} ${getScoreEmoji(scores.performance)}`);
    console.log(`   Accessibility:   ${scores.accessibility.toFixed(0)} ${getScoreEmoji(scores.accessibility)}`);
    console.log(`   Best Practices:  ${scores.bestPractices.toFixed(0)} ${getScoreEmoji(scores.bestPractices)}`);
    console.log(`   SEO:             ${scores.seo.toFixed(0)} ${getScoreEmoji(scores.seo)}`);

    // Print key metrics
    const metrics = lhr.audits.metrics.details.items[0];
    console.log(`\n⏱️  ${label} Metrics:`);
    console.log(`   First Contentful Paint:  ${metrics.firstContentfulPaint}ms`);
    console.log(`   Largest Contentful Paint: ${metrics.largestContentfulPaint}ms`);
    console.log(`   Time to Interactive:      ${metrics.interactive}ms`);
    console.log(`   Speed Index:              ${metrics.speedIndex}ms`);
    console.log(`   Total Blocking Time:      ${metrics.totalBlockingTime}ms`);
    console.log(`   Cumulative Layout Shift:  ${metrics.cumulativeLayoutShift.toFixed(3)}`);

    // Save reports
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const htmlPath = path.join(outputDir, `${label.toLowerCase().replace(' ', '-')}-${timestamp}.html`);
    const jsonPath = path.join(outputDir, `${label.toLowerCase().replace(' ', '-')}-${timestamp}.json`);

    fs.writeFileSync(htmlPath, runnerResult.report[0]);
    fs.writeFileSync(jsonPath, runnerResult.report[1]);

    console.log(`\n💾 Reports saved:`);
    console.log(`   HTML: ${htmlPath}`);
    console.log(`   JSON: ${jsonPath}`);

    return scores;
  } catch (error) {
    console.error(`\n❌ Error running Lighthouse for ${label}:`, error.message);
    return null;
  } finally {
    await chrome.kill();
  }
}

function getScoreEmoji(score) {
  if (score >= 90) return '✅';
  if (score >= 50) return '⚠️';
  return '❌';
}

function printSummary(desktopScores, mobileScores) {
  console.log('\n' + '='.repeat(60));
  console.log('📈 LIGHTHOUSE AUDIT SUMMARY');
  console.log('='.repeat(60));

  if (desktopScores) {
    console.log('\n🖥️  Desktop:');
    console.log(`   Overall: ${getOverallScore(desktopScores).toFixed(0)} ${getScoreEmoji(getOverallScore(desktopScores))}`);
  }

  if (mobileScores) {
    console.log('\n📱 Mobile:');
    console.log(`   Overall: ${getOverallScore(mobileScores).toFixed(0)} ${getScoreEmoji(getOverallScore(mobileScores))}`);
  }

  console.log('\n🎯 Targets:');
  console.log('   Performance:    > 90 ✓');
  console.log('   Accessibility:  > 90 ✓');
  console.log('   Best Practices: > 90 ✓');
  console.log('   SEO:            > 80 ✓');

  console.log('\n📁 Reports saved to: ' + outputDir);
  console.log('='.repeat(60) + '\n');
}

function getOverallScore(scores) {
  return (scores.performance + scores.accessibility + scores.bestPractices + scores.seo) / 4;
}

async function main() {
  console.log('🚀 Starting Lighthouse Audit');
  console.log('   Make sure the backend server is running on port 8080');
  console.log('   Run: make ava-run (from project root)');

  // Check if server is running
  try {
    const http = require('http');
    await new Promise((resolve, reject) => {
      const req = http.get(url, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          reject(new Error(`Server returned status ${res.statusCode}`));
        }
      });
      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Connection timeout'));
      });
    });
  } catch (error) {
    console.error(`\n❌ Cannot connect to ${url}`);
    console.error('   Make sure the backend server is running:');
    console.error('   1. cd to project root');
    console.error('   2. Run: make ava-run');
    console.error('   3. Wait for server to start');
    console.error('   4. Run this script again\n');
    process.exit(1);
  }

  // Run audits
  const desktopScores = await runLighthouse(url, lighthouseConfig, 'Desktop');
  const mobileScores = await runLighthouse(url, mobileConfig, 'Mobile');

  // Print summary
  printSummary(desktopScores, mobileScores);
}

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { runLighthouse };
