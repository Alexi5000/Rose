# 🔧 Frontend CSS/JS Not Loading - Fix Guide

## 🔍 Problem

The frontend at http://localhost:3002 is loading the HTML but CSS and JavaScript modules are not rendering. The page shows only the title "ROSE THE HEALER SHAMAN" without styling or functionality.

## 🎯 Root Cause

The Vite dev server is running on port 3002, but there's likely a module loading issue. This can happen when:
1. Vite's HMR (Hot Module Replacement) websocket can't connect
2. Module imports are failing
3. Browser cache is stale
4. TypeScript compilation errors

## ✅ Solution Steps

### Step 1: Clear Browser Cache

**In your browser:**
1. Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
2. Select "Cached images and files"
3. Click "Clear data"
4. **OR** do a hard refresh: `Ctrl + Shift + R` (or `Cmd + Shift + R`)

### Step 2: Check Browser Console

1. Press `F12` to open DevTools
2. Go to the **Console** tab
3. Look for errors (red text)
4. Take a screenshot and share any errors you see

Common errors to look for:
- `Failed to load module`
- `CORS error`
- `WebSocket connection failed`
- `TypeScript compilation error`

### Step 3: Restart Frontend with Clean Build

```powershell
# Stop the current dev server (Ctrl+C in terminal)

# Clean node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install

# Clear Vite cache
Remove-Item -Recurse -Force node_modules/.vite

# Start fresh
npm run dev
```

### Step 4: Access Correct URL

Make sure you're accessing:
```
http://localhost:3002
```

NOT:
- ~~http://localhost:3000~~ (port might be in use)
- ~~http://localhost:8000~~ (that's the backend)

### Step 5: Check Network Tab

1. Open DevTools (`F12`)
2. Go to **Network** tab
3. Refresh the page (`F5`)
4. Look for failed requests (red status codes)
5. Check if `/src/main.tsx` is loading

## 🚀 Quick Fix Script

I'll create a script to restart everything cleanly:

```powershell
# Stop current servers
# Press Ctrl+C in the terminal

# Run this:
python scripts/restart_dev_clean.py
```

## 🔍 Diagnostic Commands

Run these to check what's happening:

```powershell
# Check if Vite is running
netstat -ano | findstr ":3002"

# Check Vite process
Get-Process | Where-Object {$_.ProcessName -like "*node*"}

# Test Vite server
Invoke-WebRequest -Uri "http://localhost:3002" -UseBasicParsing

# Check for TypeScript errors
cd frontend
npx tsc --noEmit
```

## 📊 Expected Behavior

When working correctly, you should see:

1. **In Browser:**
   - Beautiful 3D ice cave scene
   - Aurora borealis effect
   - Voice button at bottom
   - Smooth animations
   - Settings panel in top right

2. **In Console:**
   - `🔌 Initializing API client with base URL: http://localhost:8000/api/v1`
   - `✅ Connected to Rose API version: 1.0.0`
   - No red errors

3. **In Network Tab:**
   - All requests return 200 OK
   - `/src/main.tsx` loads successfully
   - CSS files load
   - Three.js modules load

## 🆘 If Still Not Working

### Option 1: Use Production Build

```powershell
# Build frontend
cd frontend
npm run build
cd ..

# Access via backend
# Open: http://localhost:8000
```

### Option 2: Check for Port Conflicts

```powershell
# See what's using ports
netstat -ano | findstr ":3000 :3001 :3002"

# Kill conflicting processes
taskkill /PID <PID> /F
```

### Option 3: Try Different Browser

- Chrome/Edge: Best compatibility
- Firefox: Good alternative
- Safari: May have issues with WebGL

## 📸 What to Share for Help

If still having issues, share:

1. **Screenshot of browser showing the issue**
2. **Browser console errors** (F12 → Console tab)
3. **Network tab** (F12 → Network tab, refresh page)
4. **Terminal output** where dev server is running
5. **Output of:** `cd frontend && npx tsc --noEmit`

## 🎯 Most Likely Fix

Based on the screenshot, the most likely fix is:

**Hard refresh the browser:**
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

This clears the browser cache and forces a fresh load of all assets.

---

**Let me know what errors you see in the browser console and I'll help fix them!**
