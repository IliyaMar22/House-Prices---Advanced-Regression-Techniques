# 🤖 Ollama Setup Guide - Free AI-Powered Financial Analysis

## 📋 Overview

This guide will help you set up **Ollama** for AI-powered financial analysis. Ollama is a **100% FREE**, **local**, and **private** AI platform that runs on your computer.

### **Why Ollama?**

- ✅ **100% Free** - No API costs, ever
- ✅ **Private** - Your financial data never leaves your computer
- ✅ **No Rate Limits** - Analyze as much as you want
- ✅ **Offline** - Works without internet connection
- ✅ **Fast** - Runs on your GPU/CPU

---

## 🚀 Installation Steps

### **Step 1: Download Ollama**

**For macOS:**
```bash
# Visit https://ollama.ai and download the macOS app
# OR install via Homebrew:
brew install ollama
```

**For Windows:**
```bash
# Download from: https://ollama.ai/download/windows
# Run the installer
```

**For Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### **Step 2: Start Ollama**

**macOS:**
- Open the Ollama app from Applications
- OR run in terminal: `ollama serve`

**Windows:**
- Ollama runs automatically after installation
- Check system tray for Ollama icon

**Linux:**
```bash
ollama serve
```

### **Step 3: Download AI Model**

Open a terminal and run:

```bash
# Download Llama 3.1 8B (Recommended - ~4.7GB)
ollama pull llama3.1:8b

# Alternative: Smaller model for faster analysis
ollama pull llama3.1:3b

# Alternative: Larger model for better analysis (if you have 16GB+ RAM)
ollama pull llama3.1:70b
```

**Note:** The first download will take 5-15 minutes depending on your internet speed.

### **Step 4: Verify Installation**

```bash
# Check if Ollama is running
ollama list

# Test the model
ollama run llama3.1:8b "Analyze this financial data: Revenue 19.95M, OPEX 4.77M, Equity 14.46M"
```

If you see a response, you're ready! ✅

---

## 💻 System Requirements

### **Minimum Requirements:**
- **RAM:** 8GB (for 8B models)
- **Disk Space:** 5GB free
- **OS:** macOS 11+, Windows 10+, or Linux

### **Recommended:**
- **RAM:** 16GB+ (for 70B models or faster processing)
- **GPU:** Optional, but speeds up analysis
- **Disk Space:** 10GB+ (for multiple models)

---

## 🎯 Running the Analysis

Once Ollama is installed and running:

```bash
# Navigate to the project directory
cd /Users/bilyana/Downloads/.github-main/profile/financial-review-pipeline

# Run the LLM-powered analysis
python3 bulgarian_llm_analysis.py
```

### **What the AI Will Generate:**

1. **Executive Summary** - AI-generated overview of financial health
2. **Key Insights** - 5-7 intelligent insights about performance
3. **Risk Assessment** - AI analysis of financial risks
4. **Recommendations** - Actionable suggestions for improvement
5. **Trend Analysis** - AI-detected patterns and trends
6. **Q&A System** - Ask questions about your financial data

---

## 🔧 Troubleshooting

### **Issue: "Ollama not found"**
**Solution:**
```bash
# Check if Ollama is installed
which ollama

# If not found, reinstall from https://ollama.ai
```

### **Issue: "Connection refused"**
**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, run the analysis
python3 bulgarian_llm_analysis.py
```

### **Issue: "Model not found"**
**Solution:**
```bash
# Pull the model
ollama pull llama3.1:8b

# Verify it's downloaded
ollama list
```

### **Issue: "Out of memory"**
**Solution:**
```bash
# Use a smaller model
ollama pull llama3.1:3b

# Update bulgarian_llm_analysis.py to use smaller model:
# Change: model="llama3.1:8b" to model="llama3.1:3b"
```

---

## 📊 Available Models

### **Recommended for Financial Analysis:**

| Model | Size | RAM Required | Speed | Quality |
|-------|------|--------------|-------|---------|
| **llama3.1:8b** | ~4.7GB | 8GB | Fast | Excellent ⭐ |
| llama3.1:3b | ~2GB | 4GB | Very Fast | Good |
| llama3.1:70b | ~40GB | 64GB | Slow | Best |
| qwen2.5:7b | ~4.4GB | 8GB | Fast | Excellent |
| mistral:7b | ~4.1GB | 8GB | Fast | Very Good |
| phi3:3.8b | ~2.3GB | 4GB | Very Fast | Good |

### **Download Multiple Models:**

```bash
# For best results
ollama pull llama3.1:8b

# For faster analysis (lighter model)
ollama pull llama3.1:3b

# For financial-specific tasks
ollama pull qwen2.5:7b
```

---

## 🌐 Alternative: Using Free Cloud APIs

If you can't run Ollama locally, you can use these free cloud options:

### **Option 1: Google Gemini (Free)**
```python
# Install: pip install google-generativeai
import google.generativeai as genai

genai.configure(api_key='YOUR_FREE_API_KEY')
model = genai.GenerativeModel('gemini-pro')
```
- **Free Tier:** 60 requests/minute
- **Get API Key:** https://makersuite.google.com/app/apikey

### **Option 2: Groq (Free)**
```python
# Install: pip install groq
from groq import Groq

client = Groq(api_key='YOUR_FREE_API_KEY')
```
- **Free Tier:** Very generous
- **Get API Key:** https://console.groq.com

### **Option 3: OpenRouter (Free Tier)**
```python
# Install: pip install openai
import openai

openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = 'YOUR_FREE_API_KEY'
```
- **Free Tier:** Access to multiple models
- **Get API Key:** https://openrouter.ai

---

## 🎯 Next Steps

1. **Install Ollama** following the steps above
2. **Download a model** (recommended: llama3.1:8b)
3. **Run the analysis:**
   ```bash
   python3 bulgarian_llm_analysis.py
   ```
4. **Review the AI-generated insights** in the markdown report

---

## 📞 Support

**Issues with Ollama?**
- Visit: https://github.com/ollama/ollama/issues
- Discord: https://discord.gg/ollama

**Issues with the Analysis?**
- Check the terminal output for error messages
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Try a different model if you're having memory issues

---

## 🎉 Success!

Once everything is working, you'll have:
- ✅ **AI-powered financial insights** generated automatically
- ✅ **Context-aware analysis** understanding your business
- ✅ **100% privacy** - no data sent to cloud
- ✅ **$0 cost** - completely free forever

**Enjoy your AI-powered financial analysis!** 🚀

