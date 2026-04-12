require('dotenv').config();
const { Client, GatewayIntentBits, Collection, EmbedBuilder } = require('discord.js');
const path = require('path');
const fs = require('fs');
const commitScheduler = require('./modules/commitScheduler');
const sessionManager = require('./modules/sessionManager');
const bannerUI = require('./modules/bannerUI');
const buttonHandler = require('./modules/buttonHandler');
const cliHandler = require('./modules/cliHandler');
const tempRepoManager = require('./modules/tempRepoManager');
const aiHandler = require('./modules/aiHandler');
const userConfigManager = require('./modules/userConfigManager');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

client.commands = new Collection();

function loadCommands(dir) {
  const commands = [];
  
  if (!fs.existsSync(dir)) {
    console.log(`Commands directory not found: ${dir}`);
    return commands;
  }

  const files = fs.readdirSync(dir).filter(file => file.endsWith('.js'));
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const command = require(filePath);
    
    if (Array.isArray(command)) {
      commands.push(...command);
    } else if (command.data && command.execute) {
      commands.push(command);
    }
  }

  return commands;
}

async function registerCommands() {
  const commandsDir = path.join(__dirname, 'commands');
  const commandFiles = fs.readdirSync(commandsDir).filter(f => f.endsWith('.js'));

  for (const file of commandFiles) {
    const command = require(path.join(commandsDir, file));
    const commands = Array.isArray(command) ? command : [command];
    
    for (const cmd of commands) {
      client.commands.set(cmd.data.name, cmd);
      console.log(`Loaded command: ${cmd.data.name}`);
    }
  }
}

const GUILD_ID = process.env.GUILD_ID;
const CLIENT_ID = process.env.CLIENT_ID;
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const TARGET_REPO_PATH = process.env.TARGET_REPO_PATH || './repo';
const TARGET_REPO_BRANCH = process.env.TARGET_REPO_BRANCH || 'main';
const TARGET_REPO_REMOTE = process.env.TARGET_REPO_REMOTE || 'origin';

client.once('ready', async () => {
  console.log(`✅ Logged in as ${client.user.tag}`);
  
  await registerCommands();
  
  const jobsStorePath = path.join(__dirname, 'store', 'commitJobs.json');
  commitScheduler.schedulerService.initialize(jobsStorePath, {
    maxJobs: parseInt(process.env.MAX_SCHEDULED_JOBS) || 50,
    maxJobsPerUser: parseInt(process.env.MAX_JOBS_PER_USER) || 10
  });
  
  const sessionsStorePath = path.join(__dirname, 'store', 'sessions.json');
  sessionManager.initialize(sessionsStorePath, {
    retentionDays: 30
  });
  
  tempRepoManager.initialize({
    tempRepoPath: path.join(process.cwd(), 'TEMP_REPO')
  });
  
  commitScheduler.githubConnector.configure({
    repoPath: TARGET_REPO_PATH,
    branch: TARGET_REPO_BRANCH,
    remote: TARGET_REPO_REMOTE,
    pat: process.env.GITHUB_PAT
  });

  console.log('✅ Commit Scheduler module initialized');
  console.log('✅ Session Manager initialized (30-day retention)');
  console.log('✅ TEMP Repo Manager initialized');
  console.log('✅ CLI Handler ready');
  console.log('✅ Banner UI ready');
  
  setInterval(() => {
    sessionManager.cleanExpiredSessions();
  }, 24 * 60 * 60 * 1000);
  
  setInterval(() => {
    sessionManager.cleanupInactiveSessions();
    userConfigManager.cleanupInactiveUsers();
  }, 60 * 60 * 1000); // Every hour
});

client.on('interactionCreate', async (interaction) => {
  if (interaction.isModalSubmit()) {
    await buttonHandler.handleModalSubmit(interaction);
    return;
  }

  if (interaction.isButton()) {
    const result = buttonHandler.handle(interaction.customId, interaction);
    
    if (result.showBanner) {
      const embed = bannerUI.createMainBanner(interaction.user.username);
      const buttons = bannerUI.createFeatureButtons();
      await interaction.update({ embeds: [embed], components: buttons });
    }
    return;
  }

  if (!interaction.isCommand()) return;

  const command = client.commands.get(interaction.commandName);
  
  if (!command) return;

  try {
    await command.execute(interaction);
  } catch (error) {
    console.error('Command error:', error);
    
    const errorEmbed = new EmbedBuilder()
      .setColor(0xff0000)
      .setTitle('❌ Command Error')
      .setDescription(error.message)
      .setTimestamp();

    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({ embeds: [errorEmbed], ephemeral: true });
    } else {
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
    }
  }
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  
  if (!message.content.startsWith('!')) return;

  const userId = message.author.id;
  let session = sessionManager.getActiveSession(userId);
  
  if (!session) {
    session = sessionManager.createSession(userId, message.author.username, {
      repoPath: TARGET_REPO_PATH,
      repoRemote: TARGET_REPO_REMOTE,
      branch: TARGET_REPO_BRANCH
    });
    
    const welcomeEmbed = bannerUI.createMainBanner(message.author.username);
    const buttons = bannerUI.createFeatureButtons();
    
    await message.channel.send({ 
      content: `🎉 **New session started!** ${message.author.username}`,
      embeds: [welcomeEmbed],
      components: buttons
    });
    return;
  }

  const result = await cliHandler.handle(message);
  
  if (result) {
    if (result.embeds && result.components) {
      await message.channel.send({ embeds: result.embeds, components: result.components });
    } else if (result.embeds) {
      await message.channel.send({ embeds: [result] });
    }
  }
});

if (!DISCORD_TOKEN) {
  console.error('Error: DISCORD_TOKEN not found in .env');
  console.log('Please copy .env.example to .env and add your Discord bot token');
  process.exit(1);
}

client.login(DISCORD_TOKEN);

module.exports = { client, commitScheduler, sessionManager, bannerUI, buttonHandler, cliHandler, tempRepoManager };