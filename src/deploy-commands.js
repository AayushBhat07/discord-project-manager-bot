require('dotenv').config();
const { REST, Routes } = require('discord.js');
const path = require('path');
const fs = require('fs');

const commands = [];

function loadCommands(dir) {
  if (!fs.existsSync(dir)) {
    console.log(`Commands directory not found: ${dir}`);
    return;
  }

  const files = fs.readdirSync(dir).filter(file => file.endsWith('.js'));
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const command = require(filePath);
    
    if (Array.isArray(command)) {
      commands.push(...command.map(cmd => cmd.data));
    } else if (command.data) {
      commands.push(command.data);
    }
  }
}

const commandsDir = path.join(__dirname, 'commands');
loadCommands(commandsDir);

const REST_API = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN);

const CLIENT_ID = process.env.CLIENT_ID;
const GUILD_ID = process.env.GUILD_ID;

async function deployCommands() {
  try {
    console.log(`Deploying ${commands.length} commands...`);
    
    if (GUILD_ID) {
      await REST_API.put(
        Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID),
        { body: commands }
      );
      console.log(`Successfully deployed commands to guild ${GUILD_ID}`);
    } else {
      await REST_API.put(
        Routes.applicationCommands(CLIENT_ID),
        { body: commands }
      );
      console.log('Successfully deployed global commands');
    }
  } catch (error) {
    console.error('Failed to deploy commands:', error);
    process.exit(1);
  }
}

deployCommands();