const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

class BannerUI {
  constructor() {
    this.features = this.initializeFeatures();
  }

  initializeFeatures() {
    return [
      {
        id: 'commit_now',
        name: '🚀 Commit Now',
        emoji: '🚀',
        color: '#00ff00',
        description: 'Create an immediate commit with current timestamp',
        cliCommand: '!commitnow <message>',
        guiButton: 'Commit Now',
        usage: '!commitnow "Your commit message"',
        longDescription: 'Creates a GitHub commit instantly with your current timestamp and pushes to the configured repository.'
      },
      {
        id: 'commit_past',
        name: '⏰ Commit in Past',
        emoji: '⏰',
        color: '#ff9900',
        description: 'Create a backdated commit for any past date',
        cliCommand: '!commitpast <date> <time> <message>',
        guiButton: 'Commit in Past',
        usage: '!commitpast 2024-01-15 14:30 "Your message"',
        longDescription: 'Create commits with any past timestamp. Perfect for documenting work that was done earlier. Supports various date formats including relative dates like "yesterday" or "3 days ago".'
      },
      {
        id: 'commit_schedule',
        name: '📅 Schedule Commits',
        emoji: '📅',
        color: '#0099ff',
        description: 'Set up recurring commits with cron expressions',
        cliCommand: '!schedule <cron> <message>',
        guiButton: 'Schedule',
        usage: '!schedule "0 9 * * 1" "Weekly update"',
        longDescription: 'Automate your commit workflow by scheduling recurring commits. Uses standard cron expressions for flexible scheduling - daily, weekly, monthly, or custom intervals.'
      },
      {
        id: 'commit_pattern',
        name: '🎨 Pattern Art',
        emoji: '🎨',
        color: '#ff00ff',
        description: 'Generate contribution graph patterns',
        cliCommand: '!pattern <template> <message>',
        guiButton: 'Pattern',
        usage: '!pattern heart "contribution"',
        longDescription: 'Create beautiful contribution graph art with batch commits. Choose from templates like letters, shapes, and icons. Make your GitHub profile stand out!'
      },
      {
        id: 'session_manager',
        name: '📊 Session Stats',
        emoji: '📊',
        color: '#00ccff',
        description: 'View your session history and statistics',
        cliCommand: '!mystats',
        guiButton: 'My Stats',
        usage: '!mystats',
        longDescription: 'Track your commit activity across sessions. View total commits, backdated commits, scheduled jobs, and more. Sessions are stored for 30 days.'
      },
      {
        id: 'repo_manager',
        name: '📁 Repository',
        emoji: '📁',
        color: '#ffcc00',
        description: 'Configure your default repository',
        cliCommand: '!setrepo <path> or !setrepo github <owner/repo>',
        guiButton: 'Repository',
        usage: '!setrepo ./myrepo',
        longDescription: 'Set and manage your default repository for commits. You can use a local path or configure a GitHub repository by providing owner/repo format.'
      },
      {
        id: 'help',
        name: '❓ Help',
        emoji: '❓',
        color: '#ffffff',
        description: 'Show all available commands',
        cliCommand: '!help',
        guiButton: 'Help',
        usage: '!help or !detailed',
        longDescription: 'Get help with all available commands. Use !detailed for comprehensive information including examples and advanced usage.'
      },
      {
        id: 'cancel',
        name: '🛑 Cancel Job',
        emoji: '🛑',
        color: '#ff0000',
        description: 'Cancel a scheduled commit job',
        cliCommand: '!cancel <job-id>',
        guiButton: 'Cancel',
        usage: '!cancel abc-123',
        longDescription: 'Stop a scheduled commit job from running. Use !commits to see all your scheduled jobs and their IDs.'
      }
    ];
  }

  createMainBanner(userName) {
    const embed = new EmbedBuilder()
      .setTitle('🌟 Welcome to Commit Automation Hub! 🌟')
      .setDescription(`Hello **${userName}**! I'm your GitHub commit automation assistant. Interact with me using the buttons below or CLI commands.`)
      .setColor(0x5865F2)
      .setThumbnail('https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')
      .setFooter({ text: 'Use !showoptions to see this banner anytime | !detailed for full command info' })
      .setTimestamp();

    const featureFields = this.features.slice(0, 6).map(f => ({
      name: `${f.emoji} ${f.name}`,
      value: f.description,
      inline: true
    }));

    embed.addFields(featureFields);

    return embed;
  }

  createFeatureButtons() {
    const rows = [];
    
    const row1 = new ActionRowBuilder()
      .addComponents(
        new ButtonBuilder()
          .setCustomId('btn_commit_now')
          .setLabel('🚀 Commit Now')
          .setStyle(ButtonStyle.Success),
        new ButtonBuilder()
          .setCustomId('btn_commit_past')
          .setLabel('⏰ Commit in Past')
          .setStyle(ButtonStyle.Primary),
        new ButtonBuilder()
          .setCustomId('btn_commit_schedule')
          .setLabel('📅 Schedule')
          .setStyle(ButtonStyle.Primary),
        new ButtonBuilder()
          .setCustomId('btn_pattern')
          .setLabel('🎨 Pattern')
          .setStyle(ButtonStyle.Secondary)
      );

    const row2 = new ActionRowBuilder()
      .addComponents(
        new ButtonBuilder()
          .setCustomId('btn_stats')
          .setLabel('📊 My Stats')
          .setStyle(ButtonStyle.Secondary),
        new ButtonBuilder()
          .setCustomId('btn_repo')
          .setLabel('📁 Repository')
          .setStyle(ButtonStyle.Secondary),
        new ButtonBuilder()
          .setCustomId('btn_commits')
          .setLabel('📋 My Jobs')
          .setStyle(ButtonStyle.Secondary),
        new ButtonBuilder()
          .setCustomId('btn_help')
          .setLabel('❓ Help')
          .setStyle(ButtonStyle.Secondary)
      );

    rows.push(row1, row2);

    return rows;
  }

  createFeatureDetailEmbed(featureId) {
    const feature = this.features.find(f => f.id === featureId);
    if (!feature) return null;

    return new EmbedBuilder()
      .setTitle(`${feature.emoji} ${feature.name}`)
      .setDescription(feature.longDescription)
      .setColor(feature.color)
      .addFields(
        { name: '📝 Description', value: feature.description, inline: false },
        { name: '⌨️ CLI Command', value: `\`${feature.cliCommand}\``, inline: false },
        { name: '💡 Usage Example', value: feature.usage, inline: false },
        { name: '🖱️ GUI Button', value: feature.guiButton, inline: false }
      )
      .setFooter({ text: 'Use !showoptions to return to main menu' })
      .setTimestamp();
  }

  createDetailedHelpEmbed() {
    const embed = new EmbedBuilder()
      .setTitle('📚 Complete Command Reference')
      .setDescription('All available commands with detailed descriptions and usage examples')
      .setColor(0x5865F2)
      .setTimestamp();

    const cliCommands = this.features.map(f => ({
      name: `⌨️ ${f.name}`,
      value: `**CLI:** \`${f.cliCommand}\`\n**Usage:** ${f.usage}`,
      inline: false
    }));

    embed.addFields(...cliCommands);

    return embed;
  }

  createFeaturesListEmbed() {
    const embed = new EmbedBuilder()
      .setTitle('🎯 All Features')
      .setDescription('Complete list of all available features')
      .setColor(0x5865F2)
      .setTimestamp();

    this.features.forEach((f, index) => {
      embed.addFields({
        name: `${index + 1}. ${f.emoji} ${f.name}`,
        value: f.description,
        inline: false
      });
    });

    return embed;
  }

  createModal(title, customId, inputs) {
    const { ModalBuilder, TextInputBuilder, TextInputStyle } = require('discord.js');
    
    const modal = new ModalBuilder()
      .setTitle(title)
      .setCustomId(customId);

    const actionRows = inputs.map(input => {
      return new ActionRowBuilder()
        .addComponents(
          new TextInputBuilder()
            .setLabel(input.label)
            .setCustomId(input.customId)
            .setStyle(input.style || TextInputStyle.Short)
            .setPlaceholder(input.placeholder || '')
            .setRequired(input.required !== false)
        );
    });

    modal.addComponents(actionRows);

    return modal;
  }

  createCommitNowModal() {
    return this.createModal('🚀 Create Immediate Commit', 'modal_commit_now', [
      { label: 'Commit Message', customId: 'commit_message', style: 'PARAGRAPH', placeholder: 'Enter your commit message...', required: true },
      { label: 'Push to Remote?', customId: 'push_remote', style: 'SHORT', placeholder: 'true or false (default: true)', required: false }
    ]);
  }

  createCommitPastModal() {
    return this.createModal('⏰ Create Backdated Commit', 'modal_commit_past', [
      { label: 'Date', customId: 'commit_date', style: 'SHORT', placeholder: 'YYYY-MM-DD, yesterday, 3 days ago', required: true },
      { label: 'Time (optional)', customId: 'commit_time', style: 'SHORT', placeholder: 'HH:mm or HH:mm:ss', required: false },
      { label: 'Commit Message', customId: 'commit_message', style: 'PARAGRAPH', placeholder: 'Enter your commit message...', required: true }
    ]);
  }

  createScheduleModal() {
    return this.createModal('📅 Schedule Recurring Commit', 'modal_schedule', [
      { label: 'Cron Expression', customId: 'cron_expr', style: 'SHORT', placeholder: '0 9 * * 1 (every Monday 9am)', required: true },
      { label: 'Commit Message', customId: 'commit_message', style: 'PARAGRAPH', placeholder: 'Message for each scheduled commit...', required: true }
    ]);
  }

  createPatternModal() {
    return this.createModal('🎨 Generate Pattern', 'modal_pattern', [
      { label: 'Template', customId: 'pattern_template', style: 'SHORT', placeholder: 'A, B, heart, star, check, smiley', required: true },
      { label: 'Commit Message', customId: 'commit_message', style: 'PARAGRAPH', placeholder: 'Message for pattern commits...', required: true },
      { label: 'Start Week (0-52)', customId: 'start_week', style: 'SHORT', placeholder: 'Optional: 0-52', required: false }
    ]);
  }

  createRepoModal() {
    return this.createModal('📁 Configure Repository', 'modal_repo', [
      { label: 'Repository Type', customId: 'repo_type', style: 'SHORT', placeholder: 'local or github', required: true },
      { label: 'Repository Path/URL', customId: 'repo_path', style: 'SHORT', placeholder: './repo or owner/repo', required: true },
      { label: 'Branch Name', customId: 'repo_branch', style: 'SHORT', placeholder: 'main (default)', required: false }
    ]);
  }

  createSuccessEmbed(title, description, fields = []) {
    return new EmbedBuilder()
      .setTitle(`✅ ${title}`)
      .setDescription(description)
      .setColor(0x00ff00)
      .addFields(fields)
      .setTimestamp();
  }

  createErrorEmbed(title, description, fields = []) {
    return new EmbedBuilder()
      .setTitle(`❌ ${title}`)
      .setDescription(description)
      .setColor(0xff0000)
      .addFields(fields)
      .setTimestamp();
  }

  createInfoEmbed(title, description, fields = []) {
    return new EmbedBuilder()
      .setTitle(`ℹ️ ${title}`)
      .setDescription(description)
      .setColor(0x0099ff)
      .addFields(fields)
      .setTimestamp();
  }
}

module.exports = new BannerUI();