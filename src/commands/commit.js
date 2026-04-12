const { SlashCommandBuilder, SlashCommandSubcommandGroupBuilder, SlashCommandSubcommandBuilder } = require('discord.js');

module.exports = [
  {
    data: new SlashCommandBuilder()
      .setName('commit')
      .setDescription('GitHub commit automation commands')
      .addSubcommand(subcommand =>
        subcommand.setName('now')
          .setDescription('Create a commit with the current timestamp')
          .addStringOption(option =>
            option.setName('message')
              .setDescription('The commit message')
              .setRequired(true)
          )
          .addBooleanOption(option =>
            option.setName('push')
              .setDescription('Push to remote after commit? (default: true)')
              .setRequired(false)
          )
      )
      .addSubcommand(subcommand =>
        subcommand.setName('at')
          .setDescription('Create a commit with a specific timestamp')
          .addStringOption(option =>
            option.setName('date')
              .setDescription('Date (YYYY-MM-DD, "yesterday", "3 days ago")')
              .setRequired(true)
          )
          .addStringOption(option =>
            option.setName('time')
              .setDescription('Time (HH:mm or HH:mm:ss) - optional')
              .setRequired(false)
          )
          .addStringOption(option =>
            option.setName('message')
              .setDescription('The commit message')
              .setRequired(true)
          )
      )
      .addSubcommand(subcommand =>
        subcommand.setName('schedule')
          .setDescription('Schedule recurring commits')
          .addStringOption(option =>
            option.setName('cron')
              .setDescription('Cron expression (e.g., "0 9 * * 1" for Monday 9am)')
              .setRequired(true)
          )
          .addStringOption(option =>
            option.setName('message')
              .setDescription('The commit message for each scheduled commit')
              .setRequired(true)
          )
      )
      .addSubcommand(subcommand =>
        subcommand.setName('cancel')
          .setDescription('Cancel a scheduled commit job')
          .addStringOption(option =>
            option.setName('job-id')
              .setDescription('The Job ID to cancel')
              .setRequired(true)
          )
      )
      .addSubcommand(subcommand =>
        subcommand.setName('log')
          .setDescription('View all scheduled commit jobs')
          .addIntegerOption(option =>
            option.setName('page')
              .setDescription('Page number (default: 1)')
              .setRequired(false)
          )
          .addStringOption(option =>
            option.setName('status')
              .setDescription('Filter by status')
              .setRequired(false)
              .addChoices(
                { name: 'Active', value: 'active' },
                { name: 'Paused', value: 'paused' },
                { name: 'Cancelled', value: 'cancelled' }
              )
          )
      )
      .addSubcommand(subcommand =>
        subcommand.setName('pattern')
          .setDescription('Generate batch commits for GitHub contribution graph patterns')
          .addStringOption(option =>
            option.setName('template')
              .setDescription('Pattern template to use')
              .setRequired(true)
              .addChoices(
                { name: 'Letter A', value: 'A' },
                { name: 'Letter B', value: 'B' },
                { name: 'Letter C', value: 'C' },
                { name: 'Heart', value: 'heart' },
                { name: 'Star', value: 'star' },
                { name: 'Check', value: 'check' },
                { name: 'Smiley', value: 'smiley' }
              )
          )
          .addStringOption(option =>
            option.setName('message')
              .setDescription('Base commit message')
              .setRequired(true)
          )
          .addIntegerOption(option =>
            option.setName('start-week')
              .setDescription('Starting week offset (0-52)')
              .setRequired(false)
          )
          .addIntegerOption(option =>
            option.setName('start-day')
              .setDescription('Starting day (0=Sunday, 6=Saturday)')
              .setRequired(false)
          )
          .addBooleanOption(option =>
            option.setName('preview-only')
              .setDescription('Only show preview without committing')
              .setRequired(false)
          )
      ),
    async execute(interaction) {
      const subcommand = interaction.options.getSubcommand();
      const { commitScheduler } = require('../modules/commitScheduler');
      const githubConnector = commitScheduler.githubConnector;
      const timestampProcessor = commitScheduler.timestampProcessor;
      const schedulerService = commitScheduler.schedulerService;
      const patternEngine = commitScheduler.patternEngine;

      switch (subcommand) {
        case 'now': {
          await interaction.deferReply({ ephemeral: true });
          const message = interaction.options.getString('message');
          const shouldPush = interaction.options.getBoolean('push') ?? true;

          const validation = githubConnector.validateConfig();
          if (!validation.valid) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Configuration Error',
                description: validation.errors.join('\n')
              }]
            });
          }

          try {
            await githubConnector.initialize();
          } catch (error) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Initialization Failed',
                description: error.message
              }]
            });
          }

          const result = await githubConnector.createCommit(message, new Date().toISOString(), { push: shouldPush });

          if (result.success) {
            return interaction.editReply({
              embeds: [{
                color: 0x00ff00,
                title: '✅ Commit Created',
                description: message,
                fields: [
                  { name: '📅 Timestamp', value: new Date().toISOString(), inline: true },
                  { name: '📤 Pushed', value: result.pushed ? 'Yes' : 'No', inline: true }
                ],
                timestamp: new Date()
              }]
            });
          } else {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Commit Failed',
                description: `Error at stage: ${result.stage}`,
                fields: [{ name: 'Error', value: result.error }],
                timestamp: new Date()
              }]
            });
          }
        }

        case 'at': {
          await interaction.deferReply({ ephemeral: true });
          const dateInput = interaction.options.getString('date');
          const timeInput = interaction.options.getString('time');
          const message = interaction.options.getString('message');

          let timestamp;
          try {
            const datePart = timeInput ? `${dateInput} ${timeInput}` : dateInput;
            const validation = timestampProcessor.validate(datePart);
            if (!validation.valid) {
              return interaction.editReply({
                embeds: [{
                  color: 0xff0000,
                  title: '⚠️ Invalid Date/Time',
                  description: validation.error
                }]
              });
            }
            timestamp = timestampProcessor.toISOString(validation.parsed);
          } catch (error) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Date Parsing Error',
                description: error.message
              }]
            });
          }

          const validation = githubConnector.validateConfig();
          if (!validation.valid) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Configuration Error',
                description: validation.errors.join('\n')
              }]
            });
          }

          try {
            await githubConnector.initialize();
          } catch (error) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Initialization Failed',
                description: error.message
              }]
            });
          }

          const result = await githubConnector.createCommit(message, timestamp);
          const commitDate = new Date(timestamp);

          if (result.success) {
            return interaction.editReply({
              embeds: [{
                color: 0x00ff00,
                title: '✅ Backdated Commit Created',
                description: message,
                fields: [
                  { name: '📅 Commit Date', value: commitDate.toLocaleString(), inline: true },
                  { name: '📤 Pushed', value: result.pushed ? 'Yes' : 'No', inline: true }
                ],
                timestamp: new Date()
              }]
            });
          } else {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Commit Failed',
                description: `Error at stage: ${result.stage}`,
                fields: [{ name: 'Error', value: result.error }],
                timestamp: new Date()
              }]
            });
          }
        }

        case 'schedule': {
          await interaction.deferReply({ ephemeral: true });
          const cronExpression = interaction.options.getString('cron');
          const message = interaction.options.getString('message');

          if (!schedulerService.validateCronExpression(cronExpression)) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Invalid Cron Expression',
                description: 'Please provide a valid cron expression'
              }]
            });
          }

          const validation = githubConnector.validateConfig();
          if (!validation.valid) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Configuration Error',
                description: validation.errors.join('\n')
              }]
            });
          }

          const ownerId = interaction.user.id;
          const result = schedulerService.createJob(ownerId, cronExpression, message);

          if (!result.success) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Failed to Create Schedule',
                description: result.error
              }]
            });
          }

          const job = result.job;
          return interaction.editReply({
            embeds: [{
              color: 0x00ff00,
              title: '✅ Schedule Created',
              description: `Commit scheduled: "${message}"`,
              fields: [
                { name: '🆔 Job ID', value: job.id, inline: true },
                { name: '⏰ Schedule', value: cronExpression, inline: true },
                { name: '📊 Status', value: job.status, inline: true }
              ],
              footer: { text: 'Use /commit cancel with this Job ID to stop' },
              timestamp: new Date()
            }]
          });
        }

        case 'cancel': {
          await interaction.deferReply({ ephemeral: true });
          const jobId = interaction.options.getString('job-id');
          const job = schedulerService.getJob(jobId);

          if (!job) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Job Not Found',
                description: `No scheduled job found with ID: ${jobId}`,
                fields: [{ name: 'Tip', value: 'Use /commit log to see all jobs' }]
              }]
            });
          }

          if (job.ownerId !== interaction.user.id) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Permission Denied',
                description: 'You can only cancel jobs you created'
              }]
            });
          }

          const result = schedulerService.cancelJob(jobId);
          return interaction.editReply({
            embeds: [{
              color: 0x00ff00,
              title: '✅ Schedule Cancelled',
              description: `Job ${jobId} has been stopped`,
              fields: [
                { name: 'Message', value: job.message, inline: true },
                { name: 'Cron', value: job.cronExpression, inline: true }
              ],
              timestamp: new Date()
            }]
          });
        }

        case 'log': {
          await interaction.deferReply({ ephemeral: true });
          const page = interaction.options.getInteger('page') || 1;
          const statusFilter = interaction.options.getString('status');
          const userId = interaction.user.id;

          const jobs = schedulerService.listJobs({
            ownerId: userId,
            status: statusFilter,
            limit: 10
          });

          if (jobs.length === 0) {
            return interaction.editReply({
              embeds: [{
                color: 0xffaa00,
                title: '📋 No Scheduled Jobs',
                description: 'You have no scheduled commit jobs',
                fields: [{ name: 'Create', value: 'Use /commit schedule to create one' }]
              }]
            });
          }

          const jobFields = jobs.map(job => ({
            name: `🆔 ${job.id.substring(0, 8)}...`,
            value: [
              `**Message:** ${job.message}`,
              `**Schedule:** \`${job.cronExpression}\``,
              `**Status:** ${job.status}`,
              `**Next:** ${job.nextRun ? new Date(job.nextRun).toLocaleString() : 'N/A'}`
            ].join('\n')
          }));

          return interaction.editReply({
            embeds: [{
              color: 0x00ff00,
              title: '📋 Scheduled Commit Jobs',
              description: `Showing ${jobs.length} job(s)`,
              fields: jobFields,
              timestamp: new Date()
            }]
          });
        }

        case 'pattern': {
          await interaction.deferReply({ ephemeral: true });
          const templateName = interaction.options.getString('template');
          const message = interaction.options.getString('message');
          const startWeek = interaction.options.getInteger('start-week') || 0;
          const startDay = interaction.options.getInteger('start-day') || 0;
          const previewOnly = interaction.options.getBoolean('preview-only') ?? false;

          const preview = patternEngine.previewPattern(templateName);
          if (!preview.success) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Template Error',
                description: preview.error
              }]
            });
          }

          const coords = patternEngine.generatePatternCoordinates(templateName, { startWeek, startDay });

          if (previewOnly) {
            return interaction.editReply({
              embeds: [{
                color: 0x00ff00,
                title: `🔲 Pattern Preview: ${preview.template}`,
                description: `\`\`\`\n${preview.preview}\n\`\`\``,
                fields: [
                  { name: '📐 Dimensions', value: preview.dimensions, inline: true },
                  { name: '📊 Cells', value: preview.cellCount, inline: true }
                ],
                timestamp: new Date()
              }]
            });
          }

          const validation = githubConnector.validateConfig();
          if (!validation.valid) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '⚠️ Configuration Error',
                description: validation.errors.join('\n')
              }]
            });
          }

          try {
            await githubConnector.initialize();
          } catch (error) {
            return interaction.editReply({
              embeds: [{
                color: 0xff0000,
                title: '❌ Initialization Failed',
                description: error.message
              }]
            });
          }

          const result = await patternEngine.executePattern(templateName, message, {
            startWeek,
            startDay,
            push: true,
            delayBetweenCommits: 1000
          });

          if (result.success) {
            return interaction.editReply({
              embeds: [{
                color: 0x00ff00,
                title: `✅ Pattern Commits Complete`,
                description: `Created ${result.succeeded} commits`,
                fields: [
                  { name: '📊 Summary', value: `Succeeded: ${result.succeeded}\nFailed: ${result.failed}`, inline: true }
                ],
                timestamp: new Date()
              }]
            });
          } else {
            return interaction.editReply({
              embeds: [{
                color: 0xffaa00,
                title: '⚠️ Partially Complete',
                description: `Succeeded: ${result.succeeded}, Failed: ${result.failed}`,
                timestamp: new Date()
              }]
            });
          }
        }

        default:
          return interaction.editReply({ content: 'Unknown subcommand' });
      }
    }
  }
];