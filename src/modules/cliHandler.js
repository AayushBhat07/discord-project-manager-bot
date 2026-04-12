const { githubConnector, timestampProcessor, schedulerService, patternEngine } = require('./commitScheduler');
const sessionManager = require('./sessionManager');
const bannerUI = require('./bannerUI');
const aiHandler = require('./aiHandler');
const userConfigManager = require('./userConfigManager');

class CLIHandler {
  constructor() {
    this.commands = new Map();
    this.initializeCommands();
  }

  initializeCommands() {
    this.commands.set('showoptions', { handler: this.handleShowOptions.bind(this), description: 'Show the main banner with buttons' });
    this.commands.set('pastcommit', { handler: this.handlePastCommit.bind(this), description: 'Create a backdated commit' });
    this.commands.set('commitnow', { handler: this.handleCommitNow.bind(this), description: 'Create an immediate commit' });
    this.commands.set('schedule', { handler: this.handleSchedule.bind(this), description: 'Schedule recurring commits' });
    this.commands.set('pattern', { handler: this.handlePattern.bind(this), description: 'Generate pattern commits' });
    this.commands.set('cancel', { handler: this.handleCancel.bind(this), description: 'Cancel a scheduled job' });
    this.commands.set('commits', { handler: this.handleCommits.bind(this), description: 'List scheduled jobs' });
    this.commands.set('mystats', { handler: this.handleStats.bind(this), description: 'Show your session statistics' });
    this.commands.set('setrepo', { handler: this.handleSetRepo.bind(this), description: 'Configure your repository' });
    this.commands.set('detailed', { handler: this.handleDetailed.bind(this), description: 'Show detailed command information' });
    this.commands.set('help', { handler: this.handleHelp.bind(this), description: 'Show help information' });
    this.commands.set('start', { handler: this.handleStart.bind(this), description: 'Start a new session' });
    this.commands.set('ai-chat', { handler: this.handleAIChat.bind(this), description: 'Chat with AI assistant' });
    this.commands.set('setup', { handler: this.handleSetup.bind(this), description: 'Setup your GitHub credentials' });
    this.commands.set('mygithub', { handler: this.handleMyGitHub.bind(this), description: 'View your GitHub configuration' });
    this.commands.set('clearhistory', { handler: this.handleClearHistory.bind(this), description: 'Clear AI chat history' });
  }

  parseCommand(message) {
    const content = message.trim();
    
    if (!content.startsWith('!') && !content.startsWith('|')) return null;

    const isAI = content.startsWith('|');
    const prefix = isAI ? '|' : '!';
    const parts = content.slice(1).split(' ');
    const command = isAI ? 'ai-chat' : parts[0].toLowerCase();
    const args = parts.slice(1);

    return { command, args, fullArgs: parts.slice(1).join(' '), isAI };
  }

  async handle(message) {
    const parsed = this.parseCommand(message.content);
    if (!parsed) return null;

    const cmd = this.commands.get(parsed.command);
    if (!cmd) return null;

    try {
      return await cmd.handler(message, parsed.args, parsed);
    } catch (error) {
      console.error('CLI Command Error:', error);
      return bannerUI.createErrorEmbed('Command Error', error.message);
    }
  }

  async handleShowOptions(message) {
    const embed = bannerUI.createMainBanner(message.author.username);
    const buttons = bannerUI.createFeatureButtons();
    
    return {
      embeds: [embed],
      components: buttons
    };
  }

  async handlePastCommit(message, args) {
    if (args.length < 2) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !pastcommit <date> <time> "<message>"\nExample: !pastcommit 2024-01-15 14:30 "Fixed bug"');
    }

    const lastQuoteIndex = message.content.lastIndexOf('"');
    let msgArgs = [];
    
    for (let i = 0; i < args.length; i++) {
      if (args[i].startsWith('"') && args[i].length > 1) {
        const remaining = args.slice(i).join(' ');
        const endQuote = remaining.indexOf('"', 1);
        if (endQuote > -1) {
          msgArgs.push(remaining.slice(1, endQuote));
          break;
        }
      }
    }

    if (msgArgs.length === 0) {
      msgArgs = [args.slice(2).join(' ')];
    }

    const dateInput = args[0];
    const timeInput = args[1] && !args[1].includes('"') ? args[1] : null;
    const commitMessage = msgArgs[0] || args.slice(2).join(' ');

    if (!commitMessage) {
      return bannerUI.createErrorEmbed('Missing Message', 'Please provide a commit message');
    }

    let timestamp;
    try {
      const datePart = timeInput ? `${dateInput} ${timeInput}` : dateInput;
      const validation = timestampProcessor.validate(datePart);
      if (!validation.valid) {
        return bannerUI.createErrorEmbed('Invalid Date', validation.error);
      }
      timestamp = timestampProcessor.toISOString(validation.parsed);
    } catch (error) {
      return bannerUI.createErrorEmbed('Date Parsing Error', error.message);
    }

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      return bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'));
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      return bannerUI.createErrorEmbed('Initialization Failed', error.message);
    }

    const result = await githubConnector.createCommit(commitMessage, timestamp);

    if (result.success) {
      const session = sessionManager.getActiveSession(message.author.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message: commitMessage, type: 'backdated', success: true });
      }
      return bannerUI.createSuccessEmbed('Backdated Commit Created', `Successfully created commit: "${commitMessage}"`, [
        { name: '📅 Commit Date', value: new Date(timestamp).toLocaleString(), inline: true },
        { name: '🔢 Timestamp', value: timestamp, inline: true }
      ]);
    } else {
      return bannerUI.createErrorEmbed('Commit Failed', result.error);
    }
  }

  async handleCommitNow(message, args) {
    if (args.length === 0) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !commitnow "<message>"\nExample: !commitnow "Added new feature"');
    }

    const content = message.content.slice(message.content.indexOf(args[0]) - 1);
    const match = content.match(/"([^"]+)"/);
    const commitMessage = match ? match[1] : args.join(' ');

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      return bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'));
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      return bannerUI.createErrorEmbed('Initialization Failed', error.message);
    }

    const result = await githubConnector.createCommit(commitMessage, new Date().toISOString());

    if (result.success) {
      const session = sessionManager.getActiveSession(message.author.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message: commitMessage, type: 'normal', success: true });
      }
      return bannerUI.createSuccessEmbed('Commit Created', `Successfully created commit: "${commitMessage}"`, [
        { name: '📅 Timestamp', value: new Date().toISOString(), inline: true },
        { name: '📤 Pushed', value: result.pushed ? 'Yes' : 'No', inline: true }
      ]);
    } else {
      return bannerUI.createErrorEmbed('Commit Failed', result.error);
    }
  }

  async handleSchedule(message, args) {
    if (args.length < 2) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !schedule "<cron>" "<message>"\nExample: !schedule "0 9 * * 1" "Weekly report"');
    }

    const cronMatch = message.content.match(/"([^"]+)"/g);
    if (!cronMatch || cronMatch.length < 2) {
      return bannerUI.createErrorEmbed('Format Error', 'Use quotes for cron expression and message\nExample: !schedule "0 9 * * 1" "Weekly report"');
    }

    const cronExpr = cronMatch[0].replace(/"/g, '');
    const commitMessage = cronMatch[1].replace(/"/g, '');

    if (!schedulerService.validateCronExpression(cronExpr)) {
      return bannerUI.createErrorEmbed('Invalid Cron', 'Please provide a valid cron expression\nExample: 0 9 * * 1 (every Monday at 9am)');
    }

    const result = schedulerService.createJob(message.author.id, cronExpr, commitMessage);

    if (result.success) {
      const session = sessionManager.getActiveSession(message.author.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message: commitMessage, type: 'scheduled', success: true });
      }
      return bannerUI.createSuccessEmbed('Schedule Created', `Scheduled commit: "${commitMessage}"`, [
        { name: '🆔 Job ID', value: result.job.id, inline: true },
        { name: '⏰ Schedule', value: cronExpr, inline: true },
        { name: '📊 Status', value: result.job.status, inline: true }
      ]);
    } else {
      return bannerUI.createErrorEmbed('Schedule Failed', result.error);
    }
  }

  async handlePattern(message, args) {
    if (args.length < 2) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !pattern <template> "<message>"\nExample: !pattern heart "contribution"');
    }

    const template = args[0].toLowerCase();
    const content = message.content.slice(message.content.indexOf(args[1]) - 1);
    const match = content.match(/"([^"]+)"/);
    const commitMessage = match ? match[1] : args.slice(1).join(' ');

    const preview = patternEngine.previewPattern(template);
    if (!preview.success) {
      return bannerUI.createErrorEmbed('Template Error', preview.error + '\nAvailable: A, B, C, heart, star, check, smiley');
    }

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      return bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'));
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      return bannerUI.createErrorEmbed('Initialization Failed', error.message);
    }

    const result = await patternEngine.executePattern(template, commitMessage, { push: true, delayBetweenCommits: 1000 });

    if (result.success) {
      const session = sessionManager.getActiveSession(message.author.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message: `Pattern: ${template}`, type: 'pattern', success: true });
      }
      return bannerUI.createSuccessEmbed('Pattern Commits Complete', `Created ${result.succeeded} commits using ${template} pattern`, [
        { name: '📊 Summary', value: `Succeeded: ${result.succeeded}, Failed: ${result.failed}`, inline: true }
      ]);
    } else {
      return bannerUI.createErrorEmbed('Pattern Failed', `Succeeded: ${result.succeeded}, Failed: ${result.failed}`);
    }
  }

  async handleCancel(message, args) {
    if (args.length === 0) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !cancel <job-id>\nUse !commits to see job IDs');
    }

    const jobId = args[0];
    const job = schedulerService.getJob(jobId);

    if (!job) {
      return bannerUI.createErrorEmbed('Job Not Found', `No scheduled job found with ID: ${jobId}`);
    }

    if (job.ownerId !== message.author.id) {
      return bannerUI.createErrorEmbed('Permission Denied', 'You can only cancel jobs you created');
    }

    const result = schedulerService.cancelJob(jobId);

    if (result.success) {
      return bannerUI.createSuccessEmbed('Schedule Cancelled', `Job ${jobId} has been stopped`, [
        { name: 'Message', value: job.message, inline: true },
        { name: 'Schedule', value: job.cronExpression, inline: true }
      ]);
    } else {
      return bannerUI.createErrorEmbed('Cancel Failed', result.error);
    }
  }

  async handleCommits(message, args) {
    const jobs = schedulerService.listJobs({ ownerId: message.author.id, limit: 10 });

    if (jobs.length === 0) {
      return bannerUI.createInfoEmbed('No Scheduled Jobs', 'You have no scheduled commit jobs. Use !schedule to create one!');
    }

    const embed = new EmbedBuilder()
      .setTitle('📋 Your Scheduled Jobs')
      .setDescription(`Showing ${jobs.length} job(s)`)
      .setColor(0x0099ff)
      .setTimestamp();

    jobs.forEach(job => {
      embed.addFields({
        name: `🆔 ${job.id.substring(0, 8)}...`,
        value: `**Message:** ${job.message}\n**Schedule:** \`${job.cronExpression}\`\n**Status:** ${job.status}\n**Next:** ${job.nextRun ? new Date(job.nextRun).toLocaleString() : 'N/A'}`,
        inline: false
      });
    });

    return embed;
  }

  async handleStats(message) {
    const stats = sessionManager.getSessionStats(message.author.id);

    return new EmbedBuilder()
      .setTitle('📊 Your Session Statistics')
      .setDescription('Statistics across all your sessions (last 30 days)')
      .setColor(0x00ccff)
      .addFields(
        { name: '📅 Total Sessions', value: stats.totalSessions.toString(), inline: true },
        { name: '✅ Active Sessions', value: stats.activeSessions.toString(), inline: true },
        { name: '📝 Total Commits', value: stats.totalCommits.toString(), inline: true },
        { name: '⏰ Backdated Commits', value: stats.backdatedCommits.toString(), inline: true },
        { name: '📅 Scheduled Commits', value: stats.scheduledCommits.toString(), inline: true },
        { name: '🎨 Pattern Commits', value: stats.patternCommits.toString(), inline: true },
        { name: '🕐 Oldest Session', value: stats.oldestSession ? new Date(stats.oldestSession).toLocaleDateString() : 'N/A', inline: true },
        { name: '🆕 Newest Session', value: stats.newestSession ? new Date(stats.newestSession).toLocaleDateString() : 'N/A', inline: true }
      )
      .setTimestamp();
  }

  async handleSetRepo(message, args) {
    if (args.length === 0) {
      return bannerUI.createErrorEmbed('Missing Arguments', 'Usage: !setrepo <path> or !setrepo github <owner/repo>\nExample: !setrepo ./myrepo\nExample: !setrepo github username/repo');
    }

    if (args[0].toLowerCase() === 'github' && args[1]) {
      const repoPath = args[1];
      githubConnector.configure({
        repoPath: `./${repoPath.replace('/', '-')}`,
        branch: args[2] || 'main',
        remote: 'origin'
      });
      return bannerUI.createSuccessEmbed('Repository Configured', `GitHub repository set to: ${repoPath}`, [
        { name: '📁 Repository', value: repoPath, inline: true },
        { name: '🌿 Branch', value: args[2] || 'main', inline: true }
      ]);
    } else {
      const repoPath = args[0];
      githubConnector.configure({
        repoPath: repoPath,
        branch: args[1] || 'main',
        remote: 'origin'
      });
      return bannerUI.createSuccessEmbed('Repository Configured', `Local repository set to: ${repoPath}`, [
        { name: '📁 Path', value: repoPath, inline: true },
        { name: '🌿 Branch', value: args[1] || 'main', inline: true }
      ]);
    }
  }

  async handleDetailed(message) {
    return bannerUI.createDetailedHelpEmbed();
  }

  async handleHelp(message) {
    return bannerUI.createFeaturesListEmbed();
  }

  async handleStart(message) {
    let session = sessionManager.getActiveSession(message.author.id);
    
    if (session) {
      return bannerUI.createInfoEmbed('Session Active', `You already have an active session started at ${new Date(session.startTime).toLocaleString()}`);
    }

    const config = githubConnector.config;
    session = sessionManager.createSession(message.author.id, message.author.username, {
      repoPath: config.repoPath,
      repoRemote: config.remote,
      branch: config.branch
    });

    return bannerUI.createSuccessEmbed('🎉 Session Started!', `Welcome ${message.author.username}! Your session has been created.`, [
      { name: '🆔 Session ID', value: session.id, inline: true },
      { name: '📅 Started At', value: new Date(session.startTime).toLocaleString(), inline: true },
      { name: '⏰ Duration', value: '30 days (auto-expires)', inline: true }
    ]);
  }

  async handleAIChat(message, args, parsed) {
    if (!aiHandler.isEnabled()) {
      return aiHandler.createAIBadResponseEmbed('AI is not enabled. Please set AI_ENABLED=true in .env');
    }

    const userMessage = parsed.fullArgs || '';
    
    if (!userMessage.trim()) {
      const embed = aiHandler.createAIBanner();
      return embed;
    }

    const userId = message.author.id;
    const result = await aiHandler.chat(userId, userMessage);

    if (result.success) {
      const chunks = this.splitMessage(result.response);
      
      if (chunks.length === 1) {
        return new EmbedBuilder()
          .setTitle('🤖 AI Response')
          .setDescription(result.response)
          .setColor(0x9b59b6)
          .setTimestamp();
      }
      
      const embeds = chunks.map((chunk, index) => 
        new EmbedBuilder()
          .setTitle(index === 0 ? '🤖 AI Response' : '📄 (continued)')
          .setDescription(chunk)
          .setColor(0x9b59b6)
          .setTimestamp()
      );
      
      return embeds;
    } else {
      return aiHandler.createAIBadResponseEmbed(result.error);
    }
  }

  splitMessage(text, maxLength = 2000) {
    const chunks = [];
    if (text.length <= maxLength) {
      return [text];
    }
    
    const parts = text.split('\n');
    let current = '';
    
    for (const part of parts) {
      if ((current + '\n' + part).length <= maxLength) {
        current += (current ? '\n' : '') + part;
      } else {
        if (current) chunks.push(current);
        if (part.length > maxLength) {
          const subParts = [];
          while (part.length > maxLength) {
            subParts.push(part.slice(0, maxLength));
            part = part.slice(maxLength);
          }
          current = part;
          chunks.push(...subParts.slice(0, -1));
        } else {
          current = part;
        }
      }
    }
    
    if (current) chunks.push(current);
    return chunks;
  }

  async handleSetup(message, args) {
    if (args.length < 2) {
      return bannerUI.createErrorEmbed('Missing Arguments', 
        'Usage: !setup github <github-pat> <repo-url> [branch]\n' +
        'Example: !setup github ghp_xxx https://github.com/user/repo main'
      );
    }

    if (args[0].toLowerCase() !== 'github') {
      return bannerUI.createErrorEmbed('Invalid Setup', 'Currently only GitHub setup is supported\nUse: !setup github <pat> <repo-url> [branch]');
    }

    const pat = args[1];
    const repoUrl = args[2];
    const branch = args[3] || 'main';

    const userId = message.author.id;
    let config = userConfigManager.getUserConfig(userId);
    
    if (!config) {
      config = userConfigManager.createUserConfig(userId, message.author.username);
    }

    const result = userConfigManager.setRepoConfig(userId, repoUrl, branch, 'origin');
    if (!result.success) {
      return bannerUI.createErrorEmbed('Setup Failed', result.error);
    }

    userConfigManager.setGitHubPAT(userId, pat);

    return bannerUI.createSuccessEmbed('✅ GitHub Setup Complete!', 
      `Your GitHub credentials have been saved securely.`, [
        { name: '📁 Repository', value: repoUrl, inline: true },
        { name: '🌿 Branch', value: branch, inline: true },
        { name: '🔐 Status', value: 'Credentials saved', inline: true }
      ]
    );
  }

  async handleMyGitHub(message) {
    const userId = message.author.id;
    const config = userConfigManager.getUserConfig(userId);

    if (!config) {
      return bannerUI.createInfoEmbed('No Setup Found', 
        'You haven\'t configured your GitHub yet.\nUse `!setup github <pat> <repo-url>` to set up.'
      );
    }

    const hasSetup = userConfigManager.hasGitHubSetup(userId);

    return new EmbedBuilder()
      .setTitle('📡 Your GitHub Configuration')
      .setColor(hasSetup ? 0x00ff00 : 0xffaa00)
      .addFields(
        { name: '🔐 PAT Configured', value: hasSetup ? '✅ Yes' : '❌ No', inline: true },
        { name: '📁 Repository', value: config.github?.repoPath || 'Not set', inline: true },
        { name: '🌿 Branch', value: config.github?.branch || 'main', inline: true },
        { name: '🔗 Remote', value: config.github?.remote || 'origin', inline: true },
        { name: '📅 Last Updated', value: new Date(config.updatedAt).toLocaleString(), inline: true }
      )
      .setTimestamp();
  }

  async handleClearHistory(message) {
    const userId = message.author.id;
    aiHandler.clearHistory(userId);
    
    return bannerUI.createSuccessEmbed('🗑️ Chat History Cleared', 
      'Your AI conversation history has been reset.'
    );
  }
}

const { EmbedBuilder } = require('discord.js');
module.exports = new CLIHandler();