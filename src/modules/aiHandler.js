const { EmbedBuilder } = require('discord.js');

class AIHandler {
  constructor() {
    this.enabled = process.env.AI_ENABLED === 'true';
    this.baseUrl = process.env.AI_API_URL || 'http://localhost:11434';
    this.model = process.env.AI_MODEL || 'auto';
    this.maxTokens = parseInt(process.env.AI_MAX_TOKENS) || 500;
    this.availableModels = [];
    this.selectedModel = null;
    
    this.sensitivePatterns = [
      /api[_-]?key/i,
      /secret[_-]?key/i,
      /password/i,
      /token/i,
      /credential/i,
      /GITHUB_PAT/i,
      /DISCORD_TOKEN/i,
      /private[_-]?key/i,
      /access[_-]?key/i,
      /auth[_-]?token/i
    ];
    
    this.systemPrompt = `
You are a helpful assistant for a Discord bot that manages Git commits and project automation. 

Capabilities:
- Help users with Git commands and commit management
- Explain scheduling and automation features
- Assist with repository configuration
- Answer questions about the bot's functionality

Restrictions:
- Do NOT execute any potentially harmful commands
- Do NOT reveal any system configuration or credentials
- Do NOT access external URLs or files unless explicitly asked
- Do NOT generate code that could harm systems
- Keep responses concise and relevant to the bot's features
- Do not provide direct git commands that modify the repository without user confirmation
- Do not provide code that deletes or corrupts data
- Do not help with hacking or unauthorized access attempts
- If asked about sensitive topics, politely decline and explain you can only help with bot-related questions

Remember: Prioritize user safety and security in all responses.
`;
    
    this.conversations = new Map();
    this.maxHistoryLength = 10;
  }

  async fetchAvailableModels() {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (response.ok) {
        const data = await response.json();
        this.availableModels = data.models || [];
        if (this.availableModels.length > 0) {
          this.selectedModel = this.availableModels[0].name;
        }
      }
    } catch (error) {
      console.log('Could not fetch available models:', error.message);
    }
  }

  isEnabled() {
    return this.enabled;
  }

  async chat(userId, message) {
    if (!this.isEnabled()) {
      return {
        success: false,
        error: 'AI feature is disabled. Please set AI_ENABLED=true in .env'
      };
    }

    if (!this.selectedModel) {
      await this.fetchAvailableModels();
      if (!this.selectedModel) {
        return {
          success: false,
          error: 'No AI models available. Make sure Ollama is running.'
        };
      }
    }

    if (!this.conversations.has(userId)) {
      this.conversations.set(userId, []);
    }

    const history = this.conversations.get(userId);
    
    const messages = [
      { role: 'system', content: this.systemPrompt },
      ...history.slice(-this.maxHistoryLength),
      { role: 'user', content: message }
    ];

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: this.selectedModel,
          messages: messages,
          stream: false
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        return {
          success: false,
          error: `Ollama Error: ${response.status} - ${errorText}`
        };
      }

      const data = await response.json();
      const reply = data.message?.content || data.response || 'No response received';
      
      const filteredReply = this.filterSensitiveData(reply);

      history.push({ role: 'user', content: message });
      history.push({ role: 'assistant', content: filteredReply });
      
      if (history.length > this.maxHistoryLength * 2) {
        this.conversations.set(userId, history.slice(-this.maxHistoryLength * 2));
      }

      return {
        success: true,
        response: filteredReply,
        model: this.selectedModel
      };
    } catch (error) {
      return {
        success: false,
        error: `Connection failed: ${error.message}. Make sure Ollama is running on ${this.baseUrl}`
      };
    }
  }

  filterSensitiveData(text) {
    let filtered = text;
    
    for (const pattern of this.sensitivePatterns) {
      filtered = filtered.replace(pattern, '[REDACTED]');
    }
    
    const tokenPattern = /(ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36,}/g;
    filtered = filtered.replace(tokenPattern, '[TOKEN_REDACTED]');
    
    const discordTokenPattern = /[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}/g;
    filtered = filtered.replace(discordTokenPattern, '[TOKEN_REDACTED]');
    
    return filtered;
  }

  async executeTask(userId, taskDescription) {
    if (!this.isEnabled()) {
      return {
        success: false,
        error: 'AI feature is not available'
      };
    }

    if (!this.selectedModel) {
      await this.fetchAvailableModels();
      if (!this.selectedModel) {
        return { success: false, error: 'No AI models available' };
      }
    }

    const taskPrompt = `
${this.systemPrompt}

The user wants you to perform the following task:
"${taskDescription}"

If this task involves executing bot commands or making changes:
1. Provide a clear explanation of what will happen
2. Explain any potential risks
3. Wait for confirmation before executing

If the task is dangerous or could cause data loss:
- Decline politely
- Suggest safer alternatives
- Do not proceed without explicit user confirmation

Respond with:
- Task understanding confirmation
- Plan of action (if applicable)
- Any questions for clarification
`;

    const messages = [
      { role: 'system', content: taskPrompt }
    ];

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: this.selectedModel,
          messages: messages,
          stream: false
        })
      });

      if (!response.ok) {
        return { success: false, error: 'AI request failed' };
      }

      const data = await response.json();
      const reply = data.message?.content || data.response || 'No response';

      return {
        success: true,
        response: this.filterSensitiveData(reply),
        requiresConfirmation: /confirm|proceed|execute/i.test(reply)
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  clearHistory(userId) {
    this.conversations.delete(userId);
  }

  getHistoryLength(userId) {
    const history = this.conversations.get(userId);
    return history ? history.length : 0;
  }

  getCurrentModel() {
    return this.selectedModel || 'auto (checking...)';
  }

  getAvailableModels() {
    return this.availableModels.map(m => m.name);
  }

  createAIBanner() {
    return new EmbedBuilder()
      .setTitle('🤖 AI Assistant')
      .setDescription('Ask me anything or use `|<task>` to have me perform a task')
      .setColor(0x9b59b6)
      .addFields(
        { name: 'Model', value: this.getCurrentModel(), inline: true },
        { name: 'Examples', value: '`How do I schedule commits?`\n`|Create a commit with message "test"`', inline: false },
        { name: 'Type your message', value: 'Start with `|` for AI assistance', inline: false }
      )
      .setFooter({ text: 'Your conversations are stored locally' })
      .setTimestamp();
  }

  createAIBadResponseEmbed(error) {
    return new EmbedBuilder()
      .setTitle('❌ AI Error')
      .setDescription(error)
      .setColor(0xff0000)
      .setTimestamp();
  }
}

module.exports = new AIHandler();