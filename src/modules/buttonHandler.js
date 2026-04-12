const { githubConnector, timestampProcessor, schedulerService, patternEngine } = require('./commitScheduler');
const sessionManager = require('./sessionManager');
const bannerUI = require('./bannerUI');

class ButtonHandler {
  constructor() {
    this.handlers = new Map();
    this.initializeHandlers();
  }

  initializeHandlers() {
    this.handlers.set('btn_commit_now', this.handleCommitNow.bind(this));
    this.handlers.set('btn_commit_past', this.handleCommitPast.bind(this));
    this.handlers.set('btn_commit_schedule', this.handleSchedule.bind(this));
    this.handlers.set('btn_pattern', this.handlePattern.bind(this));
    this.handlers.set('btn_stats', this.handleStats.bind(this));
    this.handlers.set('btn_repo', this.handleRepo.bind(this));
    this.handlers.set('btn_commits', this.handleJobs.bind(this));
    this.handlers.set('btn_help', this.handleHelp.bind(this));
    this.handlers.set('btn_back', this.handleBack.bind(this));
  }

  handle(customId, interaction) {
    const handler = this.handlers.get(customId);
    if (handler) {
      return handler(interaction);
    }
    return { handled: false };
  }

  async handleCommitNow(interaction) {
    const modal = bannerUI.createCommitNowModal();
    await interaction.showModal(modal);
    return { handled: true, modal: true };
  }

  async handleCommitPast(interaction) {
    const modal = bannerUI.createCommitPastModal();
    await interaction.showModal(modal);
    return { handled: true, modal: true };
  }

  async handleSchedule(interaction) {
    const modal = bannerUI.createScheduleModal();
    await interaction.showModal(modal);
    return { handled: true, modal: true };
  }

  async handlePattern(interaction) {
    const modal = bannerUI.createPatternModal();
    await interaction.showModal(modal);
    return { handled: true, modal: true };
  }

  async handleStats(interaction) {
    const userId = interaction.user.id;
    const stats = sessionManager.getSessionStats(userId);

    const embed = new EmbedBuilder()
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
      .setFooter({ text: 'Use !showoptions to return to main menu' })
      .setTimestamp();

    await interaction.reply({ embeds: [embed], ephemeral: true });
    return { handled: true };
  }

  async handleRepo(interaction) {
    const modal = bannerUI.createRepoModal();
    await interaction.showModal(modal);
    return { handled: true, modal: true };
  }

  async handleJobs(interaction) {
    const userId = interaction.user.id;
    const jobs = schedulerService.listJobs({ ownerId: userId, limit: 10 });

    if (jobs.length === 0) {
      const embed = bannerUI.createInfoEmbed('📋 No Scheduled Jobs', 'You have no scheduled commit jobs. Use the Schedule button to create one!');
      await interaction.reply({ embeds: [embed], ephemeral: true });
      return { handled: true };
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

    await interaction.reply({ embeds: [embed], ephemeral: true });
    return { handled: true };
  }

  async handleHelp(interaction) {
    const embed = bannerUI.createFeaturesListEmbed();
    const row = new ActionRowBuilder()
      .addComponents(
        new ButtonBuilder()
          .setCustomId('btn_back')
          .setLabel('⬅️ Back to Menu')
          .setStyle(ButtonStyle.Secondary)
      );

    await interaction.reply({ embeds: [embed], components: [row], ephemeral: true });
    return { handled: true };
  }

  async handleBack(interaction) {
    return { handled: true, showBanner: true };
  }

  async handleModalSubmit(interaction) {
    const customId = interaction.customId;

    if (customId === 'modal_commit_now') {
      await this.processCommitNow(interaction);
    } else if (customId === 'modal_commit_past') {
      await this.processCommitPast(interaction);
    } else if (customId === 'modal_schedule') {
      await this.processSchedule(interaction);
    } else if (customId === 'modal_pattern') {
      await this.processPattern(interaction);
    } else if (customId === 'modal_repo') {
      await this.processRepo(interaction);
    }

    return { handled: true };
  }

  async processCommitNow(interaction) {
    const message = interaction.fields.getTextInputValue('commit_message');
    const pushStr = interaction.fields.getTextInputValue('push_remote');
    const push = pushStr.toLowerCase() !== 'false';

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'))], ephemeral: true });
      return;
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Initialization Failed', error.message)], ephemeral: true });
      return;
    }

    const result = await githubConnector.createCommit(message, new Date().toISOString(), { push });

    if (result.success) {
      const session = sessionManager.getActiveSession(interaction.user.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message, type: 'normal', success: true });
      }
      await interaction.reply({ 
        embeds: [bannerUI.createSuccessEmbed('Commit Created', `Successfully created commit: "${message}"`, [
          { name: '📅 Timestamp', value: new Date().toISOString(), inline: true },
          { name: '📤 Pushed', value: result.pushed ? 'Yes' : 'No', inline: true }
        ])], 
        ephemeral: true 
      });
    } else {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Commit Failed', `Error: ${result.error}`)], ephemeral: true });
    }
  }

  async processCommitPast(interaction) {
    const dateInput = interaction.fields.getTextInputValue('commit_date');
    const timeInput = interaction.fields.getTextInputValue('commit_time');
    const message = interaction.fields.getTextInputValue('commit_message');

    let timestamp;
    try {
      const datePart = timeInput ? `${dateInput} ${timeInput}` : dateInput;
      const validation = timestampProcessor.validate(datePart);
      if (!validation.valid) {
        await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Invalid Date', validation.error)], ephemeral: true });
        return;
      }
      timestamp = timestampProcessor.toISOString(validation.parsed);
    } catch (error) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Date Parsing Error', error.message)], ephemeral: true });
      return;
    }

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'))], ephemeral: true });
      return;
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Initialization Failed', error.message)], ephemeral: true });
      return;
    }

    const result = await githubConnector.createCommit(message, timestamp);

    if (result.success) {
      const session = sessionManager.getActiveSession(interaction.user.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message, type: 'backdated', success: true });
      }
      await interaction.reply({ 
        embeds: [bannerUI.createSuccessEmbed('Backdated Commit Created', `Successfully created commit: "${message}"`, [
          { name: '📅 Commit Date', value: new Date(timestamp).toLocaleString(), inline: true },
          { name: '🔢 Timestamp', value: timestamp, inline: true }
        ])], 
        ephemeral: true 
      });
    } else {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Commit Failed', `Error: ${result.error}`)], ephemeral: true });
    }
  }

  async processSchedule(interaction) {
    const cronExpr = interaction.fields.getTextInputValue('cron_expr');
    const message = interaction.fields.getTextInputValue('commit_message');

    if (!schedulerService.validateCronExpression(cronExpr)) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Invalid Cron', 'Please provide a valid cron expression. Example: 0 9 * * 1')], ephemeral: true });
      return;
    }

    const result = schedulerService.createJob(interaction.user.id, cronExpr, message);

    if (result.success) {
      const session = sessionManager.getActiveSession(interaction.user.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message, type: 'scheduled', success: true });
      }
      await interaction.reply({ 
        embeds: [bannerUI.createSuccessEmbed('Schedule Created', `Scheduled commit: "${message}"`, [
          { name: '🆔 Job ID', value: result.job.id, inline: true },
          { name: '⏰ Schedule', value: cronExpr, inline: true },
          { name: '📊 Status', value: result.job.status, inline: true }
        ])], 
        ephemeral: true 
      });
    } else {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Schedule Failed', result.error)], ephemeral: true });
    }
  }

  async processPattern(interaction) {
    const template = interaction.fields.getTextInputValue('pattern_template');
    const message = interaction.fields.getTextInputValue('commit_message');
    const startWeekStr = interaction.fields.getTextInputValue('start_week');
    const startWeek = startWeekStr ? parseInt(startWeekStr) : 0;

    const preview = patternEngine.previewPattern(template);
    if (!preview.success) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Template Error', preview.error)], ephemeral: true });
      return;
    }

    const validation = githubConnector.validateConfig();
    if (!validation.valid) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Configuration Error', validation.errors.join('\n'))], ephemeral: true });
      return;
    }

    try {
      await githubConnector.initialize();
    } catch (error) {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Initialization Failed', error.message)], ephemeral: true });
      return;
    }

    const result = await patternEngine.executePattern(template, message, { startWeek, push: true, delayBetweenCommits: 1000 });

    if (result.success) {
      const session = sessionManager.getActiveSession(interaction.user.id);
      if (session) {
        sessionManager.addCommitToSession(session.id, { message: `Pattern: ${template}`, type: 'pattern', success: true });
      }
      await interaction.reply({ 
        embeds: [bannerUI.createSuccessEmbed('Pattern Commits Complete', `Created ${result.succeeded} commits using ${template} pattern`, [
          { name: '📊 Summary', value: `Succeeded: ${result.succeeded}, Failed: ${result.failed}`, inline: true }
        ])], 
        ephemeral: true 
      });
    } else {
      await interaction.reply({ embeds: [bannerUI.createErrorEmbed('Pattern Failed', `Succeeded: ${result.succeeded}, Failed: ${result.failed}`)], ephemeral: true });
    }
  }

  async processRepo(interaction) {
    const repoType = interaction.fields.getTextInputValue('repo_type').toLowerCase();
    const repoPath = interaction.fields.getTextInputValue('repo_path');
    const branch = interaction.fields.getTextInputValue('repo_branch') || 'main';

    if (repoType === 'github') {
      githubConnector.configure({
        repoPath: `./${repoPath.replace('/', '-')}`,
        remote: 'origin',
        branch: branch
      });
    } else {
      githubConnector.configure({
        repoPath: repoPath,
        remote: 'origin',
        branch: branch
      });
    }

    await interaction.reply({ 
      embeds: [bannerUI.createSuccessEmbed('Repository Configured', `Repository set to: ${repoPath}`, [
        { name: '📁 Path/URL', value: repoPath, inline: true },
        { name: '🌿 Branch', value: branch, inline: true }
      ])], 
      ephemeral: true 
    });
  }
}

const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
module.exports = new ButtonHandler();